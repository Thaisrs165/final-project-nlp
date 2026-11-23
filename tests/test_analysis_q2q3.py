"""Fast checks for analysis_q2q3.py (no models, no full run)."""
import numpy as np
import pandas as pd
import pytest

import analysis_q2q3 as A


def test_jsd_bounds_and_symmetry():
    assert A.jsd([1, 0], [1, 0]) == pytest.approx(0)
    assert A.jsd([1, 0], [0, 1]) == pytest.approx(1)          # base 2: disjoint = 1
    p, q = [0.7, 0.2, 0.1], [0.2, 0.3, 0.5]
    assert A.jsd(p, q) == pytest.approx(A.jsd(q, p))


def test_tv_and_entropy():
    assert A.tv([1, 0], [0, 1]) == pytest.approx(1)
    assert A.tv([0.5, 0.5], [0.5, 0.5]) == pytest.approx(0)
    assert A.entropy_norm([0.25] * 4) == pytest.approx(1)
    assert A.entropy_norm([1, 0, 0, 0]) == pytest.approx(0)


def test_holm_matches_hand_example():
    # sorted p: 0.01*3=0.03, 0.02*2=0.04, 0.04*1=0.04 (monotone) ; NaN kept
    out = A.holm([0.04, 0.01, np.nan, 0.02])
    assert out[1] == pytest.approx(0.03)
    assert out[3] == pytest.approx(0.04)
    assert out[0] == pytest.approx(0.04)
    assert np.isnan(out[2])


def test_bootstrap_is_deterministic():
    x = np.arange(20, dtype=float)
    assert A.boot_ci(x) == A.boot_ci(x)
    lo, hi = A.boot_ci(x)
    assert lo < x.mean() < hi


def test_panel_rule_keeps_35_of_40():
    items = pd.read_csv(A.DATA / "vote_items.csv")
    kept, n_clear = A.kept_panel(pd.read_csv(A.DATA / "simulated_votes.csv"), items)
    assert n_clear == 7
    assert len(kept) == 35


def test_human_references():
    items = pd.read_csv(A.DATA / "vote_items.csv")
    _, n = A.references(items)
    assert n == dict(humans=10, humans_all19=19, panel=35)


def test_every_scored_vote_item_is_matched():
    """Each generic/conflicting vote item of a world with predictions maps to one scored row."""
    items = pd.read_csv(A.DATA / "vote_items.csv")
    pred = pd.read_csv(A.RES / "all.csv", usecols=["world", "id", "test_type", "traits"])
    match = A.match_vote_items(pred, items)
    scored = items[items.item_type.isin(A.AMBIGUOUS) & items.world.isin(pred.world.unique())]
    assert set(scored.item_id) <= set(match)
    assert match["c01-div"] == "cnf-abn-dau-direct-ba"
    assert match["c02-div"] == "cnf-can-eru-direct-ab"


def test_q2_flags_need_above_chance():
    q2 = A.q2_table()
    # a row can only be "informative" if the target is met AND no_name beats chance
    assert not (q2.target_informative & ~q2.no_name_above_chance).any()
    assert not (q2.target_informative & ~q2.target_met).any()
