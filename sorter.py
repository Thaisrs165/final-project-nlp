"""Shared scoring code for "Does BERT actually sort you?".

Every experiment, notebook and the app import from here, so nobody writes their
own version of a method (IMPLEMENTATION.md, step 3).

Main entry point
----------------
    predict(traits, world, method, template=0, descriptions=None, calibrate=True, name=None)
        -> {"probs": {group: p}, "raw_probs": {group: p}, "scores": {group: s}}

    method:
      "mlm"        fill-in-the-blank with BERT, scored with PLL-word-l2r
      "embed"      cosine similarity with Sentence-BERT (MiniLM)
      "bert-mean"  cosine similarity with raw BERT mean-pooling (weak baseline)
      "nli"        zero-shot NLI with BART-MNLI

    descriptions: None, or {group: description} (see load_descriptions).
      Every method runs in two variants (decision 2026-11-18, DATA_LOG.md):
        without descriptions -> the model only sees the group NAMES
                                (memory + whatever the name itself means)
        with descriptions    -> the group descriptions are also given
                                (the model can read what each group stands for)
      The invented world only makes sense WITH descriptions: BERT has never seen
      "Veltrin", so without them it can only guess.

    name: None, or a character name (research question 2: traits vs. names).
      None   -> "Someone who is brave, loyal and kind belongs to Gryffindor."
      "Ginny Weasley" -> "Ginny Weasley, who is brave, loyal and kind, belongs to Gryffindor."
      Every template has a named twin in NAMED_TEMPLATES (same index). For the
      calibration prior the name is replaced by "N/A" too, so calibration removes
      the template's bias but NOT the information carried by the name.

Other helpers: entropy, top, occlusion, load_descriptions, format_traits.
"""
from __future__ import annotations

import csv
import math
from functools import lru_cache
from pathlib import Path

# ---- Models (pinned in ONE place) -------------------------------------------
MLM_MODEL = "bert-base-uncased"                         # main subject of the study
MLM_LARGE_MODEL = "bert-large-uncased"                  # fix B (2026-11-23): does size help?
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"   # Sentence-BERT similarity
NLI_MODEL = "facebook/bart-large-mnli"                  # zero-shot NLI baseline

# ---- Worlds and their group ids (must match data/<world>/groups.csv) ---------
WORLDS = {
    "hp": ["gryffindor", "ravenclaw", "hufflepuff", "slytherin"],
    "divergent": ["abnegation", "amity", "candor", "dauntless", "erudite"],
    "got": ["stark", "lannister", "targaryen", "greyjoy", "tyrell"],
    "avatar": ["fire", "water", "earth", "air"],
    "invented": ["veltrin", "osmark", "calwen", "durrask"],
}

# The surface text the models read for each group id.
NAMES = {
    "hp": {"gryffindor": "Gryffindor", "ravenclaw": "Ravenclaw",
           "hufflepuff": "Hufflepuff", "slytherin": "Slytherin"},
    "divergent": {"abnegation": "Abnegation", "amity": "Amity", "candor": "Candor",
                  "dauntless": "Dauntless", "erudite": "Erudite"},
    "got": {"stark": "Stark", "lannister": "Lannister", "targaryen": "Targaryen",
            "greyjoy": "Greyjoy", "tyrell": "Tyrell"},
    "avatar": {"fire": "Fire Nation", "water": "Water Tribe",
               "earth": "Earth Kingdom", "air": "Air Nomads"},
    "invented": {"veltrin": "Veltrin", "osmark": "Osmark",
                 "calwen": "Calwen", "durrask": "Durrask"},
}

# ---- Prompt templates for the fill-in-the-blank method ----------------------
TEMPLATES = [
    "Someone who is {traits} belongs to {group}.",
    "A person described as {traits} would be sorted into {group}.",
    "{traits}: this sounds like a member of {group}.",
]
# Same prompts with a character name (decision 2026-11-21, DATA_LOG.md). Index i
# here is the named twin of TEMPLATES[i].
NAMED_TEMPLATES = [
    "{name}, who is {traits}, belongs to {group}.",
    "{name}, described as {traits}, would be sorted into {group}.",
    "{name} is {traits}: this sounds like a member of {group}.",
]
CONTENT_FREE = "N/A"  # used for calibration (Zhao et al. 2021)

# Cosine similarities all sit in a narrow band, so a plain softmax over them is
# almost uniform. We divide by a fixed temperature before the softmax. It is a
# constant chosen once (same value as common contrastive setups), never tuned on
# our results. Entropies are only compared WITHIN a method, never across methods.
EMBED_TEMPERATURE = 0.05

METHODS = ("mlm", "embed", "bert-mean", "nli")
# Fixes for the MLM collapse, fixed in DATA_LOG.md BEFORE they were run (2026-11-23).
# Each is reported next to plain "mlm", which stays the baseline.
#   method          model            calibration prior
MLM_VARIANTS = {
    "mlm":           (MLM_MODEL,       "na"),     # traits "N/A" (and name "N/A" if named)
    "mlm-cal":       (MLM_MODEL,       "multi"),  # fix A: mean over CF_TRAITS x CF_NAMES
    "mlm-large":     (MLM_LARGE_MODEL, "na"),     # fix B
    "mlm-large-cal": (MLM_LARGE_MODEL, "multi"),  # fix A + B
}
FIX_METHODS = ("mlm-cal", "mlm-large", "mlm-large-cal")
CF_TRAITS = ("N/A", "[MASK]", "")            # Zhao et al. 2021's content-free inputs
CF_NAMES = ("N/A", "Alex", "Sam", "Jordan")  # neutral names, for named prompts only
SEED = 42
DATA_DIR = Path(__file__).resolve().parent / "data"
BATCH_SIZE = 64


# =============================================================================
# Inputs
# =============================================================================
def parse_traits(traits) -> list[str]:
    """Accept a list, or a string separated by ';' (preferred) or ','."""
    if isinstance(traits, str):
        sep = ";" if ";" in traits else ","
        traits = traits.split(sep)
    return [t.strip() for t in traits if t and t.strip()]


def format_traits(traits) -> str:
    """['brave', 'loyal', 'reckless'] -> 'brave, loyal and reckless'."""
    ts = parse_traits(traits)
    if not ts:
        return CONTENT_FREE
    if len(ts) == 1:
        return ts[0]
    return ", ".join(ts[:-1]) + " and " + ts[-1]


def load_descriptions(world: str) -> dict[str, str]:
    """Read data/<world>/groups.csv -> {group: description}. Fails loudly if incomplete."""
    path = DATA_DIR / world / "groups.csv"
    with open(path, newline="") as f:
        rows = {r["group"].strip(): r["description"].strip() for r in csv.DictReader(f)}
    missing = [g for g in WORLDS[world] if not rows.get(g)]
    if missing:
        raise ValueError(f"{path}: no description for {missing} (step 2.1 not done yet?)")
    return {g: rows[g] for g in WORLDS[world]}


def person(traits, name=None) -> str:
    """The person sentence used by the embedding and NLI methods."""
    if name:
        return f"{name}, who is {format_traits(traits)}."
    return f"Someone who is {format_traits(traits)}."


def _context(world: str, descriptions: dict[str, str] | None) -> str:
    """Text placed before the prompt when descriptions are used."""
    if not descriptions:
        return ""
    return " ".join(f"{NAMES[world][g]}: {descriptions[g].rstrip('.')}." for g in WORLDS[world]) + " "


# =============================================================================
# Models (loaded lazily, once)
# =============================================================================
def _device():
    import torch
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


@lru_cache(maxsize=None)
def _mlm(model_name: str = MLM_MODEL):
    import torch
    from transformers import AutoModelForMaskedLM, AutoTokenizer
    torch.manual_seed(SEED)
    tok = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForMaskedLM.from_pretrained(model_name).to(_device()).eval()
    return tok, model


@lru_cache(maxsize=None)
def _bert_encoder():
    import torch
    from transformers import AutoModel, AutoTokenizer
    torch.manual_seed(SEED)
    tok = AutoTokenizer.from_pretrained(MLM_MODEL)
    model = AutoModel.from_pretrained(MLM_MODEL).to(_device()).eval()
    return tok, model


@lru_cache(maxsize=None)
def _sbert():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(EMBED_MODEL, device=str(_device()))


@lru_cache(maxsize=None)
def _nli():
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    torch.manual_seed(SEED)
    tok = AutoTokenizer.from_pretrained(NLI_MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(NLI_MODEL).to(_device()).eval()
    labels = {v.lower(): k for k, v in model.config.id2label.items()}
    return tok, model, labels["entailment"]


# =============================================================================
# Method 1: fill-in-the-blank, scored with PLL-word-l2r (Kauf & Ivanova 2023)
# =============================================================================
def l2r_mask_plan(word_ids: list[int]) -> list[list[int]]:
    """For each word piece of the group name, which pieces to mask when scoring it.

    word_ids gives, for each piece of the name, the word it belongs to
    ("Fire Nation" -> [0, 1]; "Gryffindor" split in 3 pieces -> [0, 0, 0]).
    Piece i is scored with itself AND the later pieces of the same word masked,
    so a long word isn't scored with its own continuation visible.
    """
    plan = []
    for i, w in enumerate(word_ids):
        plan.append([j for j in range(i, len(word_ids)) if word_ids[j] == w])
    return plan


def _filled(world, group, traits, template, descriptions, name=None):
    """Prompt text with the group name filled in, plus the name's character span."""
    ctx = _context(world, descriptions)
    # "" is one of the content-free inputs (fix A): keep it empty instead of "N/A"
    ttext = "" if traits == "" else format_traits(traits)
    if name:
        s = NAMED_TEMPLATES[template].format(name=name, traits=ttext, group="\x00")
    else:
        s = TEMPLATES[template].format(traits=ttext, group="\x00")
    if ttext == "":
        s = s.replace("  ", " ").replace(" ,", ",").replace(" :", ":").lstrip(": ")
    if s[0].islower():
        s = s[0].upper() + s[1:]
    i = s.index("\x00")
    name = NAMES[world][group]
    text = ctx + s.replace("\x00", name)
    start = len(ctx) + i
    return text, (start, start + len(name))


def name_pieces(world: str, group: str) -> list[str]:
    """Word pieces of a group name as BERT sees it (used by the tests and the report)."""
    tok, _ = _mlm()
    text, (a, b) = _filled(world, group, ["x"], 0, None)
    enc = tok(text, return_offsets_mapping=True)
    return [tok.convert_ids_to_tokens(t) for t, (s, e) in zip(enc["input_ids"], enc["offset_mapping"])
            if s >= a and e <= b and e > s]


def _pll(texts_spans: dict[str, tuple[str, tuple[int, int]]], model_name: str = MLM_MODEL) -> dict[str, float]:
    """PLL-word-l2r of each group name in its sentence, all groups in one batch."""
    import torch
    tok, model = _mlm(model_name)
    seqs, targets = [], []
    for g, (text, (a, b)) in texts_spans.items():
        enc = tok(text, return_offsets_mapping=True)
        ids, offs, wids = enc["input_ids"], enc["offset_mapping"], enc.word_ids()
        span = [k for k, (s, e) in enumerate(offs) if s >= a and e <= b and e > s]
        if not span:
            raise RuntimeError(f"group name not found in prompt: {text!r}")
        for k, masked in enumerate(l2r_mask_plan([wids[p] for p in span])):
            m = list(ids)
            for r in masked:
                m[span[r]] = tok.mask_token_id
            seqs.append(m)
            targets.append((g, span[k], ids[span[k]]))

    scores = {g: 0.0 for g in texts_spans}
    dev = model.device
    for start in range(0, len(seqs), BATCH_SIZE):
        chunk = seqs[start:start + BATCH_SIZE]
        width = max(len(s) for s in chunk)
        input_ids = torch.full((len(chunk), width), tok.pad_token_id)
        mask = torch.zeros((len(chunk), width), dtype=torch.long)
        for r, s in enumerate(chunk):
            input_ids[r, :len(s)] = torch.tensor(s)
            mask[r, :len(s)] = 1
        with torch.no_grad():
            logits = model(input_ids=input_ids.to(dev), attention_mask=mask.to(dev)).logits
        logp = torch.log_softmax(logits.float(), dim=-1).cpu()
        for r, (g, pos, tid) in enumerate(targets[start:start + BATCH_SIZE]):
            scores[g] += logp[r, pos, tid].item()
    return scores


def mlm_scores(traits, world, template=0, descriptions=None, name=None,
               model_name=MLM_MODEL) -> dict[str, float]:
    """Raw PLL-word-l2r score of each group name (log-probability, higher = better)."""
    return _pll({g: _filled(world, g, traits, template, descriptions, name) for g in WORLDS[world]},
                model_name)


@lru_cache(maxsize=None)
def _prior_cached(world, template, desc_items, named, calibration, model_name):
    descriptions = dict(desc_items) if desc_items else None
    if calibration == "na":
        combos = [([CONTENT_FREE], CONTENT_FREE if named else None)]
    elif calibration == "multi":
        combos = [("" if t == "" else [t], n) for t in CF_TRAITS
                  for n in (CF_NAMES if named else (None,))]
    else:
        raise ValueError(calibration)
    total = {g: 0.0 for g in WORLDS[world]}
    for traits, n in combos:
        for g, v in mlm_scores(traits, world, template, descriptions, n, model_name).items():
            total[g] += v / len(combos)
    return total


def _prior(world, template, descriptions, name, calibration="na", model_name=MLM_MODEL):
    """Content-free prior (cached per setting).
    "na":    traits 'N/A', and name 'N/A' when the prompt is the named one.
    "multi": mean over CF_TRAITS (x CF_NAMES when named), fix A."""
    items = tuple(sorted(descriptions.items())) if descriptions else None
    return dict(_prior_cached(world, template, items, bool(name), calibration, model_name))


def score_mlm(traits, world, template=0, descriptions=None, calibrate=True, name=None) -> dict[str, float]:
    """MLM score; calibrated = score(name | traits) - score(name | 'N/A') (Zhao 2021; Kurita 2019)."""
    raw = mlm_scores(traits, world, template, descriptions, name)
    if not calibrate:
        return raw
    prior = _prior(world, template, descriptions, name)
    return {g: raw[g] - prior[g] for g in raw}


# =============================================================================
# Method 2: embedding similarity (Sentence-BERT, or raw BERT mean-pooling)
# =============================================================================
def _group_texts(world, descriptions):
    if descriptions:
        return [f"{NAMES[world][g]}: {descriptions[g]}" for g in WORLDS[world]]
    return [NAMES[world][g] for g in WORLDS[world]]


def _bert_mean(texts):
    import torch
    tok, model = _bert_encoder()
    enc = tok(texts, padding=True, return_tensors="pt").to(model.device)
    with torch.no_grad():
        hidden = model(**enc).last_hidden_state
    m = enc["attention_mask"].unsqueeze(-1).float()
    return ((hidden * m).sum(1) / m.sum(1)).cpu()


def score_embed(traits, world, descriptions=None, model="minilm", name=None) -> dict[str, float]:
    """Cosine similarity between the person and each group (name, or name + description)."""
    import torch
    texts = [person(traits, name)] + _group_texts(world, descriptions)
    if model == "minilm":
        v = torch.tensor(_sbert().encode(texts, convert_to_numpy=True))
    elif model == "bert-mean":
        v = _bert_mean(texts)
    else:
        raise ValueError(model)
    v = torch.nn.functional.normalize(v.float(), dim=-1)
    sims = (v[1:] @ v[0]).tolist()
    return dict(zip(WORLDS[world], sims))


# =============================================================================
# Method 3: zero-shot NLI (Yin et al. 2019)
# =============================================================================
def score_nli(traits, world, descriptions=None, name=None) -> dict[str, float]:
    """Entailment logit of 'This person belongs to <group>.' for each group."""
    import torch
    tok, model, ent = _nli()
    premise = person(traits, name)
    hyps = []
    for g in WORLDS[world]:
        gname = NAMES[world][g]
        hyps.append(f"This person belongs to {gname} ({descriptions[g].rstrip('.')})."
                    if descriptions else f"This person belongs to {gname}.")
    enc = tok([premise] * len(hyps), hyps, padding=True, truncation=True,
              return_tensors="pt").to(model.device)
    with torch.no_grad():
        logits = model(**enc).logits.float().cpu()
    return dict(zip(WORLDS[world], logits[:, ent].tolist()))


# =============================================================================
# Probabilities, entropy, prediction
# =============================================================================
def to_probs(scores: dict[str, float], temperature: float = 1.0) -> dict[str, float]:
    m = max(scores.values())
    e = {g: math.exp((s - m) / temperature) for g, s in scores.items()}
    z = sum(e.values())
    return {g: x / z for g, x in e.items()}


def entropy(probs: dict[str, float], normalized: bool = True) -> float:
    h = -sum(p * math.log(p) for p in probs.values() if p > 0)
    return h / math.log(len(probs)) if normalized and len(probs) > 1 else h


def top(probs: dict[str, float]) -> str:
    return max(probs, key=probs.get)


def predict(traits, world, method="mlm", *, template=0, descriptions=None, calibrate=True,
            name=None) -> dict:
    """One prediction. See the module docstring for the arguments.

    raw_probs differs from probs only for "mlm" (before vs. after calibration).
    """
    if world not in WORLDS:
        raise ValueError(f"unknown world {world!r}")
    if method in MLM_VARIANTS:
        model_name, calibration = MLM_VARIANTS[method]
        raw = mlm_scores(traits, world, template, descriptions, name, model_name)
        prior = _prior(world, template, descriptions, name, calibration, model_name)
        cal = {g: raw[g] - prior[g] for g in raw}
        scores = cal if calibrate else raw
        return {"probs": to_probs(scores), "raw_probs": to_probs(raw), "scores": scores}
    if method in ("embed", "bert-mean"):
        s = score_embed(traits, world, descriptions, model="minilm" if method == "embed" else "bert-mean",
                        name=name)
        p = to_probs(s, EMBED_TEMPERATURE)
        return {"probs": p, "raw_probs": p, "scores": s}
    if method == "nli":
        s = score_nli(traits, world, descriptions, name)
        p = to_probs(s)
        return {"probs": p, "raw_probs": p, "scores": s}
    raise ValueError(f"unknown method {method!r}; use one of {METHODS + FIX_METHODS}")


def occlusion(traits, world, method="mlm", **kwargs) -> list[dict]:
    """Leave-one-trait-out (Li et al. 2016). For each trait:
    delta = p(top | all traits) - p(top | without it); flips_to = new top if it changed."""
    ts = parse_traits(traits)
    full = predict(ts, world, method, **kwargs)["probs"]
    best = top(full)
    out = []
    for i, t in enumerate(ts):
        rest = ts[:i] + ts[i + 1:]
        p = predict(rest, world, method, **kwargs)["probs"]
        new = top(p)
        out.append({"trait": t, "delta": full[best] - p[best], "flips_to": new if new != best else None})
    return out
