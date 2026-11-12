"""Shared scoring code for "Does BERT actually sort you?".

Every experiment, notebook and the app import from here, so nobody writes their
own version of a method. The methods themselves come in step 3 (IMPLEMENTATION.md):
score_mlm, score_embed, score_nli, to_probs, entropy, occlusion.

This file currently pins the setup that everyone shares.
"""

# ---- Models (pinned in ONE place) -------------------------------------------
MLM_MODEL = "bert-base-uncased"                         # main subject of the study
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"   # Sentence-BERT similarity
NLI_MODEL = "facebook/bart-large-mnli"                  # zero-shot NLI baseline

# ---- Worlds and their group ids (must match data/<world>_groups.csv) ---------
WORLDS = {
    "hp": ["gryffindor", "ravenclaw", "hufflepuff", "slytherin"],
    "divergent": ["abnegation", "amity", "candor", "dauntless", "erudite"],
    "pokemon": ["valor", "mystic", "instinct"],
    "avatar": ["fire", "water", "earth", "air"],
    "invented": ["veltrin", "osmark", "calwen", "durrask"],
}

# ---- Prompt templates for the fill-in-the-blank method ----------------------
TEMPLATES = [
    "Someone who is {traits} belongs to {group}.",
    "A person described as {traits} would be sorted into {group}.",
    "{traits}: this sounds like a member of {group}.",
]
CONTENT_FREE = "N/A"  # used for calibration (Zhao et al. 2021)

SEED = 42
