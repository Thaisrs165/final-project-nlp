"""Tests for sorter.py (IMPLEMENTATION.md, step 3).

Fast tests run without any model. Tests marked `models` load BERT, MiniLM and
BART-MNLI. Run only the fast ones with:  pytest -m "not models"
"""
import math
import time

import pytest

import sorter

# Descriptions of the invented world (our own definitions, see DATA_LOG.md).
INVENTED = {
    "veltrin": "patient, observant, methodical, reserved",
    "osmark": "warm, generous, sociable, forgiving",
    "calwen": "restless, curious, independent, spontaneous",
    "durrask": "disciplined, competitive, proud, determined",
}
HP_DESC = {
    "gryffindor": "bravery, daring, chivalry",
    "ravenclaw": "intelligence, wit, love of learning",
    "hufflepuff": "loyalty, hard work, fairness",
    "slytherin": "ambition, cunning, resourcefulness",
}


# ---------------------------------------------------------------- fast tests
def test_parse_and_format_traits():
    assert sorter.parse_traits("brave; loyal ;reckless") == ["brave", "loyal", "reckless"]
    assert sorter.parse_traits("brave, loyal") == ["brave", "loyal"]
    assert sorter.parse_traits("always tells the truth, even when it hurts; kind") == [
        "always tells the truth, even when it hurts", "kind"]
    assert sorter.format_traits(["brave"]) == "brave"
    assert sorter.format_traits(["brave", "loyal"]) == "brave and loyal"
    assert sorter.format_traits(["brave", "loyal", "reckless"]) == "brave, loyal and reckless"
    assert sorter.format_traits([]) == sorter.CONTENT_FREE


def test_l2r_mask_plan():
    # one word in 3 pieces: each piece is scored with itself and the later pieces masked
    assert sorter.l2r_mask_plan([0, 0, 0]) == [[0, 1, 2], [1, 2], [2]]
    # two words ("Fire Nation"): masking never crosses into the other word
    assert sorter.l2r_mask_plan([0, 1]) == [[0], [1]]
    assert sorter.l2r_mask_plan([0, 0, 1, 1]) == [[0, 1], [1], [2, 3], [3]]


def test_names_cover_every_group():
    for world, groups in sorter.WORLDS.items():
        assert set(sorter.NAMES[world]) == set(groups), world


def test_to_probs_and_entropy():
    p = sorter.to_probs({"a": 1.0, "b": 1.0, "c": 1.0, "d": 1.0})
    assert math.isclose(sum(p.values()), 1)
    assert math.isclose(sorter.entropy(p), 1.0)
    q = sorter.to_probs({"a": 100.0, "b": 0.0})
    assert sorter.entropy(q) < 1e-6 and sorter.top(q) == "a"


def test_context_lists_every_group():
    ctx = sorter._context("invented", INVENTED)
    for g in INVENTED:
        assert sorter.NAMES["invented"][g] in ctx
    assert sorter._context("invented", None) == ""


def test_load_descriptions_fails_loudly_when_missing(tmp_path, monkeypatch):
    (tmp_path / "hp").mkdir()
    (tmp_path / "hp" / "groups.csv").write_text("group,description,source_url\n")
    monkeypatch.setattr(sorter, "DATA_DIR", tmp_path)
    with pytest.raises(ValueError):
        sorter.load_descriptions("hp")


# --------------------------------------------------------------- model tests
@pytest.mark.models
def test_every_group_name_is_found_in_the_prompt():
    for world, groups in sorter.WORLDS.items():
        for g in groups:
            pieces = sorter.name_pieces(world, g)
            assert pieces, (world, g)
            joined = "".join(p.removeprefix("##") for p in pieces)
            assert joined == sorter.NAMES[world][g].lower().replace(" ", ""), (world, g, pieces)


@pytest.mark.models
@pytest.mark.parametrize("method", sorter.METHODS)
@pytest.mark.parametrize("desc", [None, HP_DESC])
def test_probs_sum_to_one(method, desc):
    out = sorter.predict(["brave", "loyal"], "hp", method, descriptions=desc)
    for key in ("probs", "raw_probs"):
        assert set(out[key]) == set(sorter.WORLDS["hp"])
        assert math.isclose(sum(out[key].values()), 1, abs_tol=1e-6)


@pytest.mark.models
@pytest.mark.parametrize("world,desc", [("hp", None), ("hp", HP_DESC), ("invented", INVENTED)])
@pytest.mark.parametrize("template", range(len(sorter.TEMPLATES)))
def test_calibrated_content_free_prompt_is_uniform(world, desc, template):
    out = sorter.predict([sorter.CONTENT_FREE], world, "mlm", template=template, descriptions=desc)
    k = len(sorter.WORLDS[world])
    for p in out["probs"].values():
        assert math.isclose(p, 1 / k, abs_tol=1e-6)


@pytest.mark.models
@pytest.mark.parametrize("method", sorter.METHODS)
def test_deterministic(method):
    a = sorter.predict(["curious", "kind"], "invented", method, descriptions=INVENTED)["probs"]
    b = sorter.predict(["curious", "kind"], "invented", method, descriptions=INVENTED)["probs"]
    for g in a:
        assert math.isclose(a[g], b[g], abs_tol=1e-5)


@pytest.mark.models
def test_occlusion_shape():
    traits = ["brave", "loyal", "reckless"]
    occ = sorter.occlusion(traits, "hp", "mlm")
    assert [o["trait"] for o in occ] == traits
    for o in occ:
        assert -1 <= o["delta"] <= 1
        assert o["flips_to"] is None or o["flips_to"] in sorter.WORLDS["hp"]


@pytest.mark.models
def test_one_call_is_fast_enough():
    sorter.predict(["brave"], "hp", "mlm")  # warm-up (model load)
    t = time.perf_counter()
    sorter.predict(["brave", "daring", "bold"], "hp", "mlm")
    assert time.perf_counter() - t < 2.0


@pytest.mark.models
def test_sanity_brave_daring_bold():
    """The obvious case from the plan: Gryffindor should be in the top 2.
    A failure here is a RESULT to report, not necessarily a bug, so check the
    numbers by hand before changing any code."""
    p = sorter.predict(["brave", "daring", "bold"], "hp", "mlm")["probs"]
    assert "gryffindor" in sorted(p, key=p.get, reverse=True)[:2], p
