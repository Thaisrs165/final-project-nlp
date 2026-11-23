# Avatar: The Last Airbender

**Owner:** Esther (also reviews the shortcut pairs)
**Groups:** Fire Nation, Water Tribe, Earth Kingdom, Air Nomads (ids: `fire`, `water`, `earth`, `air`, matching `sorter.WORLDS["avatar"]` and `app/worlds.json`)

Steps 2.1–2.2 of [IMPLEMENTATION.md](../../IMPLEMENTATION.md). Work only inside this folder. Shared files (`vote_items.csv`, `generic.csv`, the simulated panel) live in `data/` and are not edited here.

## Files to produce
| File | Columns |
|---|---|
| `groups.csv` | `group, description, source_url, source_quote` |
| `tests.csv` | `id, test_type, name, traits, gold_group, source_url, trait_evidence` (`test_type = canonical` for hand-made rows; step 4 appends the generated rows) |

## Target
~30 characters, plus the element-flavored vs. neutral shortcut pairs. Gold labels must come from the series.

## Checklist
- [x] `groups.csv`: one row per group, paraphrased description plus source URL (2026-11-18)
- [ ] Owner checked the descriptions against the sources
- [x] `tests.csv`: canonical rows, each with `gold_group` and `source_url` (28 canonical, 2026-11-23)
- [x] 5 traits per row, only adjectives that literally appear in the source; the sentence goes in `trait_evidence`
- [x] No trait is a group name or a word from this world's group descriptions (label leak); see `leak_words.csv`
- [x] Rows with fewer than 5 usable adjectives marked `needs_review`, not padded (Ozai, Roku, Ty Lee, Tarrlok, Suki)
- [x] Trait check done (Esther kept all 8 borderline picks, 140/140 accepted); noted in [DATA_LOG.md](../../DATA_LOG.md)
- [x] Agreement sheets made (`agreement/sheet_A.xlsx`, `sheet_B.xlsx`): 20 nameless trait sets, 5 per nation
- [ ] Agreement sheets filled by Ana and Thais (they haven't seen the character list), then `agreement.py score avatar`
- [ ] Shortcut pairs (element-flavored vs. neutral wording)
