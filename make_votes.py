"""Simulated voter panel: replaces the human-votes Google Form.

We did not have the time or the respondents for the form, so this script builds
a panel of SIMULATED voters with distinct personalities and has each of them
sort the same 39 items the form would have asked (data/vote_items.csv).

THIS IS NOT HUMAN DATA. Every output row says source=simulated, and the report
must describe Q3 as "BERT vs. a simulated, personality-diverse panel".
See DATA_LOG.md for the design decisions and their limitations.

How one voter picks a group for one item
----------------------------------------
1. Every trait phrase and every group is a vector over 10 hand-set dimensions
   (bravery, intellect, warmth, ...). The group vectors come from the same
   one-line descriptions the form showed people.
2. Item vector = weighted sum of its trait vectors. "Literal" voters weight the
   first trait more; careful voters weight later traits more.
3. Trait fit for group g = cosine(item, g), multiplied by `beta`
   (how much the voter actually reads the traits).
4. Self-projection: on ambiguous items, people put others where they would
   put themselves. Each voter's Big Five gives a personal vector, and we add
   `projection * ambiguity * cosine(self, g)`.
5. Fan bias: people who know a franchise well drift toward its "main character"
   group (`fan_bias * familiarity / 2`). Contrarians have a negative fan bias.
   The invented world has no fan bias, by construction.
6. Softmax, then mix with a uniform distribution at rate `noise`
   (random clicking), then sample one group.

Run:  python make_votes.py
"""
import csv
import math
import random
from collections import Counter, defaultdict

from sorter import SEED, WORLDS

DIMS = ["bravery", "intellect", "warmth", "ambition", "diligence",
        "honesty", "calm", "spontaneity", "selflessness", "adaptability"]

# ---- Trait phrases -> dimensions (hand-set; every phrase in vote_items.csv) --
TRAITS = {
    "smart": {"intellect": .8},
    "nice": {"warmth": .5},
    "funny": {"warmth": .3, "spontaneity": .3},
    "kind": {"warmth": .8},
    "easygoing": {"calm": .5, "spontaneity": .2},
    "polite": {"warmth": .3, "calm": .3},
    "quiet": {"calm": .5, "intellect": .2},
    "friendly": {"warmth": .6},
    "creative": {"intellect": .4, "spontaneity": .5},
    "talkative": {"honesty": .2, "spontaneity": .3, "warmth": .2},
    "sensible": {"intellect": .4, "calm": .3, "diligence": .2},
    "cheerful": {"warmth": .5, "spontaneity": .2},
    "a good listener": {"warmth": .5, "calm": .3},
    "loves music": {"spontaneity": .3, "warmth": .2},
    "confident": {"bravery": .5, "ambition": .3},
    "caring": {"warmth": .8},
    "brave": {"bravery": 1},
    "ambitious": {"ambition": 1},
    "curious": {"intellect": .6, "spontaneity": .5},
    "loyal": {"diligence": .7, "warmth": .3},
    "daring": {"bravery": .9, "spontaneity": .2},
    "studious": {"intellect": .9, "diligence": .3},
    "cunning": {"ambition": .7, "intellect": .3},
    "witty": {"intellect": .8, "spontaneity": .1},
    "bookish": {"intellect": .9},
    "original": {"intellect": .5, "spontaneity": .5},
    "patient": {"calm": .7, "diligence": .4},
    "fair": {"honesty": .5, "warmth": .3, "diligence": .3},
    "hardworking": {"diligence": 1},
    "shrewd": {"ambition": .6, "intellect": .4},
    "power-hungry": {"ambition": 1},
    "proud": {"ambition": .7, "bravery": .2},
    "selfless": {"selflessness": 1, "warmth": .3},
    "honest": {"honesty": 1},
    "intelligent": {"intellect": 1},
    "always tells the truth, even when it hurts": {"honesty": 1, "bravery": .2},
    "honorable": {"honesty": .8, "diligence": .5, "selflessness": .2},
    "charming": {"warmth": .6, "adaptability": .4},
    "reckless": {"bravery": .6, "spontaneity": .7},
    "always keeps their word, whatever it costs": {"honesty": .9, "diligence": .5},
    "adaptable": {"adaptability": 1},
    "stubborn": {"diligence": .8},
    "free-spirited": {"spontaneity": 1},
    "never gives up": {"diligence": 1},
    "can endure anything": {"diligence": .8, "bravery": .3},
    "never rushes": {"calm": .8},
    "loves doing things on a whim": {"spontaneity": 1},
    "generous with friends": {"warmth": .9},
    "hates to lose": {"ambition": .9},
    "watches carefully for a long time before acting": {"calm": .6, "intellect": .5},
}

# ---- Groups -> dimensions (from the one-line descriptions shown in the form) -
GROUPS = {
    "hp": {
        "gryffindor": {"bravery": 1},
        "ravenclaw": {"intellect": 1, "spontaneity": .2},
        "hufflepuff": {"diligence": .8, "warmth": .6, "honesty": .3},
        "slytherin": {"ambition": 1, "intellect": .2},
    },
    "divergent": {
        "abnegation": {"selflessness": 1, "warmth": .3},
        "amity": {"warmth": .8, "calm": .6},
        "candor": {"honesty": 1},
        "dauntless": {"bravery": 1},
        "erudite": {"intellect": 1},
    },
    "got": {  # from each house's words and reputation (see data/got/README.md)
        "stark": {"honesty": .8, "diligence": .6, "selflessness": .3, "bravery": .3},
        "lannister": {"ambition": .9, "intellect": .5},
        "targaryen": {"bravery": .6, "ambition": .5, "spontaneity": .5},
        "greyjoy": {"bravery": .6, "ambition": .3, "warmth": -.4, "adaptability": .3},
        "tyrell": {"warmth": .6, "intellect": .5, "adaptability": .5},
    },
    "avatar": {
        "fire": {"ambition": .8, "bravery": .4},
        "water": {"adaptability": 1, "warmth": .5},
        "earth": {"diligence": 1},
        "air": {"spontaneity": .7, "calm": .6},
    },
    "invented": {
        "veltrin": {"calm": .8, "intellect": .5, "diligence": .3},
        "osmark": {"warmth": 1},
        "calwen": {"spontaneity": .8, "intellect": .4},
        "durrask": {"ambition": .8, "diligence": .6},
    },
}

# "Main character" group a fan drifts toward. ASSUMPTION, see DATA_LOG.md.
SALIENT = {"hp": "gryffindor", "divergent": "dauntless", "got": "stark",
           "avatar": "air", "invented": None}
FRANCHISES = ["hp", "divergent", "got", "avatar"]

# ---- Archetypes -------------------------------------------------------------
# big5 ranges are (low, high) on a 1-5 scale; fam = P(not at all, a little, well)
POP_FAM = {"hp": (.1, .4, .5), "divergent": (.5, .35, .15),
           "got": (.25, .4, .35), "avatar": (.4, .35, .25)}
ANY = (1.5, 4.5)
ARCHETYPES = [
    dict(name="bookworm", n=4, desc="Introverted reader; reads every word, knows HP well",
         O=(4, 5), C=(4, 5), E=(1, 2.5), A=(3, 4), N=(2, 4),
         fam={**POP_FAM, "hp": (0, .2, .8)},
         beta=(7, 9), noise=(.01, .03), first=(1, 1), proj=(.5, 1), fan=(.3, .6)),
    dict(name="social_butterfly", n=5, desc="Outgoing and warm; answers fast, sees the best in people",
         O=(3, 4), C=(2, 4), E=(4, 5), A=(4, 5), N=(2, 3), fam=POP_FAM,
         beta=(4, 6), noise=(.04, .07), first=(1.2, 1.4), proj=(1.5, 2.5), fan=(.4, .6)),
    dict(name="competitor", n=4, desc="Athlete and gamer; values winning, loves power struggles in Game of Thrones",
         O=(2, 3.5), C=(4, 5), E=(4, 5), A=(1.5, 3), N=(1.5, 3),
         fam={**POP_FAM, "got": (0, .2, .8)},
         beta=(5, 7), noise=(.02, .04), first=(1, 1.1), proj=(1.5, 2), fan=(.7, 1)),
    dict(name="newcomer", n=5, desc="Knows none of the franchises; relies on the one-line descriptions",
         O=ANY, C=ANY, E=ANY, A=ANY, N=ANY,
         fam={f: (.8, .2, 0) for f in FRANCHISES},
         beta=(2, 3.5), noise=(.06, .1), first=(1.3, 1.5), proj=(.8, 1.2), fan=(0, 0)),
    dict(name="superfan", n=4, desc="Knows every franchise in depth; leans on canon and main characters",
         O=(4, 5), C=(2.5, 4), E=(3, 4), A=(3, 4), N=(2, 3.5),
         fam={f: (0, 0, 1) for f in FRANCHISES},
         beta=(6, 8), noise=(.01, .02), first=(1, 1), proj=(.3, .7), fan=(1.2, 1.8)),
    dict(name="rushed_clicker", n=3, desc="Inattentive; clicks almost at random (should fail the attention check)",
         O=ANY, C=(1, 2), E=ANY, A=ANY, N=ANY, fam=POP_FAM,
         beta=(1, 2), noise=(.5, .7), first=(1.5, 2), proj=(0, .5), fan=(0, .3)),
    dict(name="contrarian", n=3, desc="Avoids the obvious pick; distrusts the 'hero' group",
         O=(4, 5), C=(2, 3.5), E=(2.5, 4), A=(1, 2), N=(2.5, 4), fam=POP_FAM,
         beta=(5, 7), noise=(.02, .04), first=(1, 1), proj=(1, 1.5), fan=(-1.5, -1)),
    dict(name="careful_worrier", n=4, desc="Anxious and conscientious; reads to the end, weighs the last trait",
         O=(2.5, 4), C=(4, 5), E=(1.5, 3), A=(3.5, 4.5), N=(4, 5), fam=POP_FAM,
         beta=(7, 9), noise=(.01, .02), first=(.7, .9), proj=(.8, 1.2), fan=(.3, .5)),
    dict(name="free_spirit", n=4, desc="Artsy and spontaneous; low structure, projects curiosity",
         O=(4.5, 5), C=(1, 2), E=(3, 4.5), A=(3, 4), N=(2.5, 3.5), fam=POP_FAM,
         beta=(4, 6), noise=(.05, .07), first=(1.1, 1.3), proj=(1.8, 2.5), fan=(.2, .5)),
    dict(name="caregiver", n=4, desc="Gentle and selfless; projects warmth onto vague people",
         O=(3, 4), C=(3.5, 4.5), E=(2, 3.5), A=(4.5, 5), N=(2.5, 3.5), fam=POP_FAM,
         beta=(5, 7), noise=(.02, .04), first=(1, 1), proj=(1.8, 2.5), fan=(.3, .6)),
]


# ---- Vector helpers ---------------------------------------------------------
def vec(d):
    return [d.get(k, 0.0) for k in DIMS]


def unit(v):
    n = math.sqrt(sum(x * x for x in v))
    return [x / n for x in v] if n else v


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def big5_to_self(b):
    """Map a Big Five profile to the 10 dimensions (centered at 3 = average)."""
    O, C, E, A, N = (b[k] - 3 for k in "OCEAN")
    return unit([
        .3 * E - .3 * N,           # bravery
        .4 * O,                    # intellect
        .4 * A + .1 * E,           # warmth
        .2 * C - .3 * A + .1 * E,  # ambition
        .4 * C,                    # diligence
        .15 * C,                   # honesty
        -.3 * N - .2 * E,          # calm
        .3 * O - .3 * C,           # spontaneity
        .3 * A,                    # selflessness
        .2 * O - .1 * N,           # adaptability
    ])


GROUP_U = {w: {g: unit(vec(d)) for g, d in gs.items()} for w, gs in GROUPS.items()}
assert {w: list(g) for w, g in GROUP_U.items()}.keys() == WORLDS.keys()
for w in WORLDS:
    assert set(GROUP_U[w]) == set(WORLDS[w]), w


def softmax(xs):
    m = max(xs)
    e = [math.exp(x - m) for x in xs]
    s = sum(e)
    return [x / s for x in e]


def entropy(counts, k):
    n = sum(counts.values())
    h = -sum(c / n * math.log(c / n) for c in counts.values() if c)
    return h / math.log(k)


# ---- Build the panel --------------------------------------------------------
def make_panel(rng):
    panel, i = [], 1
    for a in ARCHETYPES:
        for _ in range(a["n"]):
            u = lambda r: round(rng.uniform(*r), 2)
            b = {k: round(rng.uniform(*a[k]), 1) for k in "OCEAN"}
            fam = {f: rng.choices([0, 1, 2], weights=a["fam"][f])[0] for f in FRANCHISES}
            v = dict(voter_id=f"v{i:02d}", archetype=a["name"], description=a["desc"], **b,
                     **{f"fam_{f}": fam[f] for f in FRANCHISES},
                     beta=u(a["beta"]), noise=u(a["noise"]), first_trait_weight=u(a["first"]),
                     projection=u(a["proj"]), fan_bias=u(a["fan"]))
            self_u = big5_to_self(b)
            v["_self"] = self_u
            for w in WORLDS:
                v[f"home_{w}"] = max(GROUP_U[w], key=lambda g: dot(self_u, GROUP_U[w][g]))
            panel.append(v)
            i += 1
    return panel


def vote_probs(voter, world, traits):
    groups = WORLDS[world]
    weights = [voter["first_trait_weight"] if j == 0 else 1.0 for j in range(len(traits))]
    item = unit([sum(w * x for w, x in zip(weights, col))
                 for col in zip(*(vec(TRAITS[t]) for t in traits))])
    fit = [dot(item, GROUP_U[world][g]) for g in groups]
    top, second = sorted(fit, reverse=True)[:2]
    ambiguity = 1 - (top - second) / top if top > 0 else 1.0
    fam = voter[f"fam_{world}"] if world in FRANCHISES else 1
    logits = []
    for g, f in zip(groups, fit):
        x = voter["beta"] * f
        x += voter["projection"] * ambiguity * dot(voter["_self"], GROUP_U[world][g])
        if g == SALIENT[world]:
            x += voter["fan_bias"] * fam / 2
        logits.append(x)
    p = softmax(logits)
    eps = voter["noise"]
    return groups, [(1 - eps) * x + eps / len(groups) for x in p]


def main():
    rng = random.Random(SEED)
    with open("data/vote_items.csv") as f:
        items = list(csv.DictReader(f))
    for it in items:
        it["traits"] = [t.strip() for t in it["traits"].split(";")]
        missing = [t for t in it["traits"] if t not in TRAITS]
        assert not missing, (it["item_id"], missing)

    panel = make_panel(rng)
    votes = []
    for v in panel:
        for it in items:
            groups, p = vote_probs(v, it["world"], it["traits"])
            g = rng.choices(groups, weights=p)[0]
            votes.append(dict(item_id=it["item_id"], world=it["world"], voter_id=v["voter_id"],
                              group=g, source="simulated"))

    cols = [k for k in panel[0] if not k.startswith("_")]
    with open("data/voter_personas.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(panel)
    with open("data/simulated_votes.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["item_id", "world", "voter_id", "group", "source"])
        w.writeheader()
        w.writerows(votes)

    # ---- Summary (copied into DATA_LOG.md) ----------------------------------
    by_item = defaultdict(Counter)
    for r in votes:
        by_item[r["item_id"]][r["group"]] += 1
    clear = {it["item_id"]: it["expected"] for it in items if it["item_type"] == "clear"}
    wrong = Counter(r["voter_id"] for r in votes
                    if r["item_id"] in clear and r["group"] != clear[r["item_id"]])
    excluded = sorted(v for v, n in wrong.items() if n >= 2)
    arch = {v["voter_id"]: v["archetype"] for v in panel}

    print(f"voters: {len(panel)}   items: {len(items)}   votes: {len(votes)}")
    print(f"excluded by the pre-registered rule (>=2 of 7 clear items wrong): "
          f"{len(excluded)} -> {[f'{v} ({arch[v]})' for v in excluded]}")
    print("\nmean normalized entropy of the vote split, by item type:")
    for t in ["clear", "conflicting", "generic"]:
        hs = [entropy(by_item[it["item_id"]], len(WORLDS[it["world"]]))
              for it in items if it["item_type"] == t]
        print(f"  {t:12s} {sum(hs) / len(hs):.3f}  (n={len(hs)})")
    conf = [it for it in items if it["item_type"] == "conflicting"]
    mass = [sum(by_item[it["item_id"]][g] for g in it["expected"].split("|")) / len(panel)
            for it in conf]
    print(f"conflicting items: mean share of votes on the two expected groups = "
          f"{sum(mass) / len(mass):.2f}")
    print("\nper item (votes):")
    for it in items:
        c = by_item[it["item_id"]]
        h = entropy(c, len(WORLDS[it["world"]]))
        dist = ", ".join(f"{g} {c[g]}" for g in WORLDS[it["world"]])
        print(f"  {it['item_id']:8s} H={h:.2f}  {dist}")
    print("\nhome group (self-projection target) counts, HP:",
          dict(Counter(v["home_hp"] for v in panel)))

    # Are the personas distinct? Per archetype, on the 32 non-clear items:
    # how often they vote with the panel majority, and how often they pick
    # the franchise's "main character" group.
    majority = {i: c.most_common(1)[0][0] for i, c in by_item.items()}
    ambiguous = {it["item_id"] for it in items if it["item_type"] != "clear"}
    salient_items = {it["item_id"]: SALIENT[it["world"]] for it in items
                     if it["item_id"] in ambiguous and SALIENT[it["world"]]}
    print("\nper archetype on non-clear items: % with majority | % main-character group")
    for a in ARCHETYPES:
        rs = [r for r in votes if arch[r["voter_id"]] == a["name"] and r["item_id"] in ambiguous]
        maj = sum(r["group"] == majority[r["item_id"]] for r in rs) / len(rs)
        sal_rs = [r for r in rs if r["item_id"] in salient_items]
        sal = sum(r["group"] == salient_items[r["item_id"]] for r in sal_rs) / len(sal_rs)
        print(f"  {a['name']:16s} {maj:5.0%} | {sal:5.0%}")


if __name__ == "__main__":
    main()
