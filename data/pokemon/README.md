# Pokémon GO

**Owner:** _TBD (fill in)_
**Groups:** Valor, Mystic, Instinct (ids: `valor`, `mystic`, `instinct`, matching `sorter.WORLDS["pokemon"]` and `app/worlds.json`)

Steps 2.1–2.2 of [IMPLEMENTATION.md](../../IMPLEMENTATION.md). Work only inside this folder. Shared files (`vote_items.csv`, `generic.csv`, the simulated panel) live in `data/` and are not edited here.

## Files to produce
| File | Columns |
|---|---|
| `groups.csv` | `group, description, source_url` |
| `tests.csv` | `id, test_type, name, traits, gold_group, source_url, trait_evidence` (`test_type = canonical` for hand-made rows; step 4 appends the generated rows) |

## Target
3 team leaders + ~30 personas. Gold labels must come from leaders: the game; personas are written from each team's official values (`source_url = persona`).

## Checklist
- [ ] `groups.csv`: one row per group, paraphrased description plus source URL
- [ ] Owner checked the descriptions against the sources
- [ ] `tests.csv`: canonical rows, each with `gold_group` and `source_url`
- [ ] 5 traits per row, only adjectives that literally appear in the source; the sentence goes in `trait_evidence`
- [ ] No trait is a group name or a word from this world's group descriptions (label leak)
- [ ] Rows with fewer than 5 usable adjectives marked `needs_review`, not padded
- [ ] Trait check done (✓/✗ per trait); share accepted noted in [DATA_LOG.md](../../DATA_LOG.md)
