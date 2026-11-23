"""Divergent experiments (Member 2, owner: Thais).

Question: when the traits point to two (or three) factions, does BERT pick one or
split its probability? And does it map the HP houses onto the Divergent factions
consistently?

Four tests (PLAN.md, member brief):
  canonical       characters from the books (traits filled in characters.csv)
  conflicting     traits from two factions mixed, in both orders
  divergent_mode  traits from three factions (Tris's aptitude result is one of them),
                  plus the canonical Divergent characters vs. the others
  cross-franchise every input is scored with BOTH label sets (factions and houses)

Three commands, run from the repo root:
  .venv/bin/python experiments/divergent.py build     # writes data/divergent/tests.csv
  .venv/bin/python experiments/divergent.py run       # scores every row (cached)
  .venv/bin/python experiments/divergent.py analyze   # tables, figures, SUMMARY.md
  .venv/bin/python experiments/divergent.py all       # the three in order

All method code lives in sorter.py. This file only builds inputs and measures.
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import sorter  # noqa: E402

WORLD = "divergent"
DIV = sorter.WORLDS["divergent"]
HP = sorter.WORLDS["hp"]
LABEL_WORLDS = (WORLD, "hp")          # every input is scored with both label sets
DATA = ROOT / "data" / WORLD
TESTS = DATA / "tests.csv"
CHARS = DATA / "characters.csv"
VOTE_ITEMS = ROOT / "data" / "vote_items.csv"
SIM_VOTES = ROOT / "data" / "simulated_votes.csv"
HUMAN_VOTES = ROOT / "data" / "human_votes.csv"   # optional, once the form is exported
OUT = ROOT / "results" / WORLD
PRED = OUT / "predictions.csv"

TEST_COLS = ["id", "test_type", "name", "traits", "gold_group", "source_url",
             "trait_evidence", "origin_id"]
PRED_COLS = ["world", "id", "origin_id", "test_type", "method", "template", "descriptions",
             "traits", "gold", "pred", "probs_json", "raw_probs_json", "entropy", "raw_entropy"]
OWN_TYPES = ("canonical", "clear", "conflicting", "divergent_mode", "generic")
TYPE_ORDER = ["clear", "canonical", "conflicting", "divergent_mode", "generic"]

# ---------------------------------------------------------------------------
# Pre-registered inputs. Written 2026-11-18, BEFORE any model output was seen.
# Changing them after looking at results makes the analysis circular: log any
# change in DATA_LOG.md.
# ---------------------------------------------------------------------------
# For each faction: (direct word, synonym 1, synonym 2).
#   direct   = the adjective of the faction's value (same stem as groups.csv:
#              intentionally leaks the label, this is the "easy" variant)
#   synonyms = same meaning, no shared stem with the description (leak-checked)
WORDS = {
    "abnegation": ("selfless", "humble", "modest"),
    "amity": ("peaceful", "gentle", "forgiving"),
    "candor": ("honest", "truthful", "blunt"),
    "dauntless": ("brave", "fearless", "daring"),
    "erudite": ("intelligent", "studious", "analytical"),
}
# The house we expect each faction to map to. Candor has no clear HP counterpart.
EXPECTED_HOUSE = {"dauntless": "gryffindor", "erudite": "ravenclaw",
                  "abnegation": "hufflepuff", "amity": "hufflepuff", "candor": None}
TRIS_APTITUDE = ("abnegation", "dauntless", "erudite")  # Wikipedia, Divergent (novel)
TRIS_SOURCE = "https://en.wikipedia.org/wiki/Divergent_(novel)"
OVERCONFIDENT = 0.8   # a conflicting input answered with max prob above this = failure
N_BOOT = 1000


# =============================================================================
# Build: data/divergent/tests.csv
# =============================================================================
def _stems(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z]+", text.lower()) if len(w) >= 4]


def leaks(trait: str, world: str = WORLD, descriptions: dict | None = None) -> list[str]:
    """Words of `trait` that share a stem (first 5 letters) with a group name or a
    word of that world's descriptions. Empty list = no label leak."""
    descriptions = descriptions if descriptions is not None else sorter.load_descriptions(world)
    banned = set()
    for g in sorter.WORLDS[world]:
        banned.update(_stems(sorter.NAMES[world][g]))
        banned.update(_stems(descriptions[g]))
    roots = set()
    for b in banned:
        for suf in ("ness", "ence", "ance", "ity", "ery", "ful", "ty", "y"):
            if b.endswith(suf) and len(b) - len(suf) >= 4:
                roots.add(b[: -len(suf)])
                break
    hits = []
    for w in _stems(trait):
        same_start = any(w[:min(5, len(w), len(b))] == b[:min(5, len(w), len(b))] for b in banned)
        if same_start or any(w.startswith(r) for r in roots):
            hits.append(w)
    return hits


def _row(id_, test_type, traits, gold, evidence, origin="", name="", source=""):
    return {"id": id_, "test_type": test_type, "name": name, "traits": "; ".join(traits),
            "gold_group": gold, "source_url": source, "trait_evidence": evidence,
            "origin_id": origin}


def build_probes(vote_items_path: Path = VOTE_ITEMS) -> list[dict]:
    """Hand-designed inputs. No character, so no source needed: they come from WORDS."""
    ab = {g: g[:3] for g in DIV}
    rows = []
    # clear: two words of ONE faction (the unambiguous baseline, same length as conflicting)
    for g in DIV:
        d, s1, s2 = WORDS[g]
        rows.append(_row(f"clr-{ab[g]}-direct", "clear", [d, s1], g, "WORDS (direct + synonym)"))
        rows.append(_row(f"clr-{ab[g]}-syn", "clear", [s1, s2], g, "WORDS (synonyms only)"))
    # conflicting: one word from A + one from B, in both orders (gold lists the order)
    for a, b in itertools.combinations(DIV, 2):
        for variant, k in (("direct", 0), ("syn", 1)):
            base = f"cnf-{ab[a]}-{ab[b]}-{variant}"
            rows.append(_row(f"{base}-ab", "conflicting", [WORDS[a][k], WORDS[b][k]],
                             f"{a}|{b}", f"WORDS ({variant})"))
            rows.append(_row(f"{base}-ba", "conflicting", [WORDS[b][k], WORDS[a][k]],
                             f"{b}|{a}", f"WORDS ({variant}), reversed order", origin=f"{base}-ab"))
    # divergent_mode: one word from each of three factions
    for trio in itertools.combinations(DIV, 3):
        for variant, k in (("direct", 0), ("syn", 1)):
            tris = trio == TRIS_APTITUDE
            rows.append(_row(f"div-{'-'.join(ab[g] for g in trio)}-{variant}", "divergent_mode",
                             [WORDS[g][k] for g in trio], "|".join(trio),
                             ("Tris's aptitude result: Abnegation, Dauntless and Erudite; "
                              if tris else "") + f"WORDS ({variant})",
                             source=TRIS_SOURCE if tris else ""))
    # generic + the clear attention item, copied from the vote items (same ids, so
    # they line up with the simulated panel and the human form)
    if vote_items_path.exists():
        with open(vote_items_path, newline="") as f:
            for r in csv.DictReader(f):
                if r["world"] != WORLD or r["item_type"] == "conflicting":
                    continue  # conflicting vote items are already in the rows above
                rows.append(_row(r["item_id"], r["item_type"], sorter.parse_traits(r["traits"]),
                                 r["expected"], "data/vote_items.csv"))
    return rows


def _slug(name: str) -> str:
    return re.sub(r"[^a-z]+", "-", name.lower()).strip("-")


def build_canonical(chars_path: Path = CHARS, descriptions: dict | None = None):
    """Canonical rows from characters.csv. Returns (rows, problems).

    A character becomes a test row only when its `traits` cell has exactly 5 traits,
    none of them leaks the label, `trait_evidence` is filled and the faction is checked.
    Everything else is reported in `problems` and left out (never padded).
    """
    rows, problems = [], []
    with open(chars_path, newline="") as f:
        for c in csv.DictReader(f):
            name = c["name"].strip()
            traits = sorter.parse_traits(c.get("traits", ""))
            if not traits:
                problems.append(f"{name}: no traits yet ({c['status']})")
                continue
            if c["status"].strip() != "ok":
                problems.append(f"{name}: status is {c['status'].strip()!r}, not 'ok'")
                continue
            if len(traits) != 5:
                problems.append(f"{name}: {len(traits)} traits, need exactly 5 (mark needs_review)")
                continue
            if not c.get("trait_evidence", "").strip():
                problems.append(f"{name}: trait_evidence is empty")
                continue
            bad = {t: leaks(t, WORLD, descriptions) for t in traits}
            bad = {t: w for t, w in bad.items() if w}
            if bad:
                problems.append(f"{name}: label leak {bad}")
                continue
            if c["gold_group"] not in DIV:
                problems.append(f"{name}: unknown gold_group {c['gold_group']!r}")
                continue
            rows.append(_row(f"can-{_slug(name)}", "canonical", traits, c["gold_group"],
                             c["trait_evidence"].strip(), name=name, source=c["source_url"]))
    return rows, problems


def build(verbose=True):
    canonical, problems = build_canonical()
    probes = build_probes()
    kept = []  # rows of other test types (e.g. step 4's make_tests.py) are left untouched
    if TESTS.exists():
        with open(TESTS, newline="") as f:
            kept = [r for r in csv.DictReader(f) if r["test_type"] not in OWN_TYPES]
    rows = canonical + probes + kept
    ids = [r["id"] for r in rows]
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        raise ValueError(f"duplicate ids in tests.csv: {sorted(dup)}")
    with open(TESTS, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=TEST_COLS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in TEST_COLS})
    if verbose:
        counts = {}
        for r in rows:
            counts[r["test_type"]] = counts.get(r["test_type"], 0) + 1
        print(f"wrote {TESTS.relative_to(ROOT)}: {counts}")
        if problems:
            print(f"{len(problems)} characters left out:")
            for p in problems:
                print("  -", p)
    return rows, problems


# =============================================================================
# Run: results/divergent/predictions.csv (cached, re-runs skip finished rows)
# =============================================================================
def load_tests() -> list[dict]:
    with open(TESTS, newline="") as f:
        return list(csv.DictReader(f))


def _key(id_, world, method, template, desc, traits):
    return (id_, world, method, str(template), str(desc), traits)


def run(methods=sorter.METHODS, limit: int | None = None):
    OUT.mkdir(parents=True, exist_ok=True)
    rows = load_tests()[:limit] if limit else load_tests()
    done = set()
    if PRED.exists():
        with open(PRED, newline="") as f:
            for r in csv.DictReader(f):
                done.add(_key(r["id"], r["world"], r["method"], r["template"],
                              r["descriptions"], r["traits"]))
    descs = {w: sorter.load_descriptions(w) for w in LABEL_WORLDS}
    jobs = []
    for r in rows:
        for world in LABEL_WORLDS:
            for method in methods:
                for template in (range(len(sorter.TEMPLATES)) if method == "mlm" else [0]):
                    for desc in (False, True):
                        if _key(r["id"], world, method, template, desc, r["traits"]) not in done:
                            jobs.append((r, world, method, template, desc))
    print(f"{len(jobs)} predictions to compute ({len(done)} cached)")
    new = not PRED.exists()
    with open(PRED, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=PRED_COLS)
        if new:
            w.writeheader()
        for n, (r, world, method, template, desc) in enumerate(jobs, 1):
            out = sorter.predict(r["traits"], world, method, template=template,
                                 descriptions=descs[world] if desc else None)
            p, raw = out["probs"], out["raw_probs"]
            w.writerow({
                "world": world, "id": r["id"], "origin_id": r.get("origin_id", ""),
                "test_type": r["test_type"], "method": method, "template": template,
                "descriptions": desc, "traits": r["traits"],
                "gold": r["gold_group"] if world == WORLD else "",
                "pred": sorter.top(p), "probs_json": json.dumps(p),
                "raw_probs_json": json.dumps(raw),
                "entropy": round(sorter.entropy(p), 6), "raw_entropy": round(sorter.entropy(raw), 6),
            })
            if n % 100 == 0:
                f.flush()
                print(f"  {n}/{len(jobs)}")
    print(f"done -> {PRED.relative_to(ROOT)}")


# =============================================================================
# Metrics (pure functions, unit-tested in tests/test_divergent.py)
# =============================================================================
def split_metrics(probs: dict[str, float], gold: str) -> dict:
    """For an input built from k groups (gold = 'a|b' or 'a|b|c', in trait order)."""
    gs = gold.split("|")
    k = len(gs)
    ranked = sorted(probs, key=probs.get, reverse=True)
    mass = sum(probs[g] for g in gs)
    inside = [probs[g] for g in gs]
    return {
        "mass": mass,                                  # chance = k / n_groups
        "topk_is_gold": set(ranked[:k]) == set(gs),    # the k mixed groups ARE the top k
        "top_in_gold": ranked[0] in gs,
        "balance": min(inside) / max(inside) if max(inside) > 0 else 0.0,  # 1 = even split
        "first_minus_second": probs[gs[0]] - probs[gs[1]],   # order effect (trait order)
        "overconfident": max(probs.values()) > OVERCONFIDENT,
    }


def correspondence(pairs: list[tuple[dict, dict]], rows=DIV, cols=HP):
    """Soft faction->house table: C[f][h] = sum_x P(f|x) P(h|x) / sum_x P(f|x).
    Each row sums to 1 and reads 'inputs that look like faction f go to house h'."""
    C = {f: {h: 0.0 for h in cols} for f in rows}
    mass = {f: 0.0 for f in rows}
    for pf, ph in pairs:
        for f in rows:
            mass[f] += pf[f]
            for h in cols:
                C[f][h] += pf[f] * ph[h]
    return {f: {h: (C[f][h] / mass[f] if mass[f] else float("nan")) for h in cols} for f in rows}


def jsd(p: dict[str, float], q: dict[str, float]) -> float:
    """Jensen-Shannon divergence, base 2 (0 = identical, 1 = disjoint)."""
    keys = set(p) | set(q)
    m = {k: (p.get(k, 0) + q.get(k, 0)) / 2 for k in keys}

    def kl(a):
        return sum(a.get(k, 0) * math.log2(a.get(k, 0) / m[k]) for k in keys if a.get(k, 0) > 0)
    return (kl(p) + kl(q)) / 2


def holm(pvals: list[float]) -> list[float]:
    """Holm-Bonferroni adjusted p-values (same order as the input)."""
    idx = sorted(range(len(pvals)), key=lambda i: pvals[i])
    adj, run_max = [1.0] * len(pvals), 0.0
    for rank, i in enumerate(idx):
        run_max = max(run_max, min(1.0, (len(pvals) - rank) * pvals[i]))
        adj[i] = run_max
    return adj


def bootstrap_ci(values, stat=None, n=N_BOOT, seed=sorter.SEED):
    import numpy as np
    stat = stat or np.mean
    v = np.asarray([x for x in values if x == x], dtype=float)
    if len(v) == 0:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    s = [stat(v[rng.integers(0, len(v), len(v))]) for _ in range(n)]
    return tuple(float(x) for x in np.percentile(s, [2.5, 97.5]))


def panel_distribution(world: str, votes_path: Path, items_path: Path = VOTE_ITEMS,
                       max_wrong: int = 2) -> dict[str, dict[str, float]]:
    """Vote split per item after the pre-registered attention rule
    (drop voters with >= max_wrong clear items wrong, counted over ALL worlds)."""
    with open(items_path, newline="") as f:
        items = {r["item_id"]: r for r in csv.DictReader(f)}
    with open(votes_path, newline="") as f:
        votes = list(csv.DictReader(f))
    wrong = {}
    for v in votes:
        it = items.get(v["item_id"])
        if it and it["item_type"] == "clear":
            wrong[v["voter_id"]] = wrong.get(v["voter_id"], 0) + (v["group"] != it["expected"])
    keep = {v for v, n in wrong.items() if n < max_wrong} if wrong else None
    dist = {}
    for v in votes:
        if v["world"] != world or (keep is not None and v["voter_id"] not in keep):
            continue
        d = dist.setdefault(v["item_id"], {g: 0 for g in sorter.WORLDS[world]})
        d[v["group"]] += 1
    return {i: {g: c / sum(d.values()) for g, c in d.items()} for i, d in dist.items()}


# =============================================================================
# Analyze
# =============================================================================
def _load_predictions():
    import pandas as pd
    df = pd.read_csv(PRED, keep_default_na=False)
    df["descriptions"] = df["descriptions"].astype(str) == "True"
    df["probs"] = df["probs_json"].map(json.loads)
    df["variant"] = df["descriptions"].map({False: "names only", True: "with descriptions"})
    return df


def _mean_probs(series):
    keys = series.iloc[0].keys()
    return {k: sum(p[k] for p in series) / len(series) for k in keys}


def _fmt(x, nd=2):
    if isinstance(x, bool):
        return "yes" if x else "no"
    if isinstance(x, float):
        return "" if x != x else f"{x:.{nd}f}"
    return str(x)


def md_table(df, nd=2) -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(map(str, cols)) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join(_fmt(r[c], nd) for c in cols) + " |")
    return "\n".join(lines)


def _p(x):
    return "" if x != x else (f"{x:.3f}" if x >= 0.001 else "<0.001")


def analyze():
    import numpy as np
    import pandas as pd
    from scipy.stats import mannwhitneyu, wilcoxon

    df = _load_predictions()
    tests = {r["id"]: r for r in load_tests()}
    chars = {}
    if CHARS.exists():
        with open(CHARS, newline="") as f:
            chars = {f"can-{_slug(r['name'])}": r for r in csv.DictReader(f)}
    OUT.mkdir(parents=True, exist_ok=True)
    keys = ["method", "variant"]
    div = df[df.world == WORLD].copy()
    report = ["# Divergent: results", "",
              f"Generated by `experiments/divergent.py analyze` from `{PRED.relative_to(ROOT)}`. "
              "Entropies are normalized (0 = certain, 1 = uniform) and are compared **within a "
              "method only**. MLM numbers are the mean over the 3 prompt templates; `tmpl_sd` is "
              "the spread of that mean across templates (Jiang et al. 2020). CIs: bootstrap 95%, "
              f"{N_BOOT} resamples over items.", ""]
    report += ["Row counts per test type: " + ", ".join(
        f"{t} {sum(1 for r in tests.values() if r['test_type'] == t)}" for t in TYPE_ORDER), ""]

    # ---- T0: sanity. Read this table first. ---------------------------------
    t0 = []
    for (w, m, v), g in df.groupby(["world"] + keys):
        counts = g.pred.value_counts(normalize=True)
        row = {"labels": w, "method": m, "variant": v, "most_common_pred": counts.index[0],
               "share_most_common": float(counts.iloc[0])}
        if w == WORLD:
            c = g[g.test_type == "clear"]
            per_item = (c.pred == c.gold).groupby(c.id).mean()
            lo, hi = bootstrap_ci(per_item)
            row.update({"clear_accuracy": float(per_item.mean()), "ci_low": lo, "ci_high": hi})
        t0.append(row)
    t0 = pd.DataFrame(t0)
    t0.to_csv(OUT / "t0_sanity.csv", index=False)
    report += ["## 0. Sanity: does the method get the EASY inputs, and does it collapse?", "",
               f"`clear_accuracy`: top-1 accuracy on the 11 single-faction inputs (chance = "
               f"{1 / len(DIV):.2f}); per template for MLM, then averaged. `share_most_common`: "
               "how often the single most frequent answer is given across ALL inputs. A value "
               "near 1 means the method collapses onto one label, and then entropy and split "
               "numbers below describe that label's prior, not the traits.", "",
               md_table(t0), ""]

    # ---- T1: entropy by test type -------------------------------------------
    item = div.groupby(keys + ["test_type", "id"], as_index=False)["entropy"].mean()
    per_t = div.groupby(keys + ["test_type", "template"])["entropy"].mean()
    t1 = []
    for (m, v, t), g in item.groupby(keys + ["test_type"]):
        lo, hi = bootstrap_ci(g.entropy)
        sd = per_t.loc[(m, v, t)].std(ddof=0) if m == "mlm" else float("nan")
        t1.append({"method": m, "variant": v, "test_type": t, "n": len(g),
                   "entropy": g.entropy.mean(), "ci_low": lo, "ci_high": hi, "tmpl_sd": sd})
    t1 = pd.DataFrame(t1)
    t1["order"] = t1.test_type.map({t: i for i, t in enumerate(TYPE_ORDER)})
    t1 = t1.sort_values(keys + ["order"]).drop(columns="order")
    t1.to_csv(OUT / "t1_entropy_by_type.csv", index=False)

    # Mann-Whitney: is entropy higher for mixed inputs than for clear ones?
    tests_rows = []
    for (m, v), g in item.groupby(keys):
        clear = g[g.test_type == "clear"].entropy
        for other in ("conflicting", "divergent_mode", "generic"):
            x = g[g.test_type == other].entropy
            if len(x) and len(clear):
                u = mannwhitneyu(x, clear, alternative="greater")
                tests_rows.append({"method": m, "variant": v, "comparison": f"{other} > clear",
                                   "diff": x.mean() - clear.mean(), "U": float(u.statistic),
                                   "p": float(u.pvalue)})
    tt = pd.DataFrame(tests_rows)
    if len(tt):
        tt["p_holm"] = holm(tt.p.tolist())
        tt["p"] = tt.p.map(_p)
        tt["p_holm"] = tt.p_holm.map(_p)
        tt.to_csv(OUT / "t1b_entropy_tests.csv", index=False)

    report += ["## 1. Entropy by input type", "",
               "Expected for a model that reads the traits: clear < conflicting < divergent_mode. "
               "Generic inputs should also be high.", "",
               md_table(t1), "", "One-sided Mann-Whitney U, Holm-corrected over the whole table:",
               "", md_table(tt) if len(tt) else "_no clear rows_", ""]

    # ---- T2: conflicting ----------------------------------------------------
    cnf = div[div.test_type == "conflicting"].copy()
    met = cnf.apply(lambda r: split_metrics(r.probs, r.gold), axis=1, result_type="expand")
    cnf = pd.concat([cnf, met], axis=1)
    cols = ["mass", "topk_is_gold", "top_in_gold", "balance", "overconfident", "first_minus_second"]
    cnf[cols] = cnf[cols].astype(float)
    ci = cnf.groupby(keys + ["id", "origin_id", "gold"], as_index=False)[cols].mean()
    t2 = []
    for (m, v), g in ci.groupby(keys):
        # order effect per pair: mean of P(first listed) - P(second listed) over both
        # orders. With no order effect, (PA-PB) is the same in both rows and this is 0.
        ab = g[g.origin_id == ""].set_index("id")
        ba = g[g.origin_id != ""].set_index("origin_id")
        d = (ab.first_minus_second + ba.first_minus_second).dropna() / 2
        try:
            p_order = float(wilcoxon(d).pvalue) if (d != 0).any() else 1.0
        except ValueError:
            p_order = float("nan")
        lo, hi = bootstrap_ci(g["mass"])
        t2.append({"method": m, "variant": v, "n": len(g),
                   "mass_on_AB": g["mass"].mean(), "ci_low": lo, "ci_high": hi,
                   "top2_is_AB": g.topk_is_gold.mean(), "top1_in_AB": g.top_in_gold.mean(),
                   "balance": g.balance.mean(), "overconfident": g.overconfident.mean(),
                   "first_listed_bonus": d.mean(), "p_order": _p(p_order)})
    t2 = pd.DataFrame(t2)
    t2.to_csv(OUT / "t2_conflicting.csv", index=False)
    n_div = len(DIV)
    report += ["## 2. Conflicting inputs: pick one or split?", "",
               f"Chance levels: mass on A+B = {2 / n_div:.2f}, top-2 = {{A, B}} = "
               f"{1 / math.comb(n_div, 2):.2f}, top-1 in {{A, B}} = {2 / n_div:.2f}. "
               "`balance` = min/max of P(A), P(B) (1 = even split). "
               f"`overconfident` = share with max prob > {OVERCONFIDENT} (a failure on a mixed "
               "input). `first_listed_bonus` = how much more probability the faction gets when "
               "its trait comes first (Wilcoxon signed-rank over the pairs).", "",
               md_table(t2), ""]

    # ---- T3: divergent mode -------------------------------------------------
    dm = div[div.test_type == "divergent_mode"].copy()
    met = dm.apply(lambda r: split_metrics(r.probs, r.gold), axis=1, result_type="expand")
    dm = pd.concat([dm, met], axis=1)
    dm[["mass", "topk_is_gold", "overconfident"]] = dm[["mass", "topk_is_gold", "overconfident"]].astype(float)
    di = dm.groupby(keys + ["id"], as_index=False)[["entropy", "mass", "topk_is_gold", "overconfident"]].mean()
    t3 = di.groupby(keys, as_index=False).agg(n=("id", "size"), entropy=("entropy", "mean"),
                                              mass_on_ABC=("mass", "mean"),
                                              top3_is_ABC=("topk_is_gold", "mean"),
                                              overconfident=("overconfident", "mean"))
    tris = di[di.id.str.startswith("div-abn-dau-eru")].pivot_table(
        index=keys, columns="id", values=["entropy", "mass"]).reset_index()
    tris.columns = [" ".join(c).strip() if isinstance(c, tuple) else c for c in tris.columns]
    t3.to_csv(OUT / "t3_divergent_mode.csv", index=False)
    tris.to_csv(OUT / "t3b_tris_aptitude.csv", index=False)
    report += ["## 3. Divergent mode (three factions at once)", "",
               f"Chance: mass on A+B+C = {3 / n_div:.2f}, top-3 = {{A, B, C}} = "
               f"{1 / math.comb(n_div, 3):.2f}.", "", md_table(t3), "",
               "Tris's aptitude result (selfless + brave + intelligent, and the synonym version):",
               "", md_table(tris), ""]

    can = item[item.test_type == "canonical"].copy()
    if len(can):
        can["divergent"] = can.id.map(lambda i: chars.get(i, {}).get("divergent", "no") == "yes")
        rows = []
        for (m, v), g in can.groupby(keys):
            a, b = g[g.divergent].entropy, g[~g.divergent].entropy
            p = float(mannwhitneyu(a, b, alternative="greater").pvalue) if len(a) and len(b) else float("nan")
            rows.append({"method": m, "variant": v, "n_divergent": len(a), "entropy_divergent": a.mean(),
                         "n_other": len(b), "entropy_other": b.mean(), "p": _p(p)})
        t3c = pd.DataFrame(rows)
        t3c.to_csv(OUT / "t3c_canonical_divergent.csv", index=False)
        report += ["Canonical characters: Divergent vs. the others (one-sided Mann-Whitney; "
                   "small n, read as a case study):", "", md_table(t3c), ""]

    # ---- T4: canonical accuracy --------------------------------------------
    cd = div[div.test_type == "canonical"]
    if len(cd):
        from sklearn.metrics import f1_score
        golds = [r["gold_group"] for r in tests.values() if r["test_type"] == "canonical"]
        majority = max(set(golds), key=golds.count)
        rows = []
        for (m, v, tpl), g in cd.groupby(keys + ["template"]):
            correct = (g.pred == g.gold).astype(float)
            lo, hi = bootstrap_ci(correct)
            rows.append({"method": m, "variant": v, "template": tpl, "n": len(g),
                         "accuracy": correct.mean(), "ci_low": lo, "ci_high": hi,
                         "macro_f1": f1_score(g.gold, g.pred, labels=DIV, average="macro",
                                              zero_division=0)})
        t4 = pd.DataFrame(rows).groupby(keys, as_index=False).agg(
            n=("n", "first"), accuracy=("accuracy", "mean"), ci_low=("ci_low", "mean"),
            ci_high=("ci_high", "mean"), macro_f1=("macro_f1", "mean"), tmpl_sd=("accuracy", "std"))
        t4.to_csv(OUT / "t4_canonical_accuracy.csv", index=False)
        report += ["## 4. Canonical characters: accuracy", "",
                   f"Chance = {1 / n_div:.2f}. Majority baseline (always '{majority}') = "
                   f"{golds.count(majority) / len(golds):.2f}: the books are mostly about Dauntless, "
                   "so accuracy must be read against this, and macro-F1 is the fairer number.", "",
                   md_table(t4), ""]
    else:
        report += ["## 4. Canonical characters: accuracy", "",
                   "_No canonical rows yet: fill `traits` and `trait_evidence` in "
                   "`data/divergent/characters.csv`, then run `build`, `run`, `analyze` again._", ""]

    # ---- T5: cross-franchise correspondence ---------------------------------
    # template-averaged probabilities: avg[(method, variant)][id][world] = {group: p}
    avg = {}
    for (w, m, v, i), g in df.groupby(["world"] + keys + ["id"]):
        avg.setdefault((m, v), {}).setdefault(i, {})[w] = _mean_probs(g.probs)
    t5, mats = [], {}
    for (m, v), byid in sorted(avg.items()):
        both = {i: p for i, p in byid.items() if WORLD in p and "hp" in p}
        ids = list(both)
        pairs = [(both[i][WORLD], both[i]["hp"]) for i in ids]
        C = correspondence(pairs)
        mats[(m, v)] = C
        top_f = [sorter.top(pf) for pf, _ in pairs]
        top_h = [sorter.top(ph) for _, ph in pairs]
        hits = [float(EXPECTED_HOUSE[f] == h) for f, h in zip(top_f, top_h) if EXPECTED_HOUSE[f]]
        brave = [float(sorter.top(pf) == "dauntless" and sorter.top(ph) == "gryffindor")
                 for i, (pf, ph) in zip(ids, pairs)
                 if any(w in tests.get(i, {}).get("traits", "").lower() for w in WORDS["dauntless"])]
        lo, hi = bootstrap_ci(hits)
        # permutation baseline: shuffle the house answers across inputs. This keeps how
        # often each label is predicted, so a method that always says "Dauntless" and
        # "Gryffindor" gets a high baseline too, and only real pairing beats it.
        rng = np.random.default_rng(sorter.SEED)
        perm = []
        for _ in range(N_BOOT):
            sh = rng.permutation(top_h)
            perm.append(np.mean([EXPECTED_HOUSE[f] == h for f, h in zip(top_f, sh)
                                 if EXPECTED_HOUSE[f]]) if hits else float("nan"))
        perm = np.asarray(perm)
        obs = float(np.mean(hits)) if hits else float("nan")
        t5.append({"method": m, "variant": v, "n_inputs": len(pairs), "n_scored": len(hits),
                   "consistent": obs, "ci_low": lo, "ci_high": hi,
                   "perm_baseline": float(np.mean(perm)),
                   "p_perm": _p(float((np.sum(perm >= obs) + 1) / (len(perm) + 1))),
                   "brave_inputs": len(brave),
                   "brave_to_dauntless_and_gryffindor": float(np.mean(brave)) if brave else float("nan")})
        pd.DataFrame(C).T.to_csv(OUT / f"t5_correspondence_{m}_{v.replace(' ', '_')}.csv")
    t5 = pd.DataFrame(t5)
    t5.to_csv(OUT / "t5_cross_franchise.csv", index=False)
    report += ["## 5. Cross-franchise: do factions map onto houses?", "",
               "Every input is scored with the faction labels AND the house labels. `consistent` = "
               "share of inputs whose top house is the one we pre-registered for its top faction "
               "(Dauntless->Gryffindor, Erudite->Ravenclaw, Abnegation/Amity->Hufflepuff; Candor "
               "inputs are left out). Compare it with `perm_baseline` (house answers shuffled "
               "across inputs, 1000 times), not with 0.25: a method that collapses onto one "
               "faction and one house gets a high score without any real mapping. "
               "`p_perm` = share of shuffles at least as consistent. Tables of P(house | faction) are in "
               "`t5_correspondence_*.csv` and the figure `fig_correspondence.png`.", "",
               md_table(t5), ""]
    for (m, v), C in mats.items():
        if m in ("mlm", "nli") and v == "with descriptions":
            tab = pd.DataFrame(C).T.reset_index().rename(columns={"index": "faction"})
            report += [f"P(house | faction), {m}, {v}:", "", md_table(tab), ""]

    # ---- T6: vs. simulated panel (and humans, when exported) ----------------
    refs = {"simulated panel": panel_distribution(WORLD, SIM_VOTES)}
    if HUMAN_VOTES.exists():
        refs["humans"] = panel_distribution(WORLD, HUMAN_VOTES)
    by_traits = {}
    for i, r in tests.items():
        by_traits.setdefault(r["traits"].replace(" ", "").lower(), i)
    with open(VOTE_ITEMS, newline="") as f:
        vitems = [r for r in csv.DictReader(f) if r["world"] == WORLD]
    t6 = []
    for (m, v), byid in sorted(avg.items()):
        g = {i: p[WORLD] for i, p in byid.items() if WORLD in p}
        for it in vitems:
            rid = it["item_id"] if it["item_id"] in g else by_traits.get(
                "; ".join(sorter.parse_traits(it["traits"])).replace(" ", "").lower())
            if rid not in g:
                continue
            for ref, dist in refs.items():
                if it["item_id"] in dist:
                    t6.append({"method": m, "variant": v, "reference": ref, "item": it["item_id"],
                               "type": it["item_type"], "traits": it["traits"],
                               "jsd": jsd(g[rid], dist[it["item_id"]]),
                               "bert_top": sorter.top(g[rid]), "ref_top": sorter.top(dist[it["item_id"]]),
                               "bert_entropy": sorter.entropy(g[rid]),
                               "ref_entropy": sorter.entropy(dist[it["item_id"]])})
    t6 = pd.DataFrame(t6)
    if len(t6):
        t6.to_csv(OUT / "t6_vs_panel.csv", index=False)
        s6 = t6.groupby(keys + ["reference", "type"], as_index=False).agg(
            n=("item", "size"), jsd=("jsd", "mean"), bert_entropy=("bert_entropy", "mean"),
            ref_entropy=("ref_entropy", "mean"))
        report += ["## 6. BERT vs. the simulated panel on the Divergent vote items", "",
                   "JSD base 2 (0 = same distribution). The panel is **simulated, not human** "
                   "(DATA_LOG.md); real form votes are added automatically once "
                   "`data/human_votes.csv` exists. Per-item rows: `t6_vs_panel.csv`.", "",
                   md_table(s6), ""]

    # ---- Figures ------------------------------------------------------------
    try:
        _figures(t1, mats)
        report += ["## Figures", "", "![entropy](fig_entropy.png)", "",
                   "![correspondence](fig_correspondence.png)", ""]
    except Exception as e:  # figures are a convenience, never block the tables
        print(f"figures skipped: {e}")
    (OUT / "SUMMARY.md").write_text("\n".join(report))
    print(f"wrote {OUT.relative_to(ROOT)}/SUMMARY.md and the t*.csv tables")


# Palette: dataviz reference instance (categorical slots 1-2, blue sequential ramp).
SERIES = {"names only": "#2a78d6", "with descriptions": "#eb6834"}
SEQ = ["#cde2fb", "#9ec5f4", "#5598e7", "#256abf", "#0d366b"]
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def _figures(t1, mats):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap

    plt.rcParams.update({"font.size": 8, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                         "xtick.color": INK2, "ytick.color": INK2, "text.color": INK})
    methods = [m for m in sorter.METHODS if m in set(t1.method)]
    types = [t for t in TYPE_ORDER if t in set(t1.test_type)]
    fig, axes = plt.subplots(1, len(methods), figsize=(1.9 * len(methods) + 0.6, 2.4),
                             sharey=True, squeeze=False)
    for ax, m in zip(axes[0], methods):
        for k, (variant, color) in enumerate(SERIES.items()):
            g = t1[(t1.method == m) & (t1.variant == variant)].set_index("test_type").reindex(types)
            x = [i + (k - 0.5) * 0.25 for i in range(len(types))]
            ax.errorbar(x, g.entropy, yerr=[g.entropy - g.ci_low, g.ci_high - g.entropy],
                        fmt="o", ms=4, color=color, ecolor=color, elinewidth=1.5, capsize=0,
                        label=variant)
        ax.set_title(m, fontsize=9)
        ax.set_xticks(range(len(types)))
        short = {"clear": "clear", "canonical": "canon.", "conflicting": "2 mixed",
                 "divergent_mode": "3 mixed", "generic": "generic"}
        ax.set_xticklabels([short[t] for t in types], fontsize=7)
        ax.set_ylim(0, 1.02)
        ax.grid(axis="y", color=GRID, lw=0.6)
        ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    axes[0][0].set_ylabel("normalized entropy")
    axes[0][0].legend(frameon=False, fontsize=7, loc="lower right")
    fig.tight_layout()
    fig.savefig(OUT / "fig_entropy.png", dpi=200)
    plt.close(fig)

    cmap = LinearSegmentedColormap.from_list("seq", SEQ)
    show = [(m, "with descriptions") for m in methods if (m, "with descriptions") in mats]
    fig, axes = plt.subplots(1, len(show), figsize=(2.3 * len(show), 2.4), squeeze=False)
    for ax, key in zip(axes[0], show):
        C = mats[key]
        M = [[C[f][h] for h in HP] for f in DIV]
        ax.imshow(M, cmap=cmap, vmin=0, vmax=1)
        for i, row in enumerate(M):
            for j, val in enumerate(row):
                ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=6.5,
                        color="#ffffff" if val > 0.55 else INK)
        ax.set_xticks(range(len(HP)))
        ax.set_xticklabels([sorter.NAMES["hp"][h][:5] for h in HP], fontsize=7)
        ax.set_yticks(range(len(DIV)))
        ax.set_yticklabels([sorter.NAMES[WORLD][f] for f in DIV], fontsize=7)
        ax.set_title(f"{key[0]} (with descr.)", fontsize=8)
        for s in ax.spines.values():
            s.set_visible(False)
    fig.suptitle("P(house | faction)", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "fig_correspondence.png", dpi=200)
    plt.close(fig)


# =============================================================================
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["build", "run", "analyze", "all"])
    ap.add_argument("--methods", nargs="+", default=list(sorter.METHODS), choices=sorter.METHODS)
    ap.add_argument("--limit", type=int, help="only the first N test rows (smoke test)")
    a = ap.parse_args(argv)
    if a.command in ("build", "all"):
        build()
    if a.command in ("run", "all"):
        run(a.methods, a.limit)
    if a.command in ("analyze", "all"):
        analyze()


if __name__ == "__main__":
    main()
