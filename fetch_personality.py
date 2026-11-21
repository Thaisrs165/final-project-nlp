"""Step 2.2 helper: traits taken literally from Fandom "Personality" sections.

Works for any world. Two commands:

  fetch  data/<world>/characters.csv  ->  data/<world>/raw/<page>.txt         (cached section text)
                                          data/<world>/trait_candidates.csv   (every usable adjective
                                                                               + the sentence it is in)
  build  data/<world>/trait_picks.csv ->  data/<world>/tests.csv              (canonical rows)

Usage:
  .venv/bin/python fetch_personality.py fetch hp --wiki harrypotter
  .venv/bin/python fetch_personality.py build hp --wiki harrypotter

Inputs
  characters.csv  name, page, gold_group, gold_source, role   (role = main | spare)
  leak_words.csv  word, group, found_in                        (optional; banned traits)
  trait_picks.csv name, traits                                 (5 traits separated by ';',
                                                                 chosen from the candidates)
Rules (IMPLEMENTATION.md step 2.2)
  * A trait must be an adjective that LITERALLY appears in the Personality section.
    `build` refuses any pick that isn't in trait_candidates.csv for that character.
  * No trait may be a leak word (group names, description words), including simple
    word forms (brave -> bravely, bravery).
  * Fewer than 5 usable picks -> the row is written with test_type `needs_review`.

The Fandom pages themselves block scripts, so this uses the wiki's public MediaWiki API.
Text is cached in data/<world>/raw/ so every trait can be traced offline.
"""
import argparse
import csv
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import OrderedDict
from html.parser import HTMLParser
from pathlib import Path

import nltk

DATA = Path(__file__).resolve().parent / "data"
UA = "Mozilla/5.0 (academic NLP course project; trait extraction)"
SECTION_RE = re.compile(r"personality", re.I)

# Adjectives that say nothing about personality.
STOP = set("""
able actual additional afraid alive available bad big black blue brown certain clear close common
complete current dark dead different difficult early entire entire eventual evident extra fellow few
final first following former full further general good great green grey high important initial
known large last late later least little long low main major many minor more most much muggle-born
new next normal obvious old only open other own particular past personal physical possible present
previous real recent red right same second several short similar single small so-called social
special strong such sure third total true usual various own whole white wide wrong young
magical non-magical half-blood pure-blood muggle wizarding dark-haired adult teenage elder older
younger youngest eldest later-life able-bodied lifelong""".split())


# ----------------------------------------------------------------- fetching
def api(wiki, **params):
    params.update(format="json", formatversion=2)
    url = f"https://{wiki}.fandom.com/api.php?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


class _Text(HTMLParser):
    """Keep paragraph text; drop references, tables, captions, quotes boxes, edit links."""
    SKIP = {"sup", "table", "figure", "figcaption", "style", "script", "aside"}

    def __init__(self):
        super().__init__()
        self.out, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        cls = dict(attrs).get("class", "") or ""
        if tag in self.SKIP or "mw-editsection" in cls or "quote" in cls.lower():
            self.skip += 1
        elif tag in ("p", "li", "br", "h2", "h3", "h4"):
            self.out.append("\n")

    def handle_endtag(self, tag):
        if self.skip and (tag in self.SKIP or tag in ("span", "div")):
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.out.append(data)


def section_text(wiki, page):
    """Return (section title, plain text) of the page's Personality section, or (None, '')."""
    secs = api(wiki, action="parse", page=page, prop="sections", redirects=1)
    if "error" in secs:
        raise RuntimeError(secs["error"].get("info", "api error"))
    sections = secs["parse"]["sections"]
    hit = next((s for s in sections if SECTION_RE.search(s["line"])), None)
    if not hit:
        return None, ""
    body = api(wiki, action="parse", page=page, prop="text", section=hit["index"], redirects=1)
    p = _Text()
    p.feed(body["parse"]["text"])
    text = html.unescape("".join(p.out))
    text = re.sub(r"\[\d+\]|\[citation needed\]", "", text)
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in text.split("\n")]
    lines = [ln for ln in lines if ln and not SECTION_RE.fullmatch(ln)]
    return re.sub(r"<[^>]+>", "", hit["line"]), "\n".join(lines)


# ------------------------------------------------------------- candidates
def leak_set(world):
    path = DATA / world / "leak_words.csv"
    words = set()
    if path.exists():
        with open(path) as f:
            words = {r["word"].strip().lower() for r in csv.DictReader(f)}
    groups_csv = DATA / world / "groups.csv"
    if groups_csv.exists():
        with open(groups_csv) as f:
            for r in csv.DictReader(f):
                words.add(r["group"].lower())
                words |= set(re.findall(r"[a-z]+", r["description"].lower()))
    return words - {"of", "and", "love", "hard", "work", "the"}


def leaks(word, banned):
    """True if word is a banned word or a simple form of one (brave/bravely/bravery).

    Hyphenated words are checked whole ("hard-working" = "hardworking") and part by
    part ("kind-hearted" contains "kind", "quick-witted" contains "wit").
    """
    w = word.lower()
    forms = {w, w.replace("-", "")} | set(w.split("-"))
    for f in forms:
        if f in banned:
            return True
        for b in banned:
            if len(b) >= 3 and (f.startswith(b) or b.startswith(f)) and len(f) >= 3 \
                    and abs(len(f) - len(b)) <= 4:
                return True
    return False


def adjectives(text):
    """[(adjective, sentence)] in order of appearance."""
    out = []
    for sent in nltk.sent_tokenize(text):
        for word, tag in nltk.pos_tag(nltk.word_tokenize(sent)):
            if tag == "JJ" and re.fullmatch(r"[a-z][a-z-]+", word) and len(word) > 3:
                out.append((word, sent))
    return out


def cmd_fetch(world, wiki):
    folder = DATA / world
    raw = folder / "raw"
    raw.mkdir(exist_ok=True)
    banned = leak_set(world)
    with open(folder / "characters.csv") as f:
        chars = list(csv.DictReader(f))
    rows, report = [], []
    for c in chars:
        cache = raw / (re.sub(r"[^A-Za-z0-9]+", "_", c["page"]) + ".txt")
        url = f"https://{wiki}.fandom.com/wiki/" + urllib.parse.quote(c["page"].replace(" ", "_"))
        if cache.exists():
            title, text = cache.read_text().split("\n", 2)[1], cache.read_text().split("\n", 2)[2]
        else:
            try:
                title, text = section_text(wiki, c["page"])
            except Exception as e:  # report and carry on
                report.append((c["name"], f"ERROR {e}", 0, 0))
                continue
            cache.write_text(f"{url}\n{title}\n{text}")
            time.sleep(0.5)
        seen = OrderedDict()
        for adj, sent in adjectives(text):
            if adj in STOP or leaks(adj, banned):
                continue
            if adj not in seen:
                seen[adj] = [0, sent]
            seen[adj][0] += 1
        for adj, (n, sent) in seen.items():
            rows.append(dict(name=c["name"], adjective=adj, count=n, sentence=sent, source_url=url))
        report.append((c["name"], title or "NO PERSONALITY SECTION", len(text.split()), len(seen)))
    with open(folder / "trait_candidates.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["name", "adjective", "count", "sentence", "source_url"])
        w.writeheader()
        w.writerows(rows)
    print(f"{'character':26s} {'section':32s} {'words':>6s} {'usable adj':>10s}")
    for name, title, nw, na in report:
        flag = "  <- fewer than 5" if na < 5 else ""
        print(f"{name:26s} {title[:32]:32s} {nw:6d} {na:10d}{flag}")


# ------------------------------------------------------------------ build
def cmd_build(world, prefix, wiki):
    folder = DATA / world
    with open(folder / "characters.csv") as f:
        chars = {r["name"]: r for r in csv.DictReader(f)}
    with open(folder / "trait_candidates.csv") as f:
        cands = {}
        for r in csv.DictReader(f):
            cands.setdefault(r["name"], {})[r["adjective"]] = r
    with open(folder / "trait_picks.csv") as f:
        picks = list(csv.DictReader(f))
    banned = leak_set(world)
    out, errors = [], []
    for i, p in enumerate(picks, 1):
        name = p["name"]
        traits = [t.strip() for t in p["traits"].split(";") if t.strip()]
        for t in traits:
            if t not in cands.get(name, {}):
                errors.append(f"{name}: '{t}' is not an adjective in their Personality section")
            if leaks(t, banned):
                errors.append(f"{name}: '{t}' is a leak word")
        c = chars[name]
        ev = " | ".join(f"{t}: {cands[name][t]['sentence']}" for t in traits if t in cands.get(name, {}))
        url = f"https://{wiki}.fandom.com/wiki/" + urllib.parse.quote(c["page"].replace(" ", "_"))
        out.append(dict(id=f"{prefix}-c{i:02d}", test_type="canonical" if len(traits) == 5 else "needs_review",
                        name=name, traits="; ".join(traits), gold_group=c["gold_group"],
                        source_url=url, trait_evidence=ev))
    if errors:
        sys.exit("Refusing to write tests.csv:\n  " + "\n  ".join(errors))
    cols = ["id", "test_type", "name", "traits", "gold_group", "source_url", "trait_evidence"]
    with open(folder / "tests.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(out)
    n_ok = sum(r["test_type"] == "canonical" for r in out)
    print(f"wrote {len(out)} rows to {folder / 'tests.csv'} ({n_ok} canonical, {len(out) - n_ok} needs_review)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["fetch", "build"])
    ap.add_argument("world")
    ap.add_argument("--wiki", required=True, help="Fandom subdomain, e.g. harrypotter")
    a = ap.parse_args()
    nltk.download("punkt_tab", quiet=True)
    nltk.download("averaged_perceptron_tagger_eng", quiet=True)
    if a.command == "fetch":
        cmd_fetch(a.world, a.wiki)
    else:
        cmd_build(a.world, a.world, a.wiki)
