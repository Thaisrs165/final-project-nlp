# Project status: read this first (updated 2026-11-23)

A one-page snapshot for everyone, and for your AI assistant. Details live in [DATA_LOG.md](DATA_LOG.md) (every decision), [REPORT_ROADMAP.md](REPORT_ROADMAP.md) (the report) and [IMPLEMENTATION.md](IMPLEMENTATION.md) (steps).

## Where we are

| Step | State |
|---|---|
| Data: HP (Ana) | ✅ done: 34 characters, test rows, human baseline (70%, κ 0.37) |
| Data: Avatar (Esther) | ✅ 28 characters + shortcut pairs; 🛑 agreement sheets not scored yet |
| Data: Divergent (Thais) | 🟡 only **4** characters (her own experiment script exists) |
| Data: Game of Thrones (Fardin) | 🛑 **not started** (0 characters) |
| Data: Invented (Esther) | 🛑 **not started** (0 personas) |
| Human form | ✅ 19 responses (10 after the attention rule, decided in advance) |
| Shared runner `run_experiments.py` | ✅ 14,100 predictions done for HP, Avatar, Divergent |
| Fixes for the "always Gryffindor" problem | ✅ all tried and reported (see below) |
| App (Gradio, Ana) | 🟡 starter works (`app/app.py`); polish + deploy to do |
| Tables and figure for the report | ⏳ next |
| Report text | ⏳ not started; who writes what is in REPORT_ROADMAP.md §5 |

## What we've found so far (HP; Avatar looks the same)

| | Correct (chance 25%) |
|---|---|
| Humans (2 annotators) | **70%** |
| NLI (BART), best model | 53% |
| Sentence-BERT | 41–44% |
| BERT fill-in-the-blank | 24–29% (about chance) |
| BERT + all fixes (better calibration, bert-large, both) | 21–32% (still about chance) |
| Small trained classifier on BERT vectors (sanity check) | 29% |

- With a character name in the prompt, plain BERT answers **Gryffindor 97 times out of 102**, whoever the name is. So swapping the name changes nothing.
- The fixes stop that collapse, but the answers spread to other wrong houses. BERT doesn't link these traits to these houses; it isn't a calibration or size problem.

## To-do by person

| Who | To do |
|---|---|
| **Thais** | Add Divergent characters (target ~25), then `make_tests.py divergent` (**after** your `divergent.py build`), then `run_experiments.py run divergent`. Write the **Introduction** (REPORT_ROADMAP.md §5). Fill in your Avatar agreement sheet if you haven't yet. |
| **Fardin** | Build Game of Thrones with the HP tools (IMPLEMENTATION.md "How to build your world"), then run the runner. Write **Results Q2 + Q3 / Figure 1**. |
| **Esther** | Build the Invented personas; score the Avatar agreement sheets (`agreement.py score avatar`). Write **Methods: models and stats** and the **Conclusion**. Note: `sorter.py` got an optional `name=` and extra fix methods (see CLAUDE.md); plain `mlm` is unchanged. |
| **Ana** | Polish and deploy the app (`app/README.md`). Write **Methods: data** + **Results Q1 / Table 2**. |
| **Team** | Pick the final editor. Each person reads only the papers they cite (REPORT_ROADMAP.md §6, 8 papers, the listed parts only). |

## How to run things (everyone uses the same code)

```
.venv/bin/python make_tests.py <world>                 # generated test rows
.venv/bin/python run_experiments.py run <world>        # all methods; cached, only new rows run
.venv/bin/python run_experiments.py run <world> --methods mlm-cal mlm-large mlm-large-cal   # the fixes
.venv/bin/python run_experiments.py occlusion          # which trait matters most
.venv/bin/python run_experiments.py summary            # accuracy table -> results/summary_q1q2.csv
.venv/bin/python run_experiments.py probe              # small trained sanity check
.venv/bin/python app/app.py                            # the app, http://127.0.0.1:7860
```

**Rules:**
- All models live in `sorter.py`. Don't write your own runner or load models elsewhere.
- The report numbers come from `results/all.csv`.
- Log every decision in DATA_LOG.md.
- The report is at most 2 pages, IEEE template, references included. Going over is an F.
