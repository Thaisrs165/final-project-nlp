# Human votes form: text to paste into Google Forms

39 sorting questions plus 1 familiarity grid. About 6–8 minutes to fill in.
Paste each **bold title** as a question title. Paste each block of options in one go: Google Forms splits a pasted multi-line list into separate options.

## Form settings (do these before sending)
- [ ] Settings → Responses → **Collect email addresses: Do not collect**. The form must stay anonymous.
- [ ] Settings → Responses → **Limit to 1 response: off**, because turning it on forces people to sign in.
- [ ] Settings → Presentation → **Shuffle question order: on**.
- [ ] On every sorting question: **Required: on** and ⋮ → **Shuffle option order: on**.
- [ ] Question type for every sorting question: **Multiple choice**. There's no "none" or "not sure" option on purpose: we want people's first instinct, as in ChaosNLI.
- [ ] If the invented house names change in step 2.4, update section 6 before sending.

---

## Form title
**Sort these people!**

## Form description
> We're a group of NLP students at Insper testing how an AI model sorts people into groups (Hogwarts houses, Divergent factions…). We need human answers to compare with it. There are no right or wrong answers: pick whatever feels closest. It's anonymous and takes about 7 minutes. Thanks!

---

## Section 1: About you

**How well do you know each of these?**
Type: **Multiple choice grid**
Rows:
```
Harry Potter
Divergent
Pokémon GO
Avatar: The Last Airbender
```
Columns:
```
Not at all
A little
Well
```

---

## Section 2: Harry Potter

Section description:
> Which Hogwarts house fits each person best?
> Gryffindor: bravery, daring, chivalry · Ravenclaw: intelligence, wit, love of learning · Hufflepuff: loyalty, hard work, fairness · Slytherin: ambition, cunning, resourcefulness

Options for **every** question in this section:
```
Gryffindor
Ravenclaw
Hufflepuff
Slytherin
```

Questions:
1. **Someone who is smart and nice.**
2. **Someone who is funny and kind.**
3. **Someone who is easygoing and polite.**
4. **Someone who is quiet and friendly.**
5. **Someone who is creative and talkative.**
6. **Someone who is sensible and cheerful.**
7. **Someone who is a good listener and loves music.**
8. **Someone who is confident and caring.**
9. **Someone who is brave and ambitious.**
10. **Someone who is curious and loyal.**
11. **Someone who is daring and studious.**
12. **Someone who is cunning and kind.**
13. **Someone who is witty, bookish and original.**
14. **Someone who is patient, fair and hardworking.**
15. **Someone who is shrewd, power-hungry and proud.**

---

## Section 3: Divergent

Section description:
> Which faction fits each person best?
> Abnegation: selflessness · Amity: peace and kindness · Candor: honesty · Dauntless: bravery · Erudite: knowledge and intelligence

Options for every question in this section:
```
Abnegation
Amity
Candor
Dauntless
Erudite
```

Questions:
16. **Someone who is smart and nice.**
17. **Someone who is funny and kind.**
18. **Someone who is easygoing and polite.**
19. **Someone who is brave and selfless.**
20. **Someone who is honest and intelligent.**
21. **Someone who always tells the truth, even when it hurts.**

---

## Section 4: Pokémon GO

Section description:
> Which team fits each person best?
> Valor: strength and passion · Mystic: wisdom and calm · Instinct: intuition and trusting your gut

Options for every question in this section:
```
Valor
Mystic
Instinct
```

Questions:
22. **Someone who is smart and nice.**
23. **Someone who is funny and kind.**
24. **Someone who is easygoing and polite.**
25. **Someone who is passionate and calm.**
26. **Someone who is analytical and impulsive.**
27. **Someone who trains hard and loves a challenge.**

---

## Section 5: Avatar: The Last Airbender

Section description:
> Which nation fits each person best?
> Fire Nation: drive, ambition, passion · Water Tribe: adaptability, community · Earth Kingdom: endurance, persistence · Air Nomads: freedom, detachment, peace

Options for every question in this section:
```
Fire Nation
Water Tribe
Earth Kingdom
Air Nomads
```

Questions:
28. **Someone who is smart and nice.**
29. **Someone who is funny and kind.**
30. **Someone who is easygoing and polite.**
31. **Someone who is ambitious and adaptable.**
32. **Someone who is stubborn and free-spirited.**
33. **Someone who never gives up and can endure anything.**

---

## Section 6: A world we made up

Section description:
> These four houses don't exist. We invented them. Using only these descriptions, which house fits each person best?
> Veltrin: patient, observant, methodical, reserved · Osmark: warm, generous, sociable, forgiving · Calwen: restless, curious, independent, spontaneous · Durrask: disciplined, competitive, proud, determined

Options for every question in this section:
```
Veltrin
Osmark
Calwen
Durrask
```

Questions:
34. **Someone who is smart and nice.**
35. **Someone who is funny and kind.**
36. **Someone who is easygoing and polite.**
37. **Someone who never rushes, but loves doing things on a whim.**
38. **Someone who is generous with friends, but hates to lose.**
39. **Someone who watches carefully for a long time before acting.**

---

## Answer key (for us only, do NOT paste into the form)

Item types:
- **generic:** no clear answer. We compare the human vote split with BERT's split.
- **conflicting:** the traits point to two groups (listed as A | B). We check whether the votes split between those two.
- **clear:** one obvious answer. This is a sanity check, and it also catches people clicking at random.

The items asked in every world (smart and nice; funny and kind; easygoing and polite) let us compare how one input is sorted in each world.

| # | id | world | type | traits | expected |
|---|---|---|---|---|---|
| 1 | g01-hp | hp | generic | smart and nice | — |
| 2 | g02-hp | hp | generic | funny and kind | — |
| 3 | g03-hp | hp | generic | easygoing and polite | — |
| 4 | g04-hp | hp | generic | quiet and friendly | — |
| 5 | g05-hp | hp | generic | creative and talkative | — |
| 6 | g06-hp | hp | generic | sensible and cheerful | — |
| 7 | g07-hp | hp | generic | a good listener and loves music | — |
| 8 | g08-hp | hp | generic | confident and caring | — |
| 9 | c01-hp | hp | conflicting | brave and ambitious | gryffindor \| slytherin |
| 10 | c02-hp | hp | conflicting | curious and loyal | ravenclaw \| hufflepuff |
| 11 | c03-hp | hp | conflicting | daring and studious | gryffindor \| ravenclaw |
| 12 | c04-hp | hp | conflicting | cunning and kind | slytherin \| hufflepuff |
| 13 | k01-hp | hp | clear | witty, bookish and original | ravenclaw |
| 14 | k02-hp | hp | clear | patient, fair and hardworking | hufflepuff |
| 15 | k03-hp | hp | clear | shrewd, power-hungry and proud | slytherin |
| 16 | g01-div | divergent | generic | smart and nice | — |
| 17 | g02-div | divergent | generic | funny and kind | — |
| 18 | g03-div | divergent | generic | easygoing and polite | — |
| 19 | c01-div | divergent | conflicting | brave and selfless | dauntless \| abnegation |
| 20 | c02-div | divergent | conflicting | honest and intelligent | candor \| erudite |
| 21 | k01-div | divergent | clear | always tells the truth, even when it hurts | candor |
| 22 | g01-pkm | pokemon | generic | smart and nice | — |
| 23 | g02-pkm | pokemon | generic | funny and kind | — |
| 24 | g03-pkm | pokemon | generic | easygoing and polite | — |
| 25 | c01-pkm | pokemon | conflicting | passionate and calm | valor \| mystic |
| 26 | c02-pkm | pokemon | conflicting | analytical and impulsive | mystic \| instinct |
| 27 | k01-pkm | pokemon | clear | trains hard and loves a challenge | valor |
| 28 | g01-ava | avatar | generic | smart and nice | — |
| 29 | g02-ava | avatar | generic | funny and kind | — |
| 30 | g03-ava | avatar | generic | easygoing and polite | — |
| 31 | c01-ava | avatar | conflicting | ambitious and adaptable | fire \| water |
| 32 | c02-ava | avatar | conflicting | stubborn and free-spirited | earth \| air |
| 33 | k01-ava | avatar | clear | never gives up and can endure anything | earth |
| 34 | g01-inv | invented | generic | smart and nice | — |
| 35 | g02-inv | invented | generic | funny and kind | — |
| 36 | g03-inv | invented | generic | easygoing and polite | — |
| 37 | c01-inv | invented | conflicting | never rushes, but loves doing things on a whim | veltrin \| calwen |
| 38 | c02-inv | invented | conflicting | generous with friends, but hates to lose | osmark \| durrask |
| 39 | k01-inv | invented | clear | watches carefully for a long time before acting | veltrin |

**Things to remember for the analysis:**
- People saw a one-line description of each group, so in the report we describe humans as sorting "with descriptions". This matches the embedding and NLI methods, which also get the descriptions.
- Use the familiarity grid to check whether people who know a franchise well vote differently. That's the human version of BERT's "memory".
- Drop a response if it gets 2 or more of the 7 **clear** items wrong. We decide this rule now, before seeing the data.
- These exact trait sets have to go into `data/generic.csv` and the conflicting test rows, so BERT is tested on the same inputs.
