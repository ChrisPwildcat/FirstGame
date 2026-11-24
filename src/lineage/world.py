"""Terrain, vegetation and the seasons.

A single temperate river valley: meadows, forest, hills and a wide shallow
river whose banks grow wild grain.
"""

import math

WATER, SHORE, GRASS, FOREST, HILLS = range(5)
TERRAIN_NAMES = {WATER: "River", SHORE: "Riverbank", GRASS: "Meadow",
                 FOREST: "Forest", HILLS: "Hills"}

# Movement speed multiplier per terrain (the river is shallow enough to wade).
SPEED_FACTOR = {WATER: 0.35, SHORE: 1.0, GRASS: 1.0, FOREST: 0.85, HILLS: 0.7}

GRASS_CAP = {WATER: 0.0, SHORE: 1.0, GRASS: 1.0, FOREST: 0.35, HILLS: 0.45}
FORAGE_CAP = {WATER: 0.0, SHORE: 0.8, GRASS: 0.3, FOREST: 1.0, HILLS: 0.2}
GRASS_GROWTH = (1.0, 0.7, 0.4, 0.04)         # by season
FORAGE_GROWTH = {                            # by terrain, by season
    SHORE: (0.1, 0.6, 1.0, 0.0),             # wild grain ripens late
    FOREST: (0.2, 1.0, 0.8, 0.0),            # berries and nuts
    GRASS: (0.4, 0.4, 0.3, 0.05),            # roots and greens
    HILLS: (0.3, 0.3, 0.2, 0.05),
}


def _noise(w, h, rng, scale, octaves=3):
    out = [0.0] * (w * h)
    amp, total = 1.0, 0.0
    for o in range(octaves):
        s = max(2, int(scale / (2 ** o)))
        gw, gh = w // s + 2, h // s + 2
        grid = [rng.random() for _ in range(gw * gh)]
        for y in range(h):
            gy = y / s
            y0 = int(gy)
            fy = gy - y0
            fy = fy * fy * (3 - 2 * fy)
            row = y0 * gw
            for x in range(w):
                gx = x / s
                x0 = int(gx)
                fx = gx - x0
                fx = fx * fx * (3 - 2 * fx)
                a = grid[row + x0]
                b = grid[row + x0 + 1]
                c = grid[row + gw + x0]
                d = grid[row + gw + x0 + 1]
                top = a + (b - a) * fx
                bot = c + (d - c) * fx
                out[y * w + x] += amp * (top + (bot - top) * fy)
        total += amp
        amp *= 0.5
    lo, hi = min(out), max(out)
    span = (hi - lo) or 1.0
    return [(v - lo) / span for v in out]


class World:
    def __init__(self, w, h, rng):
        self.w, self.h = w, h
        elev = _noise(w, h, rng, 32)
        moist = _noise(w, h, rng, 24)

        # Meandering river from west to east.
        self.river_y = []
        y = h * (0.38 + 0.24 * rng.random())
        dy = 0.0
        for _ in range(w):
            dy = (dy + rng.uniform(-0.35, 0.35)) * 0.9
            y += dy
            if y < h * 0.22 or y > h * 0.78:
                dy = -dy
                y = min(max(y, h * 0.22), h * 0.78)
            self.river_y.append(y)

        self.terrain = [GRASS] * (w * h)
        for ty in range(h):
            for tx in range(w):
                i = ty * w + tx
                dist = abs(ty + 0.5 - self.river_y[tx])
                if dist < 1.4:
                    t = WATER
                elif dist < 5.0:
                    t = SHORE
                elif elev[i] > 0.74:
                    t = HILLS
                elif moist[i] > 0.55:
                    t = FOREST
                else:
                    t = GRASS
                self.terrain[i] = t

        self.grass = [GRASS_CAP[t] * 0.85 for t in self.terrain]
        self.forage = [FORAGE_CAP[t] * 0.5 for t in self.terrain]

    # --- lookups -----------------------------------------------------------
    def index(self, x, y):
        tx = int(x)
        ty = int(y)
        if tx < 0:
            tx = 0
        elif tx >= self.w:
            tx = self.w - 1
        if ty < 0:
            ty = 0
        elif ty >= self.h:
            ty = self.h - 1
        return ty * self.w + tx

    def terrain_at(self, x, y):
        return self.terrain[self.index(x, y)]

    def speed_factor(self, x, y):
        return SPEED_FACTOR[self.terrain[self.index(x, y)]]

    def clamp_pos(self, x, y):
        return (min(max(x, 0.5), self.w - 0.5), min(max(y, 0.5), self.h - 0.5))

    def is_land(self, x, y):
        return self.terrain_at(x, y) != WATER

    # --- seasons -----------------------------------------------------------
    def grow(self, dt, season):
        gg = GRASS_GROWTH[season] * 0.05 * dt
        terrain, grass, forage = self.terrain, self.grass, self.forage
        winter = season == 3
        for i, t in enumerate(terrain):
            if t == WATER:
                continue
            cap = GRASS_CAP[t]
            g = grass[i]
            if g < cap:
                grass[i] = g + gg * (cap - g)
            fcap = FORAGE_CAP[t]
            f = forage[i]
            rate = FORAGE_GROWTH[t][season] * 0.035 * dt
            if f < fcap:
                f += rate * (fcap - f)
            if winter and t in (FOREST, SHORE):
                f *= (1 - 0.06 * dt)   # fruit rots, grain sheds
            forage[i] = f

    # --- placement helpers -------------------------------------------------
    def find_camp_site(self):
        """Riverbank land near the middle of the map, a few tiles from water."""
        best, best_score = None, 1e9
        cx, cy = self.w / 2, self.h / 2
        for ty in range(self.h):
            for tx in range(self.w):
                if self.terrain[ty * self.w + tx] != SHORE:
                    continue
                dist_river = abs(ty + 0.5 - self.river_y[tx])
                if not 3.0 < dist_river < 4.5:
                    continue
                score = math.hypot(tx - cx, ty - cy)
                if score < best_score:
                    best, best_score = (tx + 0.5, ty + 0.5), score
        return best or (cx, cy)

    def away_from_river(self, x, y):
        """Unit vertical direction pointing away from the river at column x."""
        ry = self.river_y[int(min(max(x, 0), self.w - 1))]
        return 1.0 if y > ry else -1.0
