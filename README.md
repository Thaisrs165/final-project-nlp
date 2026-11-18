# Does BERT actually sort you?

Does a frozen BERT sort people into groups (Hogwarts houses, Divergent factions…) by reasoning from their traits, or from memorized names and words? And what does it do with ambiguous input?

- Research design: [PLAN.md](PLAN.md)
- Step-by-step build plan: [IMPLEMENTATION.md](IMPLEMENTATION.md)
- Literature: [RELATED_WORK.md](RELATED_WORK.md) · [references.bib](references.bib)
- Data decisions and the simulated voter panel: [DATA_LOG.md](DATA_LOG.md)
- Human-votes form (live version): [forms/human_votes_form.md](forms/human_votes_form.md)

## Setup

Requires Python 3.11+ and Node 18+.

```bash
python3 -m venv .venv
```

```bash
.venv/bin/pip install -r requirements.txt
```

```bash
.venv/bin/python -c "import sorter; print(sorter.MLM_MODEL)"
```

Models (`bert-base-uncased`, `all-MiniLM-L6-v2`, `bart-large-mnli`) download from Hugging Face on first use. They are pinned in `sorter.py`.

## Layout

```
data/        shared CSVs (vote items, simulated panel) + one folder per world (hp/, divergent/, got/, avatar/, invented/)
sorter.py    the only place methods live (shared by experiments and app)
make_votes.py  builds the simulated voter panel (replaces the human-votes form)
notebooks/   analysis, one per research question
results/     outputs: all.csv, tables, figures
tests/       pytest for sorter.py
forms/       text of the live human-votes form
app/         interface (step 8, not built yet)
```
