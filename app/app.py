"""The Unsure Hat: Gradio app (step 8; owner Ana, quiz flow and look by Esther).

Run from the repo root:   .venv/bin/python app/app.py      -> http://127.0.0.1:7860

Three tabs, one per research question. Every number comes from sorter.py, the same
code the experiments use, so the app and the report always agree.
  1. Sort me          one question at a time -> hidden trait words -> BERT's answer   (Q1)
  2. Trick BERT       same traits with a name / no name / another name / "not"        (Q2, Q3)
  3. Why it's unsure  BERT vs. real people vs. the simulated panel on vague items      (Q3)

The hat's comments are templates filled with BERT's probabilities: no language model
writes them, so the app never claims more than the numbers say.
"""
import csv
import json
import random
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
N_Q = len(QUESTIONS)

# What the user picks -> sorter method. bert-mean is left out (weak baseline).
METHODS = {
    "BERT · fill-in-the-blank": "mlm",
    "Sentence-BERT": "embed",
    "NLI zero-shot (BART)": "nli",
}
WORLD_CHOICES = [(WORLDS[w]["name"], w) for w in sorter.WORLDS]
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII"]


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


def quiz_traits(answers, free_text):
    """Hidden trait words from the answers (+ free text) and the designers' key per world."""
    traits, keys = [], {w: Counter() for w in sorter.WORLDS}
    for q, a in zip(QUESTIONS, answers):
        if not a:
            continue
        opt = next(o for o in q["options"] if o["text"] == a)
        traits += opt["traits"]
        for w, g in opt["key"].items():
            if g and w in keys:
                keys[w][g] += 1
    return traits + split_traits(free_text or ""), keys


_CACHE = {}


def cached_probs(traits, world, method_key, with_desc):
    """{group id: p}; cached so switching world/model after the quiz is instant."""
    k = (tuple(traits), world, method_key, bool(with_desc))
    if k not in _CACHE:
        desc = sorter.load_descriptions(world) if with_desc else None
        _CACHE[k] = sorter.predict(traits, world, method_key, descriptions=desc)["probs"]
    return _CACHE[k]


def multiverse(answers, free_text, world, method_label, with_desc):
    """HTML grid: every world (rows) x our quiz key + every model (columns)."""
    traits, keys = quiz_traits(answers, free_text)
    if not traits:
        return ""

    def cell(w, g, p=None):
        grp = WORLDS[w]["groups"][g]
        pct = f"<span class='pct'>{p:.0%}</span>" if p is not None else ""
        return (f"<span class='gname'><span class='swatch' style='background:{grp['color']}'></span>"
                f"{grp['name']}</span>{pct}")

    short = {"mlm": "BERT fill-in", "embed": "Sentence-BERT", "nli": "NLI (BART)"}
    head = "".join(f"<th class='{'sel' if m == method_label else ''}' title='{m}'>{short[k]}</th>"
                   for m, k in METHODS.items())
    rows, agree = [], 0
    for w in sorter.WORLDS:
        key = keys[w].most_common(1)[0][0] if keys[w] else None
        tops = []
        tds = [f"<td class='key'>{cell(w, key) if key else '<span class=muted>no clear group</span>'}</td>"]
        for m_label, m in METHODS.items():
            probs = cached_probs(traits, w, m, with_desc)
            g = max(probs, key=probs.get)
            tops.append(g)
            tds.append(f"<td class='{'sel' if m_label == method_label else ''}'>{cell(w, g, probs[g])}</td>")
        agree += len(set(tops)) == 1
        note = ("<div class='rownote'>needs descriptions: the model has never seen these names</div>"
                if w == "invented" and not with_desc else "")
        rows.append(f"<tr class='{'cur' if w == world else ''}'><th>{WORLDS[w]['name']}{note}</th>{''.join(tds)}</tr>")
    return (f"<div class='mv'><h3>Your multiverse</h3>"
            "<p class='lead'>The same answers, sorted into every world by every model. "
            "Change <b>World</b> or <b>Model</b> at the top to see any cell in detail.</p>"
            f"<div class='mv-scroll'><table><thead><tr><th></th><th class='key'>Our quiz key</th>{head}</tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table></div>"
            f"<p class='mv-note'>The three models agree in <b>{agree} of {len(sorter.WORLDS)}</b> worlds. "
            "Where they disagree, the answer depends on <i>how</i> you ask a model, not on who you are.</p></div>")


CONSULTING = ("<div class='mv'><h3>Your multiverse</h3><p class='lead consulting'>"
              "The hat is consulting the other worlds<span class='ell'>…</span></p></div>")


def hat_voice(probs):
    """One line in the hat's voice, chosen only from the numbers."""
    if not probs:
        return ""
    ranked = sorted(probs.items(), key=lambda kv: kv[1], reverse=True)
    (top, p), (second, _) = ranked[0], ranked[1]
    if p >= 0.6:
        line = f"“{top}. There is no doubt in me.”"
    elif p >= 0.4:
        line = f"“{top}… though {second} whispers too.”"
    else:
        line = "“You are hard to read. Your words pull me in every direction.”"
    return (f"<div class='hat-line'>{line}</div>"
            f"<div class='hat-sub'>{p:.0%} sure. The hat is BERT: this is a probability over words, "
            "not an understanding of you.</div>")


def progress_html(step):
    dots = "".join(f"<span class='dot{' on' if i <= step else ''}'></span>" for i in range(N_Q))
    return (f"<div class='progress'><div class='dots'>{dots}</div>"
            f"<div class='count'>{ROMAN[step]} &nbsp;/&nbsp; {ROMAN[N_Q - 1]}</div></div>")


def question_view(step, answers):
    q = QUESTIONS[step]
    opts = [o["text"] for o in q["options"]]
    random.shuffle(opts)  # option order shouldn't hint at a group
    return (progress_html(step), f"<div class='q-text'>{q['text']}</div>",
            gr.Radio(choices=opts, value=answers[step], label=None, show_label=False))


def begin():
    answers = [None] * N_Q
    return (0, answers, gr.Column(visible=False), gr.Column(visible=True), gr.Column(visible=False),
            gr.Column(visible=False), *question_view(0, answers))


def go_next(choice, step, answers):
    if not choice:
        gr.Warning("Choose an answer first. The hat is waiting.")
        return (step, answers, gr.Column(), gr.Column(), gr.update(), gr.update(), gr.update())
    answers = list(answers)
    answers[step] = choice
    if step + 1 == N_Q:
        return (step, answers, gr.Column(visible=False), gr.Column(visible=True),
                gr.update(), gr.update(), gr.update())
    return (step + 1, answers, gr.Column(visible=True), gr.Column(visible=False),
            *question_view(step + 1, answers))


def go_back(step, answers):
    step = max(0, step - 1)
    return (step, answers, *question_view(step, answers))


def back_from_final(step, answers):
    return (step, answers, gr.Column(visible=True), gr.Column(visible=False),
            *question_view(step, answers))


def detail(answers, free_text, world, method_label, with_desc):
    """The big answer for the world and model chosen at the top."""
    traits, keys = quiz_traits(answers, free_text)
    if not traits:
        return "", {}, "", "Answer at least one question."
    p = cached_probs(traits, world, METHODS[method_label], with_desc)
    n = names(world)
    probs = {n[g]: v for g, v in p.items()}
    expected = n[keys[world].most_common(1)[0][0]] if keys[world] else "no clear group"
    title = (f"<div class='detail-title'>{WORLDS[world]['name']} "
             f"<span>· according to {method_label}</span></div>")
    note = (f"**What BERT actually saw:** {', '.join(traits)}\n\n"
            f"**What our quiz key expected in {WORLDS[world]['name']}:** {expected}\n\n"
            "The models never see the questions, only these words.")
    return title, probs, hat_voice(probs), note


def reveal(world, method_label, with_desc, free_text, answers):
    title, probs, voice, note = detail(answers, free_text, world, method_label, with_desc)
    return (True, gr.Column(visible=False), gr.Column(visible=True), title, probs, voice, note, CONSULTING)


def refresh(revealed, answers, free_text, world, method_label, with_desc):
    """World/model/descriptions changed after the quiz: recompute, no need to retake it."""
    if not revealed:
        return gr.update(), gr.update(), gr.update(), gr.update()
    return detail(answers, free_text, world, method_label, with_desc)


def refresh_grid(revealed, answers, free_text, world, method_label, with_desc):
    if not revealed:
        return gr.update()
    return multiverse(answers, free_text, world, method_label, with_desc)


def again():
    return (False, gr.Column(visible=True), gr.Column(visible=False), gr.Column(visible=False),
            gr.Column(visible=False))


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


# ------------------------------------------------------------------- look & feel
INK, SURFACE, SURFACE2, LINE = "#0b0912", "#15111f", "#1d1729", "#2e2540"
TEXT, MUTED, GOLD, GOLD_HI = "#ece6f5", "#a79cbd", "#d9b26a", "#ecc98a"


def _both(**kw):
    """Same value in light and dark mode, so the app is dark whatever the browser prefers."""
    out = {}
    for k, v in kw.items():
        out[k] = v
        if k not in ("color_accent",):
            out[k + "_dark"] = v
    return out


THEME = gr.themes.Base(
    primary_hue="amber", neutral_hue="slate",
    font=[gr.themes.GoogleFont("Inter"), "system-ui", "sans-serif"],
).set(**_both(
    body_background_fill=INK, body_text_color=TEXT, body_text_color_subdued=MUTED,
    background_fill_primary=SURFACE, background_fill_secondary=SURFACE2,
    border_color_primary=LINE, border_color_accent=GOLD, panel_background_fill=SURFACE,
    block_background_fill=SURFACE, block_border_color=LINE,
    block_label_background_fill=SURFACE2, block_label_text_color=MUTED,
    block_title_text_color=TEXT, block_info_text_color=MUTED,
    input_background_fill=SURFACE2, input_border_color=LINE, input_placeholder_color="#6f6585",
    button_primary_background_fill=f"linear-gradient(135deg, {GOLD}, #b8893f)",
    button_primary_background_fill_hover=f"linear-gradient(135deg, {GOLD_HI}, {GOLD})",
    button_primary_text_color="#1a1206",
    button_secondary_background_fill="transparent",
    button_secondary_background_fill_hover=SURFACE2,
    button_secondary_text_color=TEXT, button_secondary_border_color=LINE,
    color_accent=GOLD, color_accent_soft="rgba(217,178,106,.14)",
    checkbox_background_color=SURFACE2, checkbox_background_color_selected=GOLD,
    checkbox_border_color=LINE,
    checkbox_label_background_fill=SURFACE2,
    checkbox_label_background_fill_hover="#241d33",
    checkbox_label_background_fill_selected="rgba(217,178,106,.16)",
    checkbox_label_border_color=LINE,
    checkbox_label_text_color=TEXT, checkbox_label_text_color_selected=GOLD_HI,
    link_text_color=GOLD,
))

HEAD = ("<link rel='preconnect' href='https://fonts.googleapis.com'>"
        "<link href='https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700&display=swap' "
        "rel='stylesheet'>")

CSS = f"""
/* night sky behind everything */
body, .gradio-container {{ background:
    radial-gradient(1200px 600px at 50% -10%, rgba(124,92,255,.18), transparent 60%),
    radial-gradient(900px 500px at 90% 110%, rgba(217,178,106,.08), transparent 60%),
    {INK} !important; }}
.gradio-container {{ max-width: 980px !important; margin: 0 auto; min-width: 0 !important; width: 100%; }}
.gradio-container .main, .gradio-container main, .gradio-container .column {{ min-width: 0 !important; }}
footer {{ opacity: .35; }}

/* title */
#hat-title {{ text-align: center; padding: 28px 0 6px; }}
#hat-title h1 {{ font-family: 'Cinzel', serif; font-weight: 700; letter-spacing: .14em;
    font-size: 2.6rem; margin: 0; color: {GOLD_HI};
    text-shadow: 0 0 24px rgba(217,178,106,.35); animation: flicker 6s ease-in-out infinite; }}
#hat-title p {{ color: {MUTED}; margin: 8px 0 0; font-style: italic; }}
@keyframes flicker {{ 0%,100% {{ text-shadow: 0 0 22px rgba(217,178,106,.30); }}
    45% {{ text-shadow: 0 0 34px rgba(217,178,106,.55); }} 55% {{ text-shadow: 0 0 18px rgba(217,178,106,.25); }} }}

/* settings strip */
/* no backdrop-filter / transform / filter here: they would trap the dropdown lists
   (position: fixed) inside this strip, so they'd open in the wrong place, behind the cards */
#controls {{ border: 1px solid {LINE}; border-radius: 14px; background: rgba(21,17,31,.92);
    align-items: center; }}
#desc-toggle {{ align-self: center; }}

/* tabs */
.tab-nav button, button[role="tab"] {{ font-family: 'Cinzel', serif !important; letter-spacing: .08em;
    color: {MUTED} !important; }}
.tab-nav button.selected, button[role="tab"][aria-selected="true"] {{ color: {GOLD_HI} !important;
    border-color: {GOLD} !important; }}

/* cards */
.card {{ border: 1px solid {LINE} !important; border-radius: 18px !important;
    background: linear-gradient(180deg, rgba(29,23,41,.92), rgba(21,17,31,.92)) !important;
    box-shadow: 0 20px 60px rgba(0,0,0,.45), inset 0 1px 0 rgba(255,255,255,.03);
    padding: 26px 28px !important; }}
.card h2, .card h3 {{ font-family: 'Cinzel', serif; color: {GOLD_HI}; letter-spacing: .06em; }}
.lead {{ color: {MUTED}; font-size: 1.02rem; line-height: 1.6; }}

/* quiz */
.progress {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; }}
.dots {{ display: flex; gap: 6px; }}
.dot {{ width: 8px; height: 8px; border-radius: 50%; background: {LINE}; transition: all .4s; }}
.dot.on {{ background: {GOLD}; box-shadow: 0 0 10px rgba(217,178,106,.6); }}
.count {{ font-family: 'Cinzel', serif; color: {MUTED}; letter-spacing: .12em; font-size: .9rem; }}
.q-text {{ font-family: 'Cinzel', serif; font-size: 1.45rem; line-height: 1.45; color: {TEXT};
    margin: 4px 0 18px; }}
#q-choices label {{ padding: 14px 16px !important; border-radius: 12px !important; width: 100%;
    transition: transform .2s, border-color .2s, background .2s; }}
#q-choices label:hover {{ transform: translateX(4px); border-color: {GOLD} !important; }}
#q-choices .wrap {{ flex-direction: column; gap: 10px; }}

/* the hat speaks */
.hat-line {{ font-family: 'Cinzel', serif; font-size: 1.35rem; color: {GOLD_HI}; text-align: center;
    margin: 6px 0 4px; }}
.hat-sub {{ text-align: center; color: {MUTED}; font-size: .88rem; }}

/* intro steps */
.steps {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 6px 0 4px; }}
.steps span {{ border: 1px solid {LINE}; border-radius: 999px; padding: 4px 12px; color: {MUTED};
    font-size: .85rem; background: rgba(255,255,255,.02); }}

/* detail header */
.detail-title {{ font-family: 'Cinzel', serif; color: {MUTED}; text-align: center; letter-spacing: .08em;
    font-size: .95rem; }}
.detail-title span {{ font-family: Inter, sans-serif; font-size: .85rem; letter-spacing: 0; }}

/* the multiverse grid */
.mv h3 {{ margin-top: 0; }}
.mv-scroll {{ overflow-x: auto; margin: 10px 0 6px; }}
.mv table {{ width: 100%; border-collapse: collapse !important; border: none !important;
    font-size: .88rem; table-layout: fixed; }}
.mv th, .mv td {{ padding: 9px 10px !important; border: none !important;
    border-bottom: 1px solid {LINE} !important; text-align: left; vertical-align: top; background: none; }}
.mv tbody th {{ width: 24%; }}
.mv thead, .mv tbody, .mv tr {{ border: none !important; box-shadow: none !important; }}
.mv tbody tr:last-child th, .mv tbody tr:last-child td {{ border-bottom: none !important; }}
.gname {{ display: inline-block; padding-left: 16px; text-indent: -16px; }}
.mv td .pct {{ display: block; margin: 2px 0 0 16px; }}
.mv thead th {{ font-family: 'Cinzel', serif; font-weight: 500; color: {MUTED}; font-size: .78rem;
    letter-spacing: .06em; border-bottom: 1px solid {GOLD}44; }}
.mv tbody th {{ font-family: 'Cinzel', serif; color: {TEXT}; font-weight: 500; }}
.mv td.key {{ color: {MUTED}; }}
.mv .sel {{ background: rgba(217,178,106,.06); }}
.mv tr.cur th, .mv tr.cur td {{ background: rgba(124,92,255,.10); }}
.mv tr.cur td.sel {{ background: rgba(217,178,106,.16); box-shadow: inset 0 0 0 1px {GOLD}88; }}
.swatch {{ display: inline-block; width: 9px; height: 9px; border-radius: 50%; margin-right: 7px;
    vertical-align: middle; box-shadow: 0 0 6px rgba(255,255,255,.15); }}
.gname {{ color: {TEXT}; }}
.pct {{ color: {MUTED}; margin-left: 6px; font-variant-numeric: tabular-nums; font-size: .82rem; }}
.rownote {{ font-family: Inter, sans-serif; font-size: .72rem; color: #c9a25a; white-space: normal;
    max-width: 180px; margin-top: 3px; }}
.mv-note {{ color: {MUTED}; font-size: .9rem; margin: 10px 0 0; }}
.muted {{ color: {MUTED}; }}
.consulting {{ text-align: center; padding: 18px 0; }}
.ell {{ display: inline-block; animation: breathe 1.4s ease-in-out infinite; }}
@keyframes breathe {{ 0%,100% {{ opacity: .2; }} 50% {{ opacity: 1; }} }}
.reveal .mv tbody tr {{ animation: rise .5s cubic-bezier(.2,.7,.2,1) both; }}
.reveal .mv tbody tr:nth-child(2) {{ animation-delay: .08s; }}
.reveal .mv tbody tr:nth-child(3) {{ animation-delay: .16s; }}
.reveal .mv tbody tr:nth-child(4) {{ animation-delay: .24s; }}
.reveal .mv tbody tr:nth-child(5) {{ animation-delay: .32s; }}

/* probability labels (all tabs) */
.output-class {{ font-family: 'Cinzel', serif !important; color: {GOLD_HI} !important;
    text-shadow: 0 0 18px rgba(217,178,106,.3); }}
.confidence-set .bar, .confidence .bar {{ background: linear-gradient(90deg, #7c5cff, {GOLD}) !important; }}

/* dropdown menus get a solid background (was transparent) */
ul.options, .options {{ background: {SURFACE2} !important; border: 1px solid {LINE} !important; }}
ul.options li:hover, .options .item:hover {{ background: #2a2238 !important; }}

/* entrance animations, restarted from JS on every step */
.reveal {{ animation: rise .65s cubic-bezier(.2,.7,.2,1) both; }}
.reveal #q-choices label {{ animation: rise .55s cubic-bezier(.2,.7,.2,1) both; }}
.reveal #q-choices label:nth-child(1) {{ animation-delay: .12s; }}
.reveal #q-choices label:nth-child(2) {{ animation-delay: .20s; }}
.reveal #q-choices label:nth-child(3) {{ animation-delay: .28s; }}
.reveal #q-choices label:nth-child(4) {{ animation-delay: .36s; }}
@keyframes rise {{ from {{ opacity: 0; transform: translateY(14px); filter: blur(4px); }}
    to {{ opacity: 1; transform: none; filter: none; }} }}
.glow {{ animation: glow 1.6s ease-out both; }}
@keyframes glow {{ 0% {{ opacity: 0; transform: scale(.97); filter: blur(6px); }}
    60% {{ opacity: 1; box-shadow: 0 0 80px rgba(217,178,106,.25); }}
    100% {{ transform: none; filter: none; }} }}
#controls {{ flex-wrap: wrap !important; }}
@media (max-width: 640px) {{
    #hat-title h1 {{ font-size: 1.7rem; letter-spacing: .08em; }}
    .q-text {{ font-size: 1.15rem; }}
    .card {{ padding: 18px 16px !important; }}
    #controls .form > .block {{ min-width: 100% !important; flex-basis: 100% !important; }}
    .mv table {{ min-width: 600px; }}
    .mv-scroll::before {{ content: "swipe sideways to see every model →"; display: block;
        color: {MUTED}; font-size: .75rem; margin-bottom: 6px; position: sticky; left: 0; }}
}}
@media (prefers-reduced-motion: reduce) {{
    *, *::before, *::after {{ animation: none !important; transition: none !important; }} }}
"""

# Restart the entrance animation on whichever card is visible.
ANIMATE = """() => {
  for (const id of ['intro-card','q-card','final-card','result-card','mv-card','trick-out','unsure-out']) {
    const el = document.getElementById(id);
    if (!el || el.offsetParent === null) continue;
    const cls = id === 'result-card' ? 'glow' : 'reveal';
    el.classList.remove('reveal', 'glow'); void el.offsetWidth; el.classList.add(cls);
  }
}"""
FORCE_DARK = "() => { document.body.classList.add('dark'); }"

# ------------------------------------------------------------------------- UI
with gr.Blocks(title="The Unsure Hat") as demo:
    gr.HTML("<div id='hat-title'><h1>THE UNSURE HAT</h1>"
            "<p>Does BERT really sort you by your personality, or by words it memorized?</p></div>")
    with gr.Row(elem_id="controls"):
        world = gr.Dropdown(WORLD_CHOICES, value="hp", label="World", scale=1, min_width=170)
        method = gr.Dropdown(list(METHODS), value=list(METHODS)[0], label="Model", scale=1, min_width=230)
        with_desc = gr.Checkbox(False, label="Tell the model what each group means", scale=1,
                                min_width=230, elem_id="desc-toggle")

    # ---- I. Sort me
    with gr.Tab("I · Sort me"):
        step = gr.State(0)
        answers = gr.State([None] * N_Q)
        revealed = gr.State(False)

        with gr.Column(elem_id="intro-card", elem_classes="card") as intro_col:
            gr.HTML("<h2>One test. Five worlds. Three minds.</h2>"
                    f"<p class='lead'>Answer {N_Q} questions once, by instinct. The hat then sorts you "
                    "into <b>every world at the same time</b>: a Hogwarts house, a Divergent faction, "
                    "a Great House of Westeros, a nation of Avatar, and a world we made up. "
                    "Three different models do the sorting, and you'll see all their answers side by side.</p>"
                    "<p class='lead'>Each answer hides two words, and those words are <b>all</b> the models "
                    "ever see of you: no questions, no name.</p>"
                    "<div class='steps'><span>① 12 questions</span><span>② your answer in one world</span>"
                    "<span>③ the grid of every world × every model</span></div>")
            start = gr.Button("Put on the hat", variant="primary", size="lg")

        with gr.Column(elem_id="q-card", elem_classes="card", visible=False) as q_col:
            progress = gr.HTML()
            q_text = gr.HTML()
            q_radio = gr.Radio([], show_label=False, elem_id="q-choices")
            with gr.Row():
                back = gr.Button("← Back", variant="secondary")
                nxt = gr.Button("Continue →", variant="primary")

        with gr.Column(elem_id="final-card", elem_classes="card", visible=False) as final_col:
            gr.HTML("<h2>One last thing.</h2>"
                    "<p class='lead'>If you like, describe yourself in a few words, the way a friend "
                    "would. Or leave it empty and let your answers speak.</p>")
            free = gr.Textbox(show_label=False, placeholder=QUIZ["free_text"]["placeholder"])
            with gr.Row():
                back_final = gr.Button("← Back", variant="secondary")
                go = gr.Button("Sort me into every world", variant="primary")

        with gr.Column(elem_id="result-card", elem_classes="card", visible=False) as result_col:
            detail_title = gr.HTML()
            voice = gr.HTML()
            result = gr.Label(show_label=False, num_top_classes=5)
            seen = gr.Markdown()
        with gr.Column(elem_id="mv-card", elem_classes="card", visible=False) as mv_col:
            grid = gr.HTML()
            restart = gr.Button("Sit down again", variant="secondary")

        start.click(begin, None, [step, answers, intro_col, q_col, final_col, result_col,
                                  progress, q_text, q_radio]).then(None, js=ANIMATE)
        nxt.click(go_next, [q_radio, step, answers],
                  [step, answers, q_col, final_col, progress, q_text, q_radio]).then(None, js=ANIMATE)
        back.click(go_back, [step, answers], [step, answers, progress, q_text, q_radio]).then(None, js=ANIMATE)
        back_final.click(back_from_final, [step, answers],
                         [step, answers, q_col, final_col, progress, q_text, q_radio]).then(None, js=ANIMATE)
        go.click(reveal, [world, method, with_desc, free, answers],
                 [revealed, final_col, result_col, detail_title, result, voice, seen, grid]
                 ).then(lambda: gr.Column(visible=True), None, mv_col
                 ).then(None, js=ANIMATE
                 ).then(multiverse, [answers, free, world, method, with_desc], grid)
        restart.click(again, None, [revealed, intro_col, q_col, final_col, result_col]
                      ).then(lambda: gr.Column(visible=False), None, mv_col).then(None, js=ANIMATE)
        # After the quiz, the controls at the top re-sort the same answers: no need to retake it.
        for ctl in (world, method, with_desc):
            ctl.change(refresh, [revealed, answers, free, world, method, with_desc],
                       [detail_title, result, voice, seen]
                       ).then(refresh_grid, [revealed, answers, free, world, method, with_desc], grid)

    # ---- II. Trick BERT
    with gr.Tab("II · Trick BERT"):
        with gr.Column(elem_classes="card"):
            gr.HTML("<h2>Same person, four disguises</h2>"
                    "<p class='lead'>If the hat really reads traits, the first three should agree, "
                    "and adding <i>not</i> to every trait should change its mind.</p>")
            traits_in = gr.Textbox("energetic, independent, forceful, funny, popular", label="Traits (comma-separated)")
            with gr.Row():
                name_in = gr.Textbox("Ginny Weasley", label="Name")
                other_in = gr.Textbox("Draco Malfoy", label="Another character's name")
            go2 = gr.Button("Show the four answers", variant="primary")
        with gr.Column(elem_id="trick-out"):
            with gr.Row():
                out_name = gr.Label(label="With the name", num_top_classes=5)
                out_none = gr.Label(label="No name", num_top_classes=5)
            with gr.Row():
                out_other = gr.Label(label="Another character's name", num_top_classes=5)
                out_neg = gr.Label(label='Every trait with "not"', num_top_classes=5)
        go2.click(trick, [traits_in, name_in, other_in, world, method, with_desc],
                  [out_name, out_none, out_other, out_neg]).then(None, js=ANIMATE)

    # ---- III. Why it's unsure
    with gr.Tab("III · Why it's unsure"):
        with gr.Column(elem_classes="card"):
            gr.HTML("<h2>Where people hesitate</h2>"
                    "<p class='lead'>Vague descriptions have no single right answer. A good model "
                    "should be unsure exactly where people are unsure.</p>")
            item = gr.Dropdown(item_choices("hp"), label="A vague or mixed description")
            go3 = gr.Button("Compare with people", variant="primary")
        with gr.Column(elem_id="unsure-out"):
            with gr.Row():
                out_bert = gr.Label(label="Model", num_top_classes=5)
                out_human = gr.Label(label="Real people (form)", num_top_classes=5)
                out_sim = gr.Label(label="Simulated panel", num_top_classes=5)
            info = gr.Markdown()
        world.change(lambda w: gr.Dropdown(choices=item_choices(w), value=None), world, item)
        go3.click(compare, [item, method, with_desc], [out_bert, out_human, out_sim, info]).then(None, js=ANIMATE)

def _warm_up():
    """Load every model once in the background, so the first quiz isn't slow."""
    for m in METHODS.values():
        try:
            sorter.predict(["calm"], "hp", m)
        except Exception as e:  # never block the app on this
            print("warm-up skipped:", m, e)


if __name__ == "__main__":
    import threading
    threading.Thread(target=_warm_up, daemon=True).start()
    demo.launch(theme=THEME, css=CSS, head=HEAD, js=FORCE_DARK)
