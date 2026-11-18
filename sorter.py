"""Shared scoring code for "Does BERT actually sort you?".

Every experiment, notebook and the app import from here, so nobody writes their
own version of a method (IMPLEMENTATION.md, step 3).

Main entry point
----------------
    predict(traits, world, method, template=0, descriptions=None, calibrate=True)
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

Other helpers: entropy, top, occlusion, load_descriptions, format_traits.
"""
from __future__ import annotations

import csv
import math
from functools import lru_cache
from pathlib import Path

# ---- Models (pinned in ONE place) -------------------------------------------
MLM_MODEL = "bert-base-uncased"                         # main subject of the study
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
CONTENT_FREE = "N/A"  # used for calibration (Zhao et al. 2021)

# Cosine similarities all sit in a narrow band, so a plain softmax over them is
# almost uniform. We divide by a fixed temperature before the softmax. It is a
# constant chosen once (same value as common contrastive setups), never tuned on
# our results. Entropies are only compared WITHIN a method, never across methods.
EMBED_TEMPERATURE = 0.05

METHODS = ("mlm", "embed", "bert-mean", "nli")
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
def _mlm():
    import torch
    from transformers import AutoModelForMaskedLM, AutoTokenizer
    torch.manual_seed(SEED)
    tok = AutoTokenizer.from_pretrained(MLM_MODEL)
    model = AutoModelForMaskedLM.from_pretrained(MLM_MODEL).to(_device()).eval()
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


def _filled(world, group, traits, template, descriptions):
    """Prompt text with the group name filled in, plus the name's character span."""
    ctx = _context(world, descriptions)
    s = TEMPLATES[template].format(traits=format_traits(traits), group="\x00")
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


def _pll(texts_spans: dict[str, tuple[str, tuple[int, int]]]) -> dict[str, float]:
    """PLL-word-l2r of each group name in its sentence, all groups in one batch."""
    import torch
    tok, model = _mlm()
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


def mlm_scores(traits, world, template=0, descriptions=None) -> dict[str, float]:
    """Raw PLL-word-l2r score of each group name (log-probability, higher = better)."""
    return _pll({g: _filled(world, g, traits, template, descriptions) for g in WORLDS[world]})


def score_mlm(traits, world, template=0, descriptions=None, calibrate=True) -> dict[str, float]:
    """MLM score; calibrated = score(name | traits) - score(name | 'N/A') (Zhao 2021; Kurita 2019)."""
    raw = mlm_scores(traits, world, template, descriptions)
    if not calibrate:
        return raw
    prior = mlm_scores([CONTENT_FREE], world, template, descriptions)
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


def score_embed(traits, world, descriptions=None, model="minilm") -> dict[str, float]:
    """Cosine similarity between the person and each group (name, or name + description)."""
    import torch
    person = f"Someone who is {format_traits(traits)}."
    texts = [person] + _group_texts(world, descriptions)
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
def score_nli(traits, world, descriptions=None) -> dict[str, float]:
    """Entailment logit of 'This person belongs to <group>.' for each group."""
    import torch
    tok, model, ent = _nli()
    premise = f"Someone who is {format_traits(traits)}."
    hyps = []
    for g in WORLDS[world]:
        name = NAMES[world][g]
        hyps.append(f"This person belongs to {name} ({descriptions[g].rstrip('.')})."
                    if descriptions else f"This person belongs to {name}.")
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


def predict(traits, world, method="mlm", *, template=0, descriptions=None, calibrate=True) -> dict:
    """One prediction. See the module docstring for the arguments.

    raw_probs differs from probs only for "mlm" (before vs. after calibration).
    """
    if world not in WORLDS:
        raise ValueError(f"unknown world {world!r}")
    if method == "mlm":
        raw = mlm_scores(traits, world, template, descriptions)
        prior = mlm_scores([CONTENT_FREE], world, template, descriptions)
        cal = {g: raw[g] - prior[g] for g in raw}
        scores = cal if calibrate else raw
        return {"probs": to_probs(scores), "raw_probs": to_probs(raw), "scores": scores}
    if method in ("embed", "bert-mean"):
        s = score_embed(traits, world, descriptions, model="minilm" if method == "embed" else "bert-mean")
        p = to_probs(s, EMBED_TEMPERATURE)
        return {"probs": p, "raw_probs": p, "scores": s}
    if method == "nli":
        s = score_nli(traits, world, descriptions)
        p = to_probs(s)
        return {"probs": p, "raw_probs": p, "scores": s}
    raise ValueError(f"unknown method {method!r}; use one of {METHODS}")


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
