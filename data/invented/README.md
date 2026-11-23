# Invented world (control)

**Owners:** Ana + Esther (changed 2026-11-23). Personas drafted by Claude, reviewed by Ana.
**Groups:** Veltrin, Osmark, Calwen, Durrask (ids: `veltrin`, `osmark`, `calwen`, `durrask`, matching `sorter.WORLDS["invented"]` and `app/worlds.json`)

Steps 2.1–2.2 of [IMPLEMENTATION.md](../../IMPLEMENTATION.md). Work only inside this folder. Shared files (`vote_items.csv`, `generic.csv`, the simulated panel) live in `data/` and are not edited here.

## Files to produce
| File | Columns |
|---|---|
| `groups.csv` | `group, description, source_url, source_quote` |
| `tests.csv` | `id, test_type, name, traits, gold_group, source_url, trait_evidence` (`test_type = canonical` for hand-made rows; step 4 appends the generated rows) |

## How this world is built (decided 2026-11-23, DATA_LOG.md)
There is no outside source, so traits are **written directly** under a fixed rule: 5 per persona = 3 synonyms of the house description + 2 neutral traits; every neutral word appears in exactly 2 houses; no leak words; names share no word piece with a house name. **32 personas, 8 per house.**

```
# edit personas.csv, then:
.venv/bin/python data/invented/build_personas.py     # checks every rule, writes canonical rows
.venv/bin/python make_tests.py invented
.venv/bin/python run_experiments.py run invented
```
**Annotators must not open `personas.csv` or `tests.csv` before filling in their sheet.**

## Checklist
- [x] `groups.csv`: one row per group, paraphrased description plus source URL (2026-11-18)
- [ ] Owner checked the descriptions against the sources
- [x] Names checked online (not real brands or places) and word pieces recorded (2026-11-23)
- [x] `leak_words.csv` (51 words)
- [x] `personas.csv`: 32 personas, 8 per house, 3 fits + 2 neutral; `tests.csv` canonical rows built (2026-11-23)
- [x] Generated test rows (`make_tests.py invented`)
- [x] Ana reviewed the personas (2026-11-23)
- [x] Agreement sheets built (`agreement/`, 20 items, 5 per house)
- [ ] Agreement sheets filled in by two people who haven't seen the personas, then `agreement.py score invented`
- [ ] Runner (`run_experiments.py run invented`)
