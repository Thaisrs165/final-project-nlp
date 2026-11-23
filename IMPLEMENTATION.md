# Implementation plan, step by step

The research design lives in [PLAN.md](PLAN.md) and the literature in [RELATED_WORK.md](RELATED_WORK.md).
This file covers **what to build, in what order, and how we know each step is done**.

```
Step 1 setup ─► Step 2 data ─► Step 3 sorter.py ─► Step 4 test generator ─► Step 5 experiments ─► Step 6 analysis ─► Step 9 report
                                   │
                                   └─► Step 7 api.py ─► Step 8 Node interface ─► Step 10 presentation
```
Steps 2 and 3 can run in parallel. Step 8's front end can start alongside them if it shows only the quiz key until the API exists.

## Status (updated 2026-11-18)

| Step | State | Notes |
|---|---|---|
| 1. Setup | ✅ done | venv, pinned requirements, folder layout |
| 2. Data | 🟡 in progress | Per-world folders exist. **2.1 group descriptions written for all 5 worlds** (owners still to check). **2.2 done for HP (34) and Avatar (28)**; Divergent, GoT and Invented still empty. Owners: HP Ana, Divergent Thais, GoT Fardin, Avatar Esther, Invented Esther. Simulated panel done. **Human form: 19 responses imported** (`data/human_votes.csv`). **Primary analysis: the 10 kept by the attention rule; all 19 reported as a sensitivity analysis** (decided 2026-11-23). |
| 3. `sorter.py` | ✅ done | 4 methods, with and without descriptions, PLL-word-l2r, calibration, occlusion. Optional `name=` for Q2 (named prompt twins in `NAMED_TEMPLATES`, added 2026-11-21). **40/40 tests pass**; one MLM call takes about 0.1 s on the Mac GPU. |
| 4. `make_tests.py` | ✅ built | HP: 34 no_name, 34 name_swap, 34 negation, 28 conflicting, 25 generic. Avatar: 28 / 28 / 28 / 26 / 25. Other worlds: re-run once their canonical rows exist. |
| 5. `run_experiments.py` | ✅ built 2026-11-23 | **The one shared runner** for every world: `run`, `occlusion`, `summary`. Results in `results/all.csv`. HP, Avatar and Divergent run; others re-run once their data lands. |
| 6. Analysis | ⏳ next | Reads `results/all.csv`. Fixes A/B/C and the probe already run (DATA_LOG.md). Clustering dropped. |
| 7–8. App | 🟡 starter built 2026-11-23 | **Gradio, Ana.** `app/app.py` works end to end (3 tabs); polish + deploy to do. No separate `api.py` needed. |
| 9–10. Report, presentation | ⏳ not started | |

**Waiting on people (🛑):**
- Each owner checks their world's `data/<world>/groups.csv` against the `source_quote` column (about 10 min). GoT and Avatar need the most attention: see DATA_LOG.md.
- Review the simulated panel's assumptions (step 2.6).

**Next for Claude, once approved:**
- 2.4 invented personas (word pieces already recorded: Veltrin `ve·lt·rin`, Osmark `os·mark`, Calwen `cal·wen`, Durrask `du·rra·sk`; the web check that the names aren't real brands or places is still to do).
- ~~2.5 `generic.csv` built from `vote_items.csv`.~~ ✅ done 2026-11-21 (25 sets).
- A script that reads the form responses (attention filter, human split-half floor, humans vs. panel).

**Early observations (one example each, not results yet):**
- Calibration matters: for "brave, daring, bold", Gryffindor goes from 0.91 (raw) to 0.47 (calibrated).
- In the invented world, BERT gave "warm, generous" to Osmark (0.64) *without* descriptions, so probably something in the name's word pieces. *With* descriptions it was nearly uniform (and wrong). Fill-in-the-blank may not use in-prompt descriptions well. Check this on the full data before believing it.



## How we work

- **Claude asks for approval before starting each step** and doesn't start building anything on its own.
- **Claude stops at every 🛑 checkpoint** and tells you exactly what to do by hand, then waits until you say it's done.

### 🛑 Everything that needs a human, in order

| When | What | Who | Time |
|---|---|---|---|
| Step 2.6 | Review the simulated panel's assumptions in [DATA_LOG.md](DATA_LOG.md) (main-character groups, trait vectors) | 1 person | 20 min |
| Step 2.1 | Check the group descriptions against their sources | each world's owner | 10 min/world |
| Step 2.2 | Trait check: mark each extracted trait ✓/✗ in the Google Sheet | each world's owner | ~1 h/world |
| Step 2.3 | Sort 20 unnamed trait sets per world, independently | 2 people | 30 min each |
| Step 2.4 | Approve the invented-world personas | Esther | 20 min |
| Step 8 | ~~Decide Node vs. Gradio~~ Gradio (2026-11-23); approve the quiz keys | team | 15 min |
| Step 8 | Create the hosting account or Space, if we host online (needs your login) | 1 person | 15 min |
| Step 9 | Write the report text (one paragraph each); Claude only formats it and checks the page limit | everyone | ~4 days |
| Step 10 | Interview practice at the whiteboard | everyone | 2 days |

---

## Step 1: Setup ✅ done 2026-11-11

```
final-project-nlp/
├── data/            # shared CSVs (vote items, simulated panel, generic.csv)
│   ├── hp/          # one folder per world: groups.csv, tests.csv, README.md
│   ├── divergent/
│   ├── got/
│   ├── avatar/
│   └── invented/
├── sorter.py        # the ONLY place methods live (step 3)
├── make_tests.py    # generates the automatic test sets (step 4)
├── run_experiments.py
├── api.py           # FastAPI wrapper for the app (step 7)
├── notebooks/       # analysis, one per question (step 6)
├── results/         # all.csv, tables, figures
├── tests/           # pytest for sorter.py
└── app/             # Node interface (step 8)
```
- [x] Python 3.11+ venv (recreated 2026-11-18 with Python 3.12.11, see [DATA_LOG.md](DATA_LOG.md)), plus a `requirements.txt` with: `torch transformers sentence-transformers scikit-learn scipy pandas numpy umap-learn matplotlib fastapi uvicorn pytest`
- [x] Node 18 or newer (no npm packages needed)
- [x] Pin the model names in one place: `bert-base-uncased`, `sentence-transformers/all-MiniLM-L6-v2`, `facebook/bart-large-mnli`

**Done when:** `python -c "import sorter"` runs, and `node -v` prints 18 or higher.

---

## Step 2: Data (about 1 week)

Legend: 🤖 = Claude does it (web search plus writing the files) · 🙋 = a team member has to do it · 🛑 = Claude stops and tells you before going on.

### Who owns which world (decided 2026-11-18)
Each teammate builds steps 2.1–2.2 for **their own world, inside its own folder**, so nobody edits the same file. Each folder's `README.md` has the target size, gold-label rules and a checklist. Shared files stay in `data/` and every test type still runs on every world (PLAN.md §3).

| World | Folder | Owner |
|---|---|---|
| Harry Potter | [data/hp/](data/hp/) | Ana |
| Divergent | [data/divergent/](data/divergent/) | Thais |
| Game of Thrones | [data/got/](data/got/) | Fardin |
| Avatar | [data/avatar/](data/avatar/) | Esther (also reviews the shortcut pairs) |
| Invented | [data/invented/](data/invented/) | Esther (approves the personas) |

### 2.1 Group descriptions: `data/<world>/groups.csv` ✅ written 2026-11-18 (owner check pending)
Columns: `group, description, source_url, source_quote`
- 🤖 For each of the 5 worlds, find the official description of each group and write a short paraphrase with the source URL. Sources: the Wizarding World site and the Sorting Hat songs; the Divergent faction manifestos; each Game of Thrones house's words and reputation (Fandom / A Wiki of Ice and Fire); the Avatar nations' cultural values. The invented world uses the descriptions we write ourselves.
- 🙋 The world's owner checks that the descriptions match the source (about 10 min per world).

### How to build your world: reuse the HP tools (2.2 and 2.3)
Harry Potter (Ana) is done with two scripts that **work for every world**. Use them instead of writing your own, so all worlds are built the same way and the report can describe one method. `data/hp/` is the worked example: copy its file layout.

| Your world | Fandom wiki (`--wiki`) | API access (checked 2026-11-21) |
|---|---|---|
| Divergent | `divergent` | ⚠️ Patchy. Some pages have a "Personality" section (Jeanine Matthews), others don't (Tobias Eaton); "Beatrice Prior" returns no sections (try the page title the wiki actually uses). Expect more `needs_review` rows, and decide as a team before using other sections. |
| Game of Thrones | `gameofthrones` | ✅ works (Eddard Stark: 1,817 words) |
| Avatar | `avatar` | ✅ works through the API even though the normal pages block scripts (Zuko: 3,326 words) |
| Invented | — | No wiki. Personas are hand-written (step 2.4); only `agreement.py` applies. |

**Steps for world `<w>`** (each one has an example in `data/hp/`):
1. `data/<w>/leak_words.csv` (`word, group, found_in`): extra words a trait may not use. Group names and every word of your `groups.csv` descriptions are banned **automatically**; add the trait words from your `source_quote` and other sources.
2. `data/<w>/characters.csv` (`name, page, gold_group, gold_source, role`). `page` = exact wiki title. `gold_source` = where the group is stated (book chapter, episode, official site). `role` = `main` or `spare`. **Leave out characters whose name contains a group name** (it gives the answer away).
3. `.venv/bin/python fetch_personality.py fetch <w> --wiki <wiki>` caches each Personality section in `data/<w>/raw/` and writes `trait_candidates.csv`: every usable adjective with its sentence, leak words already removed.
4. Write `data/<w>/trait_picks.csv` (`name, traits`, 5 traits separated by `;`). **Read the sentence for every pick.** In HP, 12 of the first picks were wrong:
   - **negated**: "wasn't as short-tempered", "less outgoing";
   - **about someone else**: "murderous" described Gaunt, not Riddle;
   - **not personality**: "flamboyant clothing", "strict orders", "romantic relationship".
5. `.venv/bin/python fetch_personality.py build <w> --wiki <wiki>` writes `tests.csv`. It **refuses** any trait that isn't literally in the section or that leaks the label. Rows with fewer than 5 traits become `needs_review`. To add characters later, append them at the **end** of `trait_picks.csv` so existing ids don't change.
6. Owner's trait check: rule on the borderline traits, then log the share accepted in DATA_LOG.md.
7. `.venv/bin/python agreement.py make <w>` creates two nameless sheets plus `key.csv`. Two people **who haven't seen your character list** fill them in. Then `.venv/bin/python agreement.py score <w>` gives human accuracy and κ.
8. `.venv/bin/python make_tests.py <w>` generates the step 4 test rows (no_name, name_swap, negation, conflicting, generic). Re-run it whenever your canonical rows change; `build` keeps the generated rows but doesn't refresh them.
9. Log every decision in DATA_LOG.md (dated, newest on top).

### 2.2 Canonical characters: `data/<world>/tests.csv`
Columns: `id, test_type, name, traits, gold_group, source_url, trait_evidence`

| World | Target | Gold label must come from |
|---|---|---|
| Harry Potter | ~40, about 10 per house | Books or the official Wizarding World site, never fan guesses |
| Divergent | ~25 | Books or films |
| Avatar | ~30 | The series |
| Game of Thrones | ~30, about 6 per house | The books or the show. House by **birth**; disputed characters excluded (rules in [data/got/README.md](data/got/README.md)) |

- 🤖 Build the character list with the gold group and a source link for each.
- 🤖 **Traits:** 5 per character, taken **only from adjectives that literally appear** in the "Personality" section of the character's Fandom page. The sentence each one came from goes in `trait_evidence`, so every trait can be traced. Two filters:
  - No trait may be a group name or a word from that world's group descriptions, because that would leak the label.
  - If a page has fewer than 5 usable adjectives, mark the row `needs_review` instead of inventing traits.
- 🛑 **Checkpoint: trait check.** A Google Sheet lists every row. One person marks each trait ✓ (supported by the source) or ✗ (about 1 h for HP). Rows with any ✗ get fixed. We report the share of traits accepted in the paper.

### 2.3 Human baseline and agreement (κ)
Comparing two people's free-text trait lists with κ doesn't really work. Instead:
- 🤖 Create a Google Sheet with 20 trait sets per world, **without names**, and a dropdown to pick the group.
- 🙋 **Two team members, each on their own**, pick a group for each trait set. Don't look at each other's answers or at the gold labels. About 30 min each.
- 🤖 Compute:
  - **Human accuracy:** how well a person sorts from traits alone. This is a human baseline for Table 1.
  - **Cohen's κ** between the two people: whether the traits are informative enough for humans to agree.

### 2.4 Invented world: `data/invented/groups.csv`, `data/invented/tests.csv`
- 🤖 Check how BERT splits Veltrin, Osmark, Calwen and Durrask into word pieces and record the counts. Search each name to make sure it isn't a real brand or place, and propose replacements if any is.
- 🤖 Write 30 personas (about 7–8 per house). Use **synonyms** of the house descriptions, not the same words (for example, "never rushes" for *patient*), so BERT can't win by matching identical words.
- 🙋 Esther reviews the personas and approves them.

### 2.5 Shared test inputs
- 🤖 ✅ `data/generic.csv`: 25 vague trait sets (8 from `vote_items.csv` word for word + 17 new). `make_tests.py` adds them to every world automatically.
- 🤖 Avatar shortcut pairs: element-flavored vs. neutral wording (Esther reviews them).
- Everything else (no_name, name_swap, negation, conflicting) is generated by the script in step 4.

### 2.6 Reference votes: simulated panel ✅ done 2026-11-18
> **Update 2026-11-18:** a short human form (25 items: 20 generic + 5 attention checks) went live after all. Real votes will be compared with the panel and BERT. See DATA_LOG.md.

The Google Form was dropped (not enough time or respondents). Its 39 items are kept in `data/vote_items.csv`.
- 🤖 ✅ `make_votes.py` builds 40 simulated voters in 10 personality archetypes and writes `data/voter_personas.csv` and `data/simulated_votes.csv` (1,560 votes, `source=simulated`). Run: `.venv/bin/python make_votes.py`.
- 🤖 ✅ Attention rule applied as planned (drop voters with ≥ 2 of 7 clear items wrong): 35 voters remain.
- 🛑 **Checkpoint: review the assumptions** listed in [DATA_LOG.md](DATA_LOG.md). If anything is tuned, log it there **before** BERT's results exist.

**Done when:**
- every CSV loads with `pandas`;
- no canonical row is missing `gold_group` or `source_url`;
- the trait check is finished;
- κ and human accuracy are computed;
- the simulated panel is generated and its assumptions reviewed.

## Step 3: `sorter.py` ✅ done 2026-11-18

One module, used by the experiments **and** the app. Models load lazily, once, on the Mac GPU (MPS) when available.

```python
predict(traits, world, method, template=0, descriptions=None, calibrate=True)
    # -> {"probs": {group: p}, "raw_probs": {group: p}, "scores": {group: s}}
    # method: "mlm" | "embed" (MiniLM) | "bert-mean" (raw BERT baseline) | "nli"
load_descriptions(world)          # data/<world>/groups.csv -> {group: description}
occlusion(traits, world, method)  # [{trait, delta, flips_to}]
entropy(probs), top(probs), to_probs(scores), name_pieces(world, group)
```
`traits` can be a list or a string separated by `;` (preferred) or `,`.

**Two variants of every method** (decision 2026-11-18, [DATA_LOG.md](DATA_LOG.md)):

| | Without descriptions (`descriptions=None`) | With descriptions (`descriptions=load_descriptions(world)`) |
|---|---|---|
| MLM | `Someone who is X belongs to <name>.` | `<Name>: <description>. …` for every group, then the same prompt |
| Embedding | person vs. group **name** | person vs. `<name>: <description>` |
| NLI | `This person belongs to <name>.` | `This person belongs to <name> (<description>).` |

**MLM scoring with PLL-word-l2r** (Kauf & Ivanova 2023). For a group name with word pieces `t1..tk`:
```
score(name | traits) = Σ_i log P(t_i | sentence with t_i and the later pieces of the same word masked)
```
Multi-word names ("Fire Nation") are masked word by word. Only the name's pieces are scored, because the rest of the sentence is identical across candidates.

**Calibration** (Kurita 2019; Zhao 2021):
```
calibrated(name) = score(name | traits) − score(name | "N/A")
```
This also cancels the length penalty for long names. `raw_probs` is before calibration and `probs` after.

**Embedding probabilities:** cosine similarities sit in a narrow band, so they're divided by a fixed temperature (`EMBED_TEMPERATURE = 0.05`) before the softmax. It's set once and never tuned on our results. **Compare entropies only within a method**, never across methods.

**Occlusion:** for each trait, remove it, re-score, and set `delta = p(top group | all traits) − p(top group | without trait)`. `flips_to` is the new top group if it changed.

**Tests (`tests/test_sorter.py`):**
- [x] Every group name is found in the prompt and its word pieces rebuild the name.
- [x] Probabilities sum to 1 (every method, both variants).
- [x] The calibrated content-free prompt gives a uniform distribution (all 3 templates, both variants).
- [x] Results are deterministic.
- [x] Occlusion returns one entry per trait.
- [x] One MLM call for one world takes under 2 s.
- [x] Sanity case: "brave, daring, bold" puts Gryffindor in the top 2.

Fast tests only, no models: `.venv/bin/python -m pytest -m "not models" tests`. All tests: `.venv/bin/python -m pytest tests`.

**Done when:** the tests pass and one call takes under about 2 s for a single world.

---

## Step 4: `make_tests.py` ✅ built 2026-11-21 (HP generated; other worlds run automatically once they have canonical rows)

Reads canonical rows and writes generated rows back to `data/<world>/tests.csv`, with an `origin_id` column linking each to its source row.

| test_type | Rule |
|---|---|
| `no_name` | Drop the name. |
| `name_swap` | Use the traits of X with the name of Y from another group (at least 20 per world). |
| `negation` | Add "not" to every trait. Paired with the original through `origin_id`. |
| `conflicting` | 2–3 traits from group A plus 2–3 from group B. Gold is the pair `A\|B`. |
| `generic` | Rows of `generic.csv`, copied into every world. Gold is empty. |
| `shortcut` (Avatar) | Element-flavored vs. neutral synonyms. Hand-written in `data/avatar/shortcut_pairs.csv`; `make_tests.py` turns each pair into two rows (ids `…-el` / `…-ne`, same `origin_id`). |

**Done when:** the counts per test type are printed and checked by hand on 5 random rows.

---

## Step 5: `run_experiments.py` ✅ built 2026-11-23

> **Use this runner for every world; don't write your own.** It calls only `sorter.py`, so every world uses the same models, prompts, calibration and settings.
> ```
> .venv/bin/python run_experiments.py run [worlds]     # all methods x templates x with/without descriptions
> .venv/bin/python run_experiments.py occlusion        # canonical rows, MLM -> results/occlusion.csv
> .venv/bin/python run_experiments.py summary          # Q1/Q2 table with 95% CIs -> results/summary_q1q2.csv
> ```
> The name is passed only for `canonical` and `name_swap` rows (Q2). `needs_review` rows are skipped. Output columns = Thais's `results/divergent/predictions.csv` + `name`, `name_group`. World-specific extras (like `experiments/divergent.py`) can stay, but **headline numbers come from `results/all.csv`**.


For each world × row × method × template, compute the probabilities and write one row to `results/all.csv`:

```
world, id, origin_id, test_type, method, template, gold, pred, probs_json, raw_probs_json, entropy
```
- Cache the results, so re-runs skip rows already computed.
- Use the 3 templates for MLM only. Embedding and NLI need just one run.
- Run occlusion only on `canonical` rows, using MLM, and save it to `results/occlusion.csv`.

**Done when:** every world is in `all.csv` and the number of rows matches what we expected.

---

## Step 6: Analysis notebooks (about 1 week, split by question)

| Notebook | Owner | Computes | Output |
|---|---|---|---|
| `q1_correctness.ipynb` | M4 | Accuracy and macro-F1 per world × method, with bootstrap 95% CIs (1,000 resamples), against chance. **Real worlds vs. invented world.** | Table 1 |
| `q2_traits.ipynb` | M1 | canonical vs. no_name vs. name_swap (McNemar on paired rows); the share of name_swap predictions that follow the name; whether the top occlusion trait is the one we expected | Table 1 (rows) |
| `q3_ambiguity.ipynb` | M2 + M3 | Entropy for generic/conflicting vs. canonical (Wilcoxon); **JSD between BERT and the simulated panel**; Baan et al.'s entropy calibration error (against the panel); negation flip rate and total variation; conflicting split mass on A∪B | Figure 1 |
| ~~`clustering.ipynb`~~ | dropped 2026-11-23 | Doesn't answer Q1–Q3; no room in 2 pages | — |

**Done when:** each notebook ends with a 5-line plain-language answer to its question.

---

## Step 7: `api.py` (half a day)

A FastAPI wrapper around `sorter.py`. **This is the contract the Node app will call:**

`GET /health` → `200 {}`

`POST /sort`
```json
{ "traits": ["observant", "cautious"], "free_text": "stubborn but kind" , "worlds": ["hp", "invented"], "explain": true }
```
→
```json
{
  "model": "bert-base-uncased",
  "worlds": {
    "hp": {
      "methods": {
        "mlm":   { "probs": {"gryffindor": 0.2, "...": 0.8}, "raw_probs": {"...": 1.0} },
        "embed": { "probs": {"...": 1.0} },
        "nli":   { "probs": {"...": 1.0} }
      },
      "occlusion": [ { "trait": "cautious", "delta": 0.12, "flips_to": "hufflepuff" } ]
    }
  }
}
```
- Group ids must match the keys in `app/worlds.json`.
- `free_text`: append it to the traits as a second sentence ("They describe themselves as …"), or ignore it. Write down which in the report.
- Return `occlusion` only when `explain` is true. It's the slow part, so batch it and use the first template only.
- Run: `uvicorn api:app --port 8000`

**Done when:** `curl -X POST localhost:8000/sort` with the example body returns probabilities for every requested world.

---

## Step 8: The app (Gradio, Ana; decided 2026-11-23)

> **Decision:** Gradio instead of Node. It's faster: plain Python that imports `sorter.py` directly, with free hosting on Hugging Face Spaces. The Node design below is kept only for its tab and quiz ideas.

### Original Node proposal (superseded)

A small Node app called **"The Unsure Hat"**. It has no npm dependencies and calls `api.py` for every BERT number, so the app and the experiments always agree.

**Proposed files**
```
app/
├── server.js        # node:http only. Serves public/, plus /api/sort-quiz and /api/sort, which forward to api.py
├── questions.json   # quiz content (draft already written, see below)
├── worlds.json      # group names and colors per world (draft already written)
└── public/          # index.html, style.css, app.js (plain JS, no build step)
```

**Proposed endpoints (Node)**
| Route | Does |
|---|---|
| `GET /api/questions` | Questions *without* hidden traits or keys, so users can't game the quiz. |
| `POST /api/sort-quiz` | answers → hidden traits + quiz-key distribution (computed in Node) → forwards the traits to `api.py /sort` → returns both. |
| `POST /api/sort` | Free traits from the playground → `api.py /sort`. |
| `GET /api/health` | Whether `api.py` is reachable. |

**Screens**
1. **Quiz:** one question per screen, with the options in random order, then the optional free text. Results show all 5 worlds side by side. Each world shows what we expected (the quiz key) next to BERT's distribution, a certainty meter (1 − normalized entropy), the top occlusion traits, and an agree/disagree verdict. A method selector (MLM / embedding / NLI) and a calibrated/raw toggle switch the BERT view. A "show what BERT saw" button reveals the hidden traits.
2. **Playground:** type any traits. Example buttons try generic, conflicting and element-word inputs. A **negation check box** runs the "not …" version too and reports how far the answer moved (total variation distance) and whether the top pick changed.
3. **How it works:** one paragraph per method for a non-NLP audience. This is the Educator track.

**The Hat's comments** are templates filled with the API's numbers. No LLM writes them. Examples: "Easy. Ravenclaw (71%)", "you could be anywhere, X and Y are 8 points apart", "before calibration I'd have said X", "in the invented world my certainty drops to …".

**Rules:** escape all user text before rendering it; never show fake BERT numbers (if the API is down, show the quiz key and say BERT is offline); make it work at phone width (the class will use phones for the live vote).

**The quiz content (drafts in `app/questions.json`, review as a team)**
- 12 original scenario questions plus 1 optional free-text question. They're written in the *style* of the official tests, with nothing copied:
  - Wizarding World quiz: dilemmas, "which would sting most", choosing an object or a power.
  - Divergent aptitude test: the growling dog, the stranger who asks about someone you know.
  - Game of Thrones house values: duty, ambition, passion.
  - Avatar nations' values.
- Each option carries **2 hidden traits** (all BERT sees) and a **key** per world (what we expected, or `null`).
- No group names or element words appear anywhere in the questions or options, so the user can't steer the result and BERT can't take lexical shortcuts.
- Mixed answers produce conflicting profiles naturally, which is the ambiguity we want to show live.

**Research use (optional):** log anonymous quiz answers from classmates who consent, and report quiz-key vs. BERT agreement as another human baseline.

**Open decisions for the team**
- [ ] Node, or Gradio (Python only, simpler hosting)?
- [ ] Hosting: local machine for the presentation, or a Docker Space?
- [ ] Add the "Beat the Hat" live vote page?
- [ ] Approve the quiz keys. Some are judgment calls, for example "pocketknife" → Earth Kingdom.

**Done when:** a volunteer can take the quiz on a phone and see real BERT results for all 5 worlds in under about 10 s.

---

## Step 9: Report (about 4 days)

IEEE template, at most 2 pages. Follow the outline in PLAN.md §7. Table 1 comes from step 6 Q1/Q2, and Figure 1 from Q3. The app link goes in Material.

## Step 10: Presentation and interview (2 days)

1. Live demo:
   - one quiz taken by a volunteer;
   - in the playground: "smart, nice" (high uncertainty) → "brave, ambitious" (split) → negation check box (barely moves).
2. Then show Table 1 (the invented-world gap) and Figure 1 (BERT vs. humans).
3. Everyone runs through the whiteboard checklist in PLAN.md §8.
