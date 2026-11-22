# Notes for AI assistants working in this repo

Read these first: [PLAN.md](PLAN.md) (research design), [IMPLEMENTATION.md](IMPLEMENTATION.md) (steps, status, owners), [DATA_LOG.md](DATA_LOG.md) (every data decision, newest on top).

## ⚑ Building a world's data (steps 2.2–2.3): use the existing tools
Harry Potter was built with two reusable scripts. **For Divergent, Game of Thrones, Avatar or the invented world, use these. Don't write new extraction or agreement code.** Follow "How to build your world" in IMPLEMENTATION.md step 2, and use `data/hp/` as the worked example.

- `fetch_personality.py fetch|build <world> --wiki <fandom-subdomain>`: traits taken literally from Fandom "Personality" sections through the MediaWiki API (the pages themselves block scripts), with the sentence each one comes from, a leak-word filter, and a build step that refuses non-literal or leaking traits.
- `make_tests.py [<world>]`: step 4 generated rows (no_name, name_swap, negation, conflicting, generic) appended to `tests.csv`; safe to re-run.
- `agreement.py make|score <world>`: two nameless annotator sheets (.xlsx with dropdowns) → human accuracy and Cohen's κ.

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
