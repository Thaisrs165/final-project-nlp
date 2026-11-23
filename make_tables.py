"""Step 6: the report's Table 1, Table 2 and Figure 1, built from results/.

Reads results/all.csv, results/summary_q1q2.csv, data/*/tests.csv, the agreement
results and the human form. It never loads a model, so it runs in seconds.

  .venv/bin/python run_experiments.py summary   # refresh summary_q1q2.csv first
  .venv/bin/python make_tables.py

Output (results/report/):
  table1_data.tex / .csv      data per world (characters, rows, human accuracy, kappa)
  table2_q1q2.tex / .csv      Q1 accuracy (95% CI) + Q2 name effect, worlds with >= 10 characters
  fig1_q3.pdf / .png          Q3: JSD to human votes on vague items, and the negation shift
  q3_jsd.csv, q3_negation.csv the numbers behind Figure 1 (all methods, both variants)

Choices (logged in DATA_LOG.md, "Report tables and Figure 1"):
  * Main variant = WITH group descriptions: the human annotators and the form saw them too.
  * MLM probabilities are averaged over the 3 templates first (as in run_experiments.summary).
  * Table 2 keeps worlds with >= MIN_CANONICAL characters (Divergent has 4).
  * Negation is compared with the no_name row (same traits, no name), because canonical
    rows are scored WITH the character's name and negation rows without it.
  * Humans = the form respondents kept by the attention rule (excluded == 0).
"""
from __future__ import annotations

import csv
import json
import math
import random
from collections import defaultdict
from pathlib import Path

import sorter

ROOT = Path(__file__).resolve().parent
DATA, RES = ROOT / "data", ROOT / "results"
OUT = RES / "report"
WORLD_ORDER = ["hp", "avatar", "got", "divergent", "invented"]
WORLD_LABEL = {"hp": "Harry Potter", "avatar": "Avatar", "got": "Game of Thrones",
               "divergent": "Divergent", "invented": "Invented"}
METHODS = [("mlm", "BERT fill-in"), ("mlm-large-cal", "BERT + fixes"),
           ("embed", "Sentence-BERT"), ("nli", "NLI (BART)")]
MIN_CANONICAL = 10
N_BOOT = 1000


# --------------------------------------------------------------------------- helpers
def read_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def norm(traits):
    return "".join(traits.lower().split())


def jsd(p, q):
    """Jensen-Shannon divergence, base 2 (0 = identical, 1 = disjoint)."""
    keys = set(p) | set(q)
    m = {k: (p.get(k, 0) + q.get(k, 0)) / 2 for k in keys}

    def kl(a):
        return sum(a.get(k, 0) * math.log2(a.get(k, 0) / m[k]) for k in keys if a.get(k, 0) > 0)
    return (kl(p) + kl(q)) / 2


def tvd(p, q):
    return sum(abs(p.get(k, 0) - q.get(k, 0)) for k in set(p) | set(q)) / 2


def boot_ci(values, seed=sorter.SEED):
    rng = random.Random(seed)
    v = list(values)
    if not v:
        return float("nan"), float("nan")
    means = sorted(sum(rng.choice(v) for _ in v) / len(v) for _ in range(N_BOOT))
    return means[int(0.025 * N_BOOT)], means[int(0.975 * N_BOOT) - 1]


def mean(v):
    v = list(v)
    return sum(v) / len(v) if v else float("nan")


def template_avg(rows):
    """{(world, id, method, descriptions): probs averaged over templates}."""
    acc = defaultdict(lambda: defaultdict(float))
    n = defaultdict(int)
    for r in rows:
        k = (r["world"], r["id"], r["method"], r["descriptions"])
        for g, p in json.loads(r["probs_json"]).items():
            acc[k][g] += p
        n[k] += 1
    return {k: {g: p / n[k] for g, p in d.items()} for k, d in acc.items()}


def pct(x):
    return "--" if x != x else f"{100 * x:.0f}"


# --------------------------------------------------------------------------- Table 1
def table1():
    rows = []
    for w in WORLD_ORDER:
        tests = read_csv(DATA / w / "tests.csv")
        n_canon = sum(r["test_type"] == "canonical" for r in tests)
        n_rows = sum(r["test_type"] not in ("canonical", "needs_review") for r in tests)
        agr = DATA / w / "agreement" / "results.json"
        acc = kappa = float("nan")
        if agr.exists():
            a = json.loads(agr.read_text())
            acc, kappa = (a["accuracy_A"] + a["accuracy_B"]) / 2, a["cohen_kappa"]
        rows.append({"world": w, "groups": len(sorter.WORLDS[w]), "characters": n_canon,
                     "test_rows": n_rows, "human_acc": acc, "kappa": kappa,
                     "human_items": "probes" if w == "divergent" else "characters"})
    with open(OUT / "table1_data.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    lines = [r"\begin{table}[t]", r"\centering\footnotesize",
             r"\caption{Data per world. Human accuracy: mean of two annotators sorting 20 nameless items; $\kappa$: Cohen's kappa between them.}",
             r"\label{tab:data}", r"\begin{tabular}{lrrrrr}", r"\toprule",
             r"World & Groups & Chars. & Test rows & Human acc. (\%) & $\kappa$ \\", r"\midrule"]
    for r in rows:
        name = WORLD_LABEL[r["world"]] + (r"$^\dagger$" if r["world"] == "divergent" else "")
        k = "--" if r["kappa"] != r["kappa"] else f"{r['kappa']:.2f}"
        lines.append(f"{name} & {r['groups']} & {r['characters']} & {r['test_rows']} & "
                     f"{pct(r['human_acc'])} & {k} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}",
              r"\\[2pt]\parbox{\columnwidth}{\scriptsize $^\dagger$Only 4 characters (all Dauntless): "
              r"the source has no personality text for the other factions. Its human items are "
              r"designed single- and two-faction probes, so its $\kappa$ is not comparable to the others.}",
              r"\end{table}"]
    (OUT / "table1_data.tex").write_text("\n".join(lines) + "\n")
    return rows


# --------------------------------------------------------------------------- Table 2
def table2(t1):
    human = {r["world"]: r["human_acc"] for r in t1}
    summ = read_csv(RES / "summary_q1q2.csv")
    cell = {(r["world"], r["method"], r["descriptions"]): r for r in summ}
    worlds = [r["world"] for r in t1 if r["characters"] >= MIN_CANONICAL
              and any(k[0] == r["world"] for k in cell)]
    out = []
    for w in worlds:
        row = {"world": w, "chance": 1 / len(sorter.WORLDS[w]), "human": human[w]}
        for m, _ in METHODS:
            for desc in ("True", "False"):
                c = cell.get((w, m, desc), {})
                tag = f"{m}|{'desc' if desc == 'True' else 'names'}"
                for f in ("acc_canonical", "ci_canonical", "acc_no_name", "acc_name_swap",
                          "follows_name", "mcnemar_p_noname_vs_swap"):
                    row[f"{tag}|{f}"] = c.get(f, "")
        out.append(row)
    with open(OUT / "table2_q1q2.csv", "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(out[0]))
        wr.writeheader()
        wr.writerows(out)

    def acc(r, m):
        a, ci = r[f"{m}|desc|acc_canonical"], r[f"{m}|desc|ci_canonical"]
        if a == "":
            return "--"
        lo, hi = ci.split("-")
        return f"{100 * float(a):.0f} {{\\tiny[{100 * float(lo):.0f},{100 * float(hi):.0f}]}}"

    def q2(r, m):
        nn, sw, fo = (r[f"{m}|desc|{f}"] for f in ("acc_no_name", "acc_name_swap", "follows_name"))
        p = r[f"{m}|desc|mcnemar_p_noname_vs_swap"]
        if nn == "":
            return "--"
        star = "*" if p != "" and float(p) < 0.05 else ""
        return f"{pct(float(nn))}$\\to${pct(float(sw))}{star} ({pct(float(fo))})"

    lines = [r"\begin{table*}[t]", r"\centering\footnotesize",
             r"\caption{Q1: accuracy (\%) on canonical characters, with group descriptions, 95\% bootstrap CI in brackets. "
             r"Q2: accuracy without a name $\to$ with another group's character name (share of answers that follow the swapped name). "
             r"* McNemar $p<0.05$. MLM averaged over 3 prompts.}",
             r"\label{tab:q1q2}", r"\begin{tabular}{lrr" + "r" * len(METHODS) + "rr}", r"\toprule",
             r" & & & \multicolumn{" + str(len(METHODS)) + r"}{c}{Q1: canonical accuracy} & \multicolumn{2}{c}{Q2: no name $\to$ swapped name} \\",
             r"\cmidrule(lr){4-" + str(3 + len(METHODS)) + r"}\cmidrule(lr){" + str(4 + len(METHODS)) + "-" + str(5 + len(METHODS)) + "}",
             "World & Chance & Human & " + " & ".join(lbl for _, lbl in METHODS) + r" & BERT fill-in & NLI \\",
             r"\midrule"]
    for r in out:
        lines.append(f"{WORLD_LABEL[r['world']]} & {pct(r['chance'])} & {pct(r['human'])} & "
                     + " & ".join(acc(r, m) for m, _ in METHODS)
                     + f" & {q2(r, 'mlm')} & {q2(r, 'nli')} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table*}"]
    (OUT / "table2_q1q2.tex").write_text("\n".join(lines) + "\n")
    return out


# --------------------------------------------------------------------------- Figure 1 data
def human_dists(only_kept=True):
    keep = {r["voter_id"] for r in read_csv(DATA / "human_respondents.csv")
            if not only_kept or r["excluded"] == "0"}
    votes = defaultdict(list)
    for v in read_csv(DATA / "human_votes.csv"):
        if v["voter_id"] in keep:
            votes[v["item_id"]].append((v["voter_id"], v["group"]))
    return votes


def dist(groups, world):
    d = {g: 0.0 for g in sorter.WORLDS[world]}
    for g in groups:
        d[g] += 1 / len(groups)
    return d


def split_half_floor(votes, items, world_of, reps=N_BOOT, seed=sorter.SEED):
    """Expected JSD between two random halves of the respondents (human-vs-human floor)."""
    rng = random.Random(seed)
    voters = sorted({v for i in items for v, _ in votes[i]})
    vals = []
    for _ in range(reps):
        rng.shuffle(voters)
        a = set(voters[: len(voters) // 2])
        per = []
        for i in items:
            ga = [g for v, g in votes[i] if v in a]
            gb = [g for v, g in votes[i] if v not in a]
            if ga and gb:
                per.append(jsd(dist(ga, world_of[i]), dist(gb, world_of[i])))
        vals.append(mean(per))
    return mean(vals)


def q3(rows):
    probs = template_avg(rows)
    items = [i for i in read_csv(DATA / "vote_items.csv") if i["item_type"] == "generic"]
    world_of = {i["item_id"]: i["world"] for i in items}
    by_traits, test_rows = {}, {}
    for w in WORLD_ORDER:
        for t in read_csv(DATA / w / "tests.csv"):
            if t["test_type"] == "generic":
                by_traits.setdefault((w, norm(t["traits"])), t["id"])
            test_rows[(w, t["id"])] = t
    jrows = []
    for sample, only_kept in (("kept", True), ("all", False)):
        votes = human_dists(only_kept)
        usable = [i for i in items if votes.get(i["item_id"]) and (i["world"], norm(i["traits"])) in by_traits]
        floor = split_half_floor(votes, [i["item_id"] for i in usable], world_of)
        for m, _ in METHODS + [("bert-mean", "BERT mean-pool"), ("mlm-cal", "MLM cal"), ("mlm-large", "MLM large")]:
            for desc in ("True", "False"):
                per = []
                for i in usable:
                    rid = by_traits[(i["world"], norm(i["traits"]))]
                    p = probs.get((i["world"], rid, m, desc))
                    if p is None:
                        continue
                    h = dist([g for _, g in votes[i["item_id"]]], i["world"])
                    u = {g: 1 / len(h) for g in h}
                    per.append((jsd(p, h), jsd(u, h)))
                if not per:
                    continue
                lo, hi = boot_ci([a for a, _ in per])
                jrows.append({"sample": sample, "method": m, "descriptions": desc, "n_items": len(per),
                              "n_respondents": len({v for i in usable for v, _ in votes[i['item_id']]}),
                              "jsd_model_human": mean(a for a, _ in per), "ci_low": lo, "ci_high": hi,
                              "jsd_uniform_human": mean(b for _, b in per),
                              "model_beats_uniform": sum(a < b for a, b in per) / len(per),
                              "human_split_half_floor": floor})
    with open(OUT / "q3_jsd.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(jrows[0]))
        w.writeheader()
        w.writerows(jrows)

    # negation: no_name row (positive) vs. negation row (same character, every trait negated)
    nrows = []
    for m, _ in METHODS + [("bert-mean", "BERT mean-pool"), ("mlm-cal", "MLM cal"), ("mlm-large", "MLM large")]:
        for desc in ("True", "False"):
            pairs = []
            for (w, rid), t in test_rows.items():
                if t["test_type"] != "negation":
                    continue
                pos = probs.get((w, f"{t['origin_id']}-nn", m, desc))
                neg = probs.get((w, rid, m, desc))
                if pos and neg:
                    pairs.append((w, tvd(pos, neg), sorter.top(pos) != sorter.top(neg),
                                  sorter.entropy(pos), sorter.entropy(neg)))
            if not pairs:
                continue
            lo, hi = boot_ci([p[1] for p in pairs])
            nrows.append({"method": m, "descriptions": desc, "n_pairs": len(pairs),
                          "worlds": "+".join(sorted({p[0] for p in pairs})),
                          "tvd": mean(p[1] for p in pairs), "ci_low": lo, "ci_high": hi,
                          "flip_rate": mean(p[2] for p in pairs),
                          "entropy_positive": mean(p[3] for p in pairs),
                          "entropy_negated": mean(p[4] for p in pairs)})
    with open(OUT / "q3_negation.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(nrows[0]))
        w.writeheader()
        w.writerows(nrows)
    return jrows, nrows


# --------------------------------------------------------------------------- Figure 1
INK, INK2, GRID, MARK = "#0b0b0b", "#52514e", "#e4e3df", "#2a78d6"


def figure1(jrows, nrows):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 7, "font.family": "serif", "axes.edgecolor": GRID,
                         "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK,
                         "text.color": INK})
    labels = [lbl for _, lbl in METHODS]
    ys = list(range(len(METHODS)))[::-1]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(3.5, 1.7), sharey=True)

    J = {r["method"]: r for r in jrows if r["sample"] == "kept" and r["descriptions"] == "True"}
    for y, (m, _) in zip(ys, METHODS):
        r = J[m]
        a1.plot([r["ci_low"], r["ci_high"]], [y, y], color=MARK, lw=1.5, solid_capstyle="round")
        a1.plot(r["jsd_model_human"], y, "o", ms=4.5, color=MARK, mec="white", mew=0.8)
    ref = next(iter(J.values()))
    for x, txt, ls, ha, dx in ((ref["jsd_uniform_human"], "uniform", "--", "left", 0.01),
                               (ref["human_split_half_floor"], "humans", ":", "right", -0.01)):
        a1.axvline(x, color=INK2, lw=0.8, ls=ls)
        a1.text(x + dx, len(METHODS) - 0.45, txt, fontsize=5.5, color=INK2, ha=ha, va="bottom")
    a1.set_xlim(0, 0.6)
    a1.set_xlabel("JSD to human votes")
    a1.set_title("(a) Vague inputs", fontsize=7, loc="left")

    N = {r["method"]: r for r in nrows if r["descriptions"] == "True"}
    for y, (m, _) in zip(ys, METHODS):
        r = N[m]
        a2.plot([r["ci_low"], r["ci_high"]], [y, y], color=MARK, lw=1.5, solid_capstyle="round")
        a2.plot(r["tvd"], y, "o", ms=4.5, color=MARK, mec="white", mew=0.8)
        a2.text(r["ci_high"] + 0.02, y, f"flips {100 * r['flip_rate']:.0f}%", fontsize=5.5,
                color=INK2, va="center")
    a2.set_xlim(0, 1)
    a2.set_xlabel('shift after "not" (TVD)')
    a2.set_title('(b) Negation', fontsize=7, loc="left")

    a1.set_yticks(ys)
    a1.set_yticklabels(labels)
    a1.set_ylim(-0.6, len(METHODS) - 0.1)
    for ax in (a1, a2):
        ax.grid(axis="x", color=GRID, lw=0.5)
        ax.set_axisbelow(True)
        ax.tick_params(length=0)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
    fig.tight_layout(pad=0.3, w_pad=0.8)
    fig.savefig(OUT / "fig1_q3.pdf")
    fig.savefig(OUT / "fig1_q3.png", dpi=300)
    plt.close(fig)
    cap = (r"\begin{figure}[t]" "\n" r"\centering" "\n"
           r"\includegraphics[width=\columnwidth]{fig1_q3.pdf}" "\n"
           r"\caption{Q3, with group descriptions. (a) Jensen--Shannon divergence between each model and the "
           f"human votes ({ref['n_respondents']} respondents after the attention check) on {ref['n_items']} vague items, "
           r"with the JSD of a uniform guess and between two random halves of the respondents. "
           r"(b) Total variation between a character's traits and the same traits each preceded by ``not'' "
           f"({next(iter(N.values()))['n_pairs']} characters); lines are 95\\% bootstrap CIs.}}" "\n"
           r"\label{fig:q3}" "\n" r"\end{figure}" "\n")
    (OUT / "fig1_q3.tex").write_text(cap)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = read_csv(RES / "all.csv")
    t1 = table1()
    t2 = table2(t1)
    jrows, nrows = q3(rows)
    figure1(jrows, nrows)
    print(f"Table 1: {len(t1)} worlds · Table 2: {[r['world'] for r in t2]} · "
          f"Q3: {len(jrows)} JSD rows, {len(nrows)} negation rows")
    print(f"-> {OUT.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
