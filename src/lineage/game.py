"""Pygame front end for the Lineage domestication prototype.

Controls
  Space        pause / resume
  1 2 3 4      game speed
  WASD/arrows  pan        mouse wheel  zoom      right-drag  pan
  Left click   inspect an animal or person; click sidebar controls
  H            help        F3  show the hidden numbers      R  new world
"""

import math
import sys

import pygame

from . import observe
from .config import DAYS_PER_YEAR, MAX_STEP, PEN_CAPACITY, PEN_BUILD_DAYS
from .sim import Simulation, _dist
from .species import SPECIES
from .world import FOREST, GRASS, HILLS, SHORE, WATER

SIDEBAR_W = 360
SPEEDS = (1.0, 3.0, 10.0, 30.0)          # game days per real second
ZOOMS = (4, 5, 6, 8, 10, 12, 16, 20)

# ---------------------------------------------------------------- palette
BG = (24, 26, 30)
PANEL = (32, 35, 41)
PANEL_HI = (44, 48, 56)
TEXT = (226, 228, 232)
DIM = (150, 156, 166)
ACCENT = (232, 176, 92)
GOOD = (130, 196, 120)
BAD = (222, 112, 100)
LINE = (60, 64, 74)

ROLE_COLOR = {"gather": (120, 200, 110), "hunt": (226, 96, 80), "herd": (96, 150, 230),
              "camp": None, "child": None}

POLICY_ROWS = [
    ("waste", "Scraps & bones",
     [("camp", "Midden by camp"), ("far", "Midden far off"), ("burn", "Burn them")],
     "Where your people throw food scraps. A midden by camp feeds scavengers right "
     "beside you; far off, they eat without growing used to you; burning starves them."),
    ("scavengers", "Scavengers",
     [("tolerate", "Tolerate"), ("drive", "Drive off")],
     "Whether camp keepers chase off animals that come close. Driving them off kills "
     "the boldest, the very animals that might have stayed."),
    ("feeding", "Toss scraps",
     [(False, "No"), (True, "Yes")],
     "Camp keepers toss midden scraps to animals that come close without running."),
    ("grain", "Wild grain",
     [("fresh", "Eat fresh"), ("granary", "Store in granary")],
     "Grain from the riverbank. Fresh food rots; a granary keeps it through winter... "
     "and the mice will notice."),
    ("hunt_aurochs", "Aurochs",
     [("free", "Hunt freely"), ("cull", "Cull wild ones"), ("spare", "Spare"),
      ("capture", "Capture")],
     "Hunting freely takes the easiest (boldest) animals. Culling targets the wildest. "
     "Capture brings calm ones (usually the young) to a pen."),
    ("hunt_deer", "Red deer",
     [("free", "Hunt freely"), ("cull", "Cull wild ones"), ("spare", "Spare"),
      ("capture", "Capture")],
     "Deer are swift and plentiful. Whether they will tolerate a pen is another matter."),
    ("hunt_boar", "Wild boar",
     [("free", "Hunt freely"), ("cull", "Cull wild ones"), ("spare", "Spare"),
      ("capture", "Capture")],
     "Boar are fierce omnivores that also raid middens. Wounded boar fight back."),
    ("pen_cull", "Pen culling",
     [("calm", "Cull the wildest"), ("big", "Cull the smallest"), ("random", "Cull at random")],
     "Each autumn, and whenever the pen is overfull, your herders eat some animals. "
     "Which ones they choose shapes what the herd becomes."),
]

LABOR_ROWS = [("hunt", "Hunters"), ("herd", "Herders"), ("camp", "Camp keepers")]

HELP_TEXT = [
    "LINEAGE: a domestication prototype",
    "",
    "Your band has made camp in a river valley. There is no tech tree. Animals",
    "change because of how your people live, and each one's traits pass to its young.",
    "",
    "Leave scraps by camp and the boldest wolves may start hanging around. If the",
    "fierce ones get killed for biting and the tame ones thrive, their pups grow",
    "tamer still... Store grain and the mice move in; the cats may follow.",
    "Build a pen, capture calm young aurochs, and choose which ones you cull.",
    "",
    "You never see exact numbers, only what your people would notice (F3 shows them).",
    "",
    "Space pause · 1-4 speed · WASD/arrows/right-drag pan · wheel zoom",
    "Click an animal or person to inspect · H help · R new world",
    "",
    "Click or press any key to begin.",
]


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


class Button:
    def __init__(self, rect, action, tip=None):
        self.rect = pygame.Rect(rect)
        self.action = action
        self.tip = tip


class Game:
    def __init__(self, seed=None, size=(1360, 840)):
        pygame.init()
        pygame.display.set_caption("Lineage: domestication prototype")
        self.screen = pygame.display.set_mode(size, pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 20)
        self.font_sm = pygame.font.Font(None, 17)
        self.font_lg = pygame.font.Font(None, 30)
        self.font_xl = pygame.font.Font(None, 44)
        self.new_world(seed)
        self.show_help = True
        self.debug = False

    # -------------------------------------------------------------- setup
    def new_world(self, seed=None):
        self.sim = Simulation(seed)
        self.speed_i = 1
        self.paused = False
        self.zoom_i = ZOOMS.index(8)
        self.selected = None
        self.buttons = []
        self.hover_tip = None
        self._terrain_cache = None
        self._terrain_key = None
        self._drag = None
        self.center_on(*self.sim.camp)
        self.chron_seen = len(self.sim.chronicle)

    @property
    def tile(self):
        return ZOOMS[self.zoom_i]

    @property
    def map_rect(self):
        w, h = self.screen.get_size()
        return pygame.Rect(0, 0, max(200, w - SIDEBAR_W), h)

    def center_on(self, tx, ty):
        mr = self.map_rect
        self.cam_x = tx - mr.w / self.tile / 2
        self.cam_y = ty - mr.h / self.tile / 2
        self.clamp_cam()

    def clamp_cam(self):
        mr = self.map_rect
        w, h = self.sim.world.w, self.sim.world.h
        vw, vh = mr.w / self.tile, mr.h / self.tile
        # Centre the valley when it is smaller than the view.
        if vw >= w + 4:
            self.cam_x = (w - vw) / 2
        else:
            self.cam_x = min(max(self.cam_x, -2), w - vw + 2)
        if vh >= h + 4:
            self.cam_y = (h - vh) / 2
        else:
            self.cam_y = min(max(self.cam_y, -2), h - vh + 2)

    def to_screen(self, x, y):
        return (int((x - self.cam_x) * self.tile), int((y - self.cam_y) * self.tile))

    def to_world(self, sx, sy):
        return (sx / self.tile + self.cam_x, sy / self.tile + self.cam_y)

    # -------------------------------------------------------------- loop
    def run(self):
        while True:
            dt = self.clock.tick(60) / 1000.0
            if not self.handle_events():
                break
            self.update(min(dt, 0.1))
            self.draw()
            pygame.display.flip()
        pygame.quit()

    def update(self, dt):
        keys = pygame.key.get_pressed()
        pan = 30.0 * dt * 8 / self.tile
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.cam_x -= pan
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.cam_x += pan
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.cam_y -= pan
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.cam_y += pan
        self.clamp_cam()
        if self.show_help or self.paused or self.sim.game_over:
            return
        days = dt * SPEEDS[self.speed_i]
        budget = pygame.time.get_ticks() + 35   # ms of simulation per frame
        while days > 1e-9 and pygame.time.get_ticks() < budget:
            step = min(MAX_STEP, days)
            self.sim.step(step)
            days -= step
        if self.selected is not None and not getattr(self.selected, "alive", True):
            self.selected = None

    def handle_events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return False
            if ev.type == pygame.VIDEORESIZE:
                self._terrain_key = None
                self.clamp_cam()
            if ev.type == pygame.KEYDOWN:
                if self.show_help:
                    self.show_help = False
                    continue
                k = ev.key
                if k == pygame.K_ESCAPE:
                    if self.selected is not None:
                        self.selected = None
                    else:
                        return False
                elif k == pygame.K_SPACE:
                    self.paused = not self.paused
                elif k in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                    self.speed_i = k - pygame.K_1
                    self.paused = False
                elif k == pygame.K_h:
                    self.show_help = True
                elif k == pygame.K_F3:
                    self.debug = not self.debug
                elif k == pygame.K_r:
                    self.new_world()
                elif k == pygame.K_c:
                    self.center_on(*self.sim.camp)
                elif k in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                    self.zoom(1, None)
                elif k in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    self.zoom(-1, None)
            if ev.type == pygame.MOUSEBUTTONDOWN:
                if self.show_help:
                    self.show_help = False
                    continue
                if ev.button == 1:
                    self.click(ev.pos)
                elif ev.button == 3:
                    self._drag = (ev.pos, self.cam_x, self.cam_y)
            if ev.type == pygame.MOUSEBUTTONUP and ev.button == 3:
                self._drag = None
            if ev.type == pygame.MOUSEMOTION:
                if self._drag is not None:
                    (sx, sy), cx, cy = self._drag
                    self.cam_x = cx - (ev.pos[0] - sx) / self.tile
                    self.cam_y = cy - (ev.pos[1] - sy) / self.tile
                    self.clamp_cam()
            if ev.type == pygame.MOUSEWHEEL:
                mx, my = pygame.mouse.get_pos()
                if self.map_rect.collidepoint(mx, my):
                    self.zoom(1 if ev.y > 0 else -1, (mx, my))
        return True

    def zoom(self, direction, anchor):
        mr = self.map_rect
        if anchor is None:
            anchor = (mr.w // 2, mr.h // 2)
        wx, wy = self.to_world(*anchor)
        self.zoom_i = min(max(self.zoom_i + direction, 0), len(ZOOMS) - 1)
        self.cam_x = wx - anchor[0] / self.tile
        self.cam_y = wy - anchor[1] / self.tile
        self.clamp_cam()

    def click(self, pos):
        for b in self.buttons:
            if b.rect.collidepoint(pos):
                b.action()
                return
        if self.sim.game_over:
            self.new_world()
            return
        if not self.map_rect.collidepoint(pos):
            return
        wx, wy = self.to_world(*pos)
        best, bd = None, 1.6 * 8 / self.tile + 0.6
        for e in list(self.sim.humans) + list(self.sim.animals):
            d = _dist(wx, wy, e.x, e.y)
            if d < bd:
                best, bd = e, d
        self.selected = best

    # ------------------------------------------------------------- drawing
    def draw(self):
        self.buttons = []
        self.hover_tip = None
        self.screen.fill(BG)
        self.draw_map()
        self.draw_sidebar()
        self.draw_inspector()
        self.draw_hint_bar()
        if self.hover_tip:
            self.draw_tooltip(self.hover_tip)
        if self.sim.game_over:
            self.draw_game_over()
        if self.show_help:
            self.draw_help()

    def terrain_surface(self):
        sim = self.sim
        key = (sim.veg_version, sim.season, self.tile)
        if key == self._terrain_key:
            return self._terrain_cache
        w = sim.world
        surf = pygame.Surface((w.w, w.h))
        winter = sim.season == 3
        autumn = sim.season == 2
        for ty in range(w.h):
            for tx in range(w.w):
                i = ty * w.w + tx
                t = w.terrain[i]
                g = w.grass[i]
                f = w.forage[i]
                if t == WATER:
                    c = (52, 98, 148) if (tx + ty) % 7 else (60, 108, 158)
                elif t == FOREST:
                    c = lerp((34, 70, 42), (46, 92, 52), min(1.0, g * 2))
                    if f > 0.4 and not winter:
                        c = lerp(c, (110, 62, 96), (f - 0.4) * 0.5)
                elif t == HILLS:
                    c = lerp((120, 112, 96), (132, 140, 104), g)
                elif t == SHORE:
                    c = lerp((150, 140, 96), (104, 156, 82), g)
                    if f > 0.3 and autumn:
                        c = lerp(c, (206, 182, 98), (f - 0.3) * 0.9)
                else:
                    c = lerp((156, 142, 98), (92, 148, 70), g)
                if winter:
                    c = lerp(c, (214, 220, 226), 0.35)
                elif autumn and t in (GRASS, FOREST):
                    c = lerp(c, (170, 130, 70), 0.15)
                surf.set_at((tx, ty), c)
        big = pygame.transform.scale(surf, (w.w * self.tile, w.h * self.tile))
        self._terrain_cache = big
        self._terrain_key = key
        return big

    def draw_map(self):
        sim = self.sim
        mr = self.map_rect
        scr = self.screen
        scr.set_clip(mr)
        terr = self.terrain_surface()
        scr.blit(terr, (-self.cam_x * self.tile, -self.cam_y * self.tile))
        t = self.tile

        # Camp: huts, fire, midden, granary, pen.
        cx, cy = sim.camp
        for i, ang in enumerate((0.4, 1.9, 3.3, 4.6, 5.7)):
            hx, hy = cx + math.cos(ang) * 2.4, cy + math.sin(ang) * 2.0
            pygame.draw.circle(scr, (110, 82, 56), self.to_screen(hx, hy), max(3, int(t * 0.8)))
            pygame.draw.circle(scr, (80, 58, 40), self.to_screen(hx, hy), max(3, int(t * 0.8)), 1)
        flick = 0.75 + 0.25 * math.sin(pygame.time.get_ticks() / 90)
        pygame.draw.circle(scr, (240, 140, 50), self.to_screen(cx, cy), max(2, int(t * 0.55 * flick)))
        pygame.draw.circle(scr, (255, 220, 120), self.to_screen(cx, cy), max(1, int(t * 0.25 * flick)))
        mp = sim.midden_pos
        if mp is not None and sim.midden > 0.3:
            r = max(2, int(t * min(1.6, 0.35 + math.sqrt(sim.midden) * 0.12)))
            pygame.draw.circle(scr, (96, 74, 52), self.to_screen(*mp), r)
            pygame.draw.circle(scr, (180, 170, 150), self.to_screen(mp[0] + 0.2, mp[1] - 0.1), max(1, r // 3))
        if sim.policies["grain"] == "granary":
            gx, gy = self.to_screen(*sim.granary_pos)
            s = max(4, int(t * 1.3))
            pygame.draw.rect(scr, (150, 120, 72), (gx - s // 2, gy - s // 2, s, s))
            fill = min(1.0, sim.grain / 300.0)
            pygame.draw.rect(scr, (222, 196, 110), (gx - s // 2 + 1, gy + s // 2 - int((s - 2) * fill) - 1,
                                                    s - 2, int((s - 2) * fill)))
            pygame.draw.rect(scr, (90, 70, 44), (gx - s // 2, gy - s // 2, s, s), 1)
        p = sim.pen
        if p is not None:
            x0, y0 = self.to_screen(p.x, p.y)
            rect = pygame.Rect(x0, y0, int(p.w * t), int(p.h * t))
            if p.built:
                pygame.draw.rect(scr, (120, 88, 56), rect, max(1, t // 4))
            else:
                frac = p.progress / PEN_BUILD_DAYS
                for i in range(0, rect.w, max(3, t)):
                    pygame.draw.line(scr, (120, 88, 56), (rect.x + i, rect.y), (rect.x + i + t // 2, rect.y), 1)
                pygame.draw.rect(scr, (60, 50, 40), (rect.x, rect.bottom + 2, rect.w, 4))
                pygame.draw.rect(scr, ACCENT, (rect.x, rect.bottom + 2, int(rect.w * frac), 4))

        # Animals.
        x0, y0 = self.cam_x - 1, self.cam_y - 1
        x1, y1 = self.cam_x + mr.w / t + 1, self.cam_y + mr.h / t + 1
        for a in sim.animals:
            if not (x0 < a.x < x1 and y0 < a.y < y1):
                continue
            pos = self.to_screen(a.x, a.y)
            r = max(2, int(a.sp.radius * t * (0.65 if not a.adult else 1.0) * (0.8 + 0.4 * a.genome.size)))
            col = a.sp.color
            if sim.lives_at_camp(a) and sim.stages[a.sp.key] >= a.sp.max_stage and a.sp.key != "mouse":
                col = lerp(col, (210, 190, 160), 0.25)
            pygame.draw.circle(scr, col, pos, r)
            if a.piebald and r >= 3:
                pygame.draw.circle(scr, (236, 232, 222), (pos[0] + r // 3, pos[1] - r // 3), max(1, r // 2))
            if r >= 4:
                pygame.draw.circle(scr, (20, 20, 20), pos, r, 1)
            if a.state == "follow" and r >= 3:
                pygame.draw.circle(scr, (236, 220, 170), pos, r + 2, 1)

        # People.
        for h in sim.humans:
            if not (x0 < h.x < x1 and y0 < h.y < y1):
                continue
            pos = self.to_screen(h.x, h.y)
            r = max(2, int(t * (0.45 if h.adult else 0.32)))
            pygame.draw.circle(scr, (232, 196, 160), pos, r)
            pygame.draw.circle(scr, (60, 40, 30), pos, r, 1)
            rc = ROLE_COLOR.get(h.role)
            if rc and r >= 3:
                pygame.draw.circle(scr, rc, (pos[0], pos[1] - r - 2), max(1, r // 2))
            if (h.carry > 0 or h.carry_grain > 0) and r >= 3:
                pygame.draw.circle(scr, (200, 170, 90), (pos[0] + r, pos[1] + r // 2), max(1, r // 2))

        # Selection ring.
        e = self.selected
        if e is not None:
            pygame.draw.circle(scr, (255, 255, 255), self.to_screen(e.x, e.y), max(6, int(t * 1.1)), 2)

        # Night tint (subtle; a day is about a second).
        if sim.is_night:
            shade = pygame.Surface((mr.w, mr.h), pygame.SRCALPHA)
            shade.fill((10, 16, 40, 38))
            scr.blit(shade, (0, 0))
        scr.set_clip(None)

    # -------------------------------------------------------------- sidebar
    def text(self, s, pos, font=None, color=TEXT):
        surf = (font or self.font).render(s, True, color)
        self.screen.blit(surf, pos)
        return surf.get_width()

    def wrap(self, s, font, width):
        words = s.split()
        lines, cur = [], ""
        for w in words:
            trial = (cur + " " + w).strip()
            if font.size(trial)[0] > width and cur:
                lines.append(cur)
                cur = w
            else:
                cur = trial
        if cur:
            lines.append(cur)
        return lines

    def small_button(self, rect, label, action, tip=None, active=True):
        r = pygame.Rect(rect)
        mouse = pygame.mouse.get_pos()
        hover = r.collidepoint(mouse)
        pygame.draw.rect(self.screen, PANEL_HI if hover else (38, 42, 50), r, border_radius=4)
        pygame.draw.rect(self.screen, LINE, r, 1, border_radius=4)
        surf = self.font_sm.render(label, True, TEXT if active else DIM)
        self.screen.blit(surf, (r.x + (r.w - surf.get_width()) // 2, r.y + (r.h - surf.get_height()) // 2 + 1))
        self.buttons.append(Button(r, action, tip))
        if hover and tip:
            self.hover_tip = tip

    def section(self, title, y):
        x = self.map_rect.right + 14
        self.text(title.upper(), (x, y), self.font_sm, ACCENT)
        pygame.draw.line(self.screen, LINE, (x, y + 15), (self.screen.get_width() - 14, y + 15))
        return y + 21

    def draw_sidebar(self):
        sim = self.sim
        scr = self.screen
        mr = self.map_rect
        x = mr.right
        w = scr.get_width() - x
        pygame.draw.rect(scr, PANEL, (x, 0, w, scr.get_height()))
        pygame.draw.line(scr, LINE, (x, 0), (x, scr.get_height()))
        x += 14
        right = scr.get_width() - 14
        y = 10
        self.text("LINEAGE", (x, y), self.font_lg, TEXT)
        sp = "Paused" if self.paused else f"Speed x{int(SPEEDS[self.speed_i])}"
        sw = self.font_sm.size(sp)[0]
        self.text(sp, (right - sw, y + 6), self.font_sm, DIM if self.paused else GOOD)
        y += 28
        self.text(sim.date_str, (x, y), self.font, TEXT)
        y += 24

        # People & food.
        adults = sum(1 for h in sim.humans if h.adult)
        kids = len(sim.humans) - adults
        ratio = sim.food_ratio
        if ratio > 1.3:
            word, col = "Plenty", GOOD
        elif ratio > 1.02:
            word, col = "Enough", TEXT
        elif ratio > 0.85:
            word, col = "Lean", ACCENT
        else:
            word, col = "Hunger", BAD
        self.text(f"People {len(sim.humans)}  ({adults} adults, {kids} young)", (x, y), self.font_sm)
        y += 18
        self.text("Food:", (x, y), self.font_sm, DIM)
        self.text(word, (x + 40, y), self.font_sm, col)
        stores = f"stores {sim.fresh:.0f} fresh"
        if sim.policies["grain"] == "granary":
            stores += f", {sim.grain:.0f} grain"
        self.text(stores, (x + 100, y), self.font_sm, DIM)
        y += 22

        # Labour.
        y = self.section("Work", y)
        free = adults
        for key, label in LABOR_ROWS:
            n = min(sim.labor.get(key, 0), free)
            free -= n
            self.text(label, (x, y + 3), self.font_sm)
            bx = right - 92
            self.small_button((bx, y, 24, 20), "-", lambda k=key: self.adjust_labor(k, -1))
            self.text(str(sim.labor.get(key, 0)), (bx + 36, y + 3), self.font_sm)
            self.small_button((bx + 62, y, 24, 20), "+", lambda k=key: self.adjust_labor(k, 1))
            y += 23
        self.text("Gatherers (everyone else)", (x, y + 1), self.font_sm)
        self.text(str(max(0, free)), (right - 92 + 36, y + 1), self.font_sm)
        y += 20
        if getattr(sim, "short_handed", False):
            self.text("Food is short: camp keepers are out gathering.", (x, y), self.font_sm, ACCENT)
            y += 16
        y += 4

        # Policies.
        y = self.section("Ways of living", y)
        for key, label, options, tip in POLICY_ROWS:
            if key == "pen_cull" and (sim.pen is None or not sim.pen.built):
                continue
            cur = sim.policies[key]
            vals = [o[0] for o in options]
            i = vals.index(cur) if cur in vals else 0
            self.text(label, (x, y + 3), self.font_sm)
            bw = 150
            nxt = vals[(i + 1) % len(vals)]
            self.small_button((right - bw, y, bw, 20), options[i][1],
                              lambda k=key, v=nxt: sim.set_policy(k, v), tip)
            y += 23
        # Pen row.
        p = sim.pen
        self.text("Animal pen", (x, y + 3), self.font_sm)
        if p is None:
            self.small_button((right - 150, y, 150, 20), "Build a pen", sim.start_pen,
                              "Herders build a fenced pen beside camp. Assign at least one herder.")
        elif not p.built:
            msg = f"Building {100 * p.progress / PEN_BUILD_DAYS:.0f}%"
            if sim.labor.get("herd", 0) == 0:
                msg += " (no herders!)"
            self.text(msg, (right - 150, y + 3), self.font_sm, ACCENT)
        else:
            n = len(sim.penned())
            fod = "fodder ok" if sim.fodder > n * 2 else "fodder low"
            self.text(f"{n}/{PEN_CAPACITY} animals, {fod}", (right - 150, y + 3), self.font_sm,
                      TEXT if sim.fodder > n * 2 else ACCENT)
        y += 28

        # Species.
        y = self.section("The animals around you", y)
        for key in SPECIES:
            d = observe.describe_species(sim, key, debug=self.debug)
            pygame.draw.circle(scr, d["color"], (x + 6, y + 8), 5)
            self.text(d["name"], (x + 16, y), self.font_sm, TEXT)
            stage_col = GOOD if d["stage"] >= 3 else ACCENT if d["stage"] >= 2 else DIM
            sw = self.font_sm.size(d["stage_name"])[0]
            self.text(d["stage_name"], (right - sw, y), self.font_sm, stage_col)
            y += 15
            line = d["temper"]
            if d["trend"]:
                line += f"; {d['trend']}"
            extra = []
            if d["camp"]:
                extra.append(f"{d['camp']} at camp")
            if d["penned"]:
                extra.append(f"{d['penned']} penned")
            extra.append(d["seen"])
            line += " · " + ", ".join(extra)
            for ln in self.wrap(line, self.font_sm, right - x - 16)[:2]:
                self.text(ln, (x + 16, y), self.font_sm, DIM)
                y += 14
            if self.debug and "debug" in d:
                self.text(d["debug"], (x + 16, y), self.font_sm, (120, 170, 220))
                y += 14
            y += 4

        # Chronicle.
        y = self.section("Chronicle", y + 2)
        bottom = scr.get_height() - 8
        entries = list(reversed(sim.chronicle[-30:]))
        for day, txt in entries:
            stamp = sim.stamp(day)
            lines = self.wrap(txt, self.font_sm, right - x - 58)
            if y + 14 * len(lines) > bottom:
                break
            fresh = sim.day - day < 15
            self.text(stamp, (x, y), self.font_sm, ACCENT if fresh else DIM)
            for ln in lines:
                self.text(ln, (x + 58, y), self.font_sm, TEXT if fresh else (190, 194, 202))
                y += 14
            y += 3

    def adjust_labor(self, key, delta):
        lab = self.sim.labor
        lab[key] = max(0, min(20, lab.get(key, 0) + delta))

    # ------------------------------------------------------------ inspector
    def draw_inspector(self):
        e = self.selected
        if e is None:
            return
        sim = self.sim
        lines = []
        if hasattr(e, "sp"):
            a = e
            name = sim.display_name(a)
            title = name.capitalize()
            age_y = a.age / DAYS_PER_YEAR
            lines.append(f"{'Female' if a.female else 'Male'}, "
                         f"{'young' if not a.adult else f'{age_y:.0f} years old'}")
            lines.append(f"Temperament: {observe.boldness_word(a.genome.boldness)}, "
                         f"{observe.aggression_word(a.genome.aggression)}")
            fam = a.familiarity
            lines.append("Used to people" if fam > 0.6 else
                         "Getting used to people" if fam > 0.25 else "Unused to people")
            if a.penned:
                lines.append("Lives in your pen")
            elif sim.lives_at_camp(a):
                lines.append("Lives around your camp")
            else:
                lines.append("Lives in the wild")
            if a.camp_gen:
                lines.append(f"{a.camp_gen} generation{'s' if a.camp_gen > 1 else ''} born at camp")
            ef = a.energy / a.sp.max_energy
            lines.append("Well fed" if ef > 0.7 else "Hungry" if ef > 0.3 else "Starving")
            lines.append(f"Doing: {STATE_WORDS.get(a.state, a.state)}")
            if a.piebald:
                lines.append("Has an odd patched coat")
            if self.debug:
                lines.append(f"B={a.genome.boldness:.2f} A={a.genome.aggression:.2f} "
                             f"S={a.genome.size:.2f} F={a.familiarity:.2f} fd={sim.flight_distance(a):.1f}")
        else:
            h = e
            title = h.name
            lines.append(f"{'Adult' if h.adult else 'Child'}, {h.age / DAYS_PER_YEAR:.0f} years old")
            lines.append(f"Work: {ROLE_WORDS.get(h.role, h.role)}")
            lines.append(f"Doing: {STATE_WORDS.get(h.state, h.state)}")
            lines.append("Healthy" if h.health > 0.8 else "Weak" if h.health > 0.4 else "Very weak")
            if h.hunger > 1:
                lines.append("Hungry")
        mr = self.map_rect
        w = 300
        hgt = 34 + 17 * len(lines)
        r = pygame.Rect(12, mr.bottom - hgt - 36, w, hgt)
        s = pygame.Surface(r.size, pygame.SRCALPHA)
        s.fill((20, 22, 26, 225))
        self.screen.blit(s, r.topleft)
        pygame.draw.rect(self.screen, LINE, r, 1)
        self.text(title, (r.x + 10, r.y + 8), self.font, ACCENT)
        yy = r.y + 30
        for ln in lines:
            self.text(ln, (r.x + 10, yy), self.font_sm)
            yy += 17

    def draw_hint_bar(self):
        mr = self.map_rect
        msg = ("Space pause · 1-4 speed · WASD/right-drag pan · wheel zoom · "
               "click to inspect · C camp · H help · F3 numbers · R new world")
        s = pygame.Surface((mr.w, 22), pygame.SRCALPHA)
        s.fill((16, 18, 22, 200))
        self.screen.blit(s, (0, mr.bottom - 22))
        self.text(msg, (10, mr.bottom - 18), self.font_sm, DIM)
        seed = f"world {self.sim.seed}"
        self.text(seed, (mr.right - self.font_sm.size(seed)[0] - 10, mr.bottom - 18), self.font_sm, DIM)

    def draw_tooltip(self, tip):
        mx, my = pygame.mouse.get_pos()
        lines = self.wrap(tip, self.font_sm, 280)
        w = 300
        h = 12 + 15 * len(lines)
        x = min(mx - w - 12, self.screen.get_width() - w - 6)
        x = max(6, x)
        y = min(my + 12, self.screen.get_height() - h - 6)
        r = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.screen, (18, 20, 24), r, border_radius=5)
        pygame.draw.rect(self.screen, ACCENT, r, 1, border_radius=5)
        for i, ln in enumerate(lines):
            self.text(ln, (x + 10, y + 7 + 15 * i), self.font_sm)

    def draw_overlay_box(self, lines, title_font=None):
        mr = self.map_rect
        s = pygame.Surface((mr.w, mr.h), pygame.SRCALPHA)
        s.fill((8, 10, 14, 190))
        self.screen.blit(s, (0, 0))
        w = min(mr.w - 40, 700)
        h = 40 + 24 * len(lines)
        r = pygame.Rect((mr.w - w) // 2, (mr.h - h) // 2, w, h)
        pygame.draw.rect(self.screen, PANEL, r, border_radius=8)
        pygame.draw.rect(self.screen, ACCENT, r, 1, border_radius=8)
        y = r.y + 20
        for i, ln in enumerate(lines):
            font = (title_font or self.font_lg) if i == 0 else self.font
            col = ACCENT if i == 0 else TEXT
            self.text(ln, (r.x + 28, y), font, col)
            y += 24 if i else 30

    def draw_help(self):
        self.draw_overlay_box(HELP_TEXT)

    def draw_game_over(self):
        sim = self.sim
        done = [observe.STAGES[s] + ": " + sim.species_name(k)
                for k, s in sim.stages.items() if s >= 2]
        lines = ["Your lineage has ended",
                 f"Your people lasted until {sim.date_str}.",
                 ""]
        if done:
            lines.append("What lived alongside them:")
            lines.extend("   " + d for d in done)
        else:
            lines.append("No animal ever made its home beside them.")
        lines += ["", "Click or press R to begin again in a new valley."]
        self.draw_overlay_box(lines)


ROLE_WORDS = {"gather": "gathering", "hunt": "hunting", "herd": "herding",
              "camp": "keeping camp", "child": "growing up"}

STATE_WORDS = {
    "wander": "wandering", "forage": "foraging", "graze": "grazing", "flee": "fleeing",
    "lurk": "lurking at the edge of camp", "to_midden": "heading for the midden",
    "midden_eat": "scavenging at the midden", "to_granary": "heading for the granary",
    "granary_eat": "eating your grain", "chase": "chasing", "follow": "following a hunter",
    "prowl": "prowling near the granary",
    "idle": "resting", "milling": "around camp", "gathering": "gathering food",
    "to_patch": "heading out to gather", "returning": "heading home", "seek": "searching for prey",
    "stalk": "stalking prey", "building": "building the pen", "cutting": "cutting fodder",
    "tending": "tending the pen",
}


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="Lineage: domestication prototype")
    ap.add_argument("--seed", type=int, default=None, help="world seed")
    args = ap.parse_args(argv)
    Game(args.seed).run()


if __name__ == "__main__":
    main(sys.argv[1:])
