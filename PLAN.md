# Does BERT actually sort you? — Build plan

**Tracks:** Researcher + Educator (needed for an A).
**Thesis in one line:** We test whether a frozen BERT puts people into groups because of their traits or because of names it memorized, and what it does when the traits don't point to a single group.

We use fictional sorting systems (HP, Divergent, Game of Thrones, Avatar, and one invented world) as a controlled test bed. The project is about **BERT and ambiguity**. Harry Potter is only the setting.

---

## 1. The three questions and how each is answered

| # | Question (from our notes) | Experiment | Metric | Prior work we compare to |
|---|---|---|---|---|
| Q1 | *Is BERT answering correctly?* | Canonical characters, real franchises vs. **invented world** | Accuracy / macro-F1 vs. chance, bootstrap 95% CI | LAMA probing (Petroni 2019) |
| Q2 | *Is it looking at the traits we expected?* | (a) name kept / removed / swapped; (b) leave-one-trait-out occlusion | Accuracy drop and McNemar test; % of cases where the most influential trait is the one we expected | Jain & Wallace 2019 (why occlusion and not attention) |
| Q3 | *How does it resolve ambiguity?* | generic, conflicting, and negated inputs, compared with **a simulated, personality-diverse voter panel on the same inputs** | Entropy; Jensen–Shannon divergence between BERT's and the panel's distributions; negation flip rate | Ettinger 2020, Kassner & Schütze 2020 (negation); ChaosNLI (Nie et al. 2020) and Pavlick & Kwiatkowski 2019 (human disagreement) |

**New piece compared with the earlier plan: a reference distribution for ambiguity.**
For an ambiguous input like "smart and nice", we can't simply assume the right answer is a uniform split. The original plan was a Google Form answered by about 30 classmates, following ChaosNLI. **Changed 2026-11-18:** there wasn't time or enough respondents, so `make_votes.py` builds a **simulated panel of 40 voters** with distinct personalities (Big Five profile, franchise familiarity, reading style, self-projection, fan bias) who answer the same 39 items. The panel's vote split is the reference: a good model is uncertain where the panel is. **It is not human data**, and the report must say so and list it as a limitation. Details and assumptions: [DATA_LOG.md](DATA_LOG.md).

**Measurable objective (for the report):**
> **Targets (agreed 2026-11-23; full wording in [REPORT_ROADMAP.md](REPORT_ROADMAP.md) §4).** With 95% CIs:
> - **Q1:** BERT vs. the human baseline (HP: 70%), and real franchises vs. the invented world (Petroni 2019; Misra 2023).
> - **Q2:** name_swap accuracy is not significantly below no_name (McNemar, p ≥ 0.05) if BERT reads traits (Poerner 2020).
> - **Q3:** BERT's JSD to the human votes is below a uniform guess's (Nie 2020); the negation flip rate is compared with Ettinger (2020).

---

## 2. Technical traps to settle on day 1

1. **Group names are split into several subword tokens.** In `bert-base-uncased`, "Gryffindor", "Abnegation" and every invented name become several wordpieces, so a single `[MASK]` can't predict them.
   → Score each candidate by filling it into the prompt and computing its **pseudo-log-likelihood** (Salazar et al. 2020), using the **PLL-word-l2r** variant (Kauf & Ivanova 2023). Plain PLL inflates the scores of multi-token words, which would bias the results toward the long invented names.
2. **Name-frequency bias.** BERT may prefer "Gryffindor" simply because it is common in Wikipedia.
   → **Calibrate** against a content-free prompt ("Someone who is N/A belongs to ___") and subtract that prior (Zhao et al. 2021, *Calibrate Before Use*). Report both the raw and the calibrated scores. The size of the gap is itself a finding for Q3: *under ambiguity, does BERT fall back to the most frequent name?*
3. **Prompt sensitivity.** Use 3 prompt wordings and report the mean and spread (Jiang et al. 2020).
4. **Without descriptions, the invented world can't be scored fairly** (decided 2026-11-18). With only "Someone who is X belongs to Veltrin", BERT has no way to know what Veltrin means, so the control would sit at chance by design.
   → Every method runs in **two variants**: *without descriptions* (the model only sees the group names: memory plus whatever the name itself means) and *with descriptions* (the groups' one-line descriptions come first in the prompt). The gap between the variants, per world, separates "BERT already knew this franchise" from "BERT read the descriptions". Details: [DATA_LOG.md](DATA_LOG.md).
5. **No training on small data.** BERT stays frozen. An optional logistic-regression probe needs leave-one-out cross-validation and must be clearly labeled as a small-data sanity check (a model trained on small data is what the rubric marks as a D).

---

## 3. Scope: keep or cut

**Keep:** 3 methods (MLM pseudo-log-likelihood, embedding similarity with BERT mean-pooling vs. MiniLM, NLI zero-shot with `bart-large-mnli`), 5 worlds, 6 test types. **Clustering (ARI/NMI, UMAP) dropped 2026-11-23:** it doesn't answer Q1–Q3 and doesn't fit in 2 pages.
**Cut / appendix only:** ModernBERT comparison (only if time allows), extra franchises, the linear probe.

**One change to the member split:** keep franchise ownership for *data*, but **every test type runs on every franchise**, generated automatically from the canonical rows:

| Test type | How it's generated |
|---|---|
| `no_name` | Drop the name |
| `name_swap` | Swap names across groups |
| `negation` | Add "not" to each trait (template) |
| `conflicting` | Merge 2–3 traits from two groups |
| `generic` | A shared list of about 25 vague trait sets, written once and reused in every world |
| `invented` | Written by hand once |

Otherwise negation would be tested only on one world, and we couldn't tell a negation effect apart from that world's effect.

---

## 4. Data (minimum viable)

```
data/<world>/groups.csv   group, description, source_url    # one folder per world, one owner each
data/<world>/tests.csv    id, test_type, name, traits, gold_group, source_url, trait_evidence
data/generic.csv          id, traits                     # shared across worlds
data/vote_items.csv       item_id, world, item_type, traits, expected  # the 39 items
data/voter_personas.csv   one row per simulated voter                  # make_votes.py
data/simulated_votes.csv  item_id, world, voter_id, group, source       # make_votes.py
```

- 5 traits per character, taken from the Fandom "Personality" sections. A second annotator writes traits for 10 characters per world, and we report Cohen's κ.
- Rough size: HP 40, Divergent 25, Avatar 30, Game of Thrones 30, invented 30 personas.
- Simulated panel: 39 items (20 generic, 12 conflicting, 7 clear as an attention check), 40 voters in 10 personality archetypes. Built by `make_votes.py`, logged in [DATA_LOG.md](DATA_LOG.md).

---

## 5. The interactive part: "The Unsure Hat"

> **Decided 2026-11-23: Gradio, built by Ana** (faster than Node: plain Python, calls `sorter.py` directly, no separate `api.py` needed, free hosting on Hugging Face Spaces). The tab ideas below still apply.

Originally planned as a Gradio app on Hugging Face Spaces built on the same `sorter.py` the experiments use. It has three tabs, and each one demonstrates one of our questions live.

### Tab 1: Talk to the Hat (chatbot, Q2 + Q3)
A chat interface (`gr.Chatbot`). You describe yourself in free text and the Hat answers. **The Hat's replies are templates filled with BERT's numbers. No LLM is involved, so everything it says is a real measurement.** Examples:

- Low entropy: *"Easy. Ravenclaw (71%). The word that did it: 'curious'. Without it, I'd say Hufflepuff."* (from occlusion)
- High entropy: *"Hmm… my top three are within 6 points of each other. Honestly, my top guess is just the name I've seen most often."* (shown when raw and calibrated scores disagree)
- Negation: *"You said 'not brave'. My answer moved by only 2%. I'm known to ignore 'not'."*

The interface also shows each word of the input colored by its occlusion importance, plus a live **certainty meter** (entropy).

### Tab 2: Multiverse (Q1 + cross-franchise)
One input is sorted in all 5 worlds side by side. "brave, reckless" → Gryffindor / Dauntless / Targaryen / Fire Nation / ? (invented). This shows that BERT is consistent in the real worlds and lost in the invented one, which is the memorization finding in one picture.

### Tab 3: Beat the Hat (live game for the presentation, Q3)
1. A QR code on the slide opens a phone-friendly page.
2. The class votes on an ambiguous input before the reveal.
3. The app shows a bar chart of class votes vs. BERT.
4. Then the JSD for that item, together with the same number from our full study.

This makes the presentation interactive and ties straight back to our main metric. (Vote logging: `gr.State` plus a CSV on the Space; the simulated panel remains the reference for the report.)

**Why this counts as Educator:** it teaches people outside NLP that a model's confidence is not understanding, using a setting they already know.

---

## 6. Phases (relative; adjust to the deadline)

| Phase | Output | Owner |
|---|---|---|
| 0. Day 1 together | `sorter.py` (3 methods + pseudo-log-likelihood + calibration + occlusion + entropy), repo skeleton, simulated voter panel | all |
| 1. Lit review, about 1 week | 5-line summary per paper, BibTeX, a one-paragraph statement of the gap | all (2–3 papers each) |
| 2. Data, about 1 week | `data/*.csv`, κ, test sets generated automatically | each person's franchise |
| 3. Experiments, about 1 week | `results/all.csv` (world × method × test_type), 3 key tables, UMAP | Q1: M4 · Q2: M1 · Q3: M2 + M3 |
| 4. App, 3–4 days | Public Space link + QR code | M3 (others review) |
| 5. Report, about 4 days | IEEE PDF, at most 2 pages | 1 editor + 1 paragraph each |
| 6. Interview prep, 2 days | Whiteboard drills | all |

---

## 7. Report outline (2 pages)

1. **Intro**: start with *our doubt*: "When BERT puts us in Gryffindor, is it reading our traits, or just recognizing words?" Then related work (probing, negation, human disagreement) and the **gap**: probing studies test factual recall, but none test trait-to-group mapping under controlled ambiguity, against a memorization-free control and human uncertainty.
2. **Method**: 3 methods, pseudo-log-likelihood and calibration, test types, human study.
3. **Data**: worlds, trait sourcing, κ.
4. **Results**: 1 table (Q1/Q2 accuracy with CIs) and 1 figure (BERT vs. human distributions on ambiguous items, plus the negation flip rate).
5. **Conclusion**: answer Q1–Q3 directly, list limitations (small n, fictional settings, trait sourcing), describe the app.
6. **AI use** (one short paragraph): what we delegated (for example the Gradio boilerplate and plotting code), what worked and what didn't, and what we designed ourselves (questions, test design, calibration choice, human study).

---

## 8. Interview checklist (everyone, at a whiteboard)

- [ ] 30-second pitch
- [ ] Masked-LM probing, and why multi-token names need pseudo-log-likelihood
- [ ] Calibration: what the content-free prior is and why we subtract it
- [ ] Why every method runs with and without group descriptions (the invented world needs them)
- [ ] Cosine similarity; why raw BERT embeddings are anisotropic and Sentence-BERT is not
- [ ] NLI zero-shot: how a label becomes a hypothesis
- [ ] Entropy vs. JSD: why matching (simulated) human-like uncertainty beats a uniform distribution as the target
- [ ] Occlusion vs. attention as an explanation
- [ ] ARI/NMI; bootstrap CI; McNemar
- [ ] Why no fine-tuning
- [ ] Why the invented world is the key control

## References

See [RELATED_WORK.md](RELATED_WORK.md) (what each paper found and how we use it) and [references.bib](references.bib).
