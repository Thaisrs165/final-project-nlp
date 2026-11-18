# Human votes form (live version, 2026-11-18)

This is the text of the Google Form that went live on 2026-11-18. It's kept here for context, so the analysis and the report can point to exactly what people saw.
Background and decisions: [DATA_LOG.md](../DATA_LOG.md), entry "Short human form is live after all". All 25 items also exist in [data/vote_items.csv](../data/vote_items.csv), with the same wording.

> ⚠️ This file was written **before** the form was built in Google Forms. If any wording was changed while building it, update this file and `data/<world>/groups.csv` (the descriptions must match what people saw).

---

## Settings
- Collect email addresses: **Do not collect** (anonymous).
- Limit to 1 response: **off** (turning it on forces people to sign in).
- Shuffle question order: **on**.
- Every sorting question: **Multiple choice**, **Required**, **Shuffle option order**. There's no "I don't know" option.

---

## Title
**Which group would you put this person in?**

## Description
> **Help us test how an AI handles ambiguity** 🧠
>
> We're NLP students at Insper studying how **BERT**, a well-known AI language model, sorts people into groups such as Hogwarts houses, Divergent factions and Game of Thrones houses.
>
> Some descriptions here are clear. Others are deliberately vague, like "smart and nice", and could fit several groups. **That's the point.** For vague descriptions there's no right answer, so we can't simply grade the AI. Instead, we compare it with how *people* split their votes.
>
> - If people are divided but the AI is 90% sure, the AI is overconfident.
> - If the AI is unsure exactly where people are unsure, it handles ambiguity the way humans do.
>
> **Your answers are that human reference.** There are no right or wrong answers, so go with your first instinct and don't overthink it. A few questions have an obvious answer: they help us spot random clicking.
>
> The descriptions are in English because they're exactly what the AI sees. Anonymous · about 3 minutes · thank you! 💛

---

## Section 1: About you
**How well do you know each of these?** (Multiple choice grid)
- Rows: Harry Potter · Divergent · Game of Thrones · Avatar: The Last Airbender
- Columns: Not at all · A little · Well

## Section 2: Harry Potter
> Which Hogwarts house fits each person best?
> Gryffindor: bravery, daring · Ravenclaw: intelligence, wisdom, love of learning · Hufflepuff: loyalty, hard work, fairness · Slytherin: ambition, cunning, resourcefulness

Options: Gryffindor · Ravenclaw · Hufflepuff · Slytherin

1. Someone who is smart and nice.
2. Someone who is funny and kind.
3. Someone who is easygoing and polite.
4. Someone who is quiet and friendly.
5. Someone who is creative and talkative.
6. Someone who is sensible and cheerful.
7. Someone who is a good listener and loves music.
8. Someone who is confident and caring.
9. Someone who is witty, bookish and original.

## Section 3: Divergent
> Which faction fits each person best?
> Abnegation: selflessness · Amity: peace and kindness · Candor: honesty · Dauntless: bravery · Erudite: knowledge and intelligence

Options: Abnegation · Amity · Candor · Dauntless · Erudite

10. Someone who is smart and nice.
11. Someone who is funny and kind.
12. Someone who is easygoing and polite.
13. Someone who always tells the truth, even when it hurts.

## Section 4: Game of Thrones
> Which Great House fits each person best?
> Stark: honor, duty, loyalty · Lannister: pride, wealth, cunning · Targaryen: passion, boldness, ambition · Greyjoy: defiance, toughness, independence · Tyrell: charm, diplomacy, quiet scheming

Options: Stark · Lannister · Targaryen · Greyjoy · Tyrell

14. Someone who is smart and nice.
15. Someone who is funny and kind.
16. Someone who is easygoing and polite.
17. Someone who always keeps their word, whatever it costs.

## Section 5: Avatar: The Last Airbender
> Which nation fits each person best?
> Fire Nation: drive, ambition, passion · Water Tribe: adaptability, community · Earth Kingdom: endurance, persistence · Air Nomads: freedom, detachment, peace

Options: Fire Nation · Water Tribe · Earth Kingdom · Air Nomads

18. Someone who is smart and nice.
19. Someone who is funny and kind.
20. Someone who is easygoing and polite.
21. Someone who never gives up and can endure anything.

## Section 6: A world we made up
> These four houses don't exist. We made them up. Using only these descriptions, which house fits each person best?
> Veltrin: patient, observant, methodical, reserved · Osmark: warm, generous, sociable, forgiving · Calwen: restless, curious, independent, spontaneous · Durrask: disciplined, competitive, proud, determined

Options: Veltrin · Osmark · Calwen · Durrask

22. Someone who is smart and nice.
23. Someone who is funny and kind.
24. Someone who is easygoing and polite.
25. Someone who watches carefully for a long time before acting.

---

## For the analysis (not shown in the form)

**Attention items** (obvious answer):

| Question | id | Expected |
|---|---|---|
| 9 | `k01-hp` | Ravenclaw |
| 13 | `k01-div` | Candor |
| 17 | `k01-got` | Stark |
| 21 | `k01-ava` | Earth Kingdom |
| 25 | `k01-inv` | Veltrin |

**Rule, set before seeing any data:** drop a respondent who gets **2 or more of these 5** wrong.

**Question → `vote_items.csv` id:**

| Questions | ids |
|---|---|
| 1–8 | `g01-hp` … `g08-hp` |
| 9 | `k01-hp` |
| 10–12 | `g01-div` … `g03-div` |
| 13 | `k01-div` |
| 14–16 | `g01-got` … `g03-got` |
| 17 | `k01-got` |
| 18–20 | `g01-ava` … `g03-ava` |
| 21 | `k01-ava` |
| 22–24 | `g01-inv` … `g03-inv` |
| 25 | `k01-inv` |

**Not in the form:** the 12 conflicting items and `k02-hp` / `k03-hp` (they exist only in the simulated panel).

**Target:** about 35 responses (about 30 after the filter). 10 is the useful minimum for checking the panel.
