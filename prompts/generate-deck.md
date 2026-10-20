# Generating AI-103 cards

Two roles work on one course unit at a time: a **generator** writes the
unit's cards, then an independent **reviewer** checks them against the
source. Both read this whole file.

These are **learning cards, not only exam cards**. Each card teaches one
concept: a question, an answer of up to four bullets that hold the core,
and an explanation that makes it understood. The learner first reads the
explanations to learn the topic; later they run fast passes — question,
recall, flip, glance at the bullets, next. Every rule below serves one of
those two moments.

**Hard cap: 1000 cards for the whole deck.** It is split over the modules
by exam weight and content (`decks/ai-103/budgets.json`); each unit gets its
share as `BUDGET`. Never exceed it. When the material does not fit, put more on
one card — never drop a defined term.

## Inputs

- `UNIT`: the unit's Markdown file under `~/Documents/work/AI-103/ai-103/…`.
  Its first lines name the section (`# 1.2.3 …`) and the unit URL (`Quelle:`).
- `SECTION`: the section number, e.g. `1.2.3`.
- `BUDGET`: the most cards this unit may have.
- The unit's module folder: read the neighbouring units too, so you know the
  context and do not ask what a neighbour already covers.
- `prompts/exam-outline.md`: what the exam measures and how much.
- `decks/sample.json`: a small example of the format.

## Output

- `decks/ai-103/cards/<SECTION>.json`: a JSON list of cards, nothing else.
- `decks/ai-103/review/<SECTION>.md`: short notes (see the end).
- Images, if any, under `decks/media/ai-103/`.

After writing, run
`~/.pyenv/versions/3.12.11/bin/python scripts/build_deck.py --only <SECTION>`
from the repo root `~/Documents/Uni/vocab_trainer`. It checks your file
alone (many units are generated in parallel; never run it without `--only`).
It must print no errors; fix a length warning by splitting the card, not by
cutting content.

## Card format

```json
{
  "id": "1.2.3-01",
  "type": "basic",
  "section": "1.2.3",
  "exam_area": "plan",
  "origin": "generated",
  "source_url": "https://learn.microsoft.com/en-us/training/modules/…",
  "tags": ["benchmarks"],
  "question": "…",
  "answer": "…",
  "explanation": "…",
  "addition": "…",
  "addition_source": "https://learn.microsoft.com/…"
}
```

- `id`: `<SECTION>-NN`, numbered from 01 in card order.
- `exam_area`: one of `plan`, `genai`, `vision`, `text`, `extraction` — the
  outline group this card's fact would be examined under, not the module's
  learning path.
- `origin`: `generated`; `knowledge-check` for knowledge-check and module
  assessment questions.
- `source_url`: the unit URL from the `Quelle:` line.
- `tags`: 1–3 lowercase topic words that cross modules (`rag`, `evaluation`,
  `managed-identity`).
- All text is English Markdown. Bold the one key term in `answer`. Code goes
  in fenced ```python blocks.
- Optional image lists: `question_images`, `answer_images`,
  `explanation_images`, `addition_images`, each `[{"src": "media/ai-103/…",
  "alt": "…"}]`.

### The three text layers

- **`answer`** — the core the learner must recall, readable at a glance:
  one phrase, one sentence, or up to 4 short bullets (list cards: one
  bullet per term). About 15–50 words; the build warns above 70. Bold the
  key terms. No long reasoning — that goes in the explanation.
- **`explanation`** — why it is so and how it fits, written fresh in clear
  words. **Only facts that are in the course text.** 30–90 words; the build
  warns above 120. Never restate the answer; add what makes it stick (the
  contrast, the reason, the typical scenario).
- **`addition`** — only facts that are **not** in the course: a missing piece
  needed to understand the card, a correction, a rename, an exam-relevant
  detail the course skips. At most 50 words. Requires `addition_source`: a
  learn.microsoft.com URL **you opened with WebFetch in this run and that
  states the fact**. No source you read → no addition. Leave it out whenever
  the course is enough; most cards have none.

When the course and the current docs disagree (a renamed product, a changed
default), `answer` and `explanation` follow the course and the `addition`
names the difference with its source.

### Types

- **`basic`** — a question and its answer. The default for definitions,
  "which service/metric/setting for X", purposes and distinctions.
- **`mc`** — `options: [{"text", "correct", "why"}]`, 3–5 options. Use it
  where the exam would discriminate between near neighbours. Distractors are
  real, plausible things from the same module or domain (other metrics, other
  deployment types, other SDK methods) — never invented names, never jokes.
  Every option gets a one-sentence `why`. Several correct options make it a
  "choose N" question; then the question says how many ("Which **two** …").
  `answer` states the correct choice(s) briefly.
- **Code gap** — an `mc` whose question contains a short Python block from
  or close to the unit's code with one `___` gap, and whose options are code
  fragments. Only for SDK calls the unit actually shows. Keep the code ≤ 8
  lines.
- **`order`** — `items` in the correct order, 3–6 short steps. For processes
  and procedures (deploy then evaluate, the steps of a RAG pipeline, the
  portal steps of an exercise). `answer` summarises the sequence in a few
  words.

## What to write cards about

1. Read the unit and its neighbours fully. Then judge the unit's teaching:
   is each concept explained so a learner could explain it back? Note gaps,
   vague passages and contradictions.
2. Pick the facts the exam outline would test. Prefer: what a thing is for,
   when to choose it over its neighbour, the names of metrics, settings,
   deployment types, roles and SDK calls, limits that drive a design choice.
   Skip marketing sentences, history, and anything you could only answer by
   having memorised the page layout.
3. **One concept per card.** A card holds what belongs together: a
   question, an answer of up to **4 bullets** (the core to recall, ~15–50
   words), and an explanation that teaches it (30–90 words). Related facts
   share a card instead of being spread over five thin ones. A concept that
   needs more than 4 bullets becomes two cards.
4. **Every defined term is covered.** Whenever the course names things and
   defines them — a `**Term**: definition` list, a table, a set of metrics,
   deployment types, evaluators, tools, roles — every single term must
   appear in the **answer** of a card. A term that only appears as a
   distractor, in an explanation or in an addition is **not** covered.
   Before writing cards, list every such term of the unit under `Terms:` in
   the review notes; after writing, put the covering card id behind each
   term. No term may be left without one.

   **Every such list gets one list card**: the question names the group,
   its context and the count — "Name the **five** criteria human evaluators
   rate responses on in a structured review." The answer is one bullet per
   term: `**Term** — a few words of definition`, in the course's order. For
   lists longer than 4, the bullet limit does not apply; for lists longer
   than 8, split into two cards by a natural sub-group. The explanation adds
   how the terms differ or when each is used. In the notes, the list card id
   goes behind the list's heading.

   Spend extra cards from the budget only on terms the exam is likely to
   ask in a scenario ("Which metric checks whether a response stays on the
   user's question?" → **Relevance**), as `basic` or `mc`.
5. The question must make sense out of context, months later, shuffled among
   1000 others: name the product ("in Microsoft Foundry", "in Azure AI
   Search"), never "according to this unit" or "the tool above".
6. Exactly one defensible answer. If a reasonable expert could answer
   differently, sharpen the question.
7. Vary the direction: not only "What is X?" but "You need Y — which X?" —
   the exam asks mostly in scenarios.

How many: at most `BUDGET`, fewer if the substance is covered with fewer.
About 70 % `basic`, the rest `mc` (including code gaps) and `order`. Do not
pad. When the budget is tight, cut in this order: scenario cards for terms
already on a list card, then near-duplicates of neighbouring units, then
trivia — never a term's only appearance.

### By unit kind

- **Introduction / Summary** — no cards unless they hold a fact found nowhere
  else in the module.
- **Content units** — as above.
- **Exercise / Übung (GitHub)** — only `order` cards for the procedure and
  `basic` cards of the form "Where in the Foundry portal do you …?" /
  "Which setting/command does …?". 2–5 cards. These train for possible labs.
- **Knowledge check / Module assessment** — one `mc` per question,
  `origin: "knowledge-check"`, question and options **verbatim**. The source
  has no solution: decide the correct option(s) from the module's units, and
  say which unit supports it in each `why`. If the module text does not settle
  it, check Microsoft Learn with WebFetch and say so in the review notes. Add
  `answer` and a short `explanation`.

### Images

Only images that carry information: architecture diagrams, portal
screenshots that show where something is, charts. Never decorative icons
("Diagram of a robot"). Download with
`curl -sL -o decks/media/ai-103/<SECTION>-<short-name>.<ext> <url>`, check the
file is a real image (`file …`), and reference it as
`media/ai-103/<SECTION>-<short-name>.<ext>`. Use `answer_images` only when
the image is itself the answer.

## Review notes (`decks/ai-103/review/<SECTION>.md`)

```markdown
# <SECTION> <unit title>

Course quality: clear | thin | confusing | wrong in places — one sentence why.
Cards: N (basic a, mc b, order c). Additions: k.
- <each addition: what was missing or wrong, and the source>
- <anything you could not settle>
```

## Reviewer

You did not write these cards. Read the unit, its neighbours, this file and
`decks/ai-103/cards/<SECTION>.json`. For every card check:

1. **Correct** against the unit text. Wrong → fix it.
2. **Layers clean**: `explanation` holds only course facts; anything else
   moves to `addition`. Open every `addition_source` with WebFetch: it must
   exist and state the fact, or the addition goes.
3. **Learning card shape**: one concept, answer ≤ 4 bullets (list cards:
   one `**Term** — definition` bullet per term, ≤ 8), an explanation that
   teaches. Thin cards on the same concept get merged; an overloaded one
   gets split. The unit stays within `BUDGET`.
4. **Standalone question** with exactly one defensible answer; scenario
   phrasing where it fits.
5. **mc**: distractors plausible and real, every `why` right, "choose N"
   stated when several are correct. Code gaps: the code is valid Python and
   the right option really completes it.
6. **Coverage**: an exam-relevant fact of the unit that has no card gets
   one; a card on trivia goes. Build your own list of every defined term in
   the unit (see rule 4 above) without looking at the generator's `Terms:`
   list, then check that each term is the answer or a correct option of a
   card's answer. Add every missing term — to the fitting list card if there
   is one, otherwise as a new card — and correct the `Terms:` list in the
   notes. Every list of defined terms needs its list card ("Name the N …").
7. Knowledge-check answers: re-derive them yourself; disagree → fix and note.

Edit the card file in place, keep ids stable for cards that stay (renumber
only new ones at the end), run `scripts/build_deck.py --only <SECTION>`, and append to the
review notes:

```markdown
## Reviewer
Changed n, removed m, added k.
- <each change, one line>
```
