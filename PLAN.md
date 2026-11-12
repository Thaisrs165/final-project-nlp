# Does BERT actually sort you? — Build plan

**Tracks:** Researcher + Educator (needed for an A).
**Thesis in one line:** We test whether a frozen BERT puts people into groups because of their traits or because of names it memorized, and what it does when the traits don't point to a single group.

We use fictional sorting systems (HP, Divergent, Pokémon GO, Avatar, and one invented world) as a controlled test bed. The project is about **BERT and ambiguity**. Harry Potter is only the setting.

---

## 1. The three questions and how each is answered

| # | Question (from our notes) | Experiment | Metric | Prior work we compare to |
|---|---|---|---|---|
| Q1 | *Is BERT answering correctly?* | Canonical characters, real franchises vs. **invented world** | Accuracy / macro-F1 vs. chance, bootstrap 95% CI | LAMA probing (Petroni 2019) |
| Q2 | *Is it looking at the traits we expected?* | (a) name kept / removed / swapped; (b) leave-one-trait-out occlusion | Accuracy drop and McNemar test; % of cases where the most influential trait is the one we expected | Jain & Wallace 2019 (why occlusion and not attention) |
| Q3 | *How does it resolve ambiguity?* | generic, conflicting, and negated inputs, compared with **human votes on the same inputs** | Entropy; Jensen–Shannon divergence between BERT's and humans' distributions; negation flip rate | Ettinger 2020, Kassner & Schütze 2020 (negation); ChaosNLI (Nie et al. 2020) and Pavlick & Kwiatkowski 2019 (human disagreement) |

**New piece compared with the earlier plan: human votes as the reference for ambiguity.**
For an ambiguous input like "smart and nice", we can't simply assume the right answer is a uniform split. So we ask about 30 classmates to sort the same ambiguous inputs using a Google Form. The human vote distribution becomes the gold standard: a good model is uncertain in the same places people are. This follows ChaosNLI, and it turns Q3 from a matter of opinion into something we can measure. It is also the part of the project that makes it unique.

**Measurable objective (for the report):**
> The project succeeds if we report, with 95% CIs: (1) the accuracy gap between real franchises and the invented-world control; (2) the JSD between BERT's and humans' distributions on ambiguous inputs, compared with the canonical ones; and (3) BERT's negation flip rate, compared with Ettinger (2020).

---

## 2. Technical traps to settle on day 1

1. **Group names are split into several subword tokens.** In `bert-base-uncased`, "Gryffindor", "Abnegation" and every invented name become several wordpieces, so a single `[MASK]` can't predict them.
   → Score each candidate by filling it into the prompt and computing its **pseudo-log-likelihood** (Salazar et al. 2020), using the **PLL-word-l2r** variant (Kauf & Ivanova 2023). Plain PLL inflates the scores of multi-token words, which would bias the results toward the long invented names.
2. **Name-frequency bias.** BERT may prefer "Gryffindor" simply because it is common in Wikipedia.
   → **Calibrate** against a content-free prompt ("Someone who is N/A belongs to ___") and subtract that prior (Zhao et al. 2021, *Calibrate Before Use*). Report both the raw and the calibrated scores. The size of the gap is itself a finding for Q3: *under ambiguity, does BERT fall back to the most frequent name?*
3. **Prompt sensitivity.** Use 3 prompt wordings and report the mean and spread (Jiang et al. 2020).
4. **No training on small data.** BERT stays frozen. An optional logistic-regression probe needs leave-one-out cross-validation and must be clearly labeled as a small-data sanity check (a model trained on small data is what the rubric marks as a D).

---

## 3. Scope: keep or cut

**Keep:** 3 methods (MLM pseudo-log-likelihood, embedding similarity with BERT mean-pooling vs. MiniLM, NLI zero-shot with `bart-large-mnli`), 5 worlds, 6 test types, clustering (ARI/NMI plus one UMAP plot).
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

Otherwise negation would be tested only on Pokémon, and we couldn't tell a negation effect apart from a Pokémon effect.

---

## 4. Data (minimum viable)

```
data/<world>_groups.csv   group, official_description
data/<world>_tests.csv    id, test_type, name, traits, gold_group, source
data/generic.csv          id, traits                     # shared across worlds
data/human_votes.csv      item_id, world, voter_id, group # from the Google Form
```

- 5 traits per character, taken from the Fandom "Personality" sections. A second annotator writes traits for 10 characters per world, and we report Cohen's κ.
- Rough size: HP 40, Divergent 25, Avatar 30, Pokémon 30 personas, invented 30 personas.
- Google Form: about 40 items (20 generic, 10 conflicting, 10 canonical as a sanity check), about 30 respondents. **Send it in week 1** because responses take time to come in.

---

## 5. The interactive part: "The Unsure Hat"

> **Proposal (not built yet):** a small Node interface with a personality quiz in front, a playground and an explainer. It would be backed by the same `sorter.py` through `api.py`. See [IMPLEMENTATION.md](IMPLEMENTATION.md), steps 7–8. The tab ideas below still apply.

Originally planned as a Gradio app on Hugging Face Spaces built on the same `sorter.py` the experiments use. It has three tabs, and each one demonstrates one of our questions live.

### Tab 1: Talk to the Hat (chatbot, Q2 + Q3)
A chat interface (`gr.Chatbot`). You describe yourself in free text and the Hat answers. **The Hat's replies are templates filled with BERT's numbers. No LLM is involved, so everything it says is a real measurement.** Examples:

- Low entropy: *"Easy. Ravenclaw (71%). The word that did it: 'curious'. Without it, I'd say Hufflepuff."* (from occlusion)
- High entropy: *"Hmm… my top three are within 6 points of each other. Honestly, my top guess is just the name I've seen most often."* (shown when raw and calibrated scores disagree)
- Negation: *"You said 'not brave'. My answer moved by only 2%. I'm known to ignore 'not'."*

The interface also shows each word of the input colored by its occlusion importance, plus a live **certainty meter** (entropy).

### Tab 2: Multiverse (Q1 + cross-franchise)
One input is sorted in all 5 worlds side by side. "brave, reckless" → Gryffindor / Dauntless / Valor / Fire Nation / ? (invented). This shows that BERT is consistent in the real worlds and lost in the invented one, which is the memorization finding in one picture.

### Tab 3: Beat the Hat (live game for the presentation, Q3)
1. A QR code on the slide opens a phone-friendly page.
2. The class votes on an ambiguous input before the reveal.
3. The app shows a bar chart of class votes vs. BERT.
4. Then the JSD for that item, together with the same number from our full study.

This makes the presentation interactive and ties straight back to our main metric. (Vote logging: `gr.State` plus a CSV on the Space; the Google Form remains the reliable data source for the report.)

**Why this counts as Educator:** it teaches people outside NLP that a model's confidence is not understanding, using a setting they already know.

---

## 6. Phases (relative; adjust to the deadline)

| Phase | Output | Owner |
|---|---|---|
| 0. Day 1 together | `sorter.py` (3 methods + pseudo-log-likelihood + calibration + occlusion + entropy), repo skeleton, Google Form sent | all |
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
- [ ] Cosine similarity; why raw BERT embeddings are anisotropic and Sentence-BERT is not
- [ ] NLI zero-shot: how a label becomes a hypothesis
- [ ] Entropy vs. JSD: why matching human uncertainty beats a uniform distribution as the target
- [ ] Occlusion vs. attention as an explanation
- [ ] ARI/NMI; bootstrap CI; McNemar
- [ ] Why no fine-tuning
- [ ] Why the invented world is the key control

## References

See [RELATED_WORK.md](RELATED_WORK.md) (what each paper found and how we use it) and [references.bib](references.bib).
