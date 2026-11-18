# Game of Thrones

**Owner:** Fardin
**Groups:** Stark, Lannister, Targaryen, Greyjoy, Tyrell (ids: `stark`, `lannister`, `targaryen`, `greyjoy`, `tyrell`, matching `sorter.WORLDS["got"]` and `app/worlds.json`)

Steps 2.1–2.2 of [IMPLEMENTATION.md](../../IMPLEMENTATION.md). Work only inside this folder. Shared files (`vote_items.csv`, `generic.csv`, the simulated panel) live in `data/` and are not edited here.

## Why this world, and what's different about it
It replaced Pokémon GO on 2026-11-18 (see [DATA_LOG.md](../../DATA_LOG.md)). The house names are not trait words, so this world adds a real, heavily memorized franchise without literal labels.
**Important:** house membership is decided by **birth**, not by personality, unlike Hogwarts or the Divergent factions. Each house still has a strong, well-documented stereotype (its words and reputation), and that's what BERT and the panel are tested on. Say this in the report.

## Files to produce
| File | Columns |
|---|---|
| `groups.csv` | `group, description, source_url, source_quote` (paraphrase the house's words and reputation) |
| `tests.csv` | `id, test_type, name, traits, gold_group, source_url, trait_evidence` (`test_type = canonical` for hand-made rows; step 4 appends the generated rows) |

## Target
~30 characters, about 6 per house. Sources: the books (*A Song of Ice and Fire*, 1996–2011) or the show (2011–2019), plus the character's Fandom page.

## Gold-label rules
- Gold label = the house the character is **born** into (by family name in canon).
- **Exclude** characters whose house is disputed or changes: Jon Snow (raised Stark, born Targaryen), Joffrey/Tommen/Myrcella (Baratheon name, Lannister blood), anyone mainly known under a married name. List the exclusions here.
- Theon Greyjoy (raised by the Starks) stays as Greyjoy. He's a useful ambiguous case for the analysis.

## Checklist
- [x] `groups.csv`: one row per house, paraphrased description plus source URL (2026-11-18)
- [ ] Owner checked the descriptions against the sources
- [ ] `tests.csv`: canonical rows, each with `gold_group` and `source_url`
- [ ] 5 traits per row, only adjectives that literally appear in the source; the sentence goes in `trait_evidence`
- [ ] No trait is a house name, a house's words, or a word from this world's group descriptions (label leak)
- [ ] Rows with fewer than 5 usable adjectives marked `needs_review`, not padded
- [ ] Exclusions listed above
- [ ] Trait check done (✓/✗ per trait); share accepted noted in [DATA_LOG.md](../../DATA_LOG.md)
