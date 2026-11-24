"""Tunable constants for the Lineage domestication prototype.

Units: distances are in tiles, time is in game days.
"""

WORLD_W = 128
WORLD_H = 96

DAYS_PER_YEAR = 120
SEASON_NAMES = ("Spring", "Summer", "Autumn", "Winter")
DAYS_PER_SEASON = DAYS_PER_YEAR // 4

# Largest simulation step. Frames that cover more time are sub-stepped.
MAX_STEP = 0.25
THINK_INTERVAL = 0.3

# --- Camp -----------------------------------------------------------------
CAMP_RADIUS = 3.5          # where camp keepers mill about
CAMP_HOME_RADIUS = 18      # animals whose home range centres within this "live at camp"

# --- People ---------------------------------------------------------------
HUMAN_SPEED = 15.0
HUMAN_CAP = 30
ADULT_AGE = 13             # years
GATHER_RATE = 7.5          # food units per day on a rich patch
CARRY_CAP = 10.0
FORAGE_PER_UNIT = 0.06     # tile forage consumed per food unit gathered
THROW_RANGE = 5.0
STALK_FACTOR = 0.22        # stalking hunters are noticed at this fraction of flight distance
HUNT_GIVE_UP_DAYS = 6.0
HUNT_RADIUS = 42

# --- Food -----------------------------------------------------------------
FRESH_SPOIL = 0.035        # per day (meat, berries, ungranaried grain)
GRAIN_SPOIL = 0.003        # per day in a granary
GRANARY_CAP = 300.0
MIDDEN_DECAY = 0.05
SCRAP_FRACTION = 0.45      # scraps produced per unit of fresh food eaten
BUTCHER_SCRAPS = 0.25      # scraps produced per unit of meat butchered

# --- Animals --------------------------------------------------------------
FAMILIARITY_WEIGHT = 0.3   # how much learned familiarity adds to effective tameness
FAM_GAIN = 0.012           # per day while living near people unharmed
FAM_DECAY = 0.004          # per day while far from people
MUTATION = 0.06

# --- Pen ------------------------------------------------------------------
PEN_CAPACITY = 14
PEN_BUILD_DAYS = 25.0      # labour-days
PEN_W, PEN_H = 6, 5

DEFAULT_POLICIES = {
    "waste": "camp",        # camp | far | burn
    "scavengers": "tolerate",  # tolerate | drive
    "feeding": False,       # toss scraps to bold animals
    "grain": "fresh",       # fresh | granary
    "hunt_aurochs": "free",  # free | cull | spare | capture
    "hunt_deer": "free",
    "hunt_boar": "free",
    "pen_cull": "calm",     # calm | big | random
}

# Gathering is the default job: every adult not assigned elsewhere gathers.
DEFAULT_LABOR = {"hunt": 2, "herd": 0, "camp": 2}
