"""Fast tests for run_experiments.py helpers (no models)."""
import math

import run_experiments as rx


def test_mcnemar_exact():
    assert rx.mcnemar_p([1, 1, 0], [1, 1, 0]) == 1.0           # no discordant pairs
    # 6 discordant pairs all one way: p = 2 * (1/2)^6
    assert math.isclose(rx.mcnemar_p([1] * 6, [0] * 6), 2 / 64)
    assert rx.mcnemar_p([1, 0], [0, 1]) == 1.0


def test_bootstrap_ci_is_deterministic_and_brackets_the_mean():
    hits = [1] * 7 + [0] * 3
    lo, hi = rx.bootstrap_ci(hits)
    assert (lo, hi) == rx.bootstrap_ci(hits)
    assert lo <= 0.7 <= hi


def test_names_only_for_canonical_and_name_swap():
    rows = [{"id": "a", "test_type": "canonical", "name": "Ginny", "traits": "x"},
            {"id": "b", "test_type": "no_name", "name": "", "traits": "x"},
            {"id": "c", "test_type": "negation", "name": "Ginny", "traits": "x"},
            {"id": "d", "test_type": "name_swap", "name": "Draco", "traits": "x"}]
    names = {r["id"]: n for r, _, _, _, n in rx.jobs_for("hp", rows, ["embed"])}
    assert names == {"a": "Ginny", "b": "", "c": "", "d": "Draco"}


def test_prune_drops_only_outdated_rows(tmp_path, monkeypatch):
    import csv
    monkeypatch.setattr(rx, "load_tests", lambda w: [
        {"id": "hp-c01", "test_type": "canonical", "name": "Ginny", "traits": "brave; new"},
        {"id": "hp-c02", "test_type": "no_name", "name": "", "traits": "kind"}] if w == "hp" else [])
    path = tmp_path / "all.csv"
    rows = [{"world": "hp", "id": "hp-c01", "name": "Ginny", "traits": "brave; old"},   # outdated
            {"world": "hp", "id": "hp-c01", "name": "Ginny", "traits": "brave; new"},   # current
            {"world": "hp", "id": "hp-c02", "name": "", "traits": "kind"},              # current
            {"world": "hp", "id": "hp-c99", "name": "", "traits": "x"},                 # removed
            {"world": "got", "id": "got-c01", "name": "", "traits": "y"}]               # other world
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["world", "id", "name", "traits"])
        w.writeheader()
        w.writerows(rows)
    assert rx.prune(path, ["hp"]) == 2
    with open(path) as f:
        left = [(r["id"], r["traits"]) for r in csv.DictReader(f)]
    assert left == [("hp-c01", "brave; new"), ("hp-c02", "kind"), ("got-c01", "y")]
