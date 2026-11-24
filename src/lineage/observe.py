"""How your people *perceive* the animals around them.

Per the design doc's anti-min-max principle, the player sees tendencies in
words ("wary", "bold", growing bolder) rather than exact numbers. A debug view
can show the numbers.
"""

import math

from .config import CAMP_HOME_RADIUS
from .species import SPECIES

STAGES = ("Wild", "Wary", "Camp followers", "Tame", "Domesticated")

STAGE_UP = {
    1: "{name} have been seen watching your camp.",
    2: "Some {lname} now live off your camp and its leavings.",
    3: "The camp {lname} have grown tame. They barely flinch at your people.",
    4: "The camp {lname} are something new now. Your people call them {dname}.",
}
SPECIAL_UP = {
    ("mouse", 2): "Mice have made a home in your stores. They are house mice now.",
    ("cat", 4): "The wildcats that hunt your granary have become cats. They choose to stay.",
    ("aurochs", 4): "Generations in the pen have changed the aurochs. They are cattle now.",
    ("boar", 4): "The boar raised at camp are calmer, fatter beasts. Your people call them pigs.",
    ("deer", 2): "A few deer graze near camp, but they will never stand a fence.",
}
STAGE_DOWN = "The {lname} around camp are drifting back to the wild."


def _mean(vals):
    return sum(vals) / len(vals) if vals else 0.0


def camp_population(sim, key):
    cx, cy = sim.camp
    return [a for a in sim.animals
            if a.alive and a.sp.key == key
            and (a.penned or math.hypot(a.hx - cx, a.hy - cy) < CAMP_HOME_RADIUS)]


def species_stats(sim, key):
    allp = [a for a in sim.animals if a.alive and a.sp.key == key]
    camp = camp_population(sim, key)
    return {
        "total": len(allp),
        "camp": len(camp),
        "penned": sum(1 for a in camp if a.penned),
        "B_all": _mean([a.genome.boldness for a in allp]),
        "A_all": _mean([a.genome.aggression for a in allp]),
        "B_camp": _mean([a.genome.boldness for a in camp]),
        "A_camp": _mean([a.genome.aggression for a in camp]),
        "F_camp": _mean([a.familiarity for a in camp]),
        "S_camp": _mean([a.genome.size for a in camp]),
        "gen": max([a.camp_gen for a in camp], default=0),
    }


def _meets(stage, st, visits, slack):
    n = st["camp"]
    if stage == 1:
        return visits > 0.5 or n >= 1
    if stage == 2:
        return n >= 3 and st["B_camp"] > 0.40 - slack
    if stage == 3:
        return (n >= 4 and st["B_camp"] > 0.48 - slack and st["A_camp"] < 0.36 + slack
                and st["F_camp"] > 0.45 - slack)
    if stage == 4:
        return (n >= 5 and st["B_camp"] > 0.58 - slack and st["A_camp"] < 0.30 + slack
                and st["F_camp"] > 0.55 - slack and st["gen"] >= 4)
    return True


def update_stages(sim):
    for key, sp in SPECIES.items():
        st = species_stats(sim, key)
        cur = sim.stages[key]
        new = 0
        for s in range(1, sp.max_stage + 1):
            slack = 0.05 if s <= cur else 0.0   # hysteresis: easier to keep than to gain
            if _meets(s, st, sim.visits[key], slack):
                new = s
            else:
                break
        if new == cur:
            continue
        # Move at most one stage per check so the story reads naturally.
        new = cur + 1 if new > cur else cur - 1
        sim.stages[key] = new
        if new > cur:
            msg = SPECIAL_UP.get((key, new)) or STAGE_UP[new]
        else:
            msg = STAGE_DOWN if new >= 1 else None
        if msg:
            flag = f"stage_{key}_{new}_{'up' if new > cur else 'down'}"
            if new > cur and new >= 2:
                flag = None   # meaningful milestones may recur after a loss
            sim.log(msg.format(name=sp.name, lname=sp.name.lower(),
                               dname=sp.domestic_name.lower()), flag=flag)


def record_year(sim):
    for key in SPECIES:
        st = species_stats(sim, key)
        st["year"] = sim.year
        sim.history[key].append(st)


# ---------------------------------------------------------------- wording
def boldness_word(b):
    for limit, word in ((0.2, "skittish"), (0.32, "wary"), (0.44, "curious"),
                        (0.56, "bold"), (0.7, "trusting")):
        if b < limit:
            return word
    return "devoted"


def aggression_word(a):
    for limit, word in ((0.18, "gentle"), (0.3, "calm"), (0.42, "testy"),
                        (0.55, "fierce")):
        if a < limit:
            return word
    return "savage"


def size_word(s):
    if s < 0.38:
        return "small"
    if s > 0.62:
        return "large"
    return ""


def trend(sim, key):
    """Compare camp (or overall) boldness with a few years ago."""
    hist = sim.history[key]
    if len(hist) < 2:
        return ""
    now = species_stats(sim, key)
    past = hist[max(0, len(hist) - 4)]
    field = "B_camp" if now["camp"] >= 3 and past["camp"] >= 3 else "B_all"
    delta = now[field] - past[field]
    if delta > 0.03:
        return "growing bolder"
    if delta < -0.03:
        return "growing warier"
    return ""


def describe_species(sim, key, debug=False):
    sp = SPECIES[key]
    st = species_stats(sim, key)
    stage = sim.stages[key]
    stage_name = STAGES[stage]
    if key == "mouse" and stage == 2:
        stage_name = "House mice"
    if key == "deer" and stage == 2:
        stage_name = "Graze near camp"
    name = sim.species_name(key)
    camp_pop = st["camp"] >= 2
    b = st["B_camp"] if camp_pop else st["B_all"]
    a = st["A_camp"] if camp_pop else st["A_all"]
    temper = f"{boldness_word(b)}, {aggression_word(a)}"
    if camp_pop and size_word(st["S_camp"]):
        temper += f", {size_word(st['S_camp'])}"
    if st["total"] == 0:
        seen = "none left"
    elif st["total"] < 4:
        seen = "rarely seen"
    elif st["total"] < 15:
        seen = "a few around"
    else:
        seen = "plentiful"
    line = {
        "key": key,
        "name": name,
        "stage": stage,
        "stage_name": stage_name,
        "temper": temper,
        "trend": trend(sim, key),
        "seen": seen,
        "camp": st["camp"],
        "penned": st["penned"],
        "color": sp.color,
    }
    if debug:
        line["debug"] = (f"n={st['total']} camp={st['camp']} B={b:.2f} A={a:.2f} "
                         f"F={st['F_camp']:.2f} gen={st['gen']}")
    return line
