"""Fast tests for experiments/divergent.py (no models are loaded)."""
import csv
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "experiments"))
import divergent as dv  # noqa: E402
import sorter  # noqa: E402

DESC = sorter.load_descriptions("divergent")


def test_direct_words_leak_and_synonyms_do_not():
    for g, (direct, s1, s2) in dv.WORDS.items():
        assert dv.leaks(direct, descriptions=DESC), (g, direct)   # easy variant leaks on purpose
        assert not dv.leaks(s1, descriptions=DESC), (g, s1)
        assert not dv.leaks(s2, descriptions=DESC), (g, s2)
    assert dv.leaks("kindhearted", descriptions=DESC)        # kindness
    assert dv.leaks("Dauntless to the core", descriptions=DESC)  # group name
    assert not dv.leaks("stubborn", descriptions=DESC)


def test_probes_counts_and_gold():
    rows = dv.build_probes()
    by = {}
    for r in rows:
        by.setdefault(r["test_type"], []).append(r)
    assert len(by["clear"]) == 2 * 5 + 1                  # + k01-div from vote_items
    assert len(by["conflicting"]) == math.comb(5, 2) * 2 * 2 >= 20
    assert len(by["divergent_mode"]) == math.comb(5, 3) * 2
    assert {r["id"] for r in by["generic"]} == {"g01-div", "g02-div", "g03-div"}
    assert len({r["id"] for r in rows}) == len(rows)
    for r in by["conflicting"]:
        a, b = r["gold_group"].split("|")
        t1, t2 = sorter.parse_traits(r["traits"])
        assert t1 in dv.WORDS[a] and t2 in dv.WORDS[b]      # gold follows trait order
    # the two conflicting vote items are covered with identical traits
    traits = {r["traits"] for r in by["conflicting"]}
    assert "brave; selfless" in traits and "honest; intelligent" in traits
    tris = [r for r in by["divergent_mode"] if r["id"].startswith("div-abn-dau-eru")]
    assert len(tris) == 2 and all(r["source_url"] == dv.TRIS_SOURCE for r in tris)


def test_reversed_rows_point_to_their_pair():
    rows = {r["id"]: r for r in dv.build_probes()}
    for r in rows.values():
        if r["origin_id"]:
            o = rows[r["origin_id"]]
            assert sorter.parse_traits(r["traits"]) == sorter.parse_traits(o["traits"])[::-1]


def _chars(tmp_path, **cells):
    base = {"name": "X", "gold_group": "candor", "birth_faction": "", "divergent": "no",
            "source_url": "u", "faction_evidence": "e", "traits": "", "trait_evidence": "",
            "status": "ok", "adjectives_seen_on_wikipedia": ""}
    base.update(cells)
    p = tmp_path / "c.csv"
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(base))
        w.writeheader()
        w.writerow(base)
    return p


def test_canonical_rules(tmp_path):
    ok = "stubborn; loud; loyal; impulsive; witty"
    rows, probs = dv.build_canonical(_chars(tmp_path, traits=ok, trait_evidence="q"), DESC)
    assert len(rows) == 1 and not probs and rows[0]["id"] == "can-x"
    for cells in ({"traits": ""}, {"traits": "loud; loyal"}, {"traits": ok, "trait_evidence": ""},
                  {"traits": "honest; loud; loyal; impulsive; witty", "trait_evidence": "q"},
                  {"traits": ok, "trait_evidence": "q", "status": "needs_faction_check"}):
        rows, probs = dv.build_canonical(_chars(tmp_path, **cells), DESC)
        assert not rows and len(probs) == 1, cells


def test_real_characters_file_loads():
    rows, probs = dv.build_canonical(dv.CHARS, DESC)
    assert len(rows) + len(probs) >= 25


def test_split_metrics():
    p = {"abnegation": .45, "dauntless": .35, "amity": .1, "candor": .05, "erudite": .05}
    m = dv.split_metrics(p, "dauntless|abnegation")
    assert math.isclose(m["mass"], .8) and m["topk_is_gold"] and m["top_in_gold"]
    assert math.isclose(m["balance"], .35 / .45)
    assert math.isclose(m["first_minus_second"], -.1)
    assert not m["overconfident"]
    assert dv.split_metrics({**p, "abnegation": .9, "dauntless": 0, "amity": .1}, "dauntless|abnegation")["overconfident"]


def test_correspondence_rows_sum_to_one():
    pf = {f: 1 / 5 for f in dv.DIV}
    pf2 = {**{f: 0.0 for f in dv.DIV}, "dauntless": 1.0}
    ph = {h: 1 / 4 for h in dv.HP}
    ph2 = {**{h: 0.0 for h in dv.HP}, "gryffindor": 1.0}
    C = dv.correspondence([(pf, ph), (pf2, ph2)])
    for f in dv.DIV:
        assert math.isclose(sum(C[f].values()), 1)
    assert C["dauntless"]["gryffindor"] > C["candor"]["gryffindor"]


def test_jsd_and_holm():
    p = {"a": 1.0, "b": 0.0}
    assert dv.jsd(p, p) == 0
    assert math.isclose(dv.jsd(p, {"a": 0.0, "b": 1.0}), 1)
    assert dv.holm([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])


def test_panel_distribution_applies_attention_rule():
    d = dv.panel_distribution("divergent", dv.SIM_VOTES)
    assert {"g01-div", "c01-div", "k01-div"} <= set(d)
    for dist in d.values():
        assert math.isclose(sum(dist.values()), 1)
    # 35 of 40 voters survive the pre-registered rule (DATA_LOG.md)
    assert math.isclose(min(v for v in d["k01-div"].values() if v > 0) * 35 % 1, 0, abs_tol=1e-9)
