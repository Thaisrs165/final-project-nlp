# Related work: what backs up each part of the project

Each entry says what the paper found and **how we use it**. Full BibTeX is in [references.bib](references.bib).
Status: the venue and authors of everything marked ✅ were checked online (Nov 2026). The others are standard citations we're confident about, but still open each PDF before citing.

---

## The gap (paragraph for the intro)

Probing studies test whether BERT recalls **facts** ("Paris is the capital of [MASK]"; Petroni 2019). Later work showed that part of that "knowledge" is really guessing from the **surface form of names** (Poerner 2020; Shwartz 2020).
Stereotype studies measure **group–trait associations** (Kurita 2019; Cao 2022), but only on real social groups, where the right answer is contested.
Ambiguity studies show that models don't reproduce **human disagreement** (Nie 2020; Liu 2023), but they test it on NLI, not on trait-to-group mapping.
Personality work on fictional characters (Sang 2022; Yu 2023) **trains classifiers**. It doesn't ask what a frozen model already associates.
We found no peer-reviewed work on "sorting" fictional groups. The only things that exist are hobby projects: blogs, a Watson demo, a fastText toy.
**Our gap:** a controlled test of trait→group mapping in a frozen MLM. It compares real franchises with a memorization-free **invented world**, and it scores ambiguous inputs against **human vote distributions** instead of a single gold label.

---

## Q1: Is BERT answering correctly? (probing and memorization)

| Paper | What it found | How we use it |
|---|---|---|
| Devlin et al. 2019, *BERT* (NAACL) | The model we probe. Pretrained on Wikipedia and BookCorpus. | Explains why pre-2018 franchises may be memorized. |
| Petroni et al. 2019, *Language Models as Knowledge Bases?* (EMNLP) | Introduced the LAMA cloze-probing benchmark and showed that BERT recalls relational facts without fine-tuning. | Our fill-in-the-blank method is LAMA-style probing. |
| ✅ Poerner, Waltinger & Schütze 2020, *E-BERT* (Findings of EMNLP; arXiv preprint titled *BERT is Not a Knowledge Base (Yet)*) | BERT's LAMA precision **drops sharply when facts that can be guessed from the entity name are filtered out** (LAMA-UHN). | Direct precedent for our `name_swap` / `no_name` tests and the invented-world control. |
| ✅ Shwartz, Rudinger & Tafjord 2020, *"You are grounded!": Latent Name Artifacts* (EMNLP) | Given names get grounded to specific famous entities even in generic contexts, and **perturbing the name changes model answers**. | Justifies testing "Hermione's traits named Draco". |
| ✅ Misra, Rayz & Ettinger 2023, *COMPS* (EACL, best paper) | Uses **nonce concepts** ("wug") to test property knowledge without memorization. Models look good on the nonce setup but fail on harder pairs and with distractors. | Methodological precedent for our **invented world**: made-up names separate reasoning from recall. |
| Jiang et al. 2020, *How Can We Know What Language Models Know?* (TACL) | Probing results change a lot with prompt wording. | Why we use 3 prompt templates and report the variance. |
| ✅ Elazar et al. 2021, *Measuring and Improving Consistency in PLMs* (TACL) | PLMs give **inconsistent answers across paraphrased prompts** (ParaRel). | Same as above, plus a consistency metric across our templates. |

## Q2: Is it looking at the traits we expected? (shortcuts and explanation)

| Paper | What it found | How we use it |
|---|---|---|
| McCoy, Pavlick & Linzen 2019, *Right for the Wrong Reasons* (ACL) | NLI models exploit lexical-overlap heuristics. | Framing for the Avatar "fiery → Fire Nation" lexical-shortcut test. |
| Geirhos et al. 2020, *Shortcut Learning in Deep Neural Networks* (Nature Machine Intelligence) | General account of shortcut learning. | Defines "shortcut" in the report. |
| Jain & Wallace 2019, *Attention is not Explanation* (NAACL) | Attention weights don't reliably indicate feature importance. | Why we use **occlusion** instead of attention maps. |
| Wiegreffe & Pinter 2019, *Attention is not not Explanation* (EMNLP) | Nuanced reply to the paper above. | Shows the interviewer we know both sides of the debate. |
| Li, Monroe & Jurafsky 2016, *Understanding Neural Networks through Representation Erasure* (arXiv) | Erasing inputs to measure their importance. | The origin of our leave-one-trait-out method. |
| ✅ Kurita et al. 2019, *Measuring Bias in Contextualized Word Representations* (GeBNLP workshop) | Measures **group–attribute association in BERT's MLM** as log(p_target / p_prior), where the prior masks the attribute too. Works better than cosine-based measures. | **Our closest methodological ancestor:** same MLM association idea, same prior normalization, applied to fictional groups. |
| ✅ Cao et al. 2022, *Theory-Grounded Measurement of U.S. Social Stereotypes in English LMs* (NAACL) | Measures group–trait associations in LMs (ABC model) and **compares them with human judgments**. | Precedent for comparing an LM's trait→group mapping with human answers. Our fictional groups avoid the ethical problems of real social groups. |
| Nadeem et al. 2021, *StereoSet* (ACL); Nangia et al. 2020, *CrowS-Pairs* (EMNLP) | Benchmarks of MLM stereotype associations. | Related work: "trait→group association" is a known probing target. |

## Q3: How does it resolve ambiguity? (uncertainty, humans, negation)

| Paper | What it found | How we use it |
|---|---|---|
| ✅ Nie, Zhou & Bansal 2020, *ChaosNLI* (EMNLP) | 100 human labels per item. Models **can't recover the human label distribution** and do barely better than chance on low-agreement items. | **Our core reference for the human-vote study.** Evaluate against the distribution of human votes, not a majority label. JSD metric. |
| Pavlick & Kwiatkowski 2019, *Inherent Disagreements in Human Textual Inferences* (TACL) | Human disagreement is real signal, not noise. | Justifies treating "smart and nice" as genuinely ambiguous. |
| ✅ Baan et al. 2022, *Stop Measuring Calibration When Humans Disagree* (EMNLP) | Proposes instance-level metrics such as **human entropy calibration error** and human-distribution calibration error. | Gives us ready-made, citable metrics for BERT vs. humans on ambiguous items. |
| ✅ Liu et al. 2023, *We're Afraid Language Models Aren't Modeling Ambiguity* (EMNLP) | AmbiEnt benchmark: even GPT-4 handles ambiguity poorly. | Shows that ambiguity is an open problem, so our work is timely. |
| Zhao et al. 2021, *Calibrate Before Use* (ICML) | LMs have a **majority-label / common-token bias**. A content-free prompt ("N/A") corrects it. | Our calibration step and our hypothesis that "under ambiguity, BERT falls back to the most frequent name". |
| Ettinger 2020, *What BERT Is Not* (TACL) | Psycholinguistic diagnostics. BERT is largely **insensitive to negation**. | Our negation test and the flip rate we compare against. |
| Kassner & Schütze 2020, *Negated and Misprimed Probes* (ACL) | BERT often predicts the same answer for "X is Y" and "X is not Y". | Same as above; the negated-LAMA precedent. |
| ✅ Truong et al. 2023, *Language Models are not Naysayers* (*SEM) | Negation insensitivity persists in GPT-3-class models. | Shows the negation problem isn't solved by scale (optional ModernBERT comparison). |

## Methods (scoring and embeddings)

| Paper | What it found | How we use it |
|---|---|---|
| ✅ Salazar et al. 2020, *Masked Language Model Scoring* (ACL) | **Pseudo-log-likelihood (PLL)**: score a sentence by masking each token in turn. | How we score multi-token group names ("Gryffindor"). |
| ✅ Kauf & Ivanova 2023, *A Better Way to Do MLM Scoring* (ACL short) | The original PLL **inflates scores of multi-token words**. Their fix, **PLL-word-l2r**, also masks the later tokens of the same word. | **Important for us:** invented names are long and multi-token, so plain PLL would bias toward them. Use PLL-word-l2r. |
| Ethayarajh 2019, *How Contextual are Contextualized Word Representations?* (EMNLP) | BERT embeddings are **anisotropic**: all cosine similarities are high. | Why raw BERT mean-pooling is a weak baseline for similarity. |
| Reimers & Gurevych 2019, *Sentence-BERT* (EMNLP) | Siamese fine-tuning gives useful sentence embeddings. | Our MiniLM similarity method. |
| Yin, Hay & Roth 2019, *Benchmarking Zero-shot Text Classification* (EMNLP) | NLI models can be used as zero-shot classifiers (label → hypothesis). | Our `bart-large-mnli` baseline. |
| Rogers, Kovaleva & Rumshisky 2020, *A Primer in BERTology* (TACL) | Survey of what BERT knows. | Background citation for the intro. |

## Fictional characters and personality (domain)

| Paper | What it found | How we use it |
|---|---|---|
| Bamman, O'Connor & Smith 2013, *Learning Latent Personas of Film Characters* (ACL) | Unsupervised character personas from plot text. | Fictional characters have long been an NLP object of study. |
| ✅ Sang et al. 2022, *MBTI Personality Prediction for Fictional Characters* (Findings of EMNLP; Story2Personality) | 3,543 movie characters. **Supervised** classifiers stay below 60% macro-F1. | Contrast: they train, we probe a frozen model. Shows that trait→type mapping is hard. |
| ✅ Yu et al. 2023, *Personality Understanding of Fictional Characters during Book Reading* (ACL; PersoNet) | Fine-grained character traits from reader notes. | Precedent for annotating traits of fictional characters. |
| ✅ Chen et al. 2023, *LLMs Meet Harry Potter: A Dataset for Aligning Dialogue Agents with Characters* (Findings of EMNLP) | HP dialogue dataset with 13 annotated character attributes. | **Possible extra source of HP character attributes** to cross-check our Fandom traits. |

---

### Non-academic prior art (mention in one sentence to show we looked)
Hobby "sorting hat" projects exist: IBM Watson demo (2016), the NatLibFi fastText model on Hugging Face, and several blog classifiers. All of them **train** on house labels, and none studies ambiguity or memorization. This supports our gap claim.

### Which to cite in the 2-page report (budget: ~12)
Petroni 2019 · Poerner 2020 · Shwartz 2020 · Misra 2023 · Kurita 2019 · Nie 2020 · Baan 2022 · Zhao 2021 · Ettinger 2020 · Kauf & Ivanova 2023 · Jain & Wallace 2019 · Sang 2022.
Everything else goes in the appendix or is kept for the interview.
