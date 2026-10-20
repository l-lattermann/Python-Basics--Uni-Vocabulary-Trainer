# Vocabulary Trainer

A keyboard-only flashcard trainer for exam preparation. It runs as a small
local web app: a Python server on your Mac (standard library only, nothing to
install) and one page in the browser. Cards come as JSON decks; spacing
follows Leitner boxes counted in sessions, not days.

The current deck is **AI-103: Develop AI apps and agents on Azure**, generated
from the Microsoft Learn course with Claude Code (see [Decks](#decks)).

## Start

Double-click `start_vocabtrainer.command`. It starts the server and opens
`http://127.0.0.1:8642` in Firefox. Put Firefox in fullscreen — the page
background matches the macOS dark window colour. Closing the terminal window
stops the server.

Or from a terminal, in this folder:

```bash
python3 -m trainer                 # first deck in decks/ (Python 3.10+)
python3 -m trainer --deck sample   # a specific deck
```

## Keys

| Key | |
|---|---|
| `↑` `↓` | move the cursor (menus, options, steps) |
| `Space` | reveal · select · grab/drop a step · continue |
| `←` / `F` | didn't know it |
| `→` / `J` | knew it · submit a choice or an order |
| `D` | undo the last rating |
| `K` | star the card ★ |
| `L` | flag the card with a note; it leaves the sessions until fixed |
| `Esc` | back to the start screen (the session resumes later) |

## Card types

- **basic** — question, then the answer: the short core on top, the
  explanation below, and an **Addition** block for anything that is not in the
  course (always with its Microsoft Learn source).
- **mc** — multiple choice, single or "choose N", graded automatically, with a
  reason for every option. Code-gap questions are mc cards with a Python
  snippet.
- **order** — put the steps in order: grab a step with `Space`, move it with
  `↑` `↓`, drop it with `Space`, submit with `→`.

## How learning works

- A **session** is 50 cards. In the mixed mode up to 15 of them are new, the
  rest are due reviews; with nothing due it fills up with new cards. The
  start menu also offers *new only*, *review only* and an *exam mode* that
  runs through every mastered card once.
- **Leitner boxes**: a card you know moves up one box and comes back after
  1, 3, 7 and then 14 sessions. After box 4 it is *mastered* and only appears
  in exam mode. A miss sends it back to box 1, and it repeats within the
  session until you get it right.
- Every session counts toward those intervals, in any mode.
- The filter (exam area, chapter, origin, starred) applies to every mode.

## Files

| Path | What |
|---|---|
| `trainer/` | the app: `deck.py` (load + validate), `scheduler.py` (boxes, sessions), `storage.py` (progress file), `server.py` (JSON API), `static/` (the page) |
| `decks/<id>.json` | a deck, built by `scripts/build_deck.py` — don't edit by hand |
| `decks/<id>/` | the deck's sources: `meta.json` (title, exam areas, chapters), `cards/<section>.json`, `review/<section>.md` |
| `decks/media/<id>/` | images used by cards |
| `progress/<id>.json` | your learning state, committed so it travels with the repo |
| `progress/backups/` | the last 20 copies, one per start (not committed) |
| `prompts/` | how cards are generated and reviewed, and the exam outline |
| `legacy/` | the old terminal trainer and its `vocabulary.txt`, unchanged; start it with `legacy/start_legacy.command` |

Progress is saved after every answer (written to a temporary file, then
renamed, so a crash can't corrupt it). If you close the window mid-session,
the next start offers to continue where you stopped.

## Decks

Cards live per course unit in `decks/<id>/cards/<section>.json`.
`prompts/generate-deck.md` is the brief for Claude Code: one agent writes a
unit's cards from the course text, a second one reviews them against the
source. Each unit also gets notes on how well the course explains it in
`decks/<id>/review/`. After changing card files:

```bash
python3 scripts/build_deck.py ai-103
```

It merges the cards into `decks/ai-103.json` and stops on any format error
(missing field, unknown section, mc without a correct option, addition without
a source, …). It warns when an answer exceeds 40 words or an explanation 90.

Progress is keyed by card id, so editing a card's text keeps its progress;
deleting a card just leaves its old entry unused.

## Tests

```bash
python3 -m pytest
```

Deck validation, every scheduling rule, the progress file and the API have
tests. The page itself is tested by hand.
