"""The Lineage simulation: a band of people, a river valley, and the animals
that live alongside them.

Nothing in here says "domesticate wolves". Wolves become dogs (or don't)
because of where the camp dumps its scraps, whether people tolerate
scavengers, who gets killed for biting, and who survives the winter.
"""

import math
import random

from . import observe
from .config import (
    ADULT_AGE, BUTCHER_SCRAPS, CAMP_HOME_RADIUS, CAMP_RADIUS, CARRY_CAP,
    DAYS_PER_SEASON, DAYS_PER_YEAR, DEFAULT_LABOR, DEFAULT_POLICIES,
    FAM_DECAY, FAM_GAIN, FAMILIARITY_WEIGHT, FORAGE_PER_UNIT, FRESH_SPOIL,
    GATHER_RATE, GRAIN_SPOIL, GRANARY_CAP, HUMAN_CAP, HUMAN_SPEED, HUNT_GIVE_UP_DAYS,
    HUNT_RADIUS, MAX_STEP, MIDDEN_DECAY, PEN_BUILD_DAYS, PEN_CAPACITY, PEN_H,
    PEN_W, SCRAP_FRACTION, SEASON_NAMES, STALK_FACTOR, THINK_INTERVAL,
    THROW_RANGE, WORLD_H, WORLD_W,
)
from .genetics import Genome, clamp
from .species import SPECIES
from .world import FOREST, SHORE, WATER, World

SYLLABLES = ["a", "ka", "to", "ri", "na", "mu", "en", "sha", "lo", "ve",
             "dra", "ul", "ki", "om", "ta", "ys", "be", "ro", "ha", "il"]

HUNT_POLICY_KEY = {"aurochs": "hunt_aurochs", "deer": "hunt_deer", "boar": "hunt_boar"}


def a_(word):
    """'a wolf', 'an aurochs'."""
    return ("an " if word[:1].lower() in "aeiou" else "a ") + word


def A_(word):
    return a_(word).capitalize()


def _dist(ax, ay, bx, by):
    return math.hypot(ax - bx, ay - by)


class SpatialGrid:
    def __init__(self, cell=8):
        self.cell = cell
        self.cells = {}

    def rebuild(self, items):
        c = self.cell
        cells = {}
        for it in items:
            key = (int(it.x // c), int(it.y // c))
            lst = cells.get(key)
            if lst is None:
                cells[key] = [it]
            else:
                lst.append(it)
        self.cells = cells

    def near(self, x, y, r):
        c = self.cell
        out = []
        cells = self.cells
        for cx in range(int((x - r) // c), int((x + r) // c) + 1):
            for cy in range(int((y - r) // c), int((y + r) // c) + 1):
                lst = cells.get((cx, cy))
                if lst:
                    out.extend(lst)
        return out


class Animal:
    __slots__ = ("id", "sp", "x", "y", "tx", "ty", "state", "energy", "age",
                 "max_age", "female", "genome", "familiarity", "hx", "hy",
                 "think_t", "bred_year", "bred_day", "alive", "piebald",
                 "camp_gen", "penned", "scared_t", "follow", "prey", "dens",
                 "near_h", "cause", "cool", "meals", "goal")

    def __init__(self, aid, sp, x, y, genome, age, female, rng):
        self.id = aid
        self.sp = sp
        self.x, self.y = x, y
        self.tx = self.ty = None
        self.state = "wander"
        self.energy = sp.max_energy * 0.7
        self.age = age
        self.max_age = sp.max_age * rng.uniform(0.7, 1.2)
        self.female = female
        self.genome = genome
        self.familiarity = 0.0
        self.hx, self.hy = x, y
        self.think_t = rng.random() * THINK_INTERVAL
        self.bred_year = -1
        self.bred_day = -999.0
        self.alive = True
        self.piebald = rng.random() < genome.piebald_chance()
        self.camp_gen = 0
        self.penned = False
        self.scared_t = 0.0
        self.follow = None
        self.prey = None
        self.dens = 0
        self.near_h = 99.0
        self.cause = None
        self.cool = 0.0
        self.meals = 0.0
        self.goal = None

    @property
    def adult(self):
        return self.age >= self.sp.mature_age


class Human:
    __slots__ = ("id", "name", "x", "y", "tx", "ty", "age", "lifespan", "role",
                 "state", "carry", "carry_grain", "target", "think_t", "hunger",
                 "health", "alive", "task_t", "cause")

    def __init__(self, hid, name, x, y, age_years, rng):
        self.id = hid
        self.name = name
        self.x, self.y = x, y
        self.tx = self.ty = None
        self.age = age_years * DAYS_PER_YEAR
        self.lifespan = rng.uniform(45, 68) * DAYS_PER_YEAR
        self.role = "camp"
        self.state = "idle"
        self.carry = 0.0
        self.carry_grain = 0.0
        self.target = None
        self.think_t = rng.random() * THINK_INTERVAL
        self.hunger = 0.0
        self.health = 1.0
        self.alive = True
        self.task_t = 0.0
        self.cause = None

    @property
    def adult(self):
        return self.age >= ADULT_AGE * DAYS_PER_YEAR


class Pen:
    def __init__(self, x, y):
        self.x, self.y = x, y          # top-left corner (tiles)
        self.w, self.h = PEN_W, PEN_H
        self.progress = 0.0
        self.built = False

    @property
    def cx(self):
        return self.x + self.w / 2

    @property
    def cy(self):
        return self.y + self.h / 2


class Simulation:
    def __init__(self, seed=None):
        self.seed = seed if seed is not None else random.randrange(1_000_000)
        self.rng = random.Random(self.seed)
        self.world = World(WORLD_W, WORLD_H, self.rng)
        self.camp = self.world.find_camp_site()
        self.day = 0.0
        self._day_int = 0
        self._next_id = 1
        self.animals = []
        self.humans = []
        self.policies = dict(DEFAULT_POLICIES)
        self.labor = dict(DEFAULT_LABOR)
        self.fresh = 60.0
        self.grain = 0.0
        self.fodder = 0.0
        self.midden = 0.0
        self.pen = None
        self.pen_project = False
        self.chronicle = []
        self.flags = set()
        self.stages = {k: 0 for k in SPECIES}
        self.history = {k: [] for k in SPECIES}
        self.visits = {k: 0.0 for k in SPECIES}
        self.deaths = {}
        self.veg_version = 0
        self.income_today = 0.0
        self.short_handed = False
        self.income_avg = 8.0     # ~30-day running average of food brought in
        self.need_today = 7.0
        self.game_over = False
        self._dirty = False
        self.agrid = SpatialGrid(8)
        self.hgrid = SpatialGrid(8)
        self._place_sites()
        self._spawn_initial()
        observe.record_year(self)
        self.log("Your band makes camp on the riverbank. The valley is full of life.")

    # ------------------------------------------------------------------ util
    def new_id(self):
        self._next_id += 1
        return self._next_id

    def log(self, text, flag=None):
        if flag is not None:
            if flag in self.flags:
                return
            self.flags.add(flag)
        self.chronicle.append((self.day, text))

    @property
    def year(self):
        return int(self.day // DAYS_PER_YEAR) + 1

    @property
    def season(self):
        return int((self.day % DAYS_PER_YEAR) // DAYS_PER_SEASON) % 4

    @property
    def date_str(self):
        return f"Year {self.year}, {SEASON_NAMES[self.season]}"

    def stamp(self, day):
        y = int(day // DAYS_PER_YEAR) + 1
        s = int((day % DAYS_PER_YEAR) // DAYS_PER_SEASON) % 4
        return f"Y{y} {SEASON_NAMES[s][:3]}"

    @property
    def food_ratio(self):
        """Recent food income relative to what the band eats (1.0 = break even)."""
        return self.income_avg / max(0.5, self.need_today)

    def tameness(self, a):
        return clamp(a.genome.boldness + FAMILIARITY_WEIGHT * a.familiarity)

    @property
    def is_night(self):
        return (self.day % 1.0) > 0.62

    def capture_ease(self, a):
        """Young animals are far easier to catch and raise than adults."""
        return clamp(self.tameness(a) + (0.35 if not a.adult else 0.0))

    def flight_distance(self, a):
        fd = a.sp.base_flight * (1.0 - self.tameness(a)) ** 1.3 + 0.6
        # Hunger makes animals take risks.
        fd *= 0.6 + 0.4 * clamp(a.energy / a.sp.max_energy)
        if a.scared_t > 0:
            fd = fd * 1.8 + 2.0
        return fd

    def lives_at_camp(self, a):
        return a.penned or _dist(a.hx, a.hy, *self.camp) < CAMP_HOME_RADIUS

    def display_name(self, a, plural=False):
        sp = a.sp
        domestic = self.stages[sp.key] >= sp.max_stage and self.lives_at_camp(a)
        if plural:
            return sp.domestic_name if domestic else sp.name
        return sp.domestic_singular if domestic else sp.singular

    def species_name(self, key, plural=True):
        sp = SPECIES[key]
        if self.stages[key] >= sp.max_stage:
            return sp.domestic_name if plural else sp.domestic_singular
        return sp.name if plural else sp.singular

    # ----------------------------------------------------------------- sites
    def _land_near(self, x, y, radius=3.0, tries=40):
        w = self.world
        for _ in range(tries):
            px = x + self.rng.uniform(-radius, radius)
            py = y + self.rng.uniform(-radius, radius)
            px, py = w.clamp_pos(px, py)
            if w.is_land(px, py):
                return px, py
        return w.clamp_pos(x, y)

    def _place_sites(self):
        cx, cy = self.camp
        away = self.world.away_from_river(cx, cy)
        self.camp_midden = self.world.clamp_pos(cx + 6.5, cy + 4.0 * away)
        self.far_midden = self.world.clamp_pos(cx - 6.0, cy + 15.0 * away)
        self.granary_pos = self.world.clamp_pos(cx - 5.5, cy + 2.5 * away)
        px, py = self.world.clamp_pos(cx + 6.0, cy + 2.0 * away)
        if away < 0:
            py -= PEN_H
        self.pen_site = (px, py)

    @property
    def midden_pos(self):
        w = self.policies["waste"]
        if w == "camp":
            return self.camp_midden
        if w == "far":
            return self.far_midden
        return None

    def set_policy(self, key, value):
        old = self.policies.get(key)
        if old == value:
            return
        self.policies[key] = value
        if key == "waste":
            self.midden = 0.0   # the old heap is abandoned
        if key == "grain" and value == "fresh" and self.grain > 0:
            self.fresh += self.grain
            self.grain = 0.0

    def start_pen(self):
        if self.pen is None:
            self.pen = Pen(*self.pen_site)
            self.pen_project = True
            self.log("Your people mark out ground for an animal pen.")

    def in_pen(self, x, y):
        p = self.pen
        return p is not None and p.x <= x <= p.x + p.w and p.y <= y <= p.y + p.h

    def penned(self):
        return [a for a in self.animals if a.alive and a.penned]

    # ---------------------------------------------------------------- spawn
    def _name(self):
        r = self.rng
        n = "".join(r.choice(SYLLABLES) for _ in range(r.choice((2, 2, 3))))
        return n.capitalize()

    def _random_site(self, sp, min_dist):
        w = self.world
        cx, cy = self.camp
        best = None
        best_w = -1
        for _ in range(60):
            x = self.rng.uniform(2, w.w - 2)
            y = self.rng.uniform(2, w.h - 2)
            if _dist(x, y, cx, cy) < min_dist:
                continue
            hw = sp.habitat.get(w.terrain_at(x, y), 0.0) * self.rng.random()
            if hw > best_w:
                best, best_w = (x, y), hw
        return best or (2.0, 2.0)

    def _spawn_initial(self):
        cx, cy = self.camp
        for i in range(10):
            age = self.rng.uniform(16, 38) if i < 7 else self.rng.uniform(2, 10)
            x, y = self._land_near(cx, cy, 2.5)
            self.humans.append(Human(self.new_id(), self._name(), x, y, age, self.rng))
        for sp in SPECIES.values():
            remaining = sp.initial
            while remaining > 0:
                size = min(remaining, self.rng.randint(*sp.group_size))
                gx, gy = self._random_site(sp, sp.spawn_far)
                for _ in range(size):
                    x, y = self._land_near(gx, gy, 2.0)
                    age = self.rng.uniform(0.3, 0.8) * sp.max_age
                    a = Animal(self.new_id(), sp, x, y, Genome.random(self.rng, sp),
                               age, self.rng.random() < 0.5, self.rng)
                    a.hx, a.hy = gx, gy
                    self.animals.append(a)
                remaining -= size

    # ------------------------------------------------------------- stepping
    def advance(self, days):
        """Advance the simulation by `days`, sub-stepping as needed."""
        while days > 1e-9 and not self.game_over:
            dt = min(MAX_STEP, days)
            self.step(dt)
            days -= dt

    def step(self, dt):
        if self.game_over:
            return
        self.day += dt
        self.agrid.rebuild(self.animals)
        self.hgrid.rebuild(self.humans)
        for h in self.humans:
            if h.alive:
                self._update_human(h, dt)
        for a in self.animals:
            if a.alive:
                self._update_animal(a, dt)
        if self._dirty:
            self.animals = [a for a in self.animals if a.alive]
            self.humans = [h for h in self.humans if h.alive]
            self._dirty = False
        while self._day_int < int(self.day):
            self._day_int += 1
            self._daily()

    def _move(self, e, speed, dt):
        if e.tx is None:
            return True
        dx = e.tx - e.x
        dy = e.ty - e.y
        d = math.hypot(dx, dy)
        if d < 0.05:
            return True
        step = speed * self.world.speed_factor(e.x, e.y) * dt
        if step >= d:
            e.x, e.y = e.tx, e.ty
            return True
        e.x += dx / d * step
        e.y += dy / d * step
        return False

    def _set_target(self, e, x, y):
        e.tx, e.ty = self.world.clamp_pos(x, y)

    def _nearest_human(self, x, y, r, pred=None):
        best, bd = None, 1e9
        for h in self.hgrid.near(x, y, r):
            if not h.alive or (pred and not pred(h)):
                continue
            d = _dist(x, y, h.x, h.y)
            if d < bd:
                best, bd = h, d
        return best, bd

    def asleep(self, h):
        # A game day passes in about a second, so night is abstract: anyone not
        # actively hunting or chasing is treated as resting where they are.
        return self.is_night and h.state not in ("chase", "stalk", "seek")

    def _nearest_threat(self, x, y, r):
        """Nearest person as an animal judges it: people asleep by the fire
        count as much farther away than they are."""
        best, bd = None, 1e9
        night = self.is_night
        for h in self.hgrid.near(x, y, r):
            if not h.alive:
                continue
            d = _dist(x, y, h.x, h.y)
            if night and self.asleep(h):
                d /= 0.35
            if d < bd:
                best, bd = h, d
        return best, bd

    def kill_animal(self, a, cause):
        if not a.alive:
            return
        a.alive = False
        a.cause = cause
        self._dirty = True
        key = (a.sp.key, cause)
        self.deaths[key] = self.deaths.get(key, 0) + 1

    def kill_human(self, h, cause):
        if not h.alive:
            return
        h.alive = False
        h.cause = cause
        self._dirty = True
        self.log(f"{h.name} has died ({cause}).")

    # ---------------------------------------------------------- daily tick
    def _daily(self):
        d = self._day_int
        day_of_year = d % DAYS_PER_YEAR
        if day_of_year % DAYS_PER_SEASON == 0:
            s = self.season
            if s == 3:
                self.log("Winter sets in. The meadows go brown and the berries rot.",
                         flag="first_winter")
            if day_of_year == 0 and d > 0:
                observe.record_year(self)
            self._immigration()
        self._assign_roles()
        self.income_avg += (self.income_today - self.income_avg) * 0.035
        self.income_today = 0.0
        self._humans_eat()
        self.fresh *= (1 - FRESH_SPOIL)
        self.grain *= (1 - GRAIN_SPOIL)
        self.fodder *= 0.99
        self.midden *= (1 - MIDDEN_DECAY)
        for k in self.visits:
            self.visits[k] *= 0.95
        self._pen_daily()
        self._breed()
        self._human_lifecycle()
        if d % 5 == 0:
            self.world.grow(5, self.season)
            self.veg_version += 1
        if d % 10 == 0:
            observe.update_stages(self)
            self._scarcity_check()
        if not self.humans:
            self.game_over = True
            self.log("The last of your people is gone. The valley forgets them.")

    def _immigration(self):
        """Small animals drift in from neighbouring valleys when numbers crash."""
        for key, min_n, group in (("mouse", 8, 5), ("cat", 3, 2)):
            sp = SPECIES[key]
            n = sum(1 for a in self.animals if a.alive and a.sp is sp)
            if n < min_n and self.rng.random() < 0.5:
                edge = self.rng.choice(((2.0, None), (self.world.w - 2.0, None)))
                gx = edge[0]
                gy = self.rng.uniform(5, self.world.h - 5)
                for i in range(group):
                    x, y = self._land_near(gx, gy, 2.0)
                    a = Animal(self.new_id(), sp, x, y, Genome.random(self.rng, sp),
                               sp.mature_age * 1.2, i % 2 == 0, self.rng)
                    a.hx, a.hy = x + (8 if gx < 10 else -8), y
                    self.animals.append(a)

    def _scarcity_check(self):
        for sp in SPECIES.values():
            if not sp.huntable:
                continue
            n = sum(1 for a in self.animals if a.alive and a.sp is sp and not a.penned)
            if n == 0:
                self.log(f"The last wild {sp.singular} in the valley is gone.",
                         flag=f"extinct_{sp.key}")
            elif n < sp.initial * 0.35:
                self.log(f"{sp.name} are growing scarce. Your hunters range farther "
                         "and come back with less.", flag=f"scarce_{sp.key}")

    def _assign_roles(self):
        adults = [h for h in self.humans if h.alive and h.adult]
        for h in self.humans:
            if not h.adult:
                h.role = "child"
        want = {}
        left = len(adults)
        # When food is short, the camp keepers pitch in with gathering.
        self.short_handed = (self.food_ratio < 0.95 and
                             self.fresh + self.grain < self.need_today * 5)
        for role in ("hunt", "herd", "camp"):
            n = max(0, min(self.labor.get(role, 0), left))
            if role == "camp" and self.short_handed:
                n = min(n, 1)
            want[role] = n
            left -= n
        want["gather"] = left
        counts = {r: 0 for r in want}
        free = []
        for h in adults:
            if h.role in counts and counts[h.role] < want[h.role]:
                counts[h.role] += 1
            else:
                free.append(h)
        for h in free:
            for role in ("hunt", "herd", "camp", "gather"):
                if counts[role] < want[role]:
                    counts[role] += 1
                    self._change_role(h, role)
                    break

    def _change_role(self, h, role):
        if h.role != role:
            h.role = role
            h.state = "idle"
            h.target = None
            h.task_t = 0.0
            if h.carry or h.carry_grain:
                self._deposit(h)

    def _humans_eat(self):
        need = sum(0.75 if h.adult else 0.45 for h in self.humans)
        self.need_today = need
        if need <= 0:
            return
        eat_fresh = min(self.fresh, need)
        self.fresh -= eat_fresh
        rem = need - eat_fresh
        eat_grain = min(self.grain, rem)
        self.grain -= eat_grain
        rem -= eat_grain
        if self.policies["waste"] != "burn":
            self.midden += eat_fresh * SCRAP_FRACTION + eat_grain * 0.05
        short = rem / need
        if short > 0.05:
            self.log("Food is running short. Your people go hungry.",
                     flag=f"hungry{self.year}")
        # Share out what there is. When it runs short, some go without; the
        # frail suffer first. A band shrinks to what the land can feed.
        fed_budget = (need - rem)
        order = list(self.humans)
        self.rng.shuffle(order)
        for h in order:
            portion = 0.75 if h.adult else 0.45
            if fed_budget >= portion * 0.8:
                fed_budget -= portion
                h.hunger = max(0.0, h.hunger - 1.0)
                h.health = min(1.0, h.health + 0.03)
            else:
                h.hunger += 1.0
            if h.hunger > 4:
                frail = 1.4 if not h.adult or h.age > 50 * DAYS_PER_YEAR else 1.0
                h.health -= 0.05 * (h.hunger - 3) * frail * self.rng.uniform(0.3, 1.7)
            if h.health <= 0:
                self.kill_human(h, "starvation")

    def _human_lifecycle(self):
        for h in self.humans:
            if not h.alive:
                continue
            h.age += 1
            if h.age > h.lifespan:
                self.kill_human(h, "old age")
        adults = sum(1 for h in self.humans if h.alive and h.adult)
        alive = sum(1 for h in self.humans if h.alive)
        if adults >= 2 and alive < HUMAN_CAP:
            # Births follow the food supply: a band only grows when the land
            # (and its stores) can feed more mouths.
            ratio = self.food_ratio
            stored_days = (self.fresh + self.grain) / max(1.0, self.need_today)
            security = clamp((ratio - 1.0) * 2.5) * 0.7 + clamp(stored_days / 20) * 0.3
            hungry = sum(1 for h in self.humans if h.hunger > 1) / max(1, alive)
            rate = 0.004 * adults / 2 * security * (1 - hungry)
            if self.rng.random() < rate:
                cx, cy = self.camp
                x, y = self._land_near(cx, cy, 2.0)
                baby = Human(self.new_id(), self._name(), x, y, 0.0, self.rng)
                baby.role = "child"
                self.humans.append(baby)
                if len(self.humans) <= 14:
                    self.log(f"A child, {baby.name}, is born.")
                elif len(self.humans) >= HUMAN_CAP - 1:
                    self.log("The camp is as large as this valley can support.",
                             flag="pop_cap")

    # -------------------------------------------------------------- breeding
    def _breed(self):
        season = self.season
        yr = self.year
        # Camp and wild populations are capped separately, so a crowded
        # wilderness doesn't stop the camp lineage from breeding.
        counts = {}
        totals = {}
        for a in self.animals:
            if a.alive:
                key = (a.sp.key, self.lives_at_camp(a))
                counts[key] = counts.get(key, 0) + 1
                totals[a.sp.key] = totals.get(a.sp.key, 0) + 1
        births = []
        for a in self.animals:
            sp = a.sp
            if not (a.alive and a.female and a.adult):
                continue
            ckey = (sp.key, self.lives_at_camp(a))
            cap = sp.pop_cap if not ckey[1] else max(8, sp.pop_cap // 2)
            if counts.get(ckey, 0) >= cap or totals.get(sp.key, 0) >= sp.pop_cap * 1.4:
                continue
            if sp.seasonal:
                if season != 0 or a.bred_year == yr:
                    continue
            else:
                if season == 3 or self.day - a.bred_day < sp.breed_interval:
                    continue
            if a.energy < sp.max_energy * 0.5:
                continue
            if self.rng.random() > 0.2:
                continue
            # Animals mostly mate within their own social group: those sharing
            # a home range. This is what lets a camp lineage diverge.
            mate = None
            reach = max(22.0, sp.home_range * 2.5)
            best = 1e9
            for b in self.agrid.near(a.x, a.y, reach):
                if (b.alive and b.sp is sp and not b.female and b.adult
                        and b.penned == a.penned):
                    d = _dist(a.x, a.y, b.x, b.y)
                    if d < reach:
                        score = d * 0.5 + _dist(a.hx, a.hy, b.hx, b.hy)
                        if score < best:
                            mate, best = b, score
            if mate is None:
                continue
            a.bred_year = yr
            a.bred_day = self.day
            a.energy -= sp.max_energy * 0.25
            n = self.rng.randint(*sp.litter)
            n = max(0, min(n, cap - counts.get(ckey, 0)))
            counts[ckey] = counts.get(ckey, 0) + n
            totals[sp.key] = totals.get(sp.key, 0) + n
            for _ in range(n):
                births.append(self._make_young(a, mate))
        self.animals.extend(births)

    def _make_young(self, mother, father):
        sp = mother.sp
        g = mother.genome.child(father.genome, self.rng)
        pup = Animal(self.new_id(), sp, mother.x + self.rng.uniform(-0.5, 0.5),
                     mother.y + self.rng.uniform(-0.5, 0.5), g, 0.0,
                     self.rng.random() < 0.5, self.rng)
        pup.energy = sp.max_energy * 0.6
        pup.hx, pup.hy = mother.hx, mother.hy
        pup.penned = mother.penned
        at_camp = self.lives_at_camp(mother)
        if at_camp:
            pup.familiarity = mother.familiarity * 0.6
            pup.camp_gen = mother.camp_gen + 1
            if pup.piebald:
                self.log(f"{A_(sp.singular)} with a strange patched coat was born near camp.",
                         flag=f"piebald_{sp.key}")
            if mother.penned:
                self.log(f"The first {sp.singular} is born inside the pen.",
                         flag=f"penbirth_{sp.key}")
        return pup

    # ------------------------------------------------------------------ pen
    def _pen_daily(self):
        if self.pen is None or not self.pen.built:
            return
        penned = self.penned()
        milk = 0.0
        for a in penned:
            if a.sp.key == "aurochs" and a.female and a.adult and a.energy > a.sp.max_energy * 0.5:
                milk += 0.5
        if milk > 0:
            self.add_food(milk)
            self.log("Your people have learned to milk the penned aurochs.", flag="milk")
        # Selective culling: when the pen is overfull, and every autumn once
        # the herd is big enough, the animals your people like least are eaten.
        # *Which* ones they like least is the player's choice, and it is what
        # slowly reshapes the herd.
        autumn_cull = (self._day_int % DAYS_PER_YEAR == DAYS_PER_SEASON * 2 + 5)
        excess = len(penned) - PEN_CAPACITY
        if autumn_cull and len(penned) >= 6:
            excess = max(excess, len(penned) // 5)
        if excess > 0:
            mode = self.policies["pen_cull"]
            adults = [a for a in penned if a.adult]
            pool = adults if len(adults) > excess + 2 else penned
            if mode == "calm":
                pool.sort(key=lambda a: a.genome.boldness - a.genome.aggression)
            elif mode == "big":
                pool.sort(key=lambda a: a.genome.size)
            else:
                self.rng.shuffle(pool)
            for a in pool[:excess]:
                self.add_food(a.sp.meat * (0.6 + 0.8 * a.genome.size))
                self.kill_animal(a, "culled")
            what = {"calm": "the wildest", "big": "the smallest",
                    "random": "a few"}[mode]
            self.log(f"Your herders cull {what} of the penned animals for meat.",
                     flag=f"cull_{mode}")

    def _update_penned(self, a, dt):
        p = self.pen
        need = a.sp.metabolism * dt * 1.15
        if self.fodder >= need:
            self.fodder -= need
            a.energy = min(a.sp.max_energy, a.energy + need * 1.3)
        elif a.sp.diet == "grazer":
            # Nibble whatever grows inside the fence.
            i = self.world.index(a.x, a.y)
            g = self.world.grass[i]
            if g > 0.05:
                gain = a.sp.graze_gain * 0.6 * min(1.0, g / 0.5) * dt
                a.energy = min(a.sp.max_energy, a.energy + gain)
                self.world.grass[i] = max(0.0, g - gain * 0.02)
        a.familiarity = min(1.0, a.familiarity + 0.03 * dt)
        a.hx, a.hy = p.cx, p.cy
        if a.tx is None or self._move(a, a.sp.speed * 0.3, dt):
            self._set_target(a, p.x + 0.5 + self.rng.random() * (p.w - 1),
                             p.y + 0.5 + self.rng.random() * (p.h - 1))
        panic = (not a.sp.pennable) or (a.energy < a.sp.max_energy * 0.15)
        if panic and self.rng.random() < (0.6 if not a.sp.pennable else 0.03) * dt * (1 - self.tameness(a)):
            a.penned = False
            a.scared_t = 10.0
            a.familiarity *= 0.3
            a.hx, a.hy = self._random_site(a.sp, 20)
            if not a.sp.pennable:
                self.log(f"{A_('penned ' + a.sp.singular)} panics and smashes its way out. "
                         f"{a.sp.name} will not abide a fence.", flag=f"panic_{a.sp.key}")
            else:
                self.log(f"{A_('starving ' + a.sp.singular)} breaks out of the pen.")

    # ------------------------------------------------------------- animals
    def _update_animal(self, a, dt):
        sp = a.sp
        a.age += dt
        if a.age > a.max_age:
            self.kill_animal(a, "old age")
            return
        a.energy -= sp.metabolism * dt
        if a.energy < -sp.max_energy * 0.4:
            self.kill_animal(a, "starvation")
            return
        if a.scared_t > 0:
            a.scared_t -= dt
        if a.cool > 0:
            a.cool -= dt
        if a.meals > 0:
            a.meals -= a.meals * 0.015 * dt
            settle_at = 1.0 if sp.eats_mice else 2.0
            if (sp.scavenger or sp.eats_mice) and not self.lives_at_camp(a) and a.meals > settle_at:
                self._settle_at_camp(a)
            elif a.meals < 0.15 and self.lives_at_camp(a) and not a.penned \
                    and a.energy < sp.max_energy * 0.3:
                a.hx, a.hy = self._random_site(sp, 30)
                self.log(f"Lean times: some {sp.name.lower()} abandon the camp for the wild.",
                         flag=f"abandon_{sp.key}{self.year}")
        if a.penned:
            self._update_penned(a, dt)
            return
        # Living near people without being harmed breeds familiarity.
        if a.near_h < 15 and a.scared_t <= 0:
            a.familiarity = min(1.0, a.familiarity + FAM_GAIN * dt * (0.5 + a.genome.boldness))
        elif a.near_h > 25:
            a.familiarity = max(0.0, a.familiarity - FAM_DECAY * dt)

        a.think_t -= dt
        if a.think_t <= 0:
            a.think_t = THINK_INTERVAL * (0.8 + 0.4 * self.rng.random())
            self._think_animal(a)
            if not a.alive:
                return

        st = a.state
        if st in ("flee", "chase"):
            speed = sp.flee_speed
        elif st in ("follow", "to_midden", "to_granary", "lurk", "prowl"):
            speed = sp.speed * 2.0
        else:
            speed = sp.speed
        arrived = self._move(a, speed, dt)

        if st == "graze":
            if arrived:
                i = self.world.index(a.x, a.y)
                g = self.world.grass[i]
                if g > 0.08:
                    gain = sp.graze_gain * min(1.0, g / 0.5) * dt
                    a.energy = min(sp.max_energy, a.energy + gain)
                    self.world.grass[i] = max(0.0, g - gain * 0.02)
        elif st == "forage":
            w = self.world
            i = w.index(a.x, a.y)
            t = w.terrain[i]
            seasonal = (1.0, 1.0, 0.9, 0.65)[self.season]
            gain = sp.wild_food * seasonal * sp.habitat.get(t, 0.2) / (1 + a.dens / sp.density_k)
            if sp.diet == "omnivore" and w.forage[i] > 0.05:
                gain += 1.2 * w.forage[i]
                w.forage[i] = max(0.0, w.forage[i] - 0.02 * dt)
            a.energy = min(sp.max_energy, a.energy + gain * dt)
        elif st == "to_midden":
            mp = self.midden_pos
            if mp is None or self.midden <= 0.2:
                a.state = "wander"
            elif _dist(a.x, a.y, *mp) < 1.3:
                a.state = "midden_eat"
        elif st == "midden_eat":
            mp = self.midden_pos
            if mp is None or self.midden <= 0.1 or _dist(a.x, a.y, *mp) > 2.0:
                a.state = "wander"
            else:
                take = min(self.midden, 9.0 * dt)
                self.midden -= take
                a.energy = min(sp.max_energy, a.energy + take)
                a.meals += take / 3.0
                self.visits[sp.key] += dt
                cx, cy = self.camp
                if _dist(*mp, cx, cy) < CAMP_HOME_RADIUS:
                    pull = min(1.0, 0.35 * dt)
                    a.hx += (mp[0] - a.hx) * pull
                    a.hy += (mp[1] - a.hy) * pull
                if self.policies["waste"] == "camp":
                    self.log(f"{A_('bold ' + sp.singular)} has been seen scavenging at the midden.",
                             flag=f"midden_{sp.key}")
                if a.energy >= sp.max_energy * 0.95:
                    a.state = "wander"
        elif st == "to_granary":
            if self.grain <= 0.5:
                a.state = "wander"
            elif _dist(a.x, a.y, *self.granary_pos) < 1.2:
                a.state = "granary_eat"
        elif st == "granary_eat":
            if self.grain <= 0.2 or self.policies["grain"] != "granary":
                a.state = "wander"
            else:
                take = min(self.grain, 0.05 * dt)
                self.grain -= take
                a.energy = min(sp.max_energy, a.energy + 1.4 * dt)
                self.visits[sp.key] += dt
                a.hx += (self.granary_pos[0] - a.hx) * 0.1 * dt
                a.hy += (self.granary_pos[1] - a.hy) * 0.1 * dt
                self.log("Mice have found their way into the granary.", flag="mice_granary")
                if a.energy >= sp.max_energy * 0.95:
                    a.state = "wander"
        elif st == "chase":
            p = a.prey
            if p is None or not p.alive or self.rng.random() < 0.6 * dt:
                a.state = "wander"      # lost it; try again later
                a.prey = None
                a.cool = max(a.cool, 0.5)
            else:
                a.tx, a.ty = p.x, p.y
                if _dist(a.x, a.y, p.x, p.y) < 0.8:
                    # Mice inside the granary have cover.
                    hidden = p.state == "granary_eat"
                    if self.rng.random() < (0.12 if hidden else 0.3):
                        self.kill_animal(p, f"caught by {sp.singular}")
                        a.energy = min(sp.max_energy, a.energy + 1.8)
                        if _dist(p.x, p.y, *self.granary_pos) < 12:
                            a.meals += 0.7
                            self.log("A wildcat was seen hunting mice by the granary.",
                                     flag="cat_mice")
                    a.prey = None
                    a.state = "wander"
        elif st == "follow":
            h = a.follow
            if h is None or not h.alive or h.role != "hunt":
                a.state = "wander"
                a.follow = None
        elif st in ("flee", "prowl") and arrived:
            a.state = "wander"

    def _settle_at_camp(self, a):
        """A scavenger (or mouser) that keeps finding food here makes its den nearby."""
        if a.sp.eats_mice:
            mx, my = self.granary_pos
        else:
            mx, my = self.midden_pos or self.camp
        cx, cy = self.camp
        dx, dy = mx - cx, my - cy
        r = self.rng.uniform(5.0, 9.0)
        ang = math.atan2(dy, dx) + self.rng.uniform(-0.9, 0.9)
        hx, hy = self.world.clamp_pos(mx + math.cos(ang) * r, my + math.sin(ang) * r)
        if not self.world.is_land(hx, hy):
            hx, hy = mx, my
        a.hx, a.hy = hx, hy
        what = "the mice in your stores" if a.sp.eats_mice else "your leavings"
        self.log(f"{A_(a.sp.singular)} has made its den near your camp. It lives off {what}.",
                 flag=f"den_{a.sp.key}")

    def _flee(self, a, fx, fy, fd):
        dx, dy = a.x - fx, a.y - fy
        d = math.hypot(dx, dy) or 1.0
        run = fd * 1.4 + 3.0
        for ang in (0.0, 0.6, -0.6, 1.2, -1.2):
            c, s = math.cos(ang), math.sin(ang)
            ux = (dx * c - dy * s) / d
            uy = (dx * s + dy * c) / d
            tx, ty = self.world.clamp_pos(a.x + ux * run, a.y + uy * run)
            if self.world.is_land(tx, ty):
                break
        a.tx, a.ty = tx, ty
        a.state = "flee"
        a.follow = None
        a.prey = None

    def _wander_target(self, a, radius, cx=None, cy=None):
        w = self.world
        if cx is None:
            cx, cy = a.hx, a.hy
        best, bw = None, -1.0
        for _ in range(5):
            x, y = w.clamp_pos(cx + self.rng.uniform(-radius, radius),
                               cy + self.rng.uniform(-radius, radius))
            hw = a.sp.habitat.get(w.terrain_at(x, y), 0.0) * (0.5 + self.rng.random())
            if hw > bw:
                best, bw = (x, y), hw
        return best

    def _think_animal(self, a):
        sp = a.sp
        rng = self.rng
        state = a.state

        nh, nd = self._nearest_threat(a.x, a.y, 18)
        a.near_h = nd
        fd = self.flight_distance(a)
        if self.is_night:
            fd *= 0.7           # darkness emboldens
        if nh is not None:
            detect = fd * (STALK_FACTOR if nh.state == "stalk" else 1.0)
            if state in ("to_midden", "midden_eat", "granary_eat", "prowl", "chase"):
                detect *= 0.6     # committed: darts in and grabs a mouthful
            if nd < detect and not (state == "follow" and a.follow is nh):
                self._flee(a, nh.x, nh.y, fd)
                return
        if state == "flee":
            return

        neighbours = self.agrid.near(a.x, a.y, 12)

        # Herd alarm: if a herd-mate bolts, bolt too.
        if sp.herd:
            for b in neighbours:
                if b is not a and b.sp is sp and b.state == "flee" and b.alive:
                    if _dist(a.x, a.y, b.x, b.y) < 6:
                        a.tx, a.ty = self.world.clamp_pos(a.x + (b.tx - b.x), a.y + (b.ty - b.y))
                        a.state = "flee"
                        return

        # Mice fear cats.
        if sp.key == "mouse":
            for b in neighbours:
                if b.sp.eats_mice and b.alive and not b.penned and _dist(a.x, a.y, b.x, b.y) < 2.5:
                    self._flee(a, b.x, b.y, 3)
                    return

        # Aggressive animals sometimes go for people who come too close.
        if sp.attacks and nh is not None and nd < 3.0 and a.genome.aggression > 0.3:
            hungry = a.energy < sp.max_energy * 0.5
            p = ((a.genome.aggression - 0.3) ** 2 * 2.0 * (1.5 if hungry else 0.5)
                 * (1 - 0.5 * a.familiarity))
            if rng.random() < p:
                deterred = any(b.sp.key == "wolf" and b.alive and b is not a
                               and self.lives_at_camp(b) and self.tameness(b) > 0.8
                               and _dist(a.x, a.y, b.x, b.y) < 8 for b in neighbours)
                if deterred and sp.key != "wolf":
                    self.log("The camp dogs bark and drive off a threatening animal.",
                             flag="dogs_guard")
                    self._flee(a, nh.x, nh.y, fd + 6)
                    a.scared_t = 6.0
                else:
                    self._animal_attacks(a, nh)
                return

        # Mice are always up for free grain.
        hungry = a.energy < sp.max_energy * (0.95 if sp.raids_grain else 0.7)

        # Tame camp wolves trot after hunters.
        if (sp.key == "wolf" and self.tameness(a) > 0.8 and self.lives_at_camp(a)
                and a.energy > sp.max_energy * 0.45):
            if state == "follow" and a.follow is not None and a.follow.alive \
                    and a.follow.role == "hunt" and a.follow.state in ("seek", "stalk"):
                h = a.follow
                self._set_target(a, h.x + rng.uniform(-1.5, 1.5), h.y + rng.uniform(-1.5, 1.5))
                return
            hunter, hd = self._nearest_human(
                a.x, a.y, 15, lambda h: h.role == "hunt" and h.state in ("seek", "stalk"))
            if hunter is not None:
                a.state = "follow"
                a.follow = hunter
                self._set_target(a, hunter.x, hunter.y)
                self.log(f"A camp wolf trots after {hunter.name} on the hunt.",
                         flag="dog_follow")
                return

        if hungry:
            mp = self.midden_pos
            # Lurking costs time; a desperate animal gives up and hunts instead.
            if state == "lurk" and rng.random() < 0.12 + 0.4 * (1 - a.energy / sp.max_energy) ** 2:
                a.cool = rng.uniform(2.0, 5.0)
            if sp.scavenger and mp is not None and self.midden > 0.5 and a.cool <= 0:
                dm = _dist(a.x, a.y, *mp)
                # Close by, the smell is irresistible; from afar, an occasional
                # hungry animal comes to investigate.
                lure = self.midden / (self.midden + 8.0)
                if (dm < 22 or self.lives_at_camp(a) or state in ("lurk", "to_midden")
                        or rng.random() < 0.02 * lure * math.exp(-(dm - 22) / 25)):
                    if state == "midden_eat":
                        return
                    _, hd = self._nearest_threat(mp[0], mp[1], fd + 2)
                    if hd > fd or dm > fd + hd + 8:
                        # Head in. Flight checks above will turn it back if
                        # people are too close when it gets there.
                        if state != "to_midden":
                            a.state = "to_midden"
                            self._set_target(a, mp[0] + rng.uniform(-0.6, 0.6),
                                             mp[1] + rng.uniform(-0.6, 0.6))
                    else:
                        dx, dy = a.x - mp[0], a.y - mp[1]
                        d = math.hypot(dx, dy) or 1.0
                        r = fd + hd + 1.0
                        a.state = "lurk"
                        self._set_target(a, mp[0] + dx / d * r, mp[1] + dy / d * r)
                        self.visits[sp.key] += 0.05
                        self.log(f"{sp.name} have been seen lurking at the edge of camp.",
                                 flag=f"lurk_{sp.key}")
                    return
            if sp.raids_grain and self.policies["grain"] == "granary" and self.grain > 1.0:
                if state == "granary_eat":
                    return
                dg = _dist(a.x, a.y, *self.granary_pos)
                if dg < 25 or state == "to_granary" or (dg < 70 and rng.random() < 0.02):
                    a.state = "to_granary"
                    gx, gy = self.granary_pos
                    self._set_target(a, gx + rng.uniform(-0.8, 0.8), gy + rng.uniform(-0.8, 0.8))
                    return
            if sp.eats_mice and a.cool <= 0 and self.policies["grain"] == "granary" \
                    and self.visits["mouse"] > 1.0 and state != "prowl" \
                    and a.energy > sp.max_energy * 0.35:
                gx, gy = self.granary_pos
                dg = _dist(a.x, a.y, gx, gy)
                if a.goal == "granary" and rng.random() < 0.005:
                    a.goal = None        # gives up on the idea for now
                if dg > 9 and (dg < 22 or self.lives_at_camp(a) or a.goal == "granary"
                               or rng.random() < 0.03 * math.exp(-(dg - 22) / 25)):
                    # Prowl the outskirts, where house mice forage.
                    a.state = "prowl"
                    a.goal = "granary"
                    dx, dy = a.x - gx, a.y - gy
                    d = math.hypot(dx, dy) or 1.0
                    r = rng.uniform(4, 8)
                    self._set_target(a, gx + dx / d * r, gy + dy / d * r)
                    self.log("Wildcats have been seen prowling near your granary.",
                             flag="cat_prowl")
                    return
            if sp.eats_mice and a.cool <= 0 and rng.random() < 0.5:
                best, bd = None, 7.0
                for b in self.agrid.near(a.x, a.y, 7):
                    if b.alive and b.sp.key == "mouse":
                        d = _dist(a.x, a.y, b.x, b.y)
                        if d < bd:
                            best, bd = b, d
                if best is not None:
                    a.state = "chase"
                    a.prey = best
                    a.tx, a.ty = best.x, best.y
                    a.hx += (best.x - a.hx) * 0.1
                    a.hy += (best.y - a.hy) * 0.1
                    return
            if sp.diet == "grazer":
                self._choose_graze(a, neighbours)
                return
            if state == "forage" and rng.random() < 0.7:
                return
            a.dens = sum(1 for b in neighbours if b.sp is sp and b is not a)
            a.state = "forage"
            a.tx, a.ty = self._wander_target(a, sp.home_range)
            return

        # Not hungry: loaf about the home range.
        if state in ("midden_eat", "granary_eat", "to_midden", "to_granary", "lurk", "chase"):
            a.state = "wander"
        if sp.herd and rng.random() < 0.5:
            self._choose_graze(a, neighbours)
            return
        if rng.random() < 0.25:
            a.state = "wander"
            a.tx, a.ty = self._wander_target(a, sp.home_range * 0.5)

    def _choose_graze(self, a, neighbours):
        w = self.world
        sp = a.sp
        mates = [b for b in neighbours if b.sp is sp and b is not a and b.alive]
        if mates:
            mx = sum(b.x for b in mates) / len(mates)
            my = sum(b.y for b in mates) / len(mates)
        else:
            mx, my = a.hx, a.hy
        i = w.index(a.x, a.y)
        if a.state == "graze" and w.grass[i] > 0.35 and _dist(a.x, a.y, mx, my) < 7:
            return
        best, bs = None, -1e9
        for _ in range(8):
            x, y = w.clamp_pos(a.x + self.rng.uniform(-8, 8), a.y + self.rng.uniform(-8, 8))
            j = w.index(x, y)
            if w.terrain[j] == WATER:
                continue
            score = (w.grass[j] * 3 - _dist(x, y, mx, my) * 0.15
                     - _dist(x, y, a.hx, a.hy) * 0.03)
            if score > bs:
                best, bs = (x, y), score
        if best is not None:
            a.tx, a.ty = best
            a.state = "graze"
            a.hx += (a.x - a.hx) * 0.02
            a.hy += (a.y - a.hy) * 0.02

    def _animal_attacks(self, a, h):
        sp = a.sp
        dmg = 0.25 + 0.35 * a.genome.aggression * (0.6 + 0.8 * a.genome.size)
        h.health -= dmg
        name = self.display_name(a)
        if h.health <= 0:
            self.kill_human(h, f"killed by {a_(name)}")
        else:
            self.log(f"{A_(name)} attacked {h.name}!")
        helpers = [o for o in self.hgrid.near(a.x, a.y, 8) if o.alive and o.adult]
        p_kill = 1 - 0.5 ** (1 + len(helpers))
        if self.rng.random() < p_kill:
            self.kill_animal(a, "killed after attacking")
            self.log(f"Your people kill the {name} that attacked.",
                     flag=f"retaliate_{sp.key}{self.year}")
        else:
            a.scared_t = 15.0
            a.familiarity = 0.0
            self._flee(a, h.x, h.y, self.flight_distance(a))

    # --------------------------------------------------------------- humans
    def _update_human(self, h, dt):
        if h.health < 1.0 and h.hunger < 1:
            h.health = min(1.0, h.health + 0.02 * dt)
        h.task_t += dt
        h.think_t -= dt
        if h.think_t <= 0:
            h.think_t = THINK_INTERVAL * (0.7 + 0.3 * self.rng.random())
            role = h.role
            if role == "gather":
                self._think_gatherer(h)
            elif role == "hunt":
                self._think_hunter(h)
            elif role == "herd":
                self._think_herder(h)
            else:
                self._think_camp(h)
        speed = HUMAN_SPEED
        if h.state == "stalk":
            speed *= 0.5
        if not h.adult:
            speed *= 0.7
        arrived = self._move(h, speed, dt)
        st = h.state
        if st == "gathering" and arrived:
            w = self.world
            i = w.index(h.x, h.y)
            f = w.forage[i]
            amt = GATHER_RATE * (0.5 if self.season == 3 else 1.0) * min(1.0, f / 0.3) * dt
            amt = min(amt, f / FORAGE_PER_UNIT)
            w.forage[i] = max(0.0, f - amt * FORAGE_PER_UNIT)
            if w.terrain[i] == SHORE and self.season in (1, 2):
                h.carry_grain += amt
            else:
                h.carry += amt
        elif st == "cutting" and arrived:
            w = self.world
            i = w.index(h.x, h.y)
            g = w.grass[i]
            amt = 9.0 * min(1.0, g / 0.4) * dt
            w.grass[i] = max(0.0, g - amt * 0.04)
            h.carry += amt
        elif st == "building" and arrived and self.pen is not None and not self.pen.built:
            self.pen.progress += dt
            if self.pen.progress >= PEN_BUILD_DAYS:
                self.pen.built = True
                self.pen_project = False
                self.log("The pen is finished: a ring of stakes and woven brush.")

    def _go_camp(self, h, state="returning"):
        cx, cy = self.camp
        h.state = state
        self._set_target(h, cx + self.rng.uniform(-1.5, 1.5), cy + self.rng.uniform(-1.5, 1.5))

    def add_food(self, amount):
        self.fresh += amount
        self.income_today += amount

    def _deposit(self, h):
        if h.role == "herd":
            self.fodder += h.carry
        else:
            self.add_food(h.carry)
        if h.carry_grain:
            self.income_today += h.carry_grain
            if self.policies["grain"] == "granary":
                room = max(0.0, GRANARY_CAP - self.grain)
                self.grain += min(room, h.carry_grain)
                self.fresh += max(0.0, h.carry_grain - room)
                self.log("Your people store wild grain in a granary pit for the winter.",
                         flag="granary_first")
            else:
                self.fresh += h.carry_grain
        h.carry = 0.0
        h.carry_grain = 0.0

    def _near_camp(self, h, r=2.5):
        return _dist(h.x, h.y, *self.camp) < r

    def _think_gatherer(self, h):
        load = h.carry + h.carry_grain
        if h.state == "returning":
            if self._near_camp(h):
                self._deposit(h)
                h.state = "idle"
            return
        if h.state == "gathering":
            if h.tx is not None and _dist(h.x, h.y, h.tx, h.ty) > 0.1:
                return
            i = self.world.index(h.x, h.y)
            if load >= CARRY_CAP:
                self._go_camp(h)
                return
            if self.world.forage[i] > 0.06:
                return
        if h.state == "to_patch" and _dist(h.x, h.y, h.tx, h.ty) > 0.1:
            return
        patch = self._find_patch(h)
        if patch is None:
            if load > 0:
                self._go_camp(h)
            else:
                self._think_camp(h)
            return
        h.state = "gathering"
        h.tx, h.ty = patch

    def _find_patch(self, h):
        w = self.world
        cx, cy = self.camp
        best, bs = None, 0.0
        grain_bonus = 0.35 if self.policies["grain"] == "granary" else 0.0
        season = self.season
        for _ in range(36):
            x, y = w.clamp_pos(h.x + self.rng.uniform(-12, 12), h.y + self.rng.uniform(-12, 12))
            if self.rng.random() < 0.5:
                x, y = w.clamp_pos(cx + self.rng.uniform(-28, 28), cy + self.rng.uniform(-28, 28))
            i = w.index(x, y)
            t = w.terrain[i]
            if t == WATER:
                continue
            f = w.forage[i]
            if f < 0.15:
                continue
            bonus = grain_bonus if (t == SHORE and season in (1, 2)) else 0.0
            score = f * (1 + bonus) - _dist(x, y, cx, cy) / 70 - _dist(x, y, h.x, h.y) / 120
            if score > bs:
                best, bs = (int(x) + 0.5, int(y) + 0.5), score
        return best

    def _hunt_score(self, h, a):
        mode = self.policies.get(HUNT_POLICY_KEY.get(a.sp.key, ""), "spare")
        d = _dist(h.x, h.y, a.x, a.y)
        t = self.tameness(a)
        if mode == "free":
            return d - t * 12 - a.sp.meat * 0.3 + self.rng.uniform(0, 8)
        if mode == "cull":
            return d * 0.3 + t * 30 - a.genome.aggression * 15
        if mode == "capture":
            t = self.capture_ease(a)
            if not (self.pen and self.pen.built) or t < 0.4:
                return None
            if len(self.penned()) >= PEN_CAPACITY + 2:
                return None
            return d - t * 20
        return None

    def _think_hunter(self, h):
        cx, cy = self.camp
        if h.state == "returning":
            if self._near_camp(h):
                if h.carry > 0:
                    if self.policies["waste"] != "burn":
                        self.midden += h.carry * BUTCHER_SCRAPS
                    self.add_food(h.carry * (1 - BUTCHER_SCRAPS))
                    h.carry = 0.0
                h.state = "idle"
                h.target = None
            return
        a = h.target
        if (a is None or not a.alive or a.penned or h.task_t > HUNT_GIVE_UP_DAYS
                or _dist(a.x, a.y, cx, cy) > HUNT_RADIUS + 8
                or self._hunt_score(h, a) is None):
            if a is not None and h.task_t > HUNT_GIVE_UP_DAYS:
                h.target = None
                self._go_camp(h)      # give up, head home and try again later
                return
            h.target = None
            best, bs = None, 1e9
            for b in self.agrid.near(cx, cy, HUNT_RADIUS):
                if not b.alive or b.penned or not b.sp.huntable:
                    continue
                s = self._hunt_score(h, b)
                if s is not None and s < bs:
                    best, bs = b, s
            if best is None:
                h.state = "seek"
                if h.tx is None or _dist(h.x, h.y, h.tx, h.ty) < 1:
                    self._set_target(h, cx + self.rng.uniform(-20, 20), cy + self.rng.uniform(-20, 20))
                return
            if best is not a:
                h.task_t = 0.0
            h.target = best
            a = best
        d = _dist(h.x, h.y, a.x, a.y)
        h.state = "stalk" if d < 14 else "seek"
        self._set_target(h, a.x, a.y)
        if d > THROW_RANGE:
            return
        dogs = sum(1 for b in self.agrid.near(h.x, h.y, 6)
                   if b.alive and b.state == "follow" and b.follow is h)
        mode = self.policies.get(HUNT_POLICY_KEY.get(a.sp.key, ""), "spare")
        if mode == "capture":
            p = clamp((self.capture_ease(a) - 0.3) * 1.5) * 0.5 + 0.08 * dogs
            if self.rng.random() < p:
                a.penned = True
                a.state = "wander"
                a.tx = a.ty = None
                a.x, a.y = self.pen.cx, self.pen.cy
                self.log(f"{h.name} leads {a_('calm ' + a.sp.singular)} into the pen.",
                         flag=f"capture_{a.sp.key}")
                h.target = None
                self._go_camp(h)
            else:
                a.scared_t = 3.0
            return
        p = min(0.85, 0.4 + 0.12 * dogs)
        if self.rng.random() < p:
            meat = a.sp.meat * (0.6 + 0.8 * a.genome.size)
            self.kill_animal(a, "hunted")
            h.carry = meat
            h.target = None
            self._go_camp(h)
            for b in self.agrid.near(h.x, h.y, 6):
                if b.alive and b.follow is h:
                    b.energy = min(b.sp.max_energy, b.energy + 2.0)
                    b.familiarity = min(1.0, b.familiarity + 0.05)
            if dogs:
                self.log("With dogs at their heels, your hunters bring down prey more easily.",
                         flag="dog_hunt")
        else:
            a.scared_t = 3.0
            # A wounded, angry animal may turn on the hunter.
            if a.sp.attacks and self.rng.random() < 0.12 * a.genome.aggression ** 2:
                self._animal_attacks(a, h)

    def _think_herder(self, h):
        pen = self.pen
        if pen is None:
            self._think_camp(h)
            return
        if not pen.built:
            h.state = "building"
            if h.tx is None or _dist(h.tx, h.ty, pen.cx, pen.cy) > 4:
                self._set_target(h, pen.x + self.rng.random() * pen.w,
                                 pen.y + self.rng.random() * pen.h)
            return
        if h.state == "returning":
            if _dist(h.x, h.y, pen.cx, pen.cy) < 3.5:
                self.fodder += h.carry
                h.carry = 0.0
                h.state = "idle"
            return
        if h.state == "cutting":
            if h.carry >= CARRY_CAP * 1.5:
                h.state = "returning"
                self._set_target(h, pen.cx, pen.cy + pen.h / 2 + 0.5)
                return
            if self.world.grass[self.world.index(h.x, h.y)] > 0.15 or \
                    (h.tx is not None and _dist(h.x, h.y, h.tx, h.ty) > 0.1):
                return
        n = len(self.penned())
        if n == 0 or self.fodder > n * 5:
            h.state = "tending"
            if h.tx is None or _dist(h.x, h.y, h.tx, h.ty) < 0.2:
                self._set_target(h, pen.cx + self.rng.uniform(-4, 4),
                                 pen.cy + pen.h / 2 + 1 + self.rng.uniform(0, 1.5))
            return
        w = self.world
        best, bs = None, -1e9
        for _ in range(20):
            x, y = w.clamp_pos(pen.cx + self.rng.uniform(-15, 15),
                               pen.cy + self.rng.uniform(-15, 15))
            i = w.index(x, y)
            if w.terrain[i] in (WATER, FOREST) or self.in_pen(x, y):
                continue
            s = w.grass[i] - _dist(x, y, pen.cx, pen.cy) / 40
            if s > bs:
                best, bs = (x, y), s
        if best is not None:
            h.state = "cutting"
            h.tx, h.ty = best

    def _think_camp(self, h):
        cx, cy = self.camp
        rng = self.rng
        if h.carry or h.carry_grain:
            if self._near_camp(h):
                self._deposit(h)
            else:
                self._go_camp(h)
                return
        # Defend against attackers / drive off wild animals.
        if self.policies["scavengers"] == "drive" and h.adult:
            best, bd = None, 10.0
            for a in self.agrid.near(cx, cy, 10):
                if not a.alive or a.penned or a.sp.key == "mouse":
                    continue
                if self.stages[a.sp.key] >= a.sp.max_stage and self.lives_at_camp(a):
                    continue
                d = _dist(a.x, a.y, cx, cy)
                if d < bd:
                    best, bd = a, d
            if best is not None:
                h.state = "chase"
                self._set_target(h, best.x, best.y)
                if _dist(h.x, h.y, best.x, best.y) < 2.5:
                    best.scared_t = 10.0
                    best.familiarity = max(0.0, best.familiarity - 0.3)
                    if rng.random() < 0.25:
                        self.kill_animal(best, "driven off and speared")
                    else:
                        self._flee(best, h.x, h.y, self.flight_distance(best))
                    self.log(f"Your people drive {best.sp.name.lower()} away from camp with stones.",
                             flag=f"drive_{best.sp.key}")
                return
        # Toss scraps to bold animals.
        if self.policies["feeding"] and h.task_t > 1.0:
            if self.midden > 1.0:
                for a in self.agrid.near(h.x, h.y, 9):
                    if (a.alive and not a.penned and (a.sp.scavenger or a.sp.eats_mice)
                            and a.state != "flee"
                            and a.scared_t <= 0 and _dist(h.x, h.y, a.x, a.y) < 9):
                        a.energy = min(a.sp.max_energy, a.energy + 1.5)
                        a.familiarity = min(1.0, a.familiarity + 0.06)
                        a.hx += (cx - a.hx) * 0.1
                        a.hy += (cy - a.hy) * 0.1
                        self.midden -= 1.0
                        h.task_t = 0.0
                        self.log(f"{h.name} tosses a scrap to {a_(self.display_name(a))}. "
                                 "It does not run.", flag=f"feed_{a.sp.key}")
                        break
        if h.state != "milling" or h.tx is None or _dist(h.x, h.y, h.tx, h.ty) < 0.2:
            if h.state != "milling" or rng.random() < 0.3:
                h.state = "milling"
                ang = rng.random() * math.tau
                # By night, the camp gathers close around the fire.
                r = rng.random() * (1.5 if self.is_night else CAMP_RADIUS)
                self._set_target(h, cx + math.cos(ang) * r, cy + math.sin(ang) * r)
