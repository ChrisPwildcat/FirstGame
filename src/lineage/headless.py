"""Run the simulation without graphics and print what happened.

    python -m lineage.headless --years 40 --seed 7 --set waste=burn
"""

import argparse
import time

from . import observe
from .config import DAYS_PER_YEAR
from .sim import Simulation
from .species import SPECIES


def parse_value(v):
    if v.lower() in ("true", "on", "yes"):
        return True
    if v.lower() in ("false", "off", "no"):
        return False
    try:
        return int(v)
    except ValueError:
        return v


def run(years=30, seed=1, policies=None, labor=None, pen_year=None, verbose=True,
        on_year=None):
    sim = Simulation(seed)
    for k, v in (policies or {}).items():
        sim.set_policy(k, v)
    sim.labor.update(labor or {})
    t0 = time.time()
    for y in range(years):
        if pen_year is not None and y + 1 == pen_year:
            sim.start_pen()
        if on_year:
            on_year(sim, y + 1)
        sim.advance(DAYS_PER_YEAR)
        if verbose:
            parts = [f"Y{sim.year - 1:>3} pop={len(sim.humans):>2} food={sim.fresh:5.0f}"
                     f" grain={sim.grain:4.0f} midden={sim.midden:4.1f}"]
            for key in SPECIES:
                st = observe.species_stats(sim, key)
                parts.append(f"{key[:4]}={st['total']:>2}/{st['camp']:>2}"
                             f" B{st['B_camp'] if st['camp'] else st['B_all']:.2f}"
                             f"[{sim.stages[key]}]")
            print(" ".join(parts))
        if sim.game_over:
            break
    if verbose:
        print(f"-- {time.time() - t0:.1f}s real time --")
    return sim


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, default=30)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--set", action="append", default=[], help="policy=value")
    ap.add_argument("--labor", action="append", default=[], help="role=count")
    ap.add_argument("--pen-year", type=int, default=None)
    ap.add_argument("--chronicle", action="store_true")
    args = ap.parse_args()
    pol = dict(s.split("=", 1) for s in args.set)
    pol = {k: parse_value(v) for k, v in pol.items()}
    lab = {k: int(v) for k, v in (s.split("=", 1) for s in args.labor)}
    sim = run(args.years, args.seed, pol, lab, args.pen_year)
    if args.chronicle:
        for day, text in sim.chronicle:
            print(f"[{sim.stamp(day)}] {text}")
    print("deaths:", sorted(sim.deaths.items(), key=lambda kv: -kv[1])[:12])


if __name__ == "__main__":
    main()
