"""Step 4: generate the automatic test sets from each world's canonical rows.

Reads data/<world>/tests.csv, removes any rows this script generated before, and
appends freshly generated ones, so it is safe to re-run. Hand-made rows
(canonical, needs_review, shortcut) are never touched.

  .venv/bin/python make_tests.py            # every world that has canonical rows
  .venv/bin/python make_tests.py hp         # one world

Generated test types (IMPLEMENTATION.md step 4)
  no_name      canonical traits, name removed               gold = same group
  name_swap    traits of X, name of Y from another group    gold = X's group (the traits);
                                                            name_group = Y's group
  negation     "not <trait>" for every trait                gold = empty (we measure how far the
                                                            answer moves vs. origin_id)
  conflicting  2-3 traits from a group-A character plus     gold = "A|B"
               2-3 from a group-B character
  generic      vague trait sets: this world's generic items gold = empty
               in data/vote_items.csv, plus data/generic.csv (sets the world
               already has from vote_items are not repeated)
  conflicting  (vote_items) this world's conflicting items  gold = their "A|B"
               in data/vote_items.csv, so BERT is scored on exactly what the panel and the form saw

Every generated row has origin_id pointing at the row(s) it came from.
Randomness uses sorter.SEED, so the output is identical on every run.
"""
import csv
import itertools
import random
import sys
from collections import Counter
from pathlib import Path

from sorter import SEED, WORLDS

DATA = Path(__file__).resolve().parent / "data"
COLS = ["id", "test_type", "name", "traits", "gold_group", "source_url", "trait_evidence",
        "origin_id", "name_group"]
GENERATED = {"no_name", "name_swap", "negation", "conflicting", "generic"}
CONFLICTING_PER_PAIR = 4   # HP: 6 group pairs x 4 = 24 generated conflicting rows


def split(traits):
    return [t.strip() for t in traits.split(";") if t.strip()]


def join(traits):
    return "; ".join(traits)


def pair(world, gold):
    """'slytherin|hufflepuff' -> 'hufflepuff|slytherin' (sorter.WORLDS order), so a pair has one spelling."""
    if "|" not in gold:
        return gold
    return "|".join(sorted(gold.split("|"), key=WORLDS[world].index))


def negate(trait):
    return trait if trait.lower().startswith("not ") else f"not {trait}"


def generate(world, canon, rng):
    rows = []
    groups = WORLDS[world]

    def add(**kw):
        rows.append({c: kw.get(c, "") for c in COLS})

    for r in canon:
        add(id=f"{r['id']}-nn", test_type="no_name", traits=r["traits"],
            gold_group=r["gold_group"], origin_id=r["id"])

    # name_swap: every canonical row gets a name from a different group, chosen so
    # that names are reused as evenly as possible.
    pool = {g: [r for r in canon if r["gold_group"] == g] for g in groups}
    used = Counter()
    for r in canon:
        others = [o for g in groups if g != r["gold_group"] for o in pool[g]]
        least = min(used[o["id"]] for o in others)
        donor = rng.choice([o for o in others if used[o["id"]] == least])
        used[donor["id"]] += 1
        add(id=f"{r['id']}-ns", test_type="name_swap", name=donor["name"], traits=r["traits"],
            gold_group=r["gold_group"], origin_id=f"{r['id']}|{donor['id']}",
            name_group=donor["gold_group"])

    for r in canon:
        add(id=f"{r['id']}-neg", test_type="negation", traits=join(negate(t) for t in split(r["traits"])),
            origin_id=r["id"])

    k = 0
    for a, b in itertools.combinations(groups, 2):
        if not pool[a] or not pool[b]:
            continue
        for _ in range(CONFLICTING_PER_PAIR):
            ra, rb = rng.choice(pool[a]), rng.choice(pool[b])
            na, nb = rng.choice([(2, 3), (3, 2)])
            ta = rng.sample(split(ra["traits"]), na)
            tb = rng.sample(split(rb["traits"]), nb)
            mixed = ta + tb
            rng.shuffle(mixed)
            k += 1
            add(id=f"{world}-x{k:02d}", test_type="conflicting", traits=join(mixed),
                gold_group=f"{a}|{b}", origin_id=f"{ra['id']}|{rb['id']}")

    with open(DATA / "vote_items.csv") as f:
        items = [i for i in csv.DictReader(f) if i["world"] == world]
    for i in items:
        if i["item_type"] in ("generic", "conflicting"):
            add(id=f"{world}-v-{i['item_id']}", test_type=i["item_type"], traits=i["traits"],
                gold_group=pair(world, i["expected"]), source_url="data/vote_items.csv", origin_id=i["item_id"])

    # Shared generic sets; skip a set this world already has from vote_items.csv,
    # so it is counted once (under its vote item, which the panel also answered).
    shared = DATA / "generic.csv"
    seen = {i["traits"] for i in items if i["item_type"] == "generic"}
    if shared.exists():
        with open(shared) as f:
            for g in csv.DictReader(f):
                if g["traits"] in seen:
                    continue
                add(id=f"{world}-g-{g['id']}", test_type="generic", traits=g["traits"],
                    source_url="data/generic.csv", origin_id=g["id"])
    return rows


def run(world):
    path = DATA / world / "tests.csv"
    with open(path) as f:
        existing = list(csv.DictReader(f))
    kept = [r for r in existing if r["test_type"] not in GENERATED or not r.get("origin_id")]
    canon = [r for r in kept if r["test_type"] == "canonical"]
    if not canon:
        print(f"{world}: no canonical rows yet, skipped")
        return
    rows = generate(world, canon, random.Random(SEED))
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore")
        w.writeheader()
        w.writerows({c: r.get(c, "") for c in COLS} for r in kept + rows)
    counts = Counter(r["test_type"] for r in kept + rows)
    print(f"{world}: " + ", ".join(f"{t} {n}" for t, n in sorted(counts.items())))


if __name__ == "__main__":
    for w in (sys.argv[1:] or list(WORLDS)):
        if w not in WORLDS:
            sys.exit(f"unknown world {w!r}")
        run(w)
