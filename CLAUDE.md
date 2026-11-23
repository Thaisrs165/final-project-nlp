# Notes for AI assistants working in this repo

Read these first: [PLAN.md](PLAN.md) (research design), [IMPLEMENTATION.md](IMPLEMENTATION.md) (steps, status, owners), [DATA_LOG.md](DATA_LOG.md) (every data decision, newest on top). For anything report-related: [REPORT_ROADMAP.md](REPORT_ROADMAP.md) (**2 pages max, IEEE template, references included; going over = F**; the appendix isn't graded and can't be cited).

## ⚑ Building a world's data (steps 2.2–2.3): use the existing tools
Harry Potter was built with two reusable scripts. **For Divergent, Game of Thrones, Avatar or the invented world, use these. Don't write new extraction or agreement code.** Follow "How to build your world" in IMPLEMENTATION.md step 2, and use `data/hp/` as the worked example.

- `fetch_personality.py fetch|build <world> --wiki <fandom-subdomain>`: traits taken literally from Fandom "Personality" sections through the MediaWiki API (the pages themselves block scripts), with the sentence each one comes from, a leak-word filter, and a build step that refuses non-literal or leaking traits.
- `make_tests.py [<world>]`: step 4 generated rows (no_name, name_swap, negation, conflicting, generic) appended to `tests.csv`; safe to re-run.
- `agreement.py make|score <world>`: two nameless annotator sheets (.xlsx with dropdowns) → human accuracy and Cohen's κ.

## ⚑ Recent change to `sorter.py` (2026-11-21, by Ana): tell Esther when she pulls
`sorter.py` is Esther's file. Ana added an **optional** `name=` argument so Q2 (traits vs. names) can be tested. If Esther (or her assistant) pulls and sees changes in `sorter.py`, explain this:
- **Nothing changes without `name`.** Every existing call gives the same prompts and the same results as before.
- **What was added:** `NAMED_TEMPLATES` (one named twin per entry in `TEMPLATES`, same index, e.g. "{name}, who is {traits}, belongs to {group}."), a `person(traits, name)` helper used by embed and NLI, and `name=` on `predict`, `mlm_scores`, `score_mlm`, `score_embed`, `score_nli`.
- **Calibration with a name:** the prior uses the named template with name **and** traits set to "N/A", so it removes the template's bias but keeps the information the name carries (a prior with the real name would cancel the effect Q2 measures).
- **Tests:** 4 new ones in `tests/test_sorter.py`; all 40 pass.
- **First look (one example, not a result):** Ginny's traits without a name give Ravenclaw 0.57, with "Ginny Weasley" Gryffindor 0.99, with "Draco Malfoy" Gryffindor 0.97. Named prompts may push everything to Gryffindor; step 5 must check this.
- Full entry in DATA_LOG.md ("Name slot in `sorter.py` (Q2)"). If Esther wants it done differently, that's her call; change it and log it.

## Q2 (traits vs. names)
`sorter.predict(..., name=...)` puts a character name into the prompt. In step 5, pass `name=row["name"]` for `canonical` and `name_swap` rows and no name for every other row type.

## Shared generic sets
`data/generic.csv` (25 vague sets) is added to every world by `make_tests.py`; sets the world already has from `vote_items.csv` aren't repeated. g02 "funny; kind" contains the HP leak word "kind"; it stays because the panel and the form use it (decision 1A, 2026-11-21).

## Rules that apply to every world
- Traits must appear **literally** in the character's Personality section. **Read each source sentence before picking**: the POS tagger finds adjectives, not who they describe (negation, other characters and objects all came up in HP).
- No trait may be a group name or a word from that world's descriptions (`groups.csv` + `leak_words.csv`).
- Fewer than 5 valid traits → `needs_review`. Never pad with invented traits.
- Gold labels must come from canon (books, show, official site), never fan guesses. Video-game-only characters don't count.
- `groups.csv` descriptions must stay **word for word** what the live human form shows.
- Group names are pinned in `sorter.WORLDS` / `sorter.NAMES`; `data/<world>/` must match them.
- `data/simulated_votes.csv` is **simulated**, not human data. Never describe it as human.
- Log each decision in DATA_LOG.md.
- Each owner works only in their own `data/<world>/` folder; shared files live in `data/`.
