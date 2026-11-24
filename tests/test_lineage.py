"""Tests for the Lineage domestication prototype.

The simulation is deterministic for a given seed, so the behavioural tests
below check that the *mechanisms* produce the expected direction of change.
"""

import random

import pytest

from lineage import observe
from lineage.config import DAYS_PER_YEAR
from lineage.genetics import Genome
from lineage.sim import Simulation
from lineage.species import SPECIES
from lineage.world import WATER


def run(seed, years, policies=None, labor=None, pen_year=None):
    sim = Simulation(seed)
    for k, v in (policies or {}).items():
        sim.set_policy(k, v)
    sim.labor.update(labor or {})
    for y in range(years):
        if pen_year is not None and y + 1 == pen_year:
            sim.start_pen()
        sim.advance(DAYS_PER_YEAR)
    return sim


# ------------------------------------------------------------------ units
def test_child_traits_stay_in_range_and_track_parents():
    rng = random.Random(0)
    a = Genome(0.9, 0.1, 0.5)
    b = Genome(0.7, 0.3, 0.5)
    kids = [a.child(b, rng) for _ in range(2000)]
    assert all(0.0 <= k.boldness <= 1.0 and 0.0 <= k.aggression <= 1.0 for k in kids)
    mean_b = sum(k.boldness for k in kids) / len(kids)
    assert abs(mean_b - 0.8) < 0.03


def test_world_and_camp_are_deterministic_and_on_land():
    s1, s2 = Simulation(42), Simulation(42)
    assert s1.world.terrain == s2.world.terrain
    assert s1.camp == s2.camp
    assert s1.world.terrain_at(*s1.camp) != WATER


def test_simulation_is_deterministic():
    a, b = run(7, 2), run(7, 2)
    assert len(a.animals) == len(b.animals)
    assert len(a.humans) == len(b.humans)
    assert a.chronicle == b.chronicle


def test_flight_distance_shrinks_with_tameness():
    sim = Simulation(1)
    wolf = next(x for x in sim.animals if x.sp.key == "wolf")
    wolf.energy = wolf.sp.max_energy
    wolf.genome.boldness = 0.2
    wary = sim.flight_distance(wolf)
    wolf.genome.boldness = 0.8
    bold = sim.flight_distance(wolf)
    assert bold < wary / 3


def test_policies_cycle_and_waste_change_abandons_midden():
    sim = Simulation(1)
    sim.midden = 20
    sim.set_policy("waste", "burn")
    assert sim.midden == 0 and sim.midden_pos is None


def test_species_descriptions_have_no_numbers_unless_debug():
    sim = Simulation(3)
    for key in SPECIES:
        d = observe.describe_species(sim, key)
        assert "debug" not in d
        assert not any(ch.isdigit() for ch in d["temper"])


# -------------------------------------------------------------- behaviour
@pytest.fixture(scope="module")
def midden_run():
    return run(1, 20)


def test_band_survives_two_decades(midden_run):
    assert midden_run.humans, "the default band should not starve within 20 years"


def test_camp_wolves_are_bolder_than_wild_wolves(midden_run):
    st = observe.species_stats(midden_run, "wolf")
    assert st["camp"] >= 3
    wild = [a.genome.boldness for a in midden_run.animals
            if a.sp.key == "wolf" and not midden_run.lives_at_camp(a)]
    assert st["B_camp"] > sum(wild) / len(wild) + 0.1
    assert midden_run.stages["wolf"] >= 2


def test_burning_scraps_prevents_camp_wolves():
    sim = run(1, 20, {"waste": "burn"})
    assert observe.species_stats(sim, "wolf")["camp"] == 0
    assert sim.stages["wolf"] <= 1


def test_granary_draws_in_house_mice():
    sim = run(1, 12, {"grain": "granary"})
    assert observe.species_stats(sim, "mouse")["camp"] >= 10
    assert sim.stages["mouse"] >= 1


def test_selective_culling_makes_penned_aurochs_calmer():
    sim = run(1, 30, {"hunt_aurochs": "capture", "pen_cull": "calm"},
              {"herd": 1, "camp": 1}, pen_year=3)
    hist = [h for h in sim.history["aurochs"] if h["penned"] >= 4]
    assert len(hist) >= 5, "the pen should hold a herd for years"
    first, last = hist[0], hist[-1]
    assert last["B_camp"] > first["B_camp"] + 0.1
    assert last["A_camp"] < first["A_camp"]


def test_deer_will_not_stay_penned():
    sim = Simulation(2)
    sim.start_pen()
    sim.pen.built = True
    deer = [a for a in sim.animals if a.sp.key == "deer"][:3]
    for d in deer:
        d.penned = True
        d.x, d.y = sim.pen.cx, sim.pen.cy
    sim.fodder = 500
    sim.advance(40)
    assert not any(d.alive and d.penned for d in deer)
