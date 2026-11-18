# Data log

A running record of how the data was built and every decision that changed it.
Newest entries at the top. Anything that goes in the report's Data or Limitations section should be traceable to an entry here.

---

## 2026-11-18 · Group descriptions written (step 2.1)
**Rule.** Each `data/<world>/groups.csv` description is **word for word the one-line description the human form showed**. Humans, the simulated panel and BERT's "with descriptions" variant therefore all read the same definitions. Each row was then checked against an outside source, and the supporting text is in the new `source_quote` column. ⚠️ If anyone changed a description's wording when building the Google Form, the CSV has to be updated to match.

**How well each world is supported.**

| World | Source | Support |
|---|---|---|
| Harry Potter | Wikipedia, *Hogwarts* §Houses | ✅ Strong. Every word matches or is a synonym (courage → bravery, nerve → daring, learning → love of learning, justice → fairness). |
| Divergent | Wikipedia, *Divergent (novel)* | ✅ Strong, except Amity's "kindness", which is our addition (Wikipedia only says "peaceful"). |
| Avatar | Iroh's speech in the official live-action series (Netflix, S2E3 transcript) | 🟡 Partial. Earth (enduring), Air (freedom, detachment, peace) and Water (change, adapting) are confirmed. **Fire's "drive, ambition, passion" and Water's "community"** come from Iroh's speech in the animated episode *Bitter Work* (2006), which **couldn't be checked online** because the Avatar wiki blocks automated access. Esther checks it by hand. |
| Game of Thrones | Wikipedia, *World of A Song of Ice and Fire*; Dummies, *Game of Thrones list of houses* | 🟡 Interpretive. Sources confirm Stark's "honorable devotion to duty", Lannister wealth, Greyjoy raids and rebellion, and Tyrell cleverness and scheming. "Pride", "passion, boldness, ambition" (Targaryen) and "defiance, toughness, independence" (Greyjoy) are **our reading of each house's reputation**, not quoted traits. Fardin checks them. Mottos were deliberately left out ("Fire and Blood" would be a literal fire cue). |
| Invented | Our own definitions | Control world, no outside source. |

**For the report:** HP and Divergent descriptions are sourced. GoT and part of Avatar are our paraphrase of a reputation. Say so in Data/Limitations.

**Checked in code:** all 5 files load with `sorter.load_descriptions`, and every method runs in the "with descriptions" variant for every world.

---

## 2026-11-18 · World owners assigned
- **Harry Potter → Ana**, **Divergent → Thais**, **Game of Thrones → Fardin**, **Avatar → Esther** (Esther also reviews the Avatar shortcut pairs).
- **Invented world → Esther** (approves the personas).
- Each owner works only inside their world's folder (`data/<world>/`). Owners are listed in each folder's README and in IMPLEMENTATION.md.

---

## 2026-11-18 · Short human form is live after all
**Decision.** Alongside the simulated panel, we're running a **short real form** (about 3 minutes) so the panel can be checked against real people.
- **Items (25):** the 20 generic items of `vote_items.csv` (3 per world, 8 for HP) plus 1 clear item per world as an attention check (`k01-hp`, `k01-div`, `k01-got`, `k01-ava`, `k01-inv`). Same wording as `vote_items.csv`. Conflicting items are not included.
- **Familiarity grid:** HP, Divergent, Game of Thrones, Avatar.
- **Attention rule (set before seeing any data):** drop a respondent who gets **2 or more of the 5** clear items wrong.
- **Target:** about 35 responses, so about 30 remain after the filter. 10 is the useful minimum for checking the panel.
- **Analysis plan:** humans vs. panel vs. BERT on the same items. Report a **human split-half floor**: split respondents randomly in two, compute the JSD between the halves, and repeat about 1,000 times. That gives the distance expected between humans themselves.
- Responses will be linked to a Google Sheet and exported to `data/human_votes.csv` (`source=human`).
- The full form text (settings, description, sections, attention key, id mapping) is in [forms/human_votes_form.md](forms/human_votes_form.md).

---

## 2026-11-18 · Every method runs with and without group descriptions
**Problem.** In the fill-in-the-blank method, the prompt was only "Someone who is X belongs to Veltrin." BERT has never seen "Veltrin", and nothing in the prompt says what it means, so the invented world would sit near chance **by design**. That would make the memorization control unfair: a low score there would tell us nothing.

**Decision.** Every method (MLM, embedding, NLI) runs in two variants:
- **Without descriptions:** the model sees only the group names. A correct answer can come from memory of the franchise or from the meaning of the name itself.
- **With descriptions:** each group's one-line description (from `data/<world>/groups.csv`) comes first in the prompt, or next to the name for embedding and NLI. The model can now read what each group stands for.

**What it lets us say.**
- Invented world: only the "with" variant is meaningful. That's the pure "reads the traits" score.
- Real worlds: the **gap between the variants** shows how much BERT already knew. A small gap means the descriptions add nothing beyond memory; a large gap means BERT relied on reading them.
- Humans in the form also saw one-line descriptions, so the "with" variant is the fair comparison with the human votes and the panel.

**Known side effects to report.**
- In the "with" variant, groups are listed in a fixed order (the order in `sorter.WORLDS`). Order effects are possible.
- The embedding variant divides cosine similarities by a fixed temperature (0.05) before the softmax, so entropies are comparable within a method but not across methods.

Implemented in `sorter.py` (`descriptions=` argument of `predict`). Spec in IMPLEMENTATION.md, step 3.

---

## 2026-11-18 · Pokémon GO replaced by Game of Thrones
**Decision.** Pokémon GO is out and **Game of Thrones** is in, with id `got` and houses `stark`, `lannister`, `targaryen`, `greyjoy`, `tyrell`.
**Why.** GO's team names are trait words ("valor" means courage), so a correct answer could come from word meaning alone. GO also had almost no canonical characters (3 leaders plus invented personas). GoT house names are not trait words, there are many canonical characters, and the franchise is heavily present in pre-2018 text.
**Caveat for the report.** GoT membership is decided by **birth**, not by personality. Houses still have strong documented stereotypes (their words and reputation), and that's what we test. Gold-label and exclusion rules are in `data/got/README.md`.

### What changed
- `data/pokemon/` renamed to `data/got/`, with a new README (gold label = house of birth; exclude Jon Snow, Joffrey/Tommen/Myrcella and similar).
- `sorter.WORLDS`: `pokemon` replaced by `got`.
- `data/vote_items.csv`: the 6 `*-pkm` items replaced by `*-got`.
  - Generic items: same 3 trait sets as every other world.
  - Conflicting: `honorable; cunning` (stark|lannister) and `charming; reckless` (tyrell|targaryen).
  - Clear: `always keeps their word, whatever it costs` (stark).
- `make_votes.py`:
  - GoT house vectors (from each house's words and reputation).
  - 4 new trait phrases.
  - Main-character house = **Stark** (an assumption, as for the other worlds).
  - Population familiarity for GoT = (.25, .4, .35).
  - The competitor archetype now knows GoT well instead of Pokémon GO.
  - Persona columns are now `fam_got` / `home_got`.
- `app/worlds.json` and `app/questions.json`: GoT replaces Pokémon GO. Every quiz option has a GoT key, or `null` where no house clearly fits.

### Panel re-run (seed 42)
- HP, Divergent, Avatar and invented votes are unchanged, because the random stream is consumed in the same order. Only the GoT items are new.
- Same 5 voters excluded (v14, v16, v23, v24, v25), leaving **35**.
- Mean normalized entropy: clear 0.30 · generic 0.59 · conflicting 0.72. Conflicting items: 86% of votes on the two expected houses.
- GoT items:

  | Item | Votes (of 40) |
  |---|---|
  | smart; nice | Tyrell 26 |
  | funny; kind | Tyrell 30 |
  | easygoing; polite | split, Tyrell 13 / Targaryen 11 |
  | honorable; cunning | Stark 22 / Lannister 10 |
  | charming; reckless | Targaryen 20 / Tyrell 15 |
  | always keeps their word | Stark 35 |

- Same weak spot as before: warm generic traits pile onto the one "warm" house (Tyrell here).

---

## 2026-11-18 · One folder per world, one owner per world
- Data is split into `data/hp/`, `data/divergent/`, `data/pokemon/`, `data/avatar/`, `data/invented/`. Each holds `groups.csv`, `tests.csv` (headers only for now) and a `README.md` with the owner, target size, gold-label rules and checklist.
- Paths changed from `data/<world>_groups.csv` / `data/<world>_tests.csv` to `data/<world>/groups.csv` / `data/<world>/tests.csv` (PLAN.md, IMPLEMENTATION.md, sorter.py comment).
- Owners: **Harry Potter → Ana**. The other four worlds are still to be filled in (IMPLEMENTATION.md, "Who owns which world").
- Shared files (`vote_items.csv`, `voter_personas.csv`, `simulated_votes.csv`, later `generic.csv`) stay in `data/`.

---

## 2026-11-18 · Human-votes form replaced by a simulated voter panel

**Decision.** We dropped the Google Form (`forms/human_votes_form.md`, deleted). There wasn't enough time or enough respondents to reach 30 responses. Its 39 items are kept unchanged in `data/vote_items.csv`, and `make_votes.py` builds a panel of **40 simulated voters** with distinct personalities that answer those same items.

**This is not human data.** Every row of `data/simulated_votes.csv` has `source=simulated`. In the report:
- Q3 becomes *"BERT vs. a simulated, personality-diverse panel"*, not "BERT vs. humans".
- The ChaosNLI framing stays as motivation, but we must not claim human agreement.
- Add the limitation: the panel's choices come from a trait→group mapping **we hand-set**, so the BERT-vs-panel JSD measures how far BERT is from *our model of how people reason*, not from real people.

### Files
| File | What it is |
|---|---|
| `data/vote_items.csv` | The 39 items from the old form: `item_id, world, item_type, traits, expected`. Traits are separated by `;`. These same trait sets must go into `generic.csv` and the conflicting test rows (step 2.5), so BERT is scored on identical inputs. |
| `make_votes.py` | Generator. Standard library only, seeded with `sorter.SEED` (42), so it is deterministic: re-running gives an identical file. |
| `data/voter_personas.csv` | One row per voter: archetype, Big Five (O, C, E, A, N on a 1–5 scale), familiarity per franchise (0 = not at all, 1 = a little, 2 = well), the 5 behavior parameters, and each voter's "home" group per world. |
| `data/simulated_votes.csv` | `item_id, world, voter_id, group, source`: 40 × 39 = 1,560 rows. Same schema the form would have produced, plus `source`. |

### How a simulated voter decides
1. Every trait phrase and every group is a vector over 10 dimensions (bravery, intellect, warmth, ambition, diligence, honesty, calm, spontaneity, selflessness, adaptability). Group vectors follow the one-line descriptions the form showed respondents.
2. **Trait fit** = cosine(item, group) × `beta`, where `beta` is how closely the voter reads the traits.
3. **Word order** (`first_trait_weight`): >1 means the first trait dominates (fast readers), <1 means later traits count more (careful readers).
4. **Self-projection** (`projection`): on ambiguous items, people place others where they'd place themselves. The voter's Big Five gives a personal vector, which adds `projection × ambiguity × cosine(self, group)`. It does almost nothing on clear items.
5. **Fan bias** (`fan_bias`): people who know a franchise drift toward its "main character" group, scaled by familiarity. Contrarians have a negative value. The invented world has no fan bias by construction, which mirrors the memorization control on BERT's side.
6. **Random clicking** (`noise`): the softmax is mixed with a uniform distribution at this rate.

### The 10 archetypes (40 voters)
| Archetype | n | Personality sketch | What makes them distinct |
|---|---|---|---|
| bookworm | 4 | High O and C, introverted | Reads closely (high beta), knows HP well |
| social_butterfly | 5 | High E and A | Answers fast (first-trait bias), strong projection of warmth |
| competitor | 4 | High E and C, low A | Projects ambition/bravery, plays Pokémon GO |
| newcomer | 5 | Any | Knows none of the franchises: low beta, more noise, no fan bias |
| superfan | 4 | High O | Knows everything; strongest fan bias |
| rushed_clicker | 3 | Low C | 50–70% random clicks; **designed to fail the attention check** |
| contrarian | 3 | Low A, high O | Negative fan bias: avoids the "hero" group |
| careful_worrier | 4 | High N and C | Highest beta, weights the last trait |
| free_spirit | 4 | Very high O, low C | Projects spontaneity/curiosity |
| caregiver | 4 | Very high A | Projects warmth/selflessness |

### Assumptions to check as a team
- **Main-character groups:** HP → Gryffindor, Divergent → Dauntless, Avatar → Air Nomads (each protagonist's group), Pokémon GO → Mystic (assumed most popular team; no source).
- **Trait vectors and group vectors** are hand-set in `make_votes.py` (`TRAITS`, `GROUPS`). They are our judgment. Changing them changes the panel.
- **Big Five → dimensions** mapping (`big5_to_self`) is a rough heuristic, not taken from a published instrument.

### Results of the first run (seed 42)
- **Attention check** (rule fixed before generation: drop voters with ≥ 2 of 7 clear items wrong): 5 of 40 dropped, which leaves **35**. All 3 rushed_clickers (v23–v25) as intended, plus 2 newcomers (v14, v16).
- **Mean normalized entropy of the vote split:** clear 0.30 · generic 0.58 · conflicting 0.74. This is the ordering Q3 expects from people.
- **Conflicting items:** 87% of votes land on one of the two expected groups.
- **Archetypes vote differently** (non-clear items; first number = % voting with the panel majority, second = % picking the main-character group):

  | | majority | main char. |
  |---|---|---|
  | careful_worrier | 81% | 23% |
  | bookworm | 79% | 21% |
  | caregiver | 79% | 20% |
  | superfan | 75% | 41% |
  | contrarian | 69% | 21% |
  | social_butterfly | 67% | 29% |
  | competitor | 64% | 31% |
  | free_spirit | 55% | 25% |
  | newcomer | 50% | 27% |
  | rushed_clicker | 27% | 32% |

- **Weak spots to know about:** some generic items come out near-unanimous because a single trait word dominates in our vectors. Examples: "smart and nice" → Ravenclaw 36/40, "easygoing and polite" → Air Nomads 37/40, "funny and kind" (invented) → Osmark 38/40. Real people would probably split more. If we tune the panel, document it here as a new entry, and **don't tune it after looking at BERT's results**, or the comparison becomes circular.

### What changed elsewhere
- `PLAN.md` and `IMPLEMENTATION.md`: form steps and human checkpoints replaced by the simulated panel. The objective now says "simulated panel".
- `README.md`: form link removed, generator added.

---

## 2026-11-18 · Environment
- `.venv` created with Homebrew Python **3.12.11** (3.13 isn't installed on this machine; requirements.txt was pinned on 3.13). All pinned packages installed cleanly, and `import sorter, torch, transformers, sentence_transformers, sklearn, pandas, umap` works.
- Node is **not installed**. It's only needed for step 8 (the interface).
