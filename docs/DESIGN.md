# Lineage — Game Design Document

> Working title. Living document: add to it as ideas develop.

## 1. Vision

A **real-time** civilization game: a mix of Age of Empires' moment-to-moment play and Civilization's sweep through history. It starts in prehistory and can run as far as humanity's long-term future.

The game is built on **evolution**, not a tech tree. Your people don't research progress from a preset list. Progress *emerges* from what they actually do, where they live, and what happens to them. The world itself is the main opponent, and the measure of success is **persistence**: how long your lineage survives and thrives.

### Core pillars

1. **You cause it, you don't unlock it.** Domestication, discovery and culture come from sustained behavior in the simulation, not from menu choices.
2. **Geography is destiny, but not a cage.** Climate, terrain and local species shape each start into a different puzzle.
3. **Non-zero-sum.** Other civilizations can be rivals, partners or absorbed neighbors. Beating them is not the same as winning.
4. **Strength today creates vulnerability tomorrow.** Every success sets up the next crisis, the way it does in evolution.
5. **Plausible, not accurate.** Realism exists for flavor and intuition. When it conflicts with fun, fun wins.
6. **Understanding beats min-maxing.** The best players read the system; they don't exploit a spreadsheet.

### Touchstones

- **Age of Empires II:** real-time play, an explored map that grows, the feeling of a settlement expanding.
- **Civilization:** epic time scale, many paths, "one more turn" pull.
- **SimCity:** the system is the opponent, and building is fun with no need for war.
- **Guns, Germs, and Steel** (Jared Diamond): geography and domesticable species as the roots of history.
- **Timberborn:** a colony builder where the environment (droughts, water management) is the real challenge, and success comes from engineering a resilient settlement rather than beating rivals.

---

## 2. The World

### 2.1 Generation

- The **whole planet is generated at game start**, because the climate simulation needs the full map. It is hidden by fog of war and revealed through exploration.
- Generation follows real climate logic: **latitude, elevation, rainfall, ocean currents, rivers, prevailing winds**.
- **Biomes** come from that climate: tundra, taiga, temperate forest, grassland, steppe, desert, savanna, rainforest, highlands, wetlands, coasts, river valleys.
- **Continent shape matters.** Ideas, crops and animals spread easily **east–west** across similar climates and slowly **north–south** across climate bands.

### 2.2 Species pools

Each biome has its own pool of wild animals and plants. Species are defined by **traits, not fixed unit types** (see §3). Examples:

- Temperate river valleys: wild cattle, wild grains, wolves, boar.
- Highlands: llama/camel-like grazers, tubers.
- Dense rainforest: rich in species but few large domesticable animals.
- Steppe: wild horses, hardy grasses.

Species may be **procedurally generated** from trait templates, so no two worlds have quite the same ecology.

### 2.3 Starting density and territory

Population density comes from **carrying capacity** (how much food the land produces). Starts are not made equal; they come with **tradeoffs**:

| Start type | Advantages | Disadvantages |
|---|---|---|
| Sparse (desert, tundra) | Huge, barely contested territory early | Isolation slows idea exchange; small populations can lose knowledge |
| Dense (fertile river valley) | Fast growth, frequent contact, quick idea spread | Competition, conflict pressure, disease |
| Middle (forest, grassland) | Balanced | Fewer extremes to exploit |

**Design goal:** every start can work, and every start *plays differently*.

---

## 3. Domestication

### 3.1 Animals as behavior and genes

Every species, and every individual animal, carries **heritable traits**:

- **Flight distance:** how close humans can get before it bolts.
- **Temperament:** docile ↔ aggressive.
- **Social structure:** herds with a replaceable leader vs. solitary or territorial animals.
- **Diet:** grazers are cheap to keep; carnivores compete with you for food.
- **Captive breeding:** whether it will breed when confined.
- **Growth rate, size, hardiness, disease load.**

Offspring inherit their parents' traits with variation. **Selection pressure changes populations over generations**, whether the player means it to or not.

### 3.2 The three pathways

Based on real archaeological models of how domestication happened:

1. **Commensal (accidental):** settlement creates niches, and opportunistic species move in.
   - Waste middens → scavenging wolves → over generations, tolerant camp dogs.
   - Grain stores → mice → cats.
   - Pigeons, rats, sparrows and other urban species.
   - The player never "chose" these. They come from *how* the player lives.
2. **Prey (semi-intentional):** hunting turns into managing.
   - Sparing young and females, following herds seasonally, culling selectively.
   - Over time a hunted herd becomes a herded one.
3. **Directed (intentional):** deliberate capture, penning and selective breeding.
   - Requires knowledge, infrastructure (pens, fodder) and patience.
   - Domestic species can then be bred toward goals (size, milk, wool, speed, temperament).

The same applies to **plants**: gathering → tending wild stands → sowing → selection. Some crops start as **weeds in other crops' fields** (as rye did).

### 3.3 Early choices as flavor

There is no required checklist of choices. Early decisions just leave a **trail**:

- Settle or stay nomadic?
- Store food? Where?
- Where does waste go?
- Tolerate scavengers or drive them off?
- Which animals get spared, fed or culled?

Two players in the same valley can end up with **different companion species and different cultures**.

### 3.4 Domestication can go wrong

- Breeding aggressive lines, inbreeding and loss of hardiness.
- **Zoonotic disease:** illnesses jumping from livestock to people.
- Overgrazing and habitat damage.
- Feral reversion when animals are neglected.

---

## 4. Human Co-Evolution

Your people evolve along with their environment and practices:

- **Dairying** → lactose tolerance spreads over generations.
- **Living close to livestock** → disease resistance, but also more disease exposure early on.
- **Diet and climate** → hardiness, cold or heat adaptation.
- **Isolation vs. contact** → different immunities. Contact between long-separated peoples can be catastrophic (as in the Columbian exchange).

These are **lineage traits** that give each civilization its own identity, recording what has actually happened to it.

---

## 5. Discovery Without a Tech Tree

### 5.1 Knowledge from practice

Every activity builds experience in **practice tags**, for example:

`heat` · `cutting` · `containers` · `fiber` · `binding` · `fermentation` · `soil` · `water` · `animal-handling` · `observation` · `counting` · `pigment` · `shaping`

Your people get better at what they do repeatedly.

### 5.2 Discoveries come from overlap

Discoveries "crystallize" when **practices, local materials and circumstances** line up. They can't be picked from a list.

- `heat` + clay-lined storage pits → **fired pottery**
- stored grain + wet season + `containers` → **fermentation**
- flint knapping near hearths → **heat-treated stone**
- `fiber` + `binding` → **cordage → nets, snares, textiles**
- `animal-handling` + `binding` → **harness**

Some discoveries are **accidents** that a player can notice and pursue, or ignore.

### 5.3 Innovations are made of parts, not names

An innovation is **material + form + technique + purpose**, with stats determined by those parts.

- A "cutting tool" can be obsidian, flint, shell, bronze or iron, and each has a different edge, durability and cost.
- Two civilizations solving the same problem arrive at **different solutions** that fit their environment.

### 5.4 The player directs attention, not research

The player chooses **what people spend time on**, which builds practices. Discovery follows from that. The player is an inventor's patron, not someone working through a checklist.

### 5.5 Knowledge lives in people

- Knowledge is held by **individuals and communities**, then later by institutions and writing.
- If a population crashes, or a specialist dies with no apprentices, **knowledge can be lost** (the Tasmania effect).
- **Contact spreads ideas.** Trade, migration and intermarriage carry practices between peoples.
- Conquest can **destroy** knowledge as easily as capture it.

### 5.6 Later eras

Formal research eventually becomes possible: writing, institutions, science. It keeps the same principles. Research builds on your actual practices and materials, so it explores directions instead of buying preset inventions.

---

## 6. Time and Scale

The game is **continuous real-time**. **Spatial and temporal scale shift as the civilization grows**:

| Phase | You control | Rough time scale |
|---|---|---|
| Band | Individuals, a camp | ~1 minute ≈ a season |
| Settlement | Villages, herds, fields | ~1 minute ≈ a year |
| Region | Towns, trade routes, territory | ~1 minute ≈ years |
| Civilization | Cities, provinces, institutions | ~1 minute ≈ decades |
| Planetary | Global systems | variable |

The camera and clock pull back smoothly. Exploration reveals more of the map in the Age of Empires style.

---

## 7. The World as Opponent

### 7.1 Threats scale with you

| Scale | Example threats |
|---|---|
| Local | Predators, a harsh winter, a failed hunt, injury |
| Regional | Drought, overgrazing, floods, plague carried by trade |
| Continental | Deforestation, soil exhaustion, climate shifts, megafauna collapse |
| Global | Climate change, pandemics, weapons of mass destruction |
| Cosmic | Asteroid and comet impacts, and eventually solar expansion |

Many threats are **caused by your own success**: overhunting drives extinctions, herds bring disease, farming exhausts soil, industry changes the atmosphere.

### 7.2 Climate

- An actual atmosphere and land-use model with **lag and inertia**: consequences arrive decades after their causes.
- Effects hit **what you've built**: crops and livestock adapted to your climate fail, coastlines flood, disease ranges shift, rainfall belts move.
- Natural climate swings also happen (ice ages ending, multi-decade droughts), independent of player action.
- Avoid a single "sea-level meter." Climate has to change how the game *plays*.

### 7.3 Cosmic threats: dangerous but fair

- Impact risk is **zero early** and **rises after a game-time threshold**.
- **Astronomy and observation** buy warning time. **Technology and cooperation** buy a response.
- Impacts must be **telegraphed**. Failure should feel like "I saw it coming and wasn't ready," never "the dice hated me."
- **Solar expansion** is the final horizon: an optional epilogue for lineages that last long enough.

---

## 8. Other Peoples: Conflict and Cooperation

### 8.1 Non-zero-sum by design

Other civilizations are not just obstacles. Possible relationships:

- **Trade partners:** exchange goods, species and ideas.
- **Absorbed neighbors:** if your society offers a better life (food security, safety, culture), their people **migrate to you, intermarry and adopt your practices**, and whole groups can fold in. *This keeps the satisfying "map turns my color" feeling without war.*
- **Rivals:** competing for the same land and resources.
- **Enemies:** raids, defense, war.

### 8.2 War is a gamble with a ceiling

Conquest is an **easy early path** with built-in long-term costs:

- **Resentful populations** that resist, rebel or slow production.
- **Lost knowledge:** conquered specialists and practices disappear.
- **Monoculture:** one crop and livestock line across an empire means one blight or disease can take out everything (e.g. the Irish potato famine).
- **Militarized institutions** that are good at war and bad at cooperation and adaptation.

### 8.3 Global threats need many hands

Late-game threats (climate, pandemics, impacts) are **too big for one civilization**. Survival needs **diversity of knowledge, species and approaches**, plus cooperation. A player who conquered the world may have won against other civilizations and lost against the world.

---

## 9. Victory and Scoring

- The primary measure is **Persistence**: how long the lineage survives and thrives.
- Possible secondary measures, each a different way to be remembered:
  - **Reach:** how far your people, practices and species spread (including through absorption and trade).
  - **Legacy:** distinctive creations: domesticated species, innovations, cultural works.
  - **Resilience:** crises survived.
- A traditional "victory screen" is optional. The game should be fun to play with no end goal, as SimCity is.

---

## 10. Anti-Min-Max Principles

1. **Over-optimization creates its own problems.** Max one crop → monoculture risk. Max herds → overgrazing. Max military → resentment and lost knowledge.
2. **Imprecise information.** Players see tendencies and what their people report, not exact yield numbers.
3. **No fixed build orders.** Discovery depends on map and play, so no single opening works everywhere.
4. **The world adapts back.** Pests evolve to target your staple crop. Pathogens adapt to your herds.
5. **Score rewards resilience, not peak output.**
6. **Diminishing returns** on doing any single thing.

---

## 11. Balance Philosophy

- **Plausible, not accurate.** Use real-world logic for intuition, then tune for fun.
- **Tradeoffs, not equality.** Starts, species and strategies should differ but all be viable.
- **Fair difficulty.** Catastrophes are telegraphed; failure should be understandable.
- **Pacing guards.** Timers and thresholds keep catastrophic events from landing before the player could respond (e.g. no impacts before a set game-year).

---

## 12. Prototype Plan

Test the core loop before scaling up. If it's fun with dots on a 2D map, the full game is worth building.

### Prototype 1: Domestication (first priority)

- One temperate valley, real-time, top-down 2D.
- A band of about 10 humans.
- 3–4 animal species with heritable traits and herd behavior.
- **Commensal pathway first:** a camp that produces waste and stores food; scavengers move in and change over generations.
- Then the prey and directed pathways: sparing, feeding, penning, culling.
- **Question to answer:** Is watching a species change because of how you live engaging?

**Status: playable** (`src/lineage/`, see the README). Six species: wolves, wildcats, mice, aurochs, red deer and boar. There are three pathways: the midden draws in scavengers (commensal), hunting is a choice between hunting freely, culling the wildest, sparing or capturing (prey), and the pen has selective culling (directed). Traits are heritable and shown in words, not numbers.

**What the simulation taught us so far** (from headless runs across several worlds):

- **Dogs emerge without being asked for.** With a midden by camp and scavengers tolerated, about half of valleys produce dogs within 15–25 years. Camp wolves end up far bolder than wild ones, and aggression falls because people kill the biters. Tossing scraps raises the odds.
- **Some valleys never give you dogs.** If the local wolves start out fierce, people keep killing them and the lineage never takes hold. This is the variability we wanted.
- **Persecution selection.** Bold wild wolves drawn to camp and killed there leave the *wild* population warier over time.
- **Gene flow.** Camp boldness leaks back into the wild wolf population.
- **Bottlenecks matter.** Tiny camp lineages can die out simply by running out of females.
- **Cattle via the pen.** Capturing calves (adults are too wild) and culling the wildest each autumn produces cattle in about 30–40 years. Body size drifts smaller along the way, a domestication-syndrome effect that wasn't scripted.
- **Deer can't be domesticated.** They panic and break out of the pen, which is Diamond's point made playable.
- **Over-hunting** can wipe out the aurochs, and with them the chance of cattle.
- **Crowding.** A big, busy camp can shut scavengers out entirely. Night-time scavenging was needed to keep the commensal pathway alive.

**Known gaps:** cats rarely settle, the pig pathway is untuned, outcomes vary a lot between seeds, and there is no disease or plant domestication yet.

### Prototype 2: Discovery system

- A standalone simulation of practice tags → emergent discoveries.
- About 15–20 discoverable innovations built from parts.
- **Question to answer:** Do emergent inventions feel like *your* discoveries?

### Prototype 3: Neighbors

- One rival band: trade, absorb or fight.
- **Question to answer:** Is absorption as satisfying as conquest?

### Technology

- **Prototypes:** Python + pygame (matches the existing repo).
- **Long-term:** reevaluate (Godot is a strong candidate) once the core loop is proven.

---

## 13. Open Questions

- **AI civilizations:** how smart, and how do they pursue non-zero-sum play?
- **Multiplayer:** in scope at all? Co-op against the world could fit well.
- **Session length:** how long is a full game? Can it be played in chapters or eras?
- **Player avatar:** is there a leader or lineage character, or is the player an abstract guiding hand?
- **How much individual control** remains at later scales?
- **Visual style:** top-down 2D, isometric, 3D?
- **Procedural vs. real-Earth species:** generated species, real ones, or a mix?
- **Information display:** how to show imprecise information without frustrating players.
- **Endgame:** what does "surviving solar expansion" look like in play?

### Raised for discussion

- **Pacing over time.** Should years pass quickly at the start and slow down as technology accelerates?
  - *Notes:* This matches real history. Prehistory spans many thousands of years with slow change, and recent centuries are dense with change. It also fits §6, where the time scale already shifts with the phase of the game. The catch is that evolution needs many generations, so the early game has to run fast for domestication to happen in play time. In the prototype a year already passes in about 4 seconds at top speed. One option is to tie game speed to the *rate of change*: time runs fast when little is changing and slows when discoveries, crises or migrations pile up.
- **How detailed should reproduction be?** Do we need males and females, or would randomized asexual inheritance with mutation be enough?
  - *Notes:* The prototype found that tracking sexes creates real effects: small camp lineages die out when they run out of females, and wild males dilute the camp line. These are realistic, but also random and hard for players to read. A simpler model, where offspring copy a parent with small random mutations, would keep selection working (the core mechanic), make the code simpler and faster, and make outcomes more predictable. A middle option is to drop sexes but keep "gene flow" as a deliberate mechanic, where wild animals breeding with the camp population pulls it back toward wild traits. The choice should come down to whether the bottleneck drama is fun or just frustrating.
