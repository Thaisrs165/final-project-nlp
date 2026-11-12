# Implementation plan, step by step

The research design lives in [PLAN.md](PLAN.md) and the literature in [RELATED_WORK.md](RELATED_WORK.md).
This file covers **what to build, in what order, and how we know each step is done**.

```
Step 1 setup ─► Step 2 data ─► Step 3 sorter.py ─► Step 4 test generator ─► Step 5 experiments ─► Step 6 analysis ─► Step 9 report
                                   │
                                   └─► Step 7 api.py ─► Step 8 Node interface ─► Step 10 presentation
```
Steps 2 and 3 can run in parallel. Step 8's front end can start alongside them if it shows only the quiz key until the API exists.


## How we work

- **Claude asks for approval before starting each step** and doesn't start building anything on its own.
- **Claude stops at every 🛑 checkpoint** and tells you exactly what to do by hand, then waits until you say it's done.

### 🛑 Everything that needs a human, in order

| When | What | Who | Time |
|---|---|---|---|
| Step 2.6 (do first) | Paste [forms/human_votes_form.md](forms/human_votes_form.md) into Google Forms and apply its settings checklist | 1 person | 20 min |
| Step 2.6 | Send the form link to the class; chase until there are ≥ 30 responses | everyone | spread over 1–2 weeks |
| Step 2.1 | Check the group descriptions against their sources | each world's owner | 10 min/world |
| Step 2.2 | Trait check: mark each extracted trait ✓/✗ in the Google Sheet | each world's owner | ~1 h/world |
| Step 2.3 | Sort 20 unnamed trait sets per world, independently | 2 people | 30 min each |
| Step 2.4 | Approve the invented-world personas | Member 4 | 20 min |
| Step 2.6 | Link the form responses to a Google Sheet | 1 person | 2 min |
| Step 8 | Decide Node vs. Gradio and the hosting; approve the quiz keys | team | 30 min meeting |
| Step 8 | Create the hosting account or Space, if we host online (needs your login) | 1 person | 15 min |
| Step 9 | Write the report text (one paragraph each); Claude only formats it and checks the page limit | everyone | ~4 days |
| Step 10 | Interview practice at the whiteboard | everyone | 2 days |

---

## Step 1: Setup ✅ done 2026-11-11

```
final-project-nlp/
├── data/            # CSVs (step 2)
├── sorter.py        # the ONLY place methods live (step 3)
├── make_tests.py    # generates the automatic test sets (step 4)
├── run_experiments.py
├── api.py           # FastAPI wrapper for the app (step 7)
├── notebooks/       # analysis, one per question (step 6)
├── results/         # all.csv, tables, figures
├── tests/           # pytest for sorter.py
└── app/             # Node interface (step 8)
```
- [x] Python 3.11+ venv, plus a `requirements.txt` with: `torch transformers sentence-transformers scikit-learn scipy pandas numpy umap-learn matplotlib fastapi uvicorn pytest`
- [x] Node 18 or newer (no npm packages needed)
- [x] Pin the model names in one place: `bert-base-uncased`, `sentence-transformers/all-MiniLM-L6-v2`, `facebook/bart-large-mnli`

**Done when:** `python -c "import sorter"` runs, and `node -v` prints 18 or higher.

---

## Step 2: Data (about 1 week)

Legend: 🤖 = Claude does it (web search plus writing the files) · 🙋 = a team member has to do it · 🛑 = Claude stops and tells you before going on.

### 2.1 Group descriptions: `data/<world>_groups.csv`
Columns: `group, description, source_url`
- 🤖 For each of the 5 worlds, find the official description of each group and write a short paraphrase with the source URL. Sources: the Wizarding World site and the Sorting Hat songs; the Divergent faction manifestos; the Pokémon GO team leaders' statements; the Avatar nations' cultural values. The invented world uses the descriptions we write ourselves.
- 🙋 The world's owner checks that the descriptions match the source (about 10 min per world).

### 2.2 Canonical characters: `data/<world>_tests.csv`
Columns: `id, test_type, name, traits, gold_group, source_url, trait_evidence`

| World | Target | Gold label must come from |
|---|---|---|
| Harry Potter | ~40, about 10 per house | Books or the official Wizarding World site, never fan guesses |
| Divergent | ~25 | Books or films |
| Avatar | ~30 | The series |
| Pokémon GO | 3 leaders + ~30 personas | Personas are written from each team's official values (`source = persona`) |

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

### 2.4 Invented world: `data/invented_groups.csv`, `data/invented_tests.csv`
- 🤖 Check how BERT splits Veltrin, Osmark, Calwen and Durrask into word pieces and record the counts. Search each name to make sure it isn't a real brand or place, and propose replacements if any is.
- 🤖 Write 30 personas (about 7–8 per house). Use **synonyms** of the house descriptions, not the same words (for example, "never rushes" for *patient*), so BERT can't win by matching identical words.
- 🙋 Member 4 reviews the personas and approves them.

### 2.5 Shared test inputs
- 🤖 `data/generic.csv`: 25 vague trait sets ("smart, nice", "funny, a good friend").
- 🤖 Avatar shortcut pairs: element-flavored vs. neutral wording (Member 3 reviews them).
- Everything else (no_name, name_swap, negation, conflicting) is generated by the script in step 4.

### 2.6 Human votes form: `data/human_votes.csv`
- 🤖 ✅ The questions, options and form settings are written in [forms/human_votes_form.md](forms/human_votes_form.md). There are 39 sorting items across 5 worlds (generic, conflicting and clear), a familiarity grid, and an answer key that stays with us.
- 🛑 **Checkpoint: build the form.** One person pastes the questions into Google Forms and applies the settings checklist at the top of that file (about 20 min).
- 🛑 **Checkpoint: send the form** to the class (WhatsApp, Slack, etc.). Target at least 30 responses. **Do this in week 1**, because it's the slowest step of the whole project.
- 🛑 **Checkpoint: link the responses** to a Google Sheet (Responses → Link to Sheets). Then 🤖 Claude reads it through the Sheets connector and writes `data/human_votes.csv`.

**Done when:**
- every CSV loads with `pandas`;
- no canonical row is missing `gold_group` or `source_url`;
- the trait check is finished;
- κ and human accuracy are computed;
- the form has at least 30 responses.

## Step 3: `sorter.py` (2–3 days, written together on day 1–2)

One module, used by the experiments **and** the app. Load the models once, at import time or lazily.

```python
TEMPLATES = [
    "Someone who is {traits} belongs to {group}.",
    "A person described as {traits} would be sorted into {group}.",
    "{traits}: this sounds like a member of {group}.",
]
CONTENT_FREE = "N/A"

def score_mlm(traits, groups, template, calibrate=True) -> dict[str, float]
def score_embed(traits, group_descriptions, model="minilm"|"bert-mean") -> dict[str, float]
def score_nli(traits, groups) -> dict[str, float]
def to_probs(scores) -> dict[str, float]      # softmax over the group scores
def entropy(probs, normalized=True) -> float
def occlusion(traits, groups, method) -> list[dict]   # [{trait, delta, flips_to}]
```

**MLM scoring with PLL-word-l2r** (Kauf & Ivanova 2023). For a sentence with the group name filled in, where the name has word pieces `t1..tk`:
```
score(name | traits) = Σ_i log P(t_i | sentence with t_i..t_k masked)
```
In other words, mask the current word piece **and every later piece of the same name**, then read the probability of the current piece. Only the name's pieces are scored, because the rest of the sentence is identical across candidates.

**Calibration** (Kurita 2019; Zhao 2021):
```
calibrated(name) = score(name | traits) − score(name | "N/A")
```
This also cancels the length penalty for long names. Report both `raw_probs` and calibrated `probs`.

**Occlusion:** for each trait, remove it, re-score, and set `delta = p(top group | all traits) − p(top group | without trait)`. `flips_to` is the new top group if it changed.

**Tests (`tests/test_sorter.py`):**
- [ ] The word-piece count for each group name matches what we recorded.
- [ ] Probabilities sum to 1.
- [ ] The calibrated content-free prompt gives a uniform distribution.
- [ ] Results are deterministic (`torch.manual_seed`, `model.eval()`).
- [ ] An obvious sanity case: "brave, daring, bold" puts Gryffindor in the top 2.

**Done when:** the tests pass and one call takes under about 2 s on CPU for a single world.

---

## Step 4: `make_tests.py` (1 day)

Reads canonical rows and writes generated rows back to `data/<world>_tests.csv`, with an `origin_id` column linking each to its source row.

| test_type | Rule |
|---|---|
| `no_name` | Drop the name. |
| `name_swap` | Use the traits of X with the name of Y from another group (at least 20 per world). |
| `negation` | Add "not" to every trait. Paired with the original through `origin_id`. |
| `conflicting` | 2–3 traits from group A plus 2–3 from group B. Gold is the pair `A\|B`. |
| `generic` | Rows of `generic.csv`, copied into every world. Gold is empty. |
| `shortcut` (Avatar) | Element-flavored vs. neutral synonyms, hand-written pairs. |

**Done when:** the counts per test type are printed and checked by hand on 5 random rows.

---

## Step 5: `run_experiments.py` (1 day of code, then it runs)

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
| `q3_ambiguity.ipynb` | M2 + M3 | Entropy for generic/conflicting vs. canonical (Wilcoxon); **JSD between BERT and human votes**; Baan et al.'s human-entropy calibration error; negation flip rate and total variation; conflicting split mass on A∪B | Figure 1 |
| `clustering.ipynb` | whoever finishes first | ARI/NMI of KMeans on the embeddings vs. true groups; UMAP plot | Appendix |

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

## Step 8: Node interface (2–3 days, proposed, not built)

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
  - Pokémon GO leaders: trust your gut, the evidence, or your strength.
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
