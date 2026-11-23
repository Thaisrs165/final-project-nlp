# The Unsure Hat (app, step 8, owner: Ana; quiz flow and look: Esther, 2026-11-23)

Gradio app for the Educator track. It teaches that a model's confidence isn't understanding. Every number comes from `sorter.py`, the same code as the experiments.

```
.venv/bin/python app/app.py        # then open http://127.0.0.1:7860
```
All models are loaded in a background thread when the app starts (`_warm_up`), so the first quiz isn't slow: the grid (15 predictions) takes about 4–5 s; after that, switching world/model is instant.

| Tab | Question | What it shows |
|---|---|---|
| I · Sort me | Q1 | **One test, every world.** The 12-question quiz (`questions.json`) is taken once, one question at a time: intro card → questions (progress dots, Back / Continue, options shuffled so their order doesn't hint at a group, Continue blocked until you answer) → optional free text → reveal. Each answer carries 2 hidden trait words, the only thing the models see. The reveal has two parts: **(1) detail** for the world and model chosen at the top (probabilities, a line in the hat's voice **chosen only from the probabilities** (`hat_voice`), the words BERT saw, our quiz key); **(2) the multiverse grid** (`multiverse`): every world × our quiz key + every model, with each group's colour from `worlds.json`, and how many worlds the 3 models agree on. After the quiz, changing World, Model or descriptions **re-sorts the same answers instantly**, with no retake (predictions are cached in `cached_probs`). |
| II · Trick BERT | Q2, Q3 | The same traits with a name, no name, another character's name, and with "not". With the default model you can watch the Gryffindor pull live. |
| III · Why it's unsure | Q3 | Vague and mixed items: the model vs. **real people** (form, after the attention check) vs. the **simulated panel** (always labelled as simulated). |

The controls at the top (world, model, with/without descriptions) apply to every tab.

## Look and feel
- Dark theme for every tab: near-black violet with gold accents, set in `THEME` for both light and dark mode, so the app is dark whatever the browser prefers. Headings use Cinzel (Google Fonts), body text uses Inter.
- Every tab uses the same cards, and the probability bars run from violet to gold.
- Entrance animations on each question, option and result, restarted from JS after every click (`ANIMATE`). They're switched off for people who prefer reduced motion.
- Responsive: no horizontal scroll at phone width; the settings stack vertically.
- Fixed from the starter: dropdown lists had no background, and the model name was cut off.
- Don't put `backdrop-filter`, `transform` or `filter` on the settings strip or anything around a dropdown. Gradio's option list is `position: fixed`, so any of these traps it: it opens in the wrong place, behind the cards (found and fixed 2026-11-23).
- Gradio 6 takes `theme`, `css`, `js` and `head` in `demo.launch(...)`, not in `gr.Blocks(...)`.

## Files
- `app.py`: the app (starter: works end to end; wording and styling to be polished)
- `questions.json`: quiz questions, options, hidden traits and the designers' key
- `worlds.json`: display names and colours per group

## To do (owner)
- [x] Polish the wording and look (2026-11-23, Esther)
- [x] Per-group colours from `worlds.json` are used in the multiverse grid
- [ ] Deploy decision (team): Gradio Spaces now need a paid plan (checked 2026-11-23). Recommendation: run locally plus the temporary `GRADIO_SHARE=True` link. Ready-made Space files in [space/README.md](../space/README.md).
- [ ] Optional: a 1–2 min screen recording of the app for the report's Material
- [ ] Put the link / QR code in the report's Conclusion
