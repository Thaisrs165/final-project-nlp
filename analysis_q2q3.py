"""Step 6: Q2 (traits or names?) and Q3 (ambiguity) analysis, plus Figure 1.

Every choice here was fixed in DATA_LOG.md ("Step 6, Q2 and Q3: analysis choices
fixed BEFORE computing them") before any number was computed. Change a choice only
with a new, dated DATA_LOG entry.

Reads   results/all.csv, results/occlusion.csv, results/summary_q1q2.csv,
        data/vote_items.csv, data/human_votes.csv, data/human_respondents.csv,
        data/simulated_votes.csv
Writes  results/q2q3/*.csv, results/q2q3/fig1.png, results/q2q3/fig1.pdf,
        results/q2q3/SUMMARY.md

Usage:  .venv/bin/python analysis_q2q3.py
Deterministic: every random step uses seed 42.
"""
import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent
RES = ROOT / "results"
DATA = ROOT / "data"
OUT = RES / "q2q3"

MAIN = ["mlm", "embed", "bert-mean", "nli"]
FIXES = ["mlm-cal", "mlm-large", "mlm-large-cal"]
N_BOOT, N_SPLITS, SEED = 2000, 1000, 42
AMBIGUOUS = ("generic", "conflicting")


# ------------------------------------------------------------------ helpers
def entropy_norm(p):
    """Shannon entropy divided by log(K): 0 = certain, 1 = uniform."""
    p = np.asarray(p, float)
    nz = p[p > 0]
    return float(-(nz * np.log(nz)).sum() / np.log(len(p)))


def jsd(p, q):
    """Jensen-Shannon divergence, base 2 (0 = identical, 1 = disjoint)."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    p, q = p / p.sum(), q / q.sum()
    m = (p + q) / 2

    def kl(a, b):
        nz = a > 0
        return float((a[nz] * np.log2(a[nz] / b[nz])).sum())

    return 0.5 * kl(p, m) + 0.5 * kl(q, m)


def tv(p, q):
    """Total variation distance (0 = same distribution, 1 = disjoint)."""
    return 0.5 * float(np.abs(np.asarray(p, float) - np.asarray(q, float)).sum())


def boot_ci(x, n=N_BOOT, seed=SEED):
    """95% percentile bootstrap CI of the mean, resampling items."""
    x = np.asarray(x, float)
    if len(x) < 2:
        return (np.nan, np.nan)
    rng = np.random.default_rng(seed)
    means = x[rng.integers(0, len(x), (n, len(x)))].mean(axis=1)
    return (float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)))


def holm(pvals):
    """Holm-Bonferroni adjusted p-values (NaN entries are left out and kept NaN)."""
    p = np.asarray(pvals, float)
    out = np.full_like(p, np.nan)
    idx = np.where(~np.isnan(p))[0]
    order = idx[np.argsort(p[idx])]
    m, running = len(order), 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * p[i]))
        out[i] = running
    return out


def fmt_ci(ci, nd=3):
    return "–" if np.isnan(ci[0]) else f"{ci[0]:.{nd}f} to {ci[1]:.{nd}f}"


# ---------------------------------------------------------------- loading
def load_predictions(path=RES / "all.csv"):
    """One row per (world, id, method, descriptions): probabilities averaged over
    templates (only mlm-type methods have more than one), groups in a fixed order."""
    a = pd.read_csv(path)
    rows = []
    keys = ["world", "id", "origin_id", "test_type", "method", "descriptions", "traits"]
    for k, g in a.groupby(keys, dropna=False, sort=False):
        groups = list(json.loads(g.probs_json.iloc[0]).keys())
        probs = np.mean([[json.loads(s)[x] for x in groups] for s in g.probs_json], axis=0)
        raw = np.mean([[json.loads(s)[x] for x in groups] for s in g.raw_probs_json], axis=0)
        rows.append(dict(zip(keys, k), gold=g.gold.iloc[0], groups=groups,
                         probs=probs / probs.sum(), raw=raw / raw.sum()))
    p = pd.DataFrame(rows)
    p["pred"] = [g[int(np.argmax(x))] for g, x in zip(p.groups, p.probs)]
    p["pred_raw"] = [g[int(np.argmax(x))] for g, x in zip(p.groups, p.raw)]
    p["H"] = [entropy_norm(x) for x in p.probs]
    return p


def kept_panel(votes, items):
    """Simulated voters kept by the panel's own rule: >= 2 of 7 clear items wrong -> dropped."""
    clear = items[items.item_type == "clear"][["item_id", "expected"]]
    v = votes.merge(clear, on="item_id")
    wrong = (v.group.str.lower() != v.expected.str.lower()).groupby(v.voter_id).sum()
    return set(wrong[wrong < 2].index), len(clear)


def references(items):
    """{name: votes DataFrame} for the reference distributions."""
    hv = pd.read_csv(DATA / "human_votes.csv")
    resp = pd.read_csv(DATA / "human_respondents.csv")
    sv = pd.read_csv(DATA / "simulated_votes.csv")
    kept_h = set(resp.loc[resp.excluded == 0, "voter_id"])
    kept_s, _ = kept_panel(sv, items)
    return {
        "humans": hv[hv.voter_id.isin(kept_h)],
        "humans_all19": hv,
        "panel": sv[sv.voter_id.isin(kept_s)],
    }, dict(humans=len(kept_h), humans_all19=hv.voter_id.nunique(), panel=len(kept_s))


def vote_shares(votes, item_id, groups):
    c = votes[votes.item_id == item_id].group.str.lower().value_counts()
    v = np.array([c.get(g, 0) for g in groups], float)
    return v / v.sum() if v.sum() else None


def match_vote_items(pred, items):
    """vote item_id -> scored row id, matched by world + exact trait text (generic/conflicting)."""
    amb = pred[pred.test_type.isin(AMBIGUOUS)][["world", "id", "traits"]].drop_duplicates()
    amb["key"] = amb.traits.str.replace(" ", "").str.lower()
    out = {}
    for _, it in items[items.item_type.isin(AMBIGUOUS)].iterrows():
        key = it.traits.replace(" ", "").lower()
        hit = amb[(amb.world == it.world) & (amb.key == key)]
        if len(hit):
            out[it.item_id] = hit.id.iloc[0]
    return out


# --------------------------------------------------------------------- Q2
def q2_table(summary_path=RES / "summary_q1q2.csv"):
    s = pd.read_csv(summary_path)
    lo = s.ci_no_name.astype(str).str.split("-").str[0].astype(float)
    s["no_name_above_chance"] = lo > s.chance
    s["target_met"] = s.mcnemar_p_noname_vs_swap >= 0.05
    s["target_informative"] = s.target_met & s.no_name_above_chance
    s["name_effect"] = (s.acc_canonical - s.acc_no_name).round(3)
    cols = ["world", "method", "descriptions", "chance", "acc_canonical", "acc_no_name",
            "acc_name_swap", "ci_no_name", "name_effect", "follows_name",
            "mcnemar_p_noname_vs_swap", "target_met", "no_name_above_chance",
            "target_informative", "n_no_name"]
    return s[cols]


def occlusion_table(path=RES / "occlusion.csv"):
    o = pd.read_csv(path)
    o["flip"] = o.flips_to.notna() & (o.flips_to.astype(str) != "")
    rows = []
    for (w, d), g in o.groupby(["world", "descriptions"]):
        per = g.groupby("id")
        any_flip = per.flip.any()
        top_pos = g.loc[per.delta.idxmax(), "position"]
        n_pos = int(g.position.max()) + 1
        k, n = int((top_pos == 0).sum()), len(top_pos)
        rows.append(dict(world=w, descriptions=d, n_characters=n,
                         share_any_single_flip=round(any_flip.mean(), 3),
                         share_top_trait_first=round(k / n, 3), chance=round(1 / n_pos, 3),
                         binom_p=round(stats.binomtest(k, n, 1 / n_pos).pvalue, 4)))
    return pd.DataFrame(rows)


# --------------------------------------------------------------------- Q3
def q3_jsd(pred, items, refs, methods):
    """Per-item JSD of each method (and of a uniform guess) to each reference."""
    match = match_vote_items(pred, items)
    p = pred.set_index(["id", "method", "descriptions"])
    rows = []
    for ref, votes in refs.items():
        for item_id in votes.item_id.unique():
            if item_id not in match:
                continue
            it = items[items.item_id == item_id].iloc[0]
            for m in methods:
                for d in (False, True):
                    if (match[item_id], m, d) not in p.index:
                        continue
                    r = p.loc[(match[item_id], m, d)]
                    share = vote_shares(votes, item_id, r.groups)
                    if share is None:
                        continue
                    uni = np.full(len(share), 1 / len(share))
                    rows.append(dict(reference=ref, item_id=item_id, world=it.world,
                                     item_type=it.item_type, method=m, descriptions=d,
                                     jsd=jsd(r.probs, share), jsd_uniform=jsd(uni, share),
                                     H_model=r.H, H_reference=entropy_norm(share)))
    return pd.DataFrame(rows)


def q3_jsd_summary(per_item):
    rows = []
    for (ref, m, d), g in per_item.groupby(["reference", "method", "descriptions"]):
        diff = (g.jsd - g.jsd_uniform).to_numpy()
        ci = boot_ci(diff)
        w = stats.wilcoxon(diff, alternative="less").pvalue if np.any(diff != 0) else np.nan
        rows.append(dict(reference=ref, method=m, descriptions=d, n_items=len(g),
                         jsd=round(g.jsd.mean(), 3), jsd_ci=fmt_ci(boot_ci(g.jsd)),
                         jsd_uniform=round(g.jsd_uniform.mean(), 3),
                         diff=round(diff.mean(), 3), diff_ci=fmt_ci(ci),
                         diff_ci_lo=ci[0], diff_ci_hi=ci[1],
                         wilcoxon_p=round(w, 4), target_met=bool(ci[1] < 0),
                         H_model=round(g.H_model.mean(), 3),
                         H_reference=round(g.H_reference.mean(), 3)))
    return pd.DataFrame(rows)


def human_floor(votes, item_ids, n_splits=N_SPLITS, seed=SEED):
    """Mean JSD between two random halves of the kept humans, averaged over the same
    items the models are compared on (fixed 2026-11-24: the clear attention items were
    counted too, which lowered the floor from 0.17 to 0.15)."""
    rng = np.random.default_rng(seed)
    voters = np.array(sorted(votes.voter_id.unique()))
    groups_by_world = {w: sorted(g.group.str.lower().unique()) for w, g in
                       pd.read_csv(DATA / "simulated_votes.csv").groupby("world")}
    items = votes[votes.item_id.isin(item_ids)][["item_id", "world"]].drop_duplicates().to_numpy()
    out = []
    for _ in range(n_splits):
        perm = rng.permutation(voters)
        a, b = set(perm[: len(perm) // 2]), set(perm[len(perm) // 2:])
        vals = []
        for item_id, world in items:
            pa = vote_shares(votes[votes.voter_id.isin(a)], item_id, groups_by_world[world])
            pb = vote_shares(votes[votes.voter_id.isin(b)], item_id, groups_by_world[world])
            if pa is not None and pb is not None:
                vals.append(jsd(pa, pb))
        out.append(np.mean(vals))
    return float(np.mean(out)), (float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5)))


def q3_entropy(pred, methods):
    rows = []
    for (w, m, d), g in pred[pred.method.isin(methods)].groupby(["world", "method", "descriptions"]):
        amb = g[g.test_type.isin(AMBIGUOUS)].H
        clear = g[g.test_type == "no_name"].H
        p = (stats.mannwhitneyu(amb, clear, alternative="greater").pvalue
             if len(amb) and len(clear) else np.nan)
        rows.append(dict(world=w, method=m, descriptions=d, n_ambiguous=len(amb),
                         n_no_name=len(clear), H_ambiguous=round(amb.mean(), 3),
                         H_no_name=round(clear.mean(), 3) if len(clear) else np.nan,
                         H_gap=round(amb.mean() - clear.mean(), 3) if len(clear) else np.nan,
                         mannwhitney_p=p))
    t = pd.DataFrame(rows)
    t["p_holm"] = holm(t.mannwhitney_p.to_numpy())
    t["more_uncertain_on_ambiguous"] = t.p_holm < 0.05
    t["mannwhitney_p"] = t.mannwhitney_p.round(4)
    t["p_holm"] = t.p_holm.round(4)
    return t


def q3_negation(pred, methods):
    rows = []
    for (w, m, d), g in pred[pred.method.isin(methods)].groupby(["world", "method", "descriptions"]):
        neg = g[g.test_type == "negation"].set_index("origin_id")
        nn = g[g.test_type == "no_name"].set_index("origin_id")
        both = neg.index.intersection(nn.index)
        if not len(both):
            continue
        tvs = [tv(neg.loc[o, "probs"], nn.loc[o, "probs"]) for o in both]
        flips = [neg.loc[o, "pred"] != nn.loc[o, "pred"] for o in both]
        base = [tv(nn.loc[a, "probs"], nn.loc[b, "probs"]) for a, b in combinations(nn.index, 2)]
        rows.append(dict(world=w, method=m, descriptions=d, n_pairs=len(both),
                         flip_rate=round(np.mean(flips), 3), tv_negation=round(np.mean(tvs), 3),
                         tv_negation_ci=fmt_ci(boot_ci(tvs)),
                         tv_other_character=round(np.mean(base), 3),
                         ratio=round(np.mean(tvs) / np.mean(base), 2) if np.mean(base) else np.nan,
                         H_negation=round(neg.loc[both, "H"].mean(), 3)))
    return pd.DataFrame(rows)


def calibration_pull(pred):
    rows = []
    sub = pred[(pred.method == "mlm") & pred.test_type.isin(["no_name", "generic"])]
    for (w, d), g in sub.groupby(["world", "descriptions"]):
        for col, label in (("pred_raw", "raw"), ("pred", "calibrated")):
            mode = g[col].mode().iloc[0]
            for t in ("no_name", "generic"):
                x = g[g.test_type == t][col]
                if len(x):
                    rows.append(dict(world=w, descriptions=d, scores=label, input=t,
                                     most_common=mode, n=len(x),
                                     share_most_common=round((x == mode).mean(), 3)))
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ figure
# Reference palette (dataviz skill, references/palette.md), light mode, slots 1-2.
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
C_HUMAN, C_PANEL = "#2a78d6", "#eb6834"
C_NEG, C_BASE = "#2a78d6", "#8a8984"
LABEL = {"mlm": "MLM", "embed": "Embed", "bert-mean": "BERT-mean", "nli": "NLI"}


def figure1(jsd_sum, floor, neg, path_png, path_pdf):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.family": "serif", "font.size": 7, "axes.edgecolor": INK2,
                         "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
                         "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6})
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(3.5, 2.15), sharey=True,
                                   gridspec_kw=dict(wspace=0.12))
    y = np.arange(len(MAIN))[::-1]
    js = jsd_sum[jsd_sum.descriptions]
    off = {"humans": 0.14, "panel": -0.14}
    for ref, color, marker, name in (("humans", C_HUMAN, "o", "Humans (n=10)"),
                                     ("panel", C_PANEL, "s", "Sim. panel")):
        r = js[js.reference == ref].set_index("method").reindex(MAIN)
        lo, hi = zip(*[tuple(map(float, s.split(" to "))) for s in r.jsd_ci])
        ax1.errorbar(r.jsd, y + off[ref], xerr=[r.jsd - np.array(lo), np.array(hi) - r.jsd],
                     fmt=marker, ms=3.5, color=color, ecolor=color, elinewidth=0.8, capsize=0,
                     mec="white", mew=0.6, label=name, zorder=3)
        ax1.axvline(r.jsd_uniform.iloc[0], color=color, lw=0.8, ls="--", zorder=1)
    ax1.axvline(floor, color=INK2, lw=0.8, ls=":", zorder=1)
    ymax = len(MAIN) - 0.45
    ax1.text(floor, ymax, "human\nfloor", ha="center", va="bottom", fontsize=5.5, color=INK2)
    u = js.jsd_uniform.groupby(js.reference).first()[["humans", "panel"]].mean()
    ax1.text(u, ymax, "uniform\nguess", ha="center", va="bottom", fontsize=5.5, color=INK2)
    ax1.set_yticks(y, [LABEL[m] for m in MAIN])
    ax1.set_xlabel("JSD to votes (lower = closer)")
    ax1.set_title("(a) Ambiguous inputs", fontsize=7, loc="left", color=INK, pad=14)
    ax1.legend(loc="upper center", bbox_to_anchor=(0.5, -0.27), ncol=1, fontsize=5.5, frameon=False,
               handletextpad=0.2, columnspacing=0.8)

    n = neg[neg.descriptions].groupby("method")[["tv_negation", "tv_other_character"]].mean()
    n = n.reindex(MAIN)
    for col, color, marker, name, dy in (("tv_negation", C_NEG, "o", '"not" added', 0.14),
                                         ("tv_other_character", C_BASE, "D", "other character", -0.14)):
        ax2.plot(n[col], y + dy, marker, ms=3.5, color=color, mec="white", mew=0.6,
                 label=name, ls="none", zorder=3)
    for yi, (a, b) in zip(y, n.to_numpy()):
        ax2.plot([a, b], [yi + 0.14, yi - 0.14], color=GRID, lw=0.8, zorder=1)
    ax2.set_xlabel("TV distance (answer shift)")
    ax2.set_title("(b) Negation", fontsize=7, loc="left", color=INK, pad=14)
    ax2.legend(loc="upper center", bbox_to_anchor=(0.5, -0.27), ncol=1, fontsize=5.5, frameon=False,
               handletextpad=0.2, columnspacing=0.8)
    ax2.set_xlim(0, 0.5)
    for ax in (ax1, ax2):
        ax.grid(axis="x", color=GRID, lw=0.5, zorder=0)
        ax.spines[["top", "right"]].set_visible(False)
        if ax is ax1:
            ax.set_xlim(left=0)
        ax.set_ylim(-0.6, len(MAIN) - 0.4)
    fig.savefig(path_png, dpi=300, bbox_inches="tight")
    fig.savefig(path_pdf, bbox_inches="tight")
    plt.close(fig)


# -------------------------------------------------------------------- main
def main():
    OUT.mkdir(exist_ok=True)
    pred = load_predictions()
    items = pd.read_csv(DATA / "vote_items.csv")
    refs, n_ref = references(items)

    q2 = q2_table()
    occ = occlusion_table()
    per_item = q3_jsd(pred, items, refs, MAIN + FIXES)
    js = q3_jsd_summary(per_item)
    floor, floor_ci = human_floor(
        refs["humans"], set(per_item[per_item.reference == "humans"].item_id))
    ent = q3_entropy(pred, MAIN + FIXES)
    neg = q3_negation(pred, MAIN + FIXES)
    cal = calibration_pull(pred)

    main_m, fix_m = q2.method.isin(MAIN), q2.method.isin(FIXES)
    q2[main_m].to_csv(OUT / "q2_names.csv", index=False)
    q2[fix_m].to_csv(OUT / "q2_names_fixes.csv", index=False)
    occ.to_csv(OUT / "q2_occlusion.csv", index=False)
    per_item.to_csv(OUT / "q3_jsd_items.csv", index=False)
    cols = [c for c in js.columns if c not in ("diff_ci_lo", "diff_ci_hi")]
    js[js.method.isin(MAIN)][cols].to_csv(OUT / "q3_jsd.csv", index=False)
    js[js.method.isin(FIXES)][cols].to_csv(OUT / "q3_jsd_fixes.csv", index=False)
    ent[ent.method.isin(MAIN)].to_csv(OUT / "q3_entropy.csv", index=False)
    ent[ent.method.isin(FIXES)].to_csv(OUT / "q3_entropy_fixes.csv", index=False)
    neg[neg.method.isin(MAIN)].to_csv(OUT / "q3_negation.csv", index=False)
    neg[neg.method.isin(FIXES)].to_csv(OUT / "q3_negation_fixes.csv", index=False)
    cal.to_csv(OUT / "q3_calibration_pull.csv", index=False)
    figure1(js[js.method.isin(MAIN)], floor, neg[neg.method.isin(MAIN)],
            OUT / "fig1.png", OUT / "fig1.pdf")
    write_summary(pred, q2, occ, js, floor, floor_ci, ent, neg, cal, n_ref)
    print(f"wrote {OUT.relative_to(ROOT)}/ (see SUMMARY.md)")


def md(df):
    """Markdown table without the optional `tabulate` dependency."""
    head = "| " + " | ".join(map(str, df.columns)) + " |"
    sep = "|" + "---|" * len(df.columns)
    body = ["| " + " | ".join("" if pd.isna(v) else str(v) for v in r) + " |"
            for r in df.itertuples(index=False)]
    return "\n".join([head, sep, *body])


def write_summary(pred, q2, occ, js, floor, floor_ci, ent, neg, cal, n_ref):
    worlds = sorted(pred.world.unique())
    m = q2[q2.method.isin(MAIN)]
    m = m[m.mcnemar_p_noname_vs_swap.notna()]   # worlds without no_name/name_swap rows (divergent)
    met, inf = int(m.target_met.sum()), int(m.target_informative.sum())
    jm = js[js.method.isin(MAIN)]
    keep = ["reference", "method", "descriptions", "n_items", "jsd", "jsd_uniform", "diff",
            "diff_ci", "wilcoxon_p", "target_met"]
    em = ent[ent.method.isin(MAIN)]
    nm = neg[neg.method.isin(MAIN)]
    lines = [
        "# Q2 and Q3: results (generated by `analysis_q2q3.py`, do not edit by hand)",
        "",
        f"Worlds with predictions: {', '.join(worlds)}. Main methods: {', '.join(MAIN)}. "
        f"Fix methods ({', '.join(FIXES)}) are in the `*_fixes.csv` files only.",
        f"References: humans kept = {n_ref['humans']} (all = {n_ref['humans_all19']}), "
        f"simulated panel kept = {n_ref['panel']} (**simulated**, not human).",
        "Choices: DATA_LOG.md, entry \"Step 6, Q2 and Q3: analysis choices fixed BEFORE computing them\".",
        "",
        "## Q2: traits or names?",
        "",
        f"Target \"McNemar p >= 0.05\" is formally met in {met} of {len(m)} rows (world x method x variant), "
        f"but informative (no_name accuracy CI above chance) in only {inf}. "
        "Worlds without no_name / name_swap rows are left out of this count.",
        "",
        md(m[["world", "method", "descriptions", "chance", "acc_canonical", "acc_no_name",
              "acc_name_swap", "name_effect", "follows_name", "mcnemar_p_noname_vs_swap",
              "no_name_above_chance"]]),
        "",
        "### Occlusion (mlm, template 0, no name)",
        "",
        md(occ),
        "",
        "## Q3: ambiguity",
        "",
        "### JSD to reference votes (pooled over worlds; diff = JSD(model) - JSD(uniform); target met if diff CI < 0)",
        "",
        md(jm[keep]),
        "",
        f"Human floor (JSD between random halves of the {n_ref['humans']} kept humans, "
        f"{N_SPLITS} splits): {floor:.3f} (95% of splits: {floor_ci[0]:.3f} to {floor_ci[1]:.3f}). "
        "Halves of 5 are noisier than the full group, so this floor is on the high side.",
        "",
        "### Entropy: ambiguous (generic + conflicting) vs. no_name (Holm-corrected one-sided Mann-Whitney)",
        "",
        md(em[["world", "method", "descriptions", "H_ambiguous", "H_no_name", "H_gap", "p_holm",
               "more_uncertain_on_ambiguous"]]),
        "",
        "### Negation (negation row vs. the same character's no_name row)",
        "",
        md(nm[["world", "method", "descriptions", "n_pairs", "flip_rate", "tv_negation",
               "tv_other_character", "ratio", "H_negation"]]),
        "",
        "### Calibration pull (original mlm): share of rows given the most common answer",
        "",
        md(cal),
        "",
        "![Figure 1](fig1.png)",
        "",
    ]
    (OUT / "SUMMARY.md").write_text("\n".join(lines))


if __name__ == "__main__":
    main()
