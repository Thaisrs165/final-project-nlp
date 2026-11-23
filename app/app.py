"""The Unsure Hat: starter Gradio app (step 8, Ana).

Run from the repo root:   .venv/bin/python app/app.py      -> http://127.0.0.1:7860

Three tabs, one per research question. Every number comes from sorter.py, the same
code the experiments use, so the app and the report always agree.
  1. Sort me        quiz -> hidden trait words -> BERT's probabilities        (Q1)
  2. Trick BERT     same traits with your name / no name / another name / "not"  (Q2, Q3)
  3. Why it's unsure  BERT vs. real people vs. the simulated panel on vague items (Q3)

This is a starter: the structure works end to end; wording, styling and extra
features are up to the app owner.
"""
import csv
import json
import sys
from collections import Counter
from pathlib import Path

import gradio as gr

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import sorter  # noqa: E402

APP = ROOT / "app"
DATA = ROOT / "data"
WORLDS = json.loads((APP / "worlds.json").read_text())
QUIZ = json.loads((APP / "questions.json").read_text())
QUESTIONS = QUIZ["questions"]

# What the user picks -> sorter method. bert-mean is left out (weak baseline).
METHODS = {
    "BERT fill-in-the-blank (the model we study)": "mlm",
    "Sentence-BERT similarity": "embed",
    "NLI zero-shot (BART)": "nli",
}
WORLD_CHOICES = [(WORLDS[w]["name"], w) for w in sorter.WORLDS]


def names(world):
    return {g: WORLDS[world]["groups"][g]["name"] for g in sorter.WORLDS[world]}


def ask(traits, world, method_label, with_desc, name=None):
    """sorter.predict -> {display name: probability} for gr.Label."""
    if not traits:
        return {}
    desc = sorter.load_descriptions(world) if with_desc else None
    probs = sorter.predict(traits, world, METHODS[method_label], descriptions=desc,
                           name=name or None)["probs"]
    n = names(world)
    return {n[g]: p for g, p in probs.items()}


def split_traits(text):
    return [t.strip() for t in text.replace(";", ",").split(",") if t.strip()]


# ------------------------------------------------------------------ tab 1: quiz
def sort_me(world, method_label, with_desc, free_text, *answers):
    traits = []
    keys = Counter()
    for q, a in zip(QUESTIONS, answers):
        if not a:
            continue
        opt = next(o for o in q["options"] if o["text"] == a)
        traits += opt["traits"]
        if opt["key"].get(world):
            keys[opt["key"][world]] += 1
    traits += split_traits(free_text or "")
    if not traits:
        return {}, "Answer at least one question."
    probs = ask(traits, world, method_label, with_desc)
    seen = ", ".join(traits)
    expected = names(world)[keys.most_common(1)[0][0]] if keys else "no clear group"
    note = (f"**What BERT actually saw:** {seen}\n\n"
            f"**What the quiz designers' key expects:** {expected}\n\n"
            "BERT never sees the questions, only these words.")
    return probs, note


# ------------------------------------------------------------ tab 2: trick BERT
def trick(traits_text, name, other_name, world, method_label, with_desc):
    traits = split_traits(traits_text)
    if not traits:
        return {}, {}, {}, {}
    negated = [t if t.lower().startswith("not ") else f"not {t}" for t in traits]
    return (ask(traits, world, method_label, with_desc, name=name),
            ask(traits, world, method_label, with_desc),
            ask(traits, world, method_label, with_desc, name=other_name),
            ask(negated, world, method_label, with_desc))


# ------------------------------------------------------- tab 3: why it's unsure
def load_votes():
    items, clear = {}, {}
    with open(DATA / "vote_items.csv") as f:
        for r in csv.DictReader(f):
            if r["item_type"] in ("generic", "conflicting"):
                items[r["item_id"]] = r
            elif r["item_type"] == "clear":
                clear[r["item_id"]] = r["expected"]
    # Same pre-set attention rule as the analysis: humans flagged in human_respondents.csv;
    # simulated voters with >= 2 clear items wrong (as in make_votes.py).
    excluded = set()
    resp = DATA / "human_respondents.csv"
    if resp.exists():
        with open(resp) as f:
            excluded = {r["voter_id"] for r in csv.DictReader(f) if r.get("excluded") == "1"}
    with open(DATA / "simulated_votes.csv") as f:
        wrong = Counter(r["voter_id"] for r in csv.DictReader(f)
                        if r["item_id"] in clear and r["group"] != clear[r["item_id"]])
    excluded |= {v for v, n in wrong.items() if n >= 2}
    votes = {"human": {}, "simulated": {}}
    for src, path in (("human", DATA / "human_votes.csv"), ("simulated", DATA / "simulated_votes.csv")):
        if not path.exists():
            continue
        with open(path) as f:
            for r in csv.DictReader(f):
                if r["item_id"] in items and r["voter_id"] not in excluded:
                    votes[src].setdefault(r["item_id"], Counter())[r["group"]] += 1
    return items, votes


ITEMS, VOTES = load_votes()


def item_choices(world):
    return [(f"{i['traits'].replace(';', ',')}  ({i['item_type']})", k)
            for k, i in ITEMS.items() if i["world"] == world]


def shares(counter, world):
    total = sum(counter.values())
    n = names(world)
    return {n[g]: counter.get(g, 0) / total for g in sorter.WORLDS[world]} if total else {}


def compare(item_id, method_label, with_desc):
    if not item_id:
        return {}, {}, {}, ""
    it = ITEMS[item_id]
    w = it["world"]
    human = VOTES["human"].get(item_id, Counter())
    sim = VOTES["simulated"].get(item_id, Counter())
    note = (f"Real people: **{sum(human.values())}** answers (after the attention check). "
            f"Simulated panel: **{sum(sim.values())}** personas (simulated, not real people).")
    return ask(it["traits"], w, method_label, with_desc), shares(human, w), shares(sim, w), note


# ------------------------------------------------------------------------- UI
with gr.Blocks(title="The Unsure Hat") as demo:
    gr.Markdown("# The Unsure Hat\nDoes BERT really sort you by your personality, or by words it memorized?")
    with gr.Row():
        world = gr.Dropdown(WORLD_CHOICES, value="hp", label="World")
        method = gr.Dropdown(list(METHODS), value=list(METHODS)[0], label="Model")
        with_desc = gr.Checkbox(False, label="Tell the model what each group means (descriptions)")

    with gr.Tab("1. Sort me"):
        answers = [gr.Radio([o["text"] for o in q["options"]], label=q["text"]) for q in QUESTIONS]
        free = gr.Textbox(label=QUIZ["free_text"]["text"], placeholder=QUIZ["free_text"]["placeholder"])
        go = gr.Button("Sort me", variant="primary")
        result = gr.Label(label="BERT's answer", num_top_classes=5)
        seen = gr.Markdown()
        go.click(sort_me, [world, method, with_desc, free, *answers], [result, seen])

    with gr.Tab("2. Trick BERT"):
        gr.Markdown("Same traits, four ways. If BERT reads the traits, the first three should agree "
                    "and the last one should change.")
        traits_in = gr.Textbox("energetic, independent, forceful, funny, popular", label="Traits (comma-separated)")
        with gr.Row():
            name_in = gr.Textbox("Ginny Weasley", label="Name")
            other_in = gr.Textbox("Draco Malfoy", label="Another character's name")
        go2 = gr.Button("Compare", variant="primary")
        with gr.Row():
            out_name = gr.Label(label="With the name", num_top_classes=5)
            out_none = gr.Label(label="No name", num_top_classes=5)
            out_other = gr.Label(label="Another character's name", num_top_classes=5)
            out_neg = gr.Label(label='Every trait with "not"', num_top_classes=5)
        go2.click(trick, [traits_in, name_in, other_in, world, method, with_desc],
                  [out_name, out_none, out_other, out_neg])

    with gr.Tab("3. Why it's unsure"):
        gr.Markdown("Vague descriptions have no single right answer. A good model should be unsure "
                    "where people are unsure.")
        item = gr.Dropdown(item_choices("hp"), label="A vague or mixed description")
        go3 = gr.Button("Compare with people", variant="primary")
        with gr.Row():
            out_bert = gr.Label(label="Model", num_top_classes=5)
            out_human = gr.Label(label="Real people (form)", num_top_classes=5)
            out_sim = gr.Label(label="Simulated panel", num_top_classes=5)
        info = gr.Markdown()
        world.change(lambda w: gr.Dropdown(choices=item_choices(w), value=None), world, item)
        go3.click(compare, [item, method, with_desc], [out_bert, out_human, out_sim, info])

if __name__ == "__main__":
    demo.launch()
