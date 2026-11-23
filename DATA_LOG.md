# Data log

A running record of how the data was built and every decision that changed it.
Newest entries at the top. Anything that goes in the report's Data or Limitations section should be traceable to an entry here.

---

## 2026-11-23 · Game of Thrones: owner rulings (Fardin), steps 2.3 and 4 re-run
- **First names only: kept.** Claude's proposal; Fardin saw it and did not object. Not an explicit ruling.
- **Olenna admitted as an exception to the birth rule.** She is born Redwyne and Tyrell by marriage, but she heads House Tyrell in the series, and without her the house had no canonical row. Added at the end of `trait_picks.csv` as `got-c24` (sharp, astute, outspoken, unafraid, intelligent), so no existing id changed. **For the report:** Tyrell rests on **one** character, who is not Tyrell by birth; every generated conflicting row with Tyrell uses her traits. Read the Tyrell numbers as a case study.
- **Trait check done: all 11 borderline traits accepted**, following the HP precedents (Cho "popular", "emotional"; Pansy "anxious", "frightened"). Share accepted as extracted: **80 of 80 traits** in the 16 canonical rows, 11 of them borderline (table in the entry below).
- **Final set: 24 rows, 16 canonical, 8 `needs_review`.** Stark 4, Lannister 6, Targaryen 2, Greyjoy 3, Tyrell 1. The imbalance goes in the limitations; use macro-F1.
- **Step 4 re-run:** 16 no_name, 16 name_swap, 16 negation, 42 conflicting (4 per house pair for all 10 pairs + the 2 vote items), 25 generic.
- **Step 2.3:** `agreement.py make got` wrote `data/got/agreement/sheet_A.xlsx`, `sheet_B.xlsx` and `key.csv` with **16 items** (every canonical row; the script asks for 20). 🛑 Two annotators who have **not** seen the GoT character list fill them in. Fardin can't be one of them: he reviewed the traits with the names.

## 2026-11-23 · Game of Thrones steps 2.2 and 4: canonical characters
Built with the HP tools (`fetch_personality.py`, `make_tests.py`), wiki `gameofthrones`. The points marked "pending" below were ruled on the same day: see the entry above.

- **Names are first names only** ("Eddard", not "Eddard Stark"). In this world the surname *is* the house, so a full name gives the answer away, and the general rule "leave out characters whose name contains a group name" would remove every character. `page` in `characters.csv` keeps the full wiki title. *Pending: Fardin confirms.*
- **Scan.** 27 house members by birth were looked up, plus 19 more pages: minor members (Rickard, Brandon, Rhaella, Alton, Joanna, Martyn, Rodrik, Maron, Victarion, Garlan, Willas), two known by a married name (Olenna, Alerie) and six *House of the Dragon* characters, which are outside our sources. **No Personality section:** Rickon, Benjen, Aeron, Mace (role `spare`) and all the minor ones.
- **Wrong page caught:** "Viserys Targaryen" is Viserys I (*House of the Dragon*). The series character is "Viserys Targaryen (son of Aerys II)".
- **Leak list:** `data/got/leak_words.csv` (56 words): house names, every description word and its word forms (honourable, proud, ambitious, defiant, independent, diplomatic…), negated forms (dishonorable, disloyal), source-quote words (devoted, wealthy, rich, fierce, rebellious, clever), house-words cues (wintry, fiery) and sigils.
- **Trait rule, fixed before picking** (close to the Divergent rule, to avoid hand-picking): the **first 5 adjectives in text order** that (a) the article itself affirms: not negated, not "not as X as", not another character's opinion; (b) describe this character; (c) are a lasting trait, not a passing state, a physical attribute or a skill; (d) keep their meaning as a bare word (said of the character, or of their own attitude, nature, temper or humour).
- **Result: 23 rows, 15 canonical, 8 `needs_review`** (not padded).

  | House | Canonical | needs_review (valid traits) |
  |---|---|---|
  | Stark | 4: Eddard, Sansa, Arya, Lyanna | Robb (3), Bran (3) |
  | Lannister | 6: Tywin, Cersei, Jaime, Tyrion, Kevan, Lancel | — |
  | Targaryen | 2: Daenerys, Viserys | Aerys (2), Rhaegar (4), Aemon (4) |
  | Greyjoy | 3: Theon, Yara, Euron | Balon (3) |
  | **Tyrell** | **0** | Margaery (3), Loras (2) |

- **Tyrell has no canonical row.** By birth, only Margaery and Loras have a Personality section, and neither reaches 5 valid traits. **Olenna** (born Redwyne, so excluded by the README rule) is fetched as `spare`; she would be a clean row: sharp, astute, outspoken, unafraid, intelligent. *Pending: Fardin decides whether to admit her as an exception.* Until then accuracy and macro-F1 for this world cover 4 houses.
- **Borderline picks, kept and flagged (11 of 75 traits). Pending: Fardin marks each ✓/✗; a ✗ turns the row into `needs_review`.**

  | Character | Trait | Why it is borderline |
  |---|---|---|
  | Sansa | susceptible | "made her tragically susceptible to the manipulations of the Lannisters" (early seasons) |
  | Sansa | effective | "effective as Lady of Winterfell": closer to competence than personality |
  | Arya | spirited | describes "her spirited indifference to rules" |
  | Arya | distrustful | "clearly distrustful of Daenerys": one situation |
  | Tywin | unfettered | "often unfettered attitude": unusual word |
  | Jaime | cold, sarcastic | first stated as what "outsiders perceive"; confirmed later ("this cold and sarcastic attitude") |
  | Tyrion | sharp | describes his "sharp intellect" |
  | Kevan | content | "always content with being a follower" |
  | Viserys | tempestuous | describes his "tempestuous temper" |
  | Euron | unnerving | describes his "unnerving coyness" |

- **Rejected after reading the sentence** (examples): negated: Kevan "decisive", Theon "malicious", Euron "impulsive", "arrogant", Sansa "cruel", Viserys "unintelligent"; another character's opinion: Robb "stupid" (Tywin), "arrogant", "foolish" (Roose Bolton), Euron "half-insane"; about someone else: Tywin "nice", "generous" (his father), Arya "fatalistic" (the Hound), Sansa "tomboyish" (Arya); not personality: Tyrion "thick" (skin), "soft" (spot), Margaery "formidable" (skill), Loras "carefree" (life).
- **A wider extractor would not fix the thin rows.** A check that also accepts participles and mis-tagged adjectives finds at most one or two more usable words on the 8 `needs_review` pages (e.g. Robb "loving", Bran "detached"). The pages are short; the tagger is not the bottleneck.
- **Step 4 (`make_tests.py got`):** 15 no_name, 15 name_swap, 15 negation, 26 conflicting (4 per house pair among Stark, Lannister, Targaryen, Greyjoy + the 2 vote items; **no generated pair has Tyrell**), 25 generic. Re-run after any change to the canonical rows.
- **Not done yet:** step 2.3 (`agreement.py make got`) waits for the rulings above, so the sheets are not built from rows that may change. Only 15 canonical rows exist and the sheet wants 20.
- **Gold labels checked against the source (2026-11-23).** Fardin doesn't know the franchise, so Claude checked every label instead of leaving it to him. For all 27 characters and Olenna, the Game of Thrones Wiki infobox gives the house and the father; `gold_source` now holds that text and the episode the wiki cites (e.g. `[S1E1]`). All 27 are born into their gold house. Members with a second house by marriage keep the birth house (Sansa, Lyanna, Cersei, Margaery); Aemon, Lancel and Loras later renounce theirs and also keep it. Olenna is confirmed as House Redwyne, Tyrell by marriage.
- **Step 2.1 owner check, done by Claude for the same reason.** Each `source_quote` in `data/got/groups.csv` was looked up on the live pages. Found word for word: Stark "honorable devotion to duty" and Tyrell "clever leaders" (Dummies); Lannister "wealthiest region due to its abundance of gold deposits", Greyjoy "fierce raids" / "terror of the seas" and Tyrell "positive image" (Wikipedia). Targaryen is a close paraphrase (Wikipedia: "wiping out three of the seven ruling houses that refused to bend their knees"). **Not found:** the Greyjoy sentence about Balon's failed rebellion is no longer on the Wikipedia page; the quote now cites the Game of Thrones Wiki for it. Description wording is unchanged. The traits marked "our reading" stay our reading: no source lists them as house traits.

## 2026-11-23 · `fetch_personality.py`: section text was being dropped (fixed)
- **Bug.** `_Text` raised its skip counter on the edit link's inner `<a>` but lowered it only on `</span>`, `</div>` and a few other end tags. The counter stayed above zero and the text up to the next `</span>` or `</div>` was lost. On the Game of Thrones wiki this emptied 4 sections (Yara, Kevan, Aemon, Lyanna) and cut the start of the others.
- **Fix.** Inside a skipped element every nested tag is counted, so only the matching end tag ends the skip. Void tags (`<br>`, `<img>`…) are ignored.
- **HP is not affected in practice.** HP reads its `raw/` cache, which was not touched. On a fresh fetch the fixed parser now also drops the quote-box captions it was meant to drop (Luna Lovegood: 939 → 866 words; the lost words are the caption line). Ana decides whether to re-fetch.

---

## 2026-11-23 · Team decisions: targets, writers, clustering, app; step 5 runner
- **Objective targets agreed** (Ana): full wording in REPORT_ROADMAP.md §4, short form in PLAN.md §1. Q1 vs. the human baseline and the invented world; Q2 McNemar no_name vs. name_swap; Q3 JSD vs. a uniform guess, negation compared with Ettinger 2020.
- **Who writes what:**
  - Intro: Thais
  - Methods, data: Ana
  - Methods, models and stats: Esther
  - Results: Ana (Q1, Table 2) + Fardin (Q2, Q3, Figure 1)
  - Conclusion: Esther
  - The final editor is still to be picked. Details in REPORT_ROADMAP.md §5.
- **Clustering dropped** (ARI/NMI, UMAP): it doesn't answer any of Q1–Q3 and there's no room in 2 pages.
- **App: Gradio, built by Ana.** Chosen over Node because it's faster: plain Python calling `sorter.py` directly, no separate `api.py`, free hosting on Hugging Face Spaces.
- **Papers:** the rubric requires a review of prior work (F without it; an A needs the gap). RELATED_WORK.md already has 34 papers; the 2-page list is **8 papers**, with the part to read in each (REPORT_ROADMAP.md §6). Whoever cites a paper opens the PDF first.
- **Step 5: `run_experiments.py`**, the one shared runner.
  - Every world's `tests.csv` × 4 methods × (3 templates for MLM, 1 otherwise) × with/without descriptions.
  - The name is passed only for canonical and name_swap rows; `needs_review` is skipped.
  - Output columns follow Thais's `results/divergent/predictions.csv`, plus `name` and `name_group`.
  - Cached, so re-runs only compute new rows.
  - `occlusion` (canonical, MLM, template 0, no name, both description variants) → `results/occlusion.csv`.
  - `summary` → `results/summary_q1q2.csv`: accuracy per world × method × descriptions on canonical, no_name and name_swap. MLM probabilities are averaged over the 3 templates first. Bootstrap 95% CI (2,000 resamples, seed 42); "follows the name" rate on name_swap; exact McNemar no_name vs. name_swap, paired by character.
  - All models stay in `sorter.py`; CLAUDE.md tells every assistant not to write another runner.
- **First full run (2026-11-23):** 5,640 predictions (HP 189 rows, Avatar 203, Divergent 78; × 12 settings each). Occlusion done for 66 canonical rows. 3 fast tests added for the runner.
- **First look at Q1/Q2 (not yet the analysis; step 6 does that properly):**
  - **HP canonical accuracy** (chance 25%, humans 70%): NLI 53% / 50% (without / with descriptions), embed 41% / 44%, MLM 29% / 24%, bert-mean 24% / 35%.
  - **Avatar** is near chance for every method (11–32%).
  - **Divergent** has only 4 canonical rows, which is too few to report.
  - **MLM collapses onto one group.** With a name and no descriptions, it answers Gryffindor in 97 of 102 HP predictions, whatever the name (name_swap: 96 of 102). Calibration doesn't remove it: the "N/A" prior doesn't capture the pull that a real name adds. With descriptions it **never** answers Gryffindor. Avatar shows the same pattern (no descriptions → mostly Earth; with descriptions → only Fire and Air).
  - So for MLM, accuracy equals the share of the favoured group, and the McNemar test can't show a name effect, because the model ignores both the traits and *which* name it is. That is a Q2/Q3 finding (a frequency fallback, as Zhao 2021 describe), not a bug.

---

## 2026-11-23 · `make_tests.py` no longer touches hand-made rows that have an `origin_id`
- After pulling Divergent: Thais's reversed conflicting probes (`cnf-…-ba`) have an `origin_id`, and `make_tests.py` treated any generated-type row with an `origin_id` as its own, so running it on Divergent would have **deleted 20 of her rows**. It wasn't run on Divergent, so nothing was lost.
- Fix: generated rows are now recognised only by their id patterns (`-nn`, `-ns`, `-neg`, `<world>-x..`, `<world>-v-..`, `<world>-g-..`). Extra columns already in a world's `tests.csv` are kept. HP and Avatar output is byte-for-byte identical; a dry run keeps all 78 Divergent rows.
- **Still open, in Thais's `experiments/divergent.py` (her file, not changed here):**
  - its `build` drops every `conflicting`/`generic` row, including the ones `make_tests.py` adds;
  - it writes without the `name_group` column, which name_swap rows need.
  - So for now, run `make_tests.py divergent` **after** her `build`, never before.
- Merged with Esther's shortcut rows (same day): their ids (`<world>-sNN-el` / `-ne`) were added to the id patterns, so re-runs replace them instead of duplicating them.

---

## 2026-11-23 · HP step 2.3: human baseline and κ (sheets returned)
- Both sheets came back complete (20/20 answers each, all from the dropdown). Scored with `agreement.py score hp` → `data/hp/agreement/results.json`. Bootstrap 95% CIs (5,000 resamples of the 20 items, seed 42).

| | Accuracy (95% CI) | Notes |
|---|---|---|
| A (Thais) | **55%** (35–75%) | never chose Ravenclaw (0/5 Ravenclaws right) |
| B (Fardin) | **85%** (70–100%) | |
| Mean (human baseline) | **70%** | chance = 25% |
| A vs. B | raw agreement 55%, **Cohen's κ = 0.37** (0.08–0.64) | "fair" agreement (Landis & Koch 1977) |

- **By house (A, B correct out of 5):** Slytherin 5, 5 · Gryffindor 3, 5 · Hufflepuff 3, 4 · **Ravenclaw 0, 3**. Both annotators were right on 10 items: 5 Slytherin, 3 Gryffindor, 2 Hufflepuff, **0 Ravenclaw**.
- **Ravenclaw is hard by construction:** the leak filter bans the words that define it ("intelligent", "wise", "witty", "learning"), so Ravenclaw rows keep traits like "quirky, serene" (Luna) or "timid, gullible" (Quirrell). Slytherin rows keep openly negative traits ("sadistic", "spiteful"), which read as "villain" without any leak word. This asymmetry is a limitation of literal Fandom traits plus the leak filter. Read BERT's per-house accuracy with it in mind.
- **Annotators:** A = Thais, B = Fardin. Ana confirmed Fardin doesn't know the books well, so his 85% isn't explained by recognising characters. Both results are kept as they are.
- **The human form points the same way:** the HP attention item k01-hp "witty, bookish, original" (gold Ravenclaw) was answered correctly by only 8/19 people, even though it uses words close to the description (see the form entry below). People find Ravenclaw hard to recognise from traits.
- The wide κ CI comes from n = 20. The report gives the CI, not just the point value.

---

## 2026-11-23 · Avatar shortcut pairs (lexical-shortcut test)
**Question.** Does BERT sort by personality, or by surface element words ("fiery" → Fire Nation)?

**Design.** `data/avatar/shortcut_pairs.csv`: **20 hand-written pairs, 5 per nation**, 3 traits each. Each pair has two versions with the same meaning:
- **element:** element-flavored words, e.g. "fiery; hot-headed; explosive", "icy; frosty; cool-headed", "rock-solid; grounded; immovable", "airy; breezy; light-hearted";
- **neutral:** synonyms without element imagery, e.g. "intense; short-tempered; volatile", "aloof; unfriendly; level-headed".

Gold = the nation the element words point to. The metric is accuracy (and the probability on gold), element vs. neutral, paired by `pair_id`. If accuracy drops sharply with neutral wording, the model relies on surface words.

**Rules.**
- Neither version may use a group id, nation name or any word of the group descriptions, so both are equally far from the descriptions. `make_tests.py` enforces this. It caught "down-to-earth" and "salt of the earth", which contain the label word "earth" itself; they were replaced with "firmly planted" and "sturdy as stone".
- These element words are banned from canonical rows (`leak_words.csv`), so they appear **only** here.
- **Approved by Esther on 2026-11-23, before any BERT run on them.** They're now frozen: editing them after seeing results would make the test circular.

**Pipeline.** `make_tests.py` now treats `shortcut` as a generated type. It rebuilds the rows from `shortcut_pairs.csv` on every run (ids `avatar-sNN-el` / `avatar-sNN-ne`, `origin_id` = pair id, `trait_evidence` = which variant), so edits go in the CSV, not in `tests.csv`. HP output is unchanged.

**Avatar now:** 28 canonical, 5 needs_review, 28 no_name, 28 name_swap, 28 negation, 26 conflicting, 25 generic, **40 shortcut** (208 rows).

---

## 2026-11-23 · Human form responses imported
**Source.** Google Forms export ("Forms NLP.xlsx", downloaded 2026-11-23): **19 responses** (2026-11-18 onward). The raw export isn't committed (it has submission timestamps); the anonymized data is:
- `data/human_votes.csv`: `item_id, world, voter_id, group, source=human`. 19 × 25 = 475 votes; voter ids h01–h19 in submission order. Columns were mapped to item ids in form order, and every answer was checked to be a group of that item's world.
- `data/human_respondents.csv`: `voter_id`, familiarity per franchise (0 = not at all, 1 = a little, 2 = well), `clear_wrong` (attention items missed, out of 5), `excluded` (1 if 2 or more missed).

**Attention rule, as set in advance (≥ 2 of 5 wrong → drop): 9 of 19 excluded, 10 kept.** That's exactly the useful minimum.

**⚠️ The attention items weren't obvious to people.** Correct answers per item, all 19 respondents:

| Item | Expected | Correct | Most common other answer |
|---|---|---|---|
| k01-hp "witty, bookish, original" | Ravenclaw | **8/19** | Slytherin 7 |
| k01-ava "never gives up, can endure anything" | Earth | 11/19 | Fire 8 |
| k01-got "always keeps their word" | Stark | 12/19 | Greyjoy 3 |
| k01-div "always tells the truth" | Candor | 14/19 | — |
| k01-inv "watches carefully…" | Veltrin | 14/19 | — |

So the rule removes people who **genuinely read the item differently**, not only random clickers. That pushes the kept sample toward consensus:
- mean normalized entropy on the 20 generic items: **0.46 with the rule (n = 10)** vs **0.67 with everyone (n = 19)**;
- simulated panel on the same items: 0.49.

**Decision (Esther, 2026-11-23):** keep the rule as the **primary** analysis (n = 10), because it was set before the data, and changing it now would be choosing the rule after seeing results. Report **all 19** as a sensitivity analysis, and say in the report that the attention items turned out to be ambiguous (k01-hp especially). This is a finding about the items, not a reason to drop people silently.

**First look (not a result).**
- With the rule, humans are about as consensual as the panel (H 0.46 vs 0.49). Several generic items are near-unanimous for people too: "smart and nice" → Ravenclaw 10/10, "funny and kind" → Amity 10/10 in Divergent. The earlier worry (2026-11-18) that the panel was too unanimous doesn't hold for these items.
- They disagree on specific items: "creative and talkative" (HP) is Gryffindor 60% for humans but Ravenclaw 91% for the panel; "easygoing and polite" is Air 50% vs 100% (Avatar) and Hufflepuff 90% vs 54% (HP).
- Familiarity ("well"): HP 14, GoT 9, Avatar 9, Divergent 3 of 19.

---

## 2026-11-23 · Avatar step 2.2: canonical characters (+ step 4 rows, 2.3 sheets)
Built with the HP tools (`fetch_personality.py`, `make_tests.py`, `agreement.py`), wiki `avatar`.

**Gold-label rule (confirmed by Esther, 2026-11-23).** Gold = the nation in the character's **Avatar Wiki infobox** (`nation =` field), cross-checked against the `ethnicity` field. The wiki pages block scripts, so the fields were read through the MediaWiki API.
- Includes both *Avatar: The Last Airbender* (2005–08) and *The Legend of Korra* (2012–14). Both are pre-2018.
- **Excluded:** characters whose ethnicity doesn't match their nation, or who changed nation: Kyoshi (Air Nomad–Earth Kingdom), Kai and Opal (Earth Kingdom-born, later Air Nation), Pema, Zaheer, Kya, and LoK Bumi (Aang's son).
- **Exception:** Tenzin, Jinora and Meelo (nation = air, Air Nomad ancestry mixed with Water Tribe) are kept, because without them the Air Nomads would have only 3 characters. In the story the Air Nomads were almost wiped out, so the imbalance is canon, not sampling.
- `characters.csv` → `gold_source` records the infobox fields for each character.

**Leak words (`data/avatar/leak_words.csv`, 53 words).**
- Nation names and bending words.
- Word forms of the description words: ambitious, passionate, adaptable, enduring, persistent, free, detached, peaceful… The automatic filter catches "bravely" from "brave" but **not** "ambitious" from "ambition", so forms must be listed.
- Words from Iroh's speech: power, strong, resilient…
- **Literal element words:** fiery, watery, fluid, earthy, grounded, airy… These belong only in the planned **shortcut test**, so canonical rows stay clean of them.
- Metaphors like "hot-headed", "warm" and "cold" aren't on the list but were **avoided by hand** in the picks for the same reason (Zuko's "hot-headed", Roku's "warm", Sozin's "cold").

**Result: 44 characters fetched → 33 rows: 28 canonical, 5 `needs_review`.**

| Nation | Canonical | needs_review |
|---|---|---|
| Fire | 7 (Zuko, Iroh, Azula, Mai, Zhao, Sozin, Ursa) | 3 (Ozai, Roku, Ty Lee) |
| Water | 7 (Katara, Sokka, Yue, Korra, Kuruk, Varrick, Noatak) | 1 (Tarrlok) |
| Earth | 8 (Toph, King Bumi, Haru, Kuei, Jet, Lin, Suyin, Lao) | 1 (Suki) |
| Air | 6 (Aang, Gyatso, Yangchen, Tenzin, Jinora, Meelo) | 0 |

- Not usable: Long Feng and Tashi (empty Personality sections); Jeong Jeong, Piandao, Izumi, Hakoda, Hama, Tonraq, Yakone (fewer than 5 adjectives).
- **Picks rejected after reading the sentence:**
  - about someone else: Mai "callous" (Azula), Sozin "manipulative"/"petty" (his father), Ty Lee "pessimistic" (Mai), "traitorous" (Zuko), Ozai "moralistic" (Zuko), Toph "goofy" (Sokka), Kuvira "forgiving" (Suyin), Yangchen "wise" (other Air Nomads), Ikki "authoritarian" (Meelo);
  - not personality: Ozai "evil" (about concepts), Zhao "sharp" ("sharp contrast"), Roku "noble" (upbringing), "volatile" (situations), "warm" (a hug), Varrick "irritable" (a rash), Suki "formidable" (her opponents), Sozin "cold" ("in cold blood"), Ikki "testy" (questions);
  - public perception only: Tarrlok "fair-minded".
- **Borderline picks for Esther's trait check:** Zuko "protective" (as a child), Mai "bitter" (one confrontation), Ursa "loving" (a relationship), Aang "carefree" (his "exterior"), Gyatso "wistful" ("wistful determination"), Kuei "fearful" (one moment), Roku "indecisive" (how he saw himself), Tarrlok "immoral" (his actions).

**Step 4:** `make_tests.py avatar` → 28 no_name, 28 name_swap, 28 negation, 26 conflicting, 25 generic (168 rows in total).
**Step 2.3:** `agreement.py make avatar` → 20 nameless sets, 5 per nation. 🛑 Two people who haven't seen the character list fill them in (not Esther).
**Trait check (Esther, 2026-11-23):** all 8 borderline picks **kept**. Accepted as extracted: 140 of 140 canonical traits (100%), after the 20 rejections above were made while reading the sentences.
**Still to do:** the agreement sheets (sent to Ana and Thais); the shortcut pairs.

---

## 2026-11-21 · Name slot in `sorter.py` (Q2) and shared `generic.csv` (step 2.5)
- **Name slot.** `predict(..., name=None)` (and `score_mlm`, `score_embed`, `score_nli`). With a name, every MLM template uses its named twin in `sorter.NAMED_TEMPLATES` ("Ginny Weasley, who is …, belongs to Gryffindor."); embed and NLI use "Ginny Weasley, who is …." as the person sentence. Without a name, the prompts are exactly as before, so existing results don't change.
  - **Calibration with a name:** the prior uses the named template with **both** name and traits set to "N/A". The prior removes the template's own bias but not what the name carries; using the real name in the prior would calibrate away the very effect Q2 measures.
  - 4 new tests (named templates line up with the plain ones; the name reaches the prompt; the named content-free prompt calibrates to uniform; a name changes the scores for every method). All 40 tests pass (8 fast, 32 with models).
  - The step 5 runner must pass `name=row["name"]` for canonical and name_swap rows and no name for every other type.
  - **First look (one example, not a result):** Ginny's traits without a name give Ravenclaw 0.57. With "Ginny Weasley" they give Gryffindor 0.99, and with "Draco Malfoy" Gryffindor 0.97. So the named prompt may simply push everything to Gryffindor, which step 5 has to check across all rows.
  - `sorter.py` is Esther's: **Ana tells her about this change.**
- **`data/generic.csv`** (columns `id, traits, source`): 25 vague two-trait sets, shared by every world. g01–g08 are the 8 distinct generic sets in `vote_items.csv`, word for word; g09 is the PLAN.md example; g10–g25 are new everyday words.
  - The new sets were checked against the HP leak list. **g02 "funny; kind" contains the HP leak word "kind" (Hufflepuff).** It stays (Ana, decision 1A): the panel and the live form already use it; the report flags its HP result.
  - `make_tests.py` skips a set that a world already has from its vote items, so nothing is counted twice. **HP generic: 8 → 25** (8 vote items + 17 from `generic.csv`). Every other world gets 25 (3 vote items + 22 from `generic.csv`) once it has canonical rows.

---

## 2026-11-21 · Step 4: generated test sets (`make_tests.py`)
- `make_tests.py` reads each world's canonical rows and **appends** generated rows to `data/<world>/tests.csv`. Two new columns: `origin_id` (the source row or rows) and `name_group` (name_swap only). Re-running gives an identical file; `fetch_personality.py build` now keeps these rows.
- **HP output:** 34 no_name, 34 name_swap, 34 negation, 28 conflicting, 8 generic.
  - **name_swap:** each character's traits get a name from another house (gold = the traits' house, `name_group` = the name's house). Names are spread out (33 distinct, none used more than twice).
  - **negation:** "not" before every trait. Gold is empty; the metric is how far the answer moves from `origin_id`.
  - **conflicting:** 24 generated (4 per house pair: 2–3 traits from a character of house A plus 2–3 from house B; gold `A|B`), plus the 4 HP conflicting items from `vote_items.csv`, so BERT is scored on exactly what the panel and the form saw. Pair order is normalized to `sorter.WORLDS` order (`c04-hp` was `slytherin|hufflepuff`, now `hufflepuff|slytherin`).
  - **generic:** the 8 HP generic items from `vote_items.csv`. The shared `data/generic.csv` (step 2.5, ~25 sets) doesn't exist yet; `make_tests.py` picks it up automatically once it does.
- ~~Open issue: no name slot in `sorter.py`~~ → fixed, see the entry above.

---

## 2026-11-21 · HP step 2.3: agreement sheets
- **`agreement.py`** (new, any world) builds two annotator sheets from the canonical rows: 20 trait sets with the names removed, stratified by house (HP: 5 per house), drawn with seed 42, in a different order per sheet, with a dropdown of the houses. The house descriptions are shown at the top, the same text as the form and BERT's "with descriptions" variant.
- `score` reads both filled sheets and reports each annotator's accuracy against gold (the human baseline for Table 1), raw agreement and Cohen's κ. Results go to `data/hp/agreement/results.json`. The scoring path was tested on throwaway copies with fake answers, which were then discarded.
- Annotators: **Thais and Fardin**. They haven't seen the HP character list; Ana didn't annotate because she reviewed every character with names and traits, so her answers would measure memory. Sheets sent 2026-11-21.
- ~~Waiting on their sheets~~ → returned 2026-11-23, see the entry above.

---

## 2026-11-21 · HP step 2.2: canonical characters
- **`fetch_personality.py`** (new, works for any world) reads each character's "Personality and traits" section through the Fandom API (the pages themselves return HTTP 402 to scripts) and caches it in `data/<world>/raw/`. It lists every adjective with its sentence (nltk POS tagger, `nltk==3.10.4` added to requirements), filters non-personality words and leak words, and builds `tests.csv` from hand-picked traits. It **refuses** any pick that isn't literally in the section or that leaks the label.
- Leak filter fixed for hyphenated words: "hard-working" = "hardworking", and "kind-hearted", "fair-minded", "quick-witted" contain banned words.
- **48 characters fetched → 41 rows in `tests.csv`: 33 canonical, 8 `needs_review`.**

  | House | Canonical | needs_review |
  |---|---|---|
  | Gryffindor | 10 | 0 |
  | Ravenclaw | 8 | 2 (Ollivander, Padma) |
  | Hufflepuff | **5** | 5 (Hannah, Ernie, Justin, Susan, Fat Friar) |
  | Slytherin | 10 | 1 (Regulus) |

- **Hufflepuff is thin on Fandom.** Its minor characters have short Personality sections (Susan Bones has none at all). That's a class imbalance to report and to handle with macro-F1.
- Excluded on purpose: founders and ghosts whose name contains the house (Helga Hufflepuff, Helena Ravenclaw), because the name gives the answer away.
- **Picks rejected after reading the sentence** (the tagger finds adjectives, not who they describe):
  - negated: Hermione "short-tempered", Padma "outgoing", Regulus "exemplary";
  - about someone else: Riddle "murderous" (Gaunt), Marietta "eager", Pansy "hostile", "offensive";
  - not personality: Dumbledore "flamboyant" (clothes), McGonagall "strict" ("strict orders"), Cho "romantic" (relationship), Sirius "rash" (advice), Hagrid "emotional" (caption).
- Gold labels: `characters.csv` → `gold_source` gives the book chapter or Wizarding World writing for each. Several come from Wizarding World writing rather than the books (Dumbledore, McGonagall, Hagrid, Flitwick, Lockhart, Trelawney, Quirrell, Myrtle, Ollivander, Sprout, Lucius, Bellatrix, Umbridge, Narcissa).
- **Trait check (Ana, 2026-11-21).** All 165 traits were read in context by Claude; Ana ruled on 6 borderline ones:
  - swapped: Cho "irrational" → "popular", Luna "dreamy" → "perceptive", Newt "astute" → "courteous", Riddle "compulsive" → "unpredictable";
  - kept: Cho "emotional", Pansy "anxious" and "frightened".
  - Accepted as extracted: 161 of 165 traits (97.6%).
- The `raw/` cache is committed for traceability (Fandom text, CC BY-SA).
- **More Hufflepuffs and Ravenclaws (Ana's choice).** All 330 pages in Fandom's Hufflepuff and Ravenclaw categories were scanned; 11 have a Personality section with at least 5 usable words. Only **Silvanus Kettleburn** passes the gold rule: Hufflepuff per Rowling's *Short Stories from Hogwarts*. Added as `hp-c42` (cheerful, dutiful, reckless, careful, professorial; the last two are borderline but approved).
  - Rejected: Theseus Scamander (house from a cast interview on a fan channel), Bilton Bilmes (Hogwarts Mystery), Constance Pickering (Wizards Unite), plus game-only characters (Beatrice Haywood, Mirabel Garlick, Sage Bragnam, Isidora Morganach).
  - **Final HP set: 34 canonical** (Gryffindor 10, Ravenclaw 8, Hufflepuff 6, Slytherin 10). The imbalance is accepted and goes in the report's limitations; macro-F1 weights each house equally.

---

## 2026-11-21 · HP: description wording follows the live form
- On 2026-11-18 Ana's branch (`hp-data`) had drafted HP descriptions as full sentences from the official harrypotter.com fact files. They were **never committed**, and main's rule supersedes them: descriptions must be word for word what the live form showed. Kept in `git stash` ("hp 2.1 sentence-version") in case they're needed.
- A side check on that draft found description *format* barely matters. On 6 clear HP cases, sentences vs. word lists: MLM 2/6 vs 1/6, embedding 5/6 vs 4/6, NLI 5/6 vs 5/6. So keeping the form wording costs nothing.
- Same check: MLM ranks **Gryffindor first for almost every input**, even after calibration (e.g. "patient, fair, hardworking" → Gryffindor 0.64 without descriptions), and goes near-uniform with descriptions (H ≈ 0.95–0.99). It's an early observation to confirm on the full data.
- **New: `data/hp/leak_words.csv`** (49 words). Step 2.2 drops any character trait on this list: house names, every description word, plus trait words in the Wikipedia quotes, the official fact files and the Sorting Hat song.
- **Things to know for the analysis:**
  - Two items deliberately use leak words. Clear item k01-hp ("witty, bookish, original"), the HP attention check on the form, uses "witty". Generic item g02-hp ("funny and kind") uses "kind", an official Hufflepuff word, so it isn't fully neutral in HP.
- **Owner check done (Ana, 2026-11-21).** Wording unchanged, sources strengthened:
  - Gryffindor's "bravery, daring" had only synonyms in the Wikipedia quote. It now cites the official fact file ("courage, bravery and determination") and the Sorting Hat song ("daring").
  - Hufflepuff now cites the official fact file, which has "hard work, patience, loyalty and fairness" word for word.
  - Ravenclaw and Slytherin keep Wikipedia, which matches them word for word.
- Common words on the leak list (kind, true, just, fair, humble, individual) **stay banned**: stricter, but no label leaks.

---

## 2026-11-18 · Group descriptions written (step 2.1)
**Rule.** Each `data/<world>/groups.csv` description is **word for word the one-line description the human form showed**. Humans, the simulated panel and BERT's "with descriptions" variant therefore all read the same definitions. Each row was then checked against an outside source, and the supporting text is in the new `source_quote` column. ⚠️ If anyone changed a description's wording when building the Google Form, the CSV has to be updated to match.

**How well each world is supported.**

| World | Source | Support |
|---|---|---|
| Harry Potter | Wikipedia, *Hogwarts* §Houses | ✅ Strong. Every word matches or is a synonym (courage → bravery, nerve → daring, learning → love of learning, justice → fairness). |
| Divergent | Wikipedia, *Divergent (novel)* | ✅ Strong, except Amity's "kindness", which is our addition (Wikipedia only says "peaceful"). |
| Avatar | Iroh's speech in the official live-action series (Netflix, S2E3 transcript) | 🟡 Partial. Earth (enduring), Air (freedom, detachment, peace) and Water (change, adapting) are confirmed. **Fire's "drive, ambition, passion" and Water's "community"** come from Iroh's speech in the animated episode *Bitter Work* (2006), which **couldn't be checked online** because the Avatar wiki blocks automated access. **Checked by hand and confirmed by Esther (2026-11-23).** |
| Game of Thrones | Wikipedia, *World of A Song of Ice and Fire*; Dummies, *Game of Thrones list of houses* | 🟡 Interpretive. Sources confirm Stark's "honorable devotion to duty", Lannister wealth, Greyjoy raids and rebellion, and Tyrell cleverness and scheming. "Pride", "passion, boldness, ambition" (Targaryen) and "defiance, toughness, independence" (Greyjoy) are **our reading of each house's reputation**, not quoted traits. Fardin checks them. Mottos were deliberately left out ("Fire and Blood" would be a literal fire cue). |
| Invented | Our own definitions | Control world, no outside source. |

**For the report:** HP and Divergent descriptions are sourced. GoT and part of Avatar are our paraphrase of a reputation. Say so in Data/Limitations.

**Checked in code:** all 5 files load with `sorter.load_descriptions`, and every method runs in the "with descriptions" variant for every world.

---

## 2026-11-18 · World owners assigned
- **Harry Potter → Ana**, **Divergent → Thais**, **Game of Thrones → Fardin**, **Avatar → Esther** (Esther also reviews the Avatar shortcut pairs).
- **Invented world → Esther** (approves the personas).
- Each owner works only inside their world's folder (`data/<world>/`). Owners are listed in each folder's README and in IMPLEMENTATION.md.

---

## 2026-11-18 · Short human form is live after all
**Decision.** Alongside the simulated panel, we're running a **short real form** (about 3 minutes) so the panel can be checked against real people.
- **Items (25):** the 20 generic items of `vote_items.csv` (3 per world, 8 for HP) plus 1 clear item per world as an attention check (`k01-hp`, `k01-div`, `k01-got`, `k01-ava`, `k01-inv`). Same wording as `vote_items.csv`. Conflicting items are not included.
- **Familiarity grid:** HP, Divergent, Game of Thrones, Avatar.
- **Attention rule (set before seeing any data):** drop a respondent who gets **2 or more of the 5** clear items wrong.
- **Target:** about 35 responses, so about 30 remain after the filter. 10 is the useful minimum for checking the panel.
- **Analysis plan:** humans vs. panel vs. BERT on the same items. Report a **human split-half floor**: split respondents randomly in two, compute the JSD between the halves, and repeat about 1,000 times. That gives the distance expected between humans themselves.
- Responses will be linked to a Google Sheet and exported to `data/human_votes.csv` (`source=human`).
- The full form text (settings, description, sections, attention key, id mapping) is in [forms/human_votes_form.md](forms/human_votes_form.md).

---

## 2026-11-18 · Every method runs with and without group descriptions
**Problem.** In the fill-in-the-blank method, the prompt was only "Someone who is X belongs to Veltrin." BERT has never seen "Veltrin", and nothing in the prompt says what it means, so the invented world would sit near chance **by design**. That would make the memorization control unfair: a low score there would tell us nothing.

**Decision.** Every method (MLM, embedding, NLI) runs in two variants:
- **Without descriptions:** the model sees only the group names. A correct answer can come from memory of the franchise or from the meaning of the name itself.
- **With descriptions:** each group's one-line description (from `data/<world>/groups.csv`) comes first in the prompt, or next to the name for embedding and NLI. The model can now read what each group stands for.

**What it lets us say.**
- Invented world: only the "with" variant is meaningful. That's the pure "reads the traits" score.
- Real worlds: the **gap between the variants** shows how much BERT already knew. A small gap means the descriptions add nothing beyond memory; a large gap means BERT relied on reading them.
- Humans in the form also saw one-line descriptions, so the "with" variant is the fair comparison with the human votes and the panel.

**Known side effects to report.**
- In the "with" variant, groups are listed in a fixed order (the order in `sorter.WORLDS`). Order effects are possible.
- The embedding variant divides cosine similarities by a fixed temperature (0.05) before the softmax, so entropies are comparable within a method but not across methods.

Implemented in `sorter.py` (`descriptions=` argument of `predict`). Spec in IMPLEMENTATION.md, step 3.

---

## 2026-11-18 · Pokémon GO replaced by Game of Thrones
**Decision.** Pokémon GO is out and **Game of Thrones** is in, with id `got` and houses `stark`, `lannister`, `targaryen`, `greyjoy`, `tyrell`.
**Why.** GO's team names are trait words ("valor" means courage), so a correct answer could come from word meaning alone. GO also had almost no canonical characters (3 leaders plus invented personas). GoT house names are not trait words, there are many canonical characters, and the franchise is heavily present in pre-2018 text.
**Caveat for the report.** GoT membership is decided by **birth**, not by personality. Houses still have strong documented stereotypes (their words and reputation), and that's what we test. Gold-label and exclusion rules are in `data/got/README.md`.

### What changed
- `data/pokemon/` renamed to `data/got/`, with a new README (gold label = house of birth; exclude Jon Snow, Joffrey/Tommen/Myrcella and similar).
- `sorter.WORLDS`: `pokemon` replaced by `got`.
- `data/vote_items.csv`: the 6 `*-pkm` items replaced by `*-got`.
  - Generic items: same 3 trait sets as every other world.
  - Conflicting: `honorable; cunning` (stark|lannister) and `charming; reckless` (tyrell|targaryen).
  - Clear: `always keeps their word, whatever it costs` (stark).
- `make_votes.py`:
  - GoT house vectors (from each house's words and reputation).
  - 4 new trait phrases.
  - Main-character house = **Stark** (an assumption, as for the other worlds).
  - Population familiarity for GoT = (.25, .4, .35).
  - The competitor archetype now knows GoT well instead of Pokémon GO.
  - Persona columns are now `fam_got` / `home_got`.
- `app/worlds.json` and `app/questions.json`: GoT replaces Pokémon GO. Every quiz option has a GoT key, or `null` where no house clearly fits.

### Panel re-run (seed 42)
- HP, Divergent, Avatar and invented votes are unchanged, because the random stream is consumed in the same order. Only the GoT items are new.
- Same 5 voters excluded (v14, v16, v23, v24, v25), leaving **35**.
- Mean normalized entropy: clear 0.30 · generic 0.59 · conflicting 0.72. Conflicting items: 86% of votes on the two expected houses.
- GoT items:

  | Item | Votes (of 40) |
  |---|---|
  | smart; nice | Tyrell 26 |
  | funny; kind | Tyrell 30 |
  | easygoing; polite | split, Tyrell 13 / Targaryen 11 |
  | honorable; cunning | Stark 22 / Lannister 10 |
  | charming; reckless | Targaryen 20 / Tyrell 15 |
  | always keeps their word | Stark 35 |

- Same weak spot as before: warm generic traits pile onto the one "warm" house (Tyrell here).

---

## 2026-11-18 · One folder per world, one owner per world
- Data is split into `data/hp/`, `data/divergent/`, `data/pokemon/`, `data/avatar/`, `data/invented/`. Each holds `groups.csv`, `tests.csv` (headers only for now) and a `README.md` with the owner, target size, gold-label rules and checklist.
- Paths changed from `data/<world>_groups.csv` / `data/<world>_tests.csv` to `data/<world>/groups.csv` / `data/<world>/tests.csv` (PLAN.md, IMPLEMENTATION.md, sorter.py comment).
- Owners: **Harry Potter → Ana**. The other four worlds are still to be filled in (IMPLEMENTATION.md, "Who owns which world").
- Shared files (`vote_items.csv`, `voter_personas.csv`, `simulated_votes.csv`, later `generic.csv`) stay in `data/`.

---

## 2026-11-18 · Human-votes form replaced by a simulated voter panel

**Decision.** We dropped the Google Form (`forms/human_votes_form.md`, deleted). There wasn't enough time or enough respondents to reach 30 responses. Its 39 items are kept unchanged in `data/vote_items.csv`, and `make_votes.py` builds a panel of **40 simulated voters** with distinct personalities that answer those same items.

**This is not human data.** Every row of `data/simulated_votes.csv` has `source=simulated`. In the report:
- Q3 becomes *"BERT vs. a simulated, personality-diverse panel"*, not "BERT vs. humans".
- The ChaosNLI framing stays as motivation, but we must not claim human agreement.
- Add the limitation: the panel's choices come from a trait→group mapping **we hand-set**, so the BERT-vs-panel JSD measures how far BERT is from *our model of how people reason*, not from real people.

### Files
| File | What it is |
|---|---|
| `data/vote_items.csv` | The 39 items from the old form: `item_id, world, item_type, traits, expected`. Traits are separated by `;`. These same trait sets must go into `generic.csv` and the conflicting test rows (step 2.5), so BERT is scored on identical inputs. |
| `make_votes.py` | Generator. Standard library only, seeded with `sorter.SEED` (42), so it is deterministic: re-running gives an identical file. |
| `data/voter_personas.csv` | One row per voter: archetype, Big Five (O, C, E, A, N on a 1–5 scale), familiarity per franchise (0 = not at all, 1 = a little, 2 = well), the 5 behavior parameters, and each voter's "home" group per world. |
| `data/simulated_votes.csv` | `item_id, world, voter_id, group, source`: 40 × 39 = 1,560 rows. Same schema the form would have produced, plus `source`. |

### How a simulated voter decides
1. Every trait phrase and every group is a vector over 10 dimensions (bravery, intellect, warmth, ambition, diligence, honesty, calm, spontaneity, selflessness, adaptability). Group vectors follow the one-line descriptions the form showed respondents.
2. **Trait fit** = cosine(item, group) × `beta`, where `beta` is how closely the voter reads the traits.
3. **Word order** (`first_trait_weight`): >1 means the first trait dominates (fast readers), <1 means later traits count more (careful readers).
4. **Self-projection** (`projection`): on ambiguous items, people place others where they'd place themselves. The voter's Big Five gives a personal vector, which adds `projection × ambiguity × cosine(self, group)`. It does almost nothing on clear items.
5. **Fan bias** (`fan_bias`): people who know a franchise drift toward its "main character" group, scaled by familiarity. Contrarians have a negative value. The invented world has no fan bias by construction, which mirrors the memorization control on BERT's side.
6. **Random clicking** (`noise`): the softmax is mixed with a uniform distribution at this rate.

### The 10 archetypes (40 voters)
| Archetype | n | Personality sketch | What makes them distinct |
|---|---|---|---|
| bookworm | 4 | High O and C, introverted | Reads closely (high beta), knows HP well |
| social_butterfly | 5 | High E and A | Answers fast (first-trait bias), strong projection of warmth |
| competitor | 4 | High E and C, low A | Projects ambition/bravery, plays Pokémon GO |
| newcomer | 5 | Any | Knows none of the franchises: low beta, more noise, no fan bias |
| superfan | 4 | High O | Knows everything; strongest fan bias |
| rushed_clicker | 3 | Low C | 50–70% random clicks; **designed to fail the attention check** |
| contrarian | 3 | Low A, high O | Negative fan bias: avoids the "hero" group |
| careful_worrier | 4 | High N and C | Highest beta, weights the last trait |
| free_spirit | 4 | Very high O, low C | Projects spontaneity/curiosity |
| caregiver | 4 | Very high A | Projects warmth/selflessness |

### Assumptions to check as a team
- **Main-character groups:** HP → Gryffindor, Divergent → Dauntless, Avatar → Air Nomads (each protagonist's group), Pokémon GO → Mystic (assumed most popular team; no source).
- **Trait vectors and group vectors** are hand-set in `make_votes.py` (`TRAITS`, `GROUPS`). They are our judgment. Changing them changes the panel.
- **Big Five → dimensions** mapping (`big5_to_self`) is a rough heuristic, not taken from a published instrument.

### Results of the first run (seed 42)
- **Attention check** (rule fixed before generation: drop voters with ≥ 2 of 7 clear items wrong): 5 of 40 dropped, which leaves **35**. All 3 rushed_clickers (v23–v25) as intended, plus 2 newcomers (v14, v16).
- **Mean normalized entropy of the vote split:** clear 0.30 · generic 0.58 · conflicting 0.74. This is the ordering Q3 expects from people.
- **Conflicting items:** 87% of votes land on one of the two expected groups.
- **Archetypes vote differently** (non-clear items; first number = % voting with the panel majority, second = % picking the main-character group):

  | | majority | main char. |
  |---|---|---|
  | careful_worrier | 81% | 23% |
  | bookworm | 79% | 21% |
  | caregiver | 79% | 20% |
  | superfan | 75% | 41% |
  | contrarian | 69% | 21% |
  | social_butterfly | 67% | 29% |
  | competitor | 64% | 31% |
  | free_spirit | 55% | 25% |
  | newcomer | 50% | 27% |
  | rushed_clicker | 27% | 32% |

- **Weak spots to know about:** some generic items come out near-unanimous because a single trait word dominates in our vectors. Examples: "smart and nice" → Ravenclaw 36/40, "easygoing and polite" → Air Nomads 37/40, "funny and kind" (invented) → Osmark 38/40. Real people would probably split more. If we tune the panel, document it here as a new entry, and **don't tune it after looking at BERT's results**, or the comparison becomes circular.

### What changed elsewhere
- `PLAN.md` and `IMPLEMENTATION.md`: form steps and human checkpoints replaced by the simulated panel. The objective now says "simulated panel".
- `README.md`: form link removed, generator added.

---

## 2026-11-18 · Environment
- `.venv` created with Homebrew Python **3.12.11** (3.13 isn't installed on this machine; requirements.txt was pinned on 3.13). All pinned packages installed cleanly, and `import sorter, torch, transformers, sentence_transformers, sklearn, pandas, umap` works.
- Node is **not installed**. It's only needed for step 8 (the interface).
