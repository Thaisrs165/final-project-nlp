# Project status: read this first (updated 2026-11-23)

A one-page snapshot for everyone, and for your AI assistant. Details live in [DATA_LOG.md](DATA_LOG.md) (every decision), [REPORT_ROADMAP.md](REPORT_ROADMAP.md) (the report) and [IMPLEMENTATION.md](IMPLEMENTATION.md) (steps).

## Where we are

| Step | State |
|---|---|
| Data: HP (Ana) | ✅ done: 34 characters, test rows, human baseline (70%, κ 0.37) |
| Data: Avatar (Esther) | ✅ 28 characters + 20 shortcut pairs; agreement scored (Ana 35%, Thais 40%, κ 0.11): birth-sorted like GoT |
| Data: Divergent (Thais) | 🟡 **4** characters (all Dauntless): every faction page on the wiki checked, no other character reaches 5 traits (DATA_LOG 2026-11-24); 🛑 **team decision** on the trait rule. ✅ 74 probes run (`experiments/divergent.py`); human baseline on probes 90%, κ 0.69 |
| Data: Game of Thrones (Fardin) | ✅ 16 characters (Tyrell = Olenna only) + test rows; agreement scored (28%, κ 0.22): birth-sorted like Avatar |
| Data: Invented (Ana + Esther) | ✅ 32 personas (8 per house) + test rows; agreement scored (85%, κ 0.60); run done |
| Human form | ✅ 19 responses (10 after the attention rule, decided in advance) |
| Shared runner `run_experiments.py` | ✅ 23,400 predictions: HP, Avatar, Divergent, GoT, Invented (4 methods + 3 fixes each) |
| Fixes for the "always Gryffindor" problem | ✅ all tried and reported (see below) |
| App (Gradio, Ana; redesign Esther) | ✅ dark theme, one quiz sorted into every world × every model (multiverse grid), Trick BERT, Why it's unsure. Runs locally; temporary public link with `GRADIO_SHARE=True`. **No deploy:** Gradio Spaces on Hugging Face now need a paid plan (2026-11-23; `space/README.md`). Optional: 1–2 min screen recording for the report's Material |
| Tables and figure for the report | ✅ `make_tables.py` → `results/report/` (Table 1, Table 2 with the invented world, a Q3 figure); Fardin's `results/q2q3/fig1` also exists: **pick one Figure 1**. Avatar and GoT κ are in; `make_tables.py` re-run 2026-11-23 |
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
| **Thais** | ✅ Introduction written · ✅ Tables 1–2 (`make_tables.py`) · ✅ Divergent wiki fully checked (4 characters; needs the team's rule decision to add more)  |
| **Fardin** | GoT data and first run done (DATA_LOG, 2026-11-23). Next: score the GoT agreement sheets when they come back. Write **Results Q2 + Q3 / Figure 1**. |
| **Esther** | ✅ Avatar agreement scored (invented personas were done by Ana). Write **Methods: models and stats** and the **Conclusion**. Note: `sorter.py` got an optional `name=` and extra fix methods (see CLAUDE.md); plain `mlm` is unchanged. |
| **Ana** | Write **Methods: data** + **Results Q1 / Table 2**. |
| **Team** | Pick the final editor. Pick one Figure 1. Decide the Divergent trait rule. Who runs the app (and the `GRADIO_SHARE` link + QR) at the presentation. Each person reads only the papers they cite (REPORT_ROADMAP.md §6, 8 papers, the listed parts only). |

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
