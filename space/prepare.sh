#!/usr/bin/env bash
# Copy only what the app needs into a local clone of the Hugging Face Space.
# Usage (from the repo root):   bash space/prepare.sh ../unsure-hat
set -euo pipefail
SRC="$(cd "$(dirname "$0")/.." && pwd)"
DST="${1:?give the path to your local clone of the Space}"
[ -d "$DST/.git" ] || { echo "error: $DST is not a git clone of the Space (step 4 of space/README.md)"; exit 1; }

mkdir -p "$DST/app" "$DST/data"
cp "$SRC/sorter.py" "$DST/"
cp "$SRC/app/app.py" "$SRC/app/questions.json" "$SRC/app/worlds.json" "$DST/app/"
cp "$SRC/space/requirements.txt" "$DST/requirements.txt"
cp "$SRC/space/space-card.md" "$DST/README.md"
# The app reads only these data files.
cp "$SRC"/data/{vote_items.csv,human_votes.csv,human_respondents.csv,simulated_votes.csv} "$DST/data/"
for w in hp divergent got avatar invented; do
  mkdir -p "$DST/data/$w"
  cp "$SRC/data/$w/groups.csv" "$DST/data/$w/"
done
echo "Copied into $DST. Next:"
echo "  cd $DST && git add -A && git commit -m 'Deploy The Unsure Hat' && git push"
