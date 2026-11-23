# Does BERT actually sort you?

Does a frozen BERT sort people into groups (Hogwarts houses, Divergent factions, Great Houses of Westeros, nations of Avatar…) by reasoning from their traits, or from memorized names and words? And what does it do with ambiguous input?

- **Start here:** [STATUS.md](STATUS.md) (where the project stands, who does what)
- Research design: [PLAN.md](PLAN.md) · Build plan: [IMPLEMENTATION.md](IMPLEMENTATION.md) · Report plan: [REPORT_ROADMAP.md](REPORT_ROADMAP.md)
- Literature: [RELATED_WORK.md](RELATED_WORK.md) · [references.bib](references.bib)
- Every data decision: [DATA_LOG.md](DATA_LOG.md)
- Human-votes form (live version): [forms/human_votes_form.md](forms/human_votes_form.md)

## Setup

Requires Python 3.11+.

```bash
python3 -m venv .venv
```

```bash
.venv/bin/pip install -r requirements.txt
```

```bash
.venv/bin/python -c "import sorter; print(sorter.MLM_MODEL)"
```

The models (`bert-base-uncased`, `all-MiniLM-L6-v2`, `bart-large-mnli`, plus `bert-large-uncased` for one of the fixes) download from Hugging Face on first use, about 2 GB in total. They are pinned in `sorter.py`.

## Run the app: "The Unsure Hat"

A Gradio app in which you take one 12-question quiz and get sorted into every world by every model. Details: [app/README.md](app/README.md).

```bash
.venv/bin/python app/app.py
```

Then open http://127.0.0.1:7860. The models load in the background when the app starts, so the first result can take about 10 s.

**Public link for a presentation** (temporary; works while this computer keeps the app running, for up to 72 h):

```bash
GRADIO_SHARE=True .venv/bin/python app/app.py
```

The terminal prints a `https://….gradio.live` link you can turn into a QR code.

**Permanent link:** not planned. Hugging Face now charges for Gradio Spaces (checked 2026-11-23). The ready-made files and steps are in [space/README.md](space/README.md) in case that changes.

## Run the experiments

```bash
.venv/bin/python run_experiments.py run hp
```

```bash
.venv/bin/python run_experiments.py summary
```

```bash
.venv/bin/python make_tables.py
```

All commands (occlusion, probe, the MLM fixes, per-world data tools) are listed in [STATUS.md](STATUS.md#how-to-run-things-everyone-uses-the-same-code).

## Layout

```
sorter.py             the only place models and methods live (experiments and app share it)
run_experiments.py    step 5: every world × method × test type -> results/all.csv
make_tests.py         step 4: generated test rows (no_name, name_swap, negation, conflicting, generic, shortcut)
fetch_personality.py  step 2.2: traits taken literally from Fandom "Personality" sections
agreement.py          step 2.3: human annotator sheets -> accuracy and Cohen's kappa
make_votes.py         simulated voter panel (always labelled as simulated)
analysis_q2q3.py      Q2/Q3 analysis and Figure 1
make_tables.py        report tables and figure -> results/report/
data/                 one folder per world (hp, divergent, got, avatar, invented) + shared CSVs
results/              all.csv, summaries, report tables and figures
notebooks/            exploratory notebooks
tests/                pytest (fast ones: -m "not models")
forms/                text of the live human-votes form
app/                  the Gradio app
space/                files for deploying the app to Hugging Face Spaces
```
