"""Species are bundles of behaviour, not unit types.

Whether a species *can* be domesticated falls out of these numbers: diet,
temperament, flight distance, herd structure and whether it tolerates a pen.
"""

from dataclasses import dataclass, field

from .world import FOREST, GRASS, HILLS, SHORE


@dataclass(frozen=True)
class Species:
    key: str
    name: str            # plural, wild
    singular: str
    domestic_name: str   # plural name once domesticated
    domestic_singular: str
    diet: str            # carnivore | grazer | omnivore | granivore
    color: tuple
    radius: float        # draw size in tiles
    speed: float         # tiles/day, unhurried
    flee_speed: float
    base_flight: float   # flight distance (tiles) of a fully wild animal
    mature_age: float    # days
    max_age: float       # days
    litter: tuple
    seasonal: bool       # breeds once a year in spring
    breed_interval: float  # days between litters when not seasonal
    metabolism: float    # energy / day
    max_energy: float
    meat: float
    boldness: tuple      # (mean, sd) of the starting population
    aggression: tuple
    pop_cap: int
    initial: int
    group_size: tuple
    habitat: dict = field(default_factory=dict)
    home_range: float = 14.0
    wild_food: float = 1.0     # abstract foraging gain per day
    density_k: float = 4.0     # crowding softens foraging gain
    graze_gain: float = 0.0    # grazers: gain per day on lush grass
    huntable: bool = False
    scavenger: bool = False    # will feed at a midden
    herd: bool = False
    eats_mice: bool = False
    raids_grain: bool = False
    attacks: bool = True
    pennable: bool = True      # tolerates confinement
    max_stage: int = 4
    spawn_far: float = 22.0


WOLF = Species(
    key="wolf", name="Wolves", singular="wolf",
    domestic_name="Dogs", domestic_singular="dog",
    diet="carnivore", color=(150, 150, 158), radius=0.55,
    speed=6.0, flee_speed=14.0, base_flight=15.0,
    mature_age=120, max_age=960, litter=(2, 5), seasonal=True, breed_interval=0,
    metabolism=1.0, max_energy=6.0, meat=4.0,
    boldness=(0.28, 0.10), aggression=(0.42, 0.12),
    pop_cap=30, initial=12, group_size=(3, 5),
    habitat={FOREST: 1.0, GRASS: 0.6, HILLS: 0.8, SHORE: 0.5},
    home_range=16, wild_food=3.6, density_k=8.0,
    scavenger=True,
)

WILDCAT = Species(
    key="cat", name="Wildcats", singular="wildcat",
    domestic_name="Cats", domestic_singular="cat",
    diet="carnivore", color=(196, 150, 92), radius=0.4,
    speed=5.0, flee_speed=11.0, base_flight=10.0,
    mature_age=120, max_age=960, litter=(2, 4), seasonal=True, breed_interval=0,
    metabolism=0.6, max_energy=4.0, meat=1.0,
    boldness=(0.30, 0.10), aggression=(0.32, 0.10),
    pop_cap=20, initial=8, group_size=(2, 2),
    habitat={FOREST: 0.8, GRASS: 0.7, SHORE: 0.6, HILLS: 0.5},
    home_range=12, wild_food=1.8, density_k=7.0,
    eats_mice=True, scavenger=False, attacks=False, spawn_far=16.0,
)

MOUSE = Species(
    key="mouse", name="Field mice", singular="field mouse",
    domestic_name="House mice", domestic_singular="house mouse",
    diet="granivore", color=(128, 104, 82), radius=0.22,
    speed=4.0, flee_speed=8.0, base_flight=3.0,
    mature_age=20, max_age=200, litter=(4, 7), seasonal=False, breed_interval=16,
    metabolism=0.3, max_energy=2.0, meat=0.0,
    boldness=(0.35, 0.10), aggression=(0.05, 0.03),
    pop_cap=70, initial=24, group_size=(3, 6),
    habitat={GRASS: 1.0, SHORE: 1.0, FOREST: 0.5, HILLS: 0.3},
    home_range=8, wild_food=1.0, density_k=20.0,
    raids_grain=True, attacks=False, pennable=False, max_stage=2, spawn_far=12.0,
)

AUROCHS = Species(
    key="aurochs", name="Aurochs", singular="aurochs",
    domestic_name="Cattle", domestic_singular="cow",
    diet="grazer", color=(92, 62, 40), radius=0.8,
    speed=4.0, flee_speed=11.0, base_flight=12.0,
    mature_age=240, max_age=1800, litter=(1, 1), seasonal=True, breed_interval=0,
    metabolism=1.0, max_energy=8.0, meat=12.0,
    boldness=(0.22, 0.10), aggression=(0.40, 0.12),
    pop_cap=45, initial=24, group_size=(7, 9),
    habitat={GRASS: 1.0, SHORE: 1.0, FOREST: 0.2, HILLS: 0.4},
    home_range=20, graze_gain=2.6, huntable=True, herd=True,
)

DEER = Species(
    key="deer", name="Red deer", singular="red deer",
    domestic_name="Red deer", domestic_singular="red deer",
    diet="grazer", color=(166, 98, 58), radius=0.6,
    speed=5.0, flee_speed=16.0, base_flight=16.0,
    mature_age=120, max_age=1440, litter=(1, 1), seasonal=True, breed_interval=0,
    metabolism=0.8, max_energy=6.0, meat=7.0,
    boldness=(0.18, 0.08), aggression=(0.15, 0.08),
    pop_cap=55, initial=24, group_size=(5, 8),
    habitat={GRASS: 0.9, FOREST: 0.9, SHORE: 0.7, HILLS: 0.5},
    home_range=22, graze_gain=2.2, huntable=True, herd=True,
    attacks=False, pennable=False, max_stage=2,
)

BOAR = Species(
    key="boar", name="Wild boar", singular="boar",
    domestic_name="Pigs", domestic_singular="pig",
    diet="omnivore", color=(70, 60, 56), radius=0.6,
    speed=5.0, flee_speed=12.0, base_flight=13.0,
    mature_age=150, max_age=1200, litter=(3, 6), seasonal=True, breed_interval=0,
    metabolism=1.0, max_energy=6.0, meat=6.0,
    boldness=(0.30, 0.10), aggression=(0.52, 0.12),
    pop_cap=30, initial=10, group_size=(3, 4),
    habitat={FOREST: 1.0, SHORE: 0.6, GRASS: 0.4, HILLS: 0.3},
    home_range=14, wild_food=2.4, density_k=10.0,
    huntable=True, scavenger=True,
)

SPECIES = {s.key: s for s in (WOLF, WILDCAT, MOUSE, AUROCHS, DEER, BOAR)}
HUNTABLE = [s.key for s in SPECIES.values() if s.huntable]
