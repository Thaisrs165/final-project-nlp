# The Unsure Hat (app, step 8, owner: Ana)

Gradio app for the Educator track. It teaches that a model's confidence isn't understanding. Every number comes from `sorter.py`, the same code as the experiments.

```
.venv/bin/python app/app.py        # then open http://127.0.0.1:7860
```
The first click on each model is slow while it loads (BART-NLI is the biggest); after that it's fast.

| Tab | Question | What it shows |
|---|---|---|
| 1. Sort me | Q1 | The 12-question quiz (`questions.json`). Each answer carries 2 hidden trait words, the only thing the model sees. It shows the model's probabilities, the exact words it saw, and what our quiz key expected. |
| 2. Trick BERT | Q2, Q3 | The same traits with a name, no name, another character's name, and with "not". With the default model you can watch the Gryffindor pull live. |
| 3. Why it's unsure | Q3 | Vague and mixed items: the model vs. **real people** (form, after the attention check) vs. the **simulated panel** (always labelled as simulated). |

The controls at the top (world, model, with/without descriptions) apply to every tab.

## Files
- `app.py`: the app (starter: works end to end; wording and styling to be polished)
- `questions.json`: quiz questions, options, hidden traits and the designers' key
- `worlds.json`: display names and colours per group

## To do (owner)
- [ ] Polish the wording and add the colours from `worlds.json`
- [ ] Deploy to Hugging Face Spaces (needs a login). The Space runs `app/app.py` and needs `sorter.py`, `data/`, `app/` and `requirements.txt`
- [ ] Put the link / QR code in the report's Conclusion
