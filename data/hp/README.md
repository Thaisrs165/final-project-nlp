# Harry Potter

**Owner:** Ana
**Groups:** Gryffindor, Ravenclaw, Hufflepuff, Slytherin (ids: `gryffindor`, `ravenclaw`, `hufflepuff`, `slytherin`, matching `sorter.WORLDS["hp"]` and `app/worlds.json`)

Steps 2.1–2.2 of [IMPLEMENTATION.md](../../IMPLEMENTATION.md). Work only inside this folder. Shared files (`vote_items.csv`, `generic.csv`, the simulated panel) live in `data/` and are not edited here.

## Files to produce
| File | Columns |
|---|---|
| `groups.csv` | `group, description, source_url, source_quote` |
| `leak_words.csv` | `word, group, found_in`: 49 words a character trait may not use (house names, every description word, plus trait words from the Wikipedia quotes, the official fact files and the Sorting Hat song). |
| `tests.csv` | `id, test_type, name, traits, gold_group, source_url, trait_evidence` (`test_type = canonical` for hand-made rows; step 4 appends the generated rows) |

## Target
~40 characters, about 10 per house. Gold labels must come from the books or the official Wizarding World site, never fan guesses.

## Checklist
- [x] `groups.csv`: one row per group, paraphrased description plus source URL (2026-11-18)
- [x] Owner checked the descriptions against the sources (2026-11-21). Wording kept identical to the live form; Gryffindor and Hufflepuff now cite the official fact files, which match word for word.
- [ ] `tests.csv`: canonical rows, each with `gold_group` and `source_url`
- [ ] 5 traits per row, only adjectives that literally appear in the source; the sentence goes in `trait_evidence`
- [ ] No trait is a group name or a word from this world's group descriptions (label leak)
- [ ] Rows with fewer than 5 usable adjectives marked `needs_review`, not padded
- [ ] Trait check done (✓/✗ per trait); share accepted noted in [DATA_LOG.md](../../DATA_LOG.md)
