# FirstGame

My first attempt at writing a game in python.
Setup tools enabled.
Reticulating splines.

## Lineage: domestication prototype

`src/lineage/` is the first playable prototype of **Lineage**, an evolution-driven
civilization game. The full concept is in [`docs/DESIGN.md`](docs/DESIGN.md).

This prototype tests one question: *is it engaging to watch a species change
because of how your people live?* There is no tech tree and no "domesticate"
button. Every animal carries heritable traits (boldness, aggression, size), and
your band's everyday choices decide which animals survive and breed:

- **Leave scraps by camp** and the boldest wolves start scavenging. The fierce
  ones get killed for biting, the tame ones thrive, and their pups are born at
  camp. Over generations you may end up with dogs, or not.
- **Store grain in a granary** and mice move in. Wildcats may follow them.
- **Build a pen**, capture calm young aurochs, and choose which ones to cull.
  Cull the wildest and you breed cattle. Cull the smallest and you breed size.
- **Deer will never tolerate a fence,** and over-hunting can empty the valley.

You only see what your people would notice ("wary", "growing bolder"). Press
**F3** to see the actual numbers.

### Run it

```bash
pip install -r requirements.txt      # pygame-ce (plain `pygame` also works)
cd src
python -m lineage                    # play
python -m lineage --seed 7           # a specific valley
```

Or install it with `pip install -e .` and run `lineage`.

**Controls:** Space pause · 1–4 speed · WASD / arrows / right-drag to pan ·
mouse wheel to zoom · click an animal or person to inspect them · C to center on camp ·
H for help · F3 for numbers · R for a new world.

### Headless runs (for tuning)

```bash
cd src
python -m lineage.headless --years 40 --seed 2 --chronicle
python -m lineage.headless --years 40 --set grain=granary --set feeding=true
python -m lineage.headless --years 40 --set hunt_aurochs=capture --labor herd=1 --pen-year 3
```

### Tests

```bash
python -m pytest        # from the repo root; takes about a minute and a half
```

### Code map

| File | What it does |
|---|---|
| `src/lineage/sim.py` | The simulation: people, animals, camp, midden, granary, pen, breeding |
| `src/lineage/species.py` | Species as bundles of behaviour (diet, flight distance, herd, pen tolerance) |
| `src/lineage/genetics.py` | Heritable traits and inheritance |
| `src/lineage/world.py` | River-valley generation, vegetation, seasons |
| `src/lineage/observe.py` | Domestication stages and how traits are described in words |
| `src/lineage/game.py` | Pygame front end |
| `src/lineage/headless.py` | Command-line runner for balancing |
| `src/lineage/config.py` | Tunable constants |
