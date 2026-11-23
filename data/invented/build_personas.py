"""Invented world: personas.csv -> canonical rows in tests.csv (owners: Ana + Esther).

The invented world has no outside source, so the personas are written by the team
under a rule fixed in advance (DATA_LOG.md, 2026-11-23):
  * 5 traits per persona: 3 synonyms of the house description ("fits") + 2 neutral
    traits that point to no house ("neutral").
  * No trait may be a house name, a description word or a word form of one
    (leak_words.csv + groups.csv, same filter as fetch_personality.py).
  * Every neutral word appears in exactly 2 different houses, so it can't give a house away.
  * Names are invented and share no word piece with a house name.

Edit personas.csv, then run from the repo root:
  .venv/bin/python data/invented/build_personas.py
  .venv/bin/python make_tests.py invented
  .venv/bin/python run_experiments.py run invented
It refuses to write tests.csv if any rule is broken. Generated rows are kept.
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from fetch_personality import leak_set, leaks  # noqa: E402
from sorter import NAMES, WORLDS  # noqa: E402

WORLD = "invented"
FOLDER = ROOT / "data" / WORLD
COLS = ["id", "test_type", "name", "traits", "gold_group", "source_url", "trait_evidence"]


def split(s):
    return [t.strip() for t in s.split(";") if t.strip()]


def check(rows):
    errors = []
    banned = leak_set(WORLD)
    neutral_houses = defaultdict(set)
    try:
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained("bert-base-uncased")
        house_pieces = {p.removeprefix("##") for n in NAMES[WORLD].values() for p in tok.tokenize(n)}
    except Exception:  # offline: skip the word-piece check, say so
        tok, house_pieces = None, set()
        print("note: tokenizer unavailable, word-piece check on names skipped")
    seen_names = set()
    for r in rows:
        name, g = r["name"], r["gold_group"]
        traits, fits, neutral = split(r["traits"]), split(r["fits"]), split(r["neutral"])
        if g not in WORLDS[WORLD]:
            errors.append(f"{name}: unknown house {g!r}")
        if len(fits) != 3 or len(neutral) != 2 or sorted(traits) != sorted(fits + neutral):
            errors.append(f"{name}: traits must be exactly the 3 fits + 2 neutral")
        for t in traits:
            if leaks(t, banned):
                errors.append(f"{name}: '{t}' is a leak word")
        for t in neutral:
            neutral_houses[t].add(g)
        if name in seen_names:
            errors.append(f"{name}: duplicate name")
        seen_names.add(name)
        if tok:
            shared = {p.removeprefix("##") for p in tok.tokenize(name)} & house_pieces
            if shared:
                errors.append(f"{name}: shares word pieces {sorted(shared)} with a house name")
    for t, hs in neutral_houses.items():
        if len(hs) < 2:
            errors.append(f"neutral '{t}' appears in only one house ({hs.pop()}): it would give that house away")
    return errors


def main():
    with open(FOLDER / "personas.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    errors = check(rows)
    if errors:
        sys.exit("Refusing to write tests.csv:\n  " + "\n  ".join(errors))
    out = [dict(id=f"inv-c{i:02d}", test_type="canonical", name=r["name"], traits=r["traits"],
                gold_group=r["gold_group"], source_url="data/invented/personas.csv",
                trait_evidence=f"written by the team: fits = {r['fits']} | neutral = {r['neutral']}")
           for i, r in enumerate(rows, 1)]
    path = FOLDER / "tests.csv"
    cols, other = COLS[:], []
    if path.exists():
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            cols += [c for c in (reader.fieldnames or []) if c not in cols]
            other = [r for r in reader if r["test_type"] not in ("canonical", "needs_review")]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, restval="")
        w.writeheader()
        w.writerows(out + other)
    by = defaultdict(int)
    for r in out:
        by[r["gold_group"]] += 1
    print(f"wrote {len(out)} canonical rows ({dict(by)}); kept {len(other)} other rows. "
          f"Now run: make_tests.py {WORLD}")


if __name__ == "__main__":
    main()
