"""Step 2.3: human baseline and inter-annotator agreement (kappa), for any world.

Two team members each sort the same 20 canonical trait sets, with the names
removed, without looking at each other's answers or at the gold labels.

  make   data/<world>/tests.csv -> data/<world>/agreement/sheet_A.xlsx, sheet_B.xlsx
                                   (same 20 items, different order, dropdown per row)
                                   data/<world>/agreement/key.csv  (item -> test id, gold)
  score  the two filled sheets  -> human accuracy per annotator, Cohen's kappa,
                                   data/<world>/agreement/results.json

Usage:
  .venv/bin/python agreement.py make hp
  .venv/bin/python agreement.py score hp

The sheets show the group descriptions from groups.csv, the same ones the human
form and BERT's "with descriptions" variant use. Items are stratified across
groups (as evenly as the canonical rows allow) and drawn with sorter.SEED.
"""
import argparse
import csv
import json
import random
from pathlib import Path

from sorter import SEED, WORLDS, NAMES

DATA = Path(__file__).resolve().parent / "data"
N_ITEMS = 20


def folder(world):
    f = DATA / world / "agreement"
    f.mkdir(exist_ok=True)
    return f


def pick_items(world, rng):
    with open(DATA / world / "tests.csv") as f:
        rows = [r for r in csv.DictReader(f) if r["test_type"] == "canonical"]
    by_group = {g: [r for r in rows if r["gold_group"] == g] for g in WORLDS[world]}
    for g in by_group.values():
        rng.shuffle(g)
    chosen = []
    while len(chosen) < N_ITEMS and any(by_group.values()):
        for g in WORLDS[world]:  # round-robin keeps the groups as even as possible
            if by_group[g] and len(chosen) < N_ITEMS:
                chosen.append(by_group[g].pop())
    return chosen


def write_sheet(path, world, items, annotator):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.worksheet.datavalidation import DataValidation

    with open(DATA / world / "groups.csv") as f:
        desc = {r["group"]: r["description"] for r in csv.DictReader(f)}
    names = [NAMES[world][g] for g in WORLDS[world]]

    wb = Workbook()
    ws = wb.active
    ws.title = f"Annotator {annotator}"
    ws["A1"] = f"Annotator {annotator}: pick the group that fits each person best."
    ws["A1"].font = Font(bold=True, size=13)
    ws["A2"] = ("Work alone. Don't look at the other sheet, tests.csv or key.csv. "
                "Go with your judgement from the traits only. Every row needs an answer.")
    for i, g in enumerate(WORLDS[world]):
        ws.cell(row=3 + i, column=1, value=f"{NAMES[world][g]}: {desc[g]}").font = Font(italic=True)
    head = 4 + len(WORLDS[world])
    for c, h in enumerate(["item", "traits", "your answer"], 1):
        cell = ws.cell(row=head, column=c, value=h)
        cell.font = Font(bold=True)
        cell.fill = PatternFill("solid", fgColor="DDDDDD")
    dv = DataValidation(type="list", formula1='"' + ",".join(names) + '"', allow_blank=False)
    ws.add_data_validation(dv)
    for k, it in enumerate(items):
        r = head + 1 + k
        ws.cell(row=r, column=1, value=it["item"])
        ws.cell(row=r, column=2, value=it["traits"].replace("; ", ", "))
        ans = ws.cell(row=r, column=3)
        ans.fill = PatternFill("solid", fgColor="FFF6D5")
        dv.add(ans)
    ws.column_dimensions["A"].width = 8
    ws.column_dimensions["B"].width = 62
    ws.column_dimensions["C"].width = 20
    for row in ws.iter_rows(min_row=1, max_row=head - 1):
        for cell in row:
            cell.alignment = Alignment(wrap_text=False)
    wb.save(path)


def cmd_make(world):
    rng = random.Random(SEED)
    chosen = pick_items(world, rng)
    items = [dict(item=f"{world}-a{i:02d}", test_id=r["id"], traits=r["traits"], gold=r["gold_group"])
             for i, r in enumerate(chosen, 1)]
    out = folder(world)
    for annotator in "AB":
        order = items[:]
        rng.shuffle(order)
        write_sheet(out / f"sheet_{annotator}.xlsx", world, order, annotator)
    with open(out / "key.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["item", "test_id", "gold"])
        w.writeheader()
        w.writerows({k: it[k] for k in ("item", "test_id", "gold")} for it in items)
    counts = {g: sum(it["gold"] == g for it in items) for g in WORLDS[world]}
    print(f"{len(items)} items per sheet, by gold group: {counts}")
    print(f"wrote {out}/sheet_A.xlsx, sheet_B.xlsx, key.csv")


def read_answers(path, world):
    from openpyxl import load_workbook
    by_name = {NAMES[world][g].lower(): g for g in WORLDS[world]}
    ws = load_workbook(path, data_only=True).active
    ans = {}
    for row in ws.iter_rows(values_only=True):
        if row and isinstance(row[0], str) and row[0].startswith(f"{world}-a"):
            v = (row[2] or "").strip().lower()
            if v not in by_name:
                raise SystemExit(f"{path.name}: item {row[0]} has no valid answer ({row[2]!r})")
            ans[row[0]] = by_name[v]
    return ans


def cmd_score(world):
    from sklearn.metrics import cohen_kappa_score
    out = folder(world)
    with open(out / "key.csv") as f:
        key = {r["item"]: r["gold"] for r in csv.DictReader(f)}
    a = read_answers(out / "sheet_A.xlsx", world)
    b = read_answers(out / "sheet_B.xlsx", world)
    items = sorted(key)
    missing = [i for i in items if i not in a or i not in b]
    if missing:
        raise SystemExit(f"unanswered items: {missing}")
    ya, yb, gold = [a[i] for i in items], [b[i] for i in items], [key[i] for i in items]
    res = {
        "world": world, "n_items": len(items), "chance": 1 / len(WORLDS[world]),
        "accuracy_A": sum(x == g for x, g in zip(ya, gold)) / len(items),
        "accuracy_B": sum(x == g for x, g in zip(yb, gold)) / len(items),
        "raw_agreement": sum(x == y for x, y in zip(ya, yb)) / len(items),
        "cohen_kappa": cohen_kappa_score(ya, yb, labels=WORLDS[world]),
        "per_item": [dict(item=i, gold=key[i], A=a[i], B=b[i]) for i in items],
    }
    with open(out / "results.json", "w") as f:
        json.dump(res, f, indent=2)
    print(f"human accuracy: A {res['accuracy_A']:.0%}, B {res['accuracy_B']:.0%} "
          f"(chance {res['chance']:.0%}); agreement {res['raw_agreement']:.0%}; "
          f"Cohen's kappa {res['cohen_kappa']:.2f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["make", "score"])
    ap.add_argument("world", choices=list(WORLDS))
    a = ap.parse_args()
    cmd_make(a.world) if a.command == "make" else cmd_score(a.world)
