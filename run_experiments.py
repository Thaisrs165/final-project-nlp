"""Step 5: the ONE shared experiment runner. Every world, every method, same settings.

Reads data/<world>/tests.csv for every world, scores each row with sorter.predict
and appends to results/all.csv. Re-running only computes what's missing (cached),
so it's safe to run again after a world adds rows.

  .venv/bin/python run_experiments.py run                 # every world, every method
  .venv/bin/python run_experiments.py run hp avatar       # some worlds
  .venv/bin/python run_experiments.py run hp --methods mlm --limit 20   # quick try
  .venv/bin/python run_experiments.py occlusion           # Q2b: leave-one-trait-out, canonical rows
  .venv/bin/python run_experiments.py summary             # Q1/Q2 accuracy table + 95% CIs
  .venv/bin/python run_experiments.py probe               # fix C: small-data sanity check (trained!)

What each row is scored with (IMPLEMENTATION.md step 5)
  methods       sorter.METHODS (mlm, embed, bert-mean, nli); models pinned in sorter.py
  templates     all 3 for mlm (we report the mean and spread), template 0 for the others
  descriptions  both variants: without (group names only) and with groups.csv descriptions
  name          the character name for `canonical` and `name_swap` rows, so Q2 can compare
                name kept / removed (no_name) / swapped. No name for every other type.
  skipped       `needs_review` rows (fewer than 5 traits)

Output columns are the same as Thais's results/divergent/predictions.csv, plus
`name` (the name given to the model, empty if none) and `name_group` (the house
the swapped-in name belongs to). Randomness: none; BERT is frozen and inference is
deterministic. Never write a second runner: add options here instead.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

import sorter

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results"
PRED = OUT / "all.csv"
SUMMARY = OUT / "summary_q1q2.csv"
OCCL = OUT / "occlusion.csv"
PROBE = OUT / "probe.csv"
OCCL_COLS = ["world", "id", "descriptions", "traits", "gold", "pred_full", "trait", "position",
             "delta", "flips_to"]
COLS = ["world", "id", "origin_id", "test_type", "method", "template", "descriptions",
        "name", "name_group", "traits", "gold", "pred", "probs_json", "raw_probs_json",
        "entropy", "raw_entropy"]
NAMED_TYPES = {"canonical", "name_swap"}
SKIP_TYPES = {"needs_review"}
N_BOOT = 2000


def load_tests(world):
    path = ROOT / "data" / world / "tests.csv"
    if not path.exists():
        return []
    with open(path, newline="") as f:
        return [r for r in csv.DictReader(f) if r["test_type"] not in SKIP_TYPES and r["traits"].strip()]


def key(world, id_, method, template, desc, name, traits):
    return (world, id_, method, str(template), str(desc), name, traits)


def jobs_for(world, rows, methods):
    for r in rows:
        name = r.get("name", "").strip() if r["test_type"] in NAMED_TYPES else ""
        for method in methods:
            for template in (range(len(sorter.TEMPLATES)) if method in sorter.MLM_VARIANTS else [0]):
                for desc in (False, True):
                    yield r, method, template, desc, name


def prune(path, worlds, has_name=True):
    """Drop cached rows that no longer match tests.csv (a row's traits or name changed, or
    the row was removed / became needs_review), so nothing is counted twice. Only the
    given worlds are touched; returns how many rows were dropped."""
    if not path.exists():
        return 0
    current = {}
    for w in worlds:
        for r in load_tests(w):
            name = r.get("name", "").strip() if r["test_type"] in NAMED_TYPES else ""
            current[(w, r["id"])] = (r["traits"], name)
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        cols, rows = reader.fieldnames, list(reader)
    keep = [r for r in rows if r["world"] not in worlds or (
        (r["world"], r["id"]) in current
        and current[(r["world"], r["id"])][0] == r["traits"]
        and (not has_name or current[(r["world"], r["id"])][1] == r["name"]))]
    if len(keep) < len(rows):
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(keep)
        print(f"{path.name}: dropped {len(rows) - len(keep)} outdated rows")
    return len(rows) - len(keep)


def run(worlds, methods, limit=None):
    OUT.mkdir(exist_ok=True)
    if not limit:
        prune(PRED, [w for w in worlds if load_tests(w)])
    done = set()
    if PRED.exists():
        with open(PRED, newline="") as f:
            done = {key(r["world"], r["id"], r["method"], r["template"], r["descriptions"],
                        r["name"], r["traits"]) for r in csv.DictReader(f)}
    todo = []
    for w in worlds:
        rows = load_tests(w)[:limit] if limit else load_tests(w)
        if not rows:
            print(f"{w}: no rows yet, skipped")
            continue
        n0 = len(todo)
        todo += [(w, *j) for j in jobs_for(w, rows, methods)
                 if key(w, j[0]["id"], j[1], j[2], j[3], j[4], j[0]["traits"]) not in done]
        print(f"{w}: {len(rows)} rows, {len(todo) - n0} predictions to compute")
    print(f"total {len(todo)} to compute ({len(done)} cached)")
    descs = {}
    new = not PRED.exists()
    with open(PRED, "a", newline="") as f:
        out = csv.DictWriter(f, fieldnames=COLS)
        if new:
            out.writeheader()
        for n, (w, r, method, template, desc, name) in enumerate(todo, 1):
            if desc and w not in descs:
                descs[w] = sorter.load_descriptions(w)
            res = sorter.predict(r["traits"], w, method, template=template,
                                 descriptions=descs[w] if desc else None, name=name or None)
            p, raw = res["probs"], res["raw_probs"]
            out.writerow({
                "world": w, "id": r["id"], "origin_id": r.get("origin_id", ""),
                "test_type": r["test_type"], "method": method, "template": template,
                "descriptions": desc, "name": name, "name_group": r.get("name_group", ""),
                "traits": r["traits"], "gold": r["gold_group"], "pred": sorter.top(p),
                "probs_json": json.dumps(p), "raw_probs_json": json.dumps(raw),
                "entropy": round(sorter.entropy(p), 6), "raw_entropy": round(sorter.entropy(raw), 6),
            })
            if n % 200 == 0:
                f.flush()
                print(f"  {n}/{len(todo)}")
    print(f"done -> {PRED.relative_to(ROOT)}")


# ---------------------------------------------------------------- occlusion
def occlusion(worlds):
    """Leave-one-trait-out (Li et al. 2016) on canonical rows: MLM, template 0, no name
    (we want the traits' own effect), with and without descriptions. Cached like `run`."""
    OUT.mkdir(exist_ok=True)
    prune(OCCL, [w for w in worlds if load_tests(w)], has_name=False)
    done = set()
    if OCCL.exists():
        with open(OCCL, newline="") as f:
            done = {(r["world"], r["id"], r["descriptions"], r["traits"]) for r in csv.DictReader(f)}
    new = not OCCL.exists()
    with open(OCCL, "a", newline="") as f:
        out = csv.DictWriter(f, fieldnames=OCCL_COLS)
        if new:
            out.writeheader()
        for w in worlds:
            rows = [r for r in load_tests(w) if r["test_type"] == "canonical"]
            descs = sorter.load_descriptions(w) if rows else None
            for r in rows:
                for desc in (False, True):
                    if (w, r["id"], str(desc), r["traits"]) in done:
                        continue
                    kw = {"descriptions": descs if desc else None}
                    full = sorter.top(sorter.predict(r["traits"], w, "mlm", **kw)["probs"])
                    for pos, o in enumerate(sorter.occlusion(r["traits"], w, "mlm", **kw)):
                        out.writerow({"world": w, "id": r["id"], "descriptions": desc,
                                      "traits": r["traits"], "gold": r["gold_group"], "pred_full": full,
                                      "trait": o["trait"], "position": pos, "delta": round(o["delta"], 6),
                                      "flips_to": o["flips_to"] or ""})
            print(f"{w}: {len(rows)} canonical rows done")
    print(f"done -> {OCCL.relative_to(ROOT)}")


# -------------------------------------------------------------------- probe
def probe(worlds):
    """Fix C (DATA_LOG 2026-11-23): logistic regression on sentence vectors of
    "Someone who is <traits>." (no names), leave-one-character-out per world, canonical
    rows only. A SMALL-DATA SANITY CHECK, not zero-shot: report it separately."""
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import LeaveOneOut, cross_val_predict
    out = []
    for w in worlds:
        rows = [r for r in load_tests(w) if r["test_type"] == "canonical"]
        y = [r["gold_group"] for r in rows]
        if len(rows) < 10 or len(set(y)) < 2:
            print(f"{w}: {len(rows)} canonical rows, too few for a probe, skipped")
            continue
        texts = [sorter.person(r["traits"]) for r in rows]
        for feats in ("bert-mean", "minilm"):
            if feats == "bert-mean":
                X = sorter._bert_mean(texts).numpy()
            else:
                X = sorter._sbert().encode(texts, convert_to_numpy=True)
            clf = LogisticRegression(C=1.0, max_iter=1000)
            pred = cross_val_predict(clf, np.asarray(X), y, cv=LeaveOneOut())
            hits = [int(p == g) for p, g in zip(pred, y)]
            lo, hi = bootstrap_ci(hits)
            majority = max(y.count(g) for g in set(y)) / len(y)
            out.append({"world": w, "features": feats, "n": len(y), "accuracy": round(sum(hits) / len(y), 3),
                        "ci95": f"{lo:.2f}-{hi:.2f}", "majority_baseline": round(majority, 3),
                        "chance": round(1 / len(sorter.WORLDS[w]), 3)})
            print(f"{w:9s} {feats:9s} n={len(y)} acc={out[-1]['accuracy']} ({out[-1]['ci95']}) "
                  f"majority={out[-1]['majority_baseline']}")
    with open(PROBE, "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=["world", "features", "n", "accuracy", "ci95",
                                           "majority_baseline", "chance"])
        wr.writeheader()
        wr.writerows(out)
    print(f"-> {PROBE.relative_to(ROOT)}  (small-data sanity check: trained, NOT zero-shot)")


# ------------------------------------------------------------------ summary
def bootstrap_ci(hits, n=N_BOOT, seed=sorter.SEED):
    rng = random.Random(seed)
    k = len(hits)
    means = sorted(sum(rng.choice(hits) for _ in range(k)) / k for _ in range(n))
    return means[int(0.025 * n)], means[int(0.975 * n) - 1]


def mcnemar_p(a, b):
    """Exact two-sided McNemar test on paired 0/1 outcomes (a vs b)."""
    from math import comb
    n01 = sum(1 for x, y in zip(a, b) if x and not y)
    n10 = sum(1 for x, y in zip(a, b) if y and not x)
    n = n01 + n10
    if n == 0:
        return 1.0
    k = min(n01, n10)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


def summary():
    """Q1/Q2 table: accuracy (95% CI) per world x method x descriptions on canonical,
    no_name and name_swap rows; MLM is averaged over the 3 templates per row first.
    For name_swap also: how often the answer follows the swapped NAME's group, and
    McNemar no_name vs. name_swap (paired by character)."""
    with open(PRED, newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["test_type"] in ("canonical", "no_name", "name_swap")]
    # average probabilities over templates -> one prediction per (row, method, desc)
    agg = defaultdict(lambda: defaultdict(float))
    meta = {}
    for r in rows:
        k = (r["world"], r["method"], r["descriptions"], r["test_type"], r["id"])
        for g, p in json.loads(r["probs_json"]).items():
            agg[k][g] += p
        meta[k] = r
    cells = defaultdict(dict)
    for k, probs in agg.items():
        r = meta[k]
        pred = max(probs, key=probs.get)
        char = r["id"].split("-ns")[0].split("-nn")[0]
        cells[k[:3]].setdefault(k[3], {})[char] = (pred == r["gold"], pred == r["name_group"])
    out = []
    for (world, method, desc), by_type in sorted(cells.items()):
        row = {"world": world, "method": method, "descriptions": desc,
               "chance": round(1 / len(sorter.WORLDS[world]), 3)}
        for t in ("canonical", "no_name", "name_swap"):
            d = by_type.get(t, {})
            hits = [int(v[0]) for v in d.values()]
            row[f"n_{t}"] = len(hits)
            if hits:
                lo, hi = bootstrap_ci(hits)
                row[f"acc_{t}"] = round(sum(hits) / len(hits), 3)
                row[f"ci_{t}"] = f"{lo:.2f}-{hi:.2f}"
        swap, nn = by_type.get("name_swap", {}), by_type.get("no_name", {})
        if swap:
            row["follows_name"] = round(sum(v[1] for v in swap.values()) / len(swap), 3)
        both = sorted(set(swap) & set(nn))
        if both:
            row["mcnemar_p_noname_vs_swap"] = round(mcnemar_p([nn[c][0] for c in both],
                                                                [swap[c][0] for c in both]), 4)
        out.append(row)
    cols = sorted({c for r in out for c in r}, key=lambda c: (
        ["world", "method", "descriptions", "chance"].index(c) if c in ("world", "method", "descriptions", "chance") else 9, c))
    with open(SUMMARY, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(out)
    print(f"{'world':9s} {'method':9s} {'desc':5s} {'canon':>6s} {'no_name':>8s} {'swap':>6s} {'follows':>8s} {'p':>7s}")
    for r in out:
        print(f"{r['world']:9s} {r['method']:9s} {r['descriptions'][:5]:5s} {r.get('acc_canonical', ''):>6} "
              f"{r.get('acc_no_name', ''):>8} {r.get('acc_name_swap', ''):>6} {r.get('follows_name', ''):>8} "
              f"{r.get('mcnemar_p_noname_vs_swap', ''):>7}")
    print(f"-> {SUMMARY.relative_to(ROOT)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["run", "occlusion", "summary", "probe"])
    ap.add_argument("worlds", nargs="*", help="default: every world")
    ap.add_argument("--methods", nargs="+", default=list(sorter.METHODS),
                    choices=sorter.METHODS + sorter.FIX_METHODS,
                    help="default: the 4 main methods; add the fixes with e.g. --methods mlm-cal mlm-large")
    ap.add_argument("--limit", type=int, help="first N rows per world (for a quick try)")
    a = ap.parse_args()
    for w in a.worlds:
        if w not in sorter.WORLDS:
            sys.exit(f"unknown world {w!r}")
    if a.command == "run":
        run(a.worlds or list(sorter.WORLDS), a.methods, a.limit)
    elif a.command == "probe":
        probe(a.worlds or list(sorter.WORLDS))
    elif a.command == "occlusion":
        occlusion(a.worlds or list(sorter.WORLDS))
    else:
        summary()
