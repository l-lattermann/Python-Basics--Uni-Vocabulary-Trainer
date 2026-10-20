"""Leitner scheduling and session building."""
import random

INTERVALS = {1: 1, 2: 3, 3: 7, 4: 14}
MASTERED = 5
SESSION_SIZE = 50
NEW_PER_SESSION = 15
MODES = ("mixed", "new", "review", "exam")
FILTER_FIELDS = {"exam_areas": list, "sections": list, "origins": list, "starred": bool}
NEW_CARD = {"box": 0, "due": None, "reviews": 0, "lapses": 0, "starred": False, "flag": None}
SCHEDULE_FIELDS = ("box", "due", "reviews", "lapses")
COUNTS = ("total", "due", "new", "mastered")


def state_of(progress, card_id):
    """Return a card's progress state; the new-card default when it has none."""
    return progress["cards"].get(card_id, NEW_CARD)


def entry(progress, card_id):
    """Return a card's stored progress state, creating it if absent."""
    return progress["cards"].setdefault(card_id, dict(NEW_CARD))


def is_due(state, number):
    """Tell whether a card is due in session `number`."""
    return state["box"] in INTERVALS and state["due"] <= number


def matches(card, state, flt):
    """Tell whether a card passes a session filter."""
    sections = flt.get("sections")
    return ((not flt.get("exam_areas") or card.get("exam_area") in flt["exam_areas"])
            and (not sections or any(in_section(card["section"], prefix) for prefix in sections))
            and (not flt.get("origins") or card["origin"] in flt["origins"])
            and (not flt.get("starred") or state["starred"]))


def in_section(section, prefix):
    """Tell whether a section lies in the chapter `prefix`: 1.2 holds 1.2 and 1.2.3, not 1.20."""
    return section == prefix or section.startswith(prefix + ".")


def candidates(deck, progress, flt):
    """Return (card, state) for unflagged cards passing the filter, in deck order."""
    states = ((card, state_of(progress, card["id"])) for card in deck["cards"])
    return [(card, state) for card, state in states if state["flag"] is None and matches(card, state, flt)]


def check_request(mode, flt):
    """Raise ValueError for an unknown mode or a malformed filter."""
    if mode not in MODES:
        raise ValueError(f"mode must be one of {', '.join(MODES)}")
    if not isinstance(flt, dict):
        raise ValueError("filter must be an object")
    for key, value in flt.items():
        if key not in FILTER_FIELDS or not isinstance(value, FILTER_FIELDS[key]) or (
                isinstance(value, list) and not all(isinstance(item, str) for item in value)):
            raise ValueError(f"bad filter field {key!r}")


def build(deck, progress, mode, flt, rng=random):
    """Pick the card ids for the next session, shuffled."""
    number = progress["session"] + 1
    pool = candidates(deck, progress, flt)
    if mode == "exam":
        ids = [card["id"] for card, state in pool if state["box"] == MASTERED]
    else:
        due = [card["id"] for card, state in sorted(pool, key=lambda cs: cs[1]["due"] or 0)
               if is_due(state, number)]
        new = [card["id"] for card, state in pool if state["box"] == 0]
        if mode == "new":
            ids = new[:SESSION_SIZE]
        elif mode == "review":
            ids = due[:SESSION_SIZE]
        else:
            new_count = min(len(new), max(NEW_PER_SESSION, SESSION_SIZE - len(due)))
            ids = due[:SESSION_SIZE - new_count] + new[:new_count]
    rng.shuffle(ids)
    return ids


def start(deck, progress, mode, flt, rng=random):
    """Begin the next session and return it; None when no card qualifies."""
    check_request(mode, flt)
    ids = build(deck, progress, mode, flt, rng)
    pool = candidates(deck, progress, flt)
    if not ids and mode in ("mixed", "review") and not any(state["box"] == 0 for _, state in pool):
        # No new cards left to pass the sessions with: skip ahead to the next due one.
        progress["session"] += next_due_in(deck, progress, flt) or 0
        ids = build(deck, progress, mode, flt, rng)
    if not ids:
        return None
    progress["session"] += 1
    progress["current"] = {"number": progress["session"], "mode": mode, "filter": flt,
                           "pending": ids, "rated": {}, "history": [], "seqs": []}
    return progress["current"]


def next_due_in(deck, progress, flt):
    """Count the sessions to do before the earliest scheduled card is due; None if none is."""
    dues = [state["due"] for _, state in candidates(deck, progress, flt) if state["box"] in INTERVALS]
    return max(min(dues) - progress["session"] - 1, 0) if dues else None


def rate(progress, card_id, correct, seq=None):
    """Apply a rating to a pending card; return its state, or None for an already-seen seq."""
    current = progress["current"]
    if current and seq is not None and seq in current["seqs"]:
        return None
    if not current or card_id not in current["pending"]:
        raise ValueError(f"card {card_id!r} is not pending in the current session")
    state = entry(progress, card_id)
    if card_id not in current["rated"]:
        current["rated"][card_id] = {"before": dict(state), "correct": correct}
        if correct:
            state["box"] = min(state["box"] + 1, MASTERED)
        else:
            state["lapses"] += state["box"] > 0
            state["box"] = 1
        state["due"] = current["number"] + INTERVALS[state["box"]] if state["box"] in INTERVALS else None
    state["reviews"] += 1
    index = None
    if correct:
        index = current["pending"].index(card_id)
        del current["pending"][index]
    current["history"].append({"id": card_id, "index": index})
    if seq is not None:
        current["seqs"].append(seq)
    return state


def undo(progress):
    """Revert the latest rating of the current session; return the card id."""
    current = progress["current"]
    if not current or not current["history"]:
        raise ValueError("nothing to undo")
    last = current["history"].pop()
    card_id = last["id"]
    state = progress["cards"][card_id]
    if any(rating["id"] == card_id for rating in current["history"]):
        state["reviews"] -= 1
    else:
        before = current["rated"].pop(card_id)["before"]
        state.update({key: before[key] for key in SCHEDULE_FIELDS})
    if last["index"] is not None:
        current["pending"].insert(last["index"], card_id)
    return card_id


def toggle_star(progress, card_id):
    """Flip a card's star and return the new value."""
    state = entry(progress, card_id)
    state["starred"] = not state["starred"]
    return state["starred"]


def set_flag(progress, card_id, note):
    """Flag a card with a note, or clear the flag with None; a flagged card leaves the current session."""
    entry(progress, card_id)["flag"] = note
    current = progress["current"]
    if note is not None and current and card_id in current["pending"]:
        current["pending"].remove(card_id)


def stats(deck, progress):
    """Count cards per box, plus total, due, new and mastered per card section and exam area."""
    number = progress["session"] + 1
    boxes = {str(box): 0 for box in range(MASTERED + 1)}
    areas = {area: dict(boxes) for area in deck.get("exam_areas") or {}}
    sections, area_counts = {}, {area: dict.fromkeys(COUNTS, 0) for area in areas}
    due = new = flagged = 0
    for card in deck["cards"]:
        state = state_of(progress, card["id"])
        box = str(state["box"])
        boxes[box] += 1
        counts = [sections.setdefault(card["section"], dict.fromkeys(COUNTS, 0))]
        if card.get("exam_area"):
            areas[card["exam_area"]][box] += 1
            counts.append(area_counts[card["exam_area"]])
        unflagged = state["flag"] is None
        flagged += not unflagged
        due += unflagged and is_due(state, number)
        new += unflagged and state["box"] == 0
        for count in counts:
            count["total"] += 1
            count["due"] += unflagged and is_due(state, number)
            count["new"] += unflagged and state["box"] == 0
            count["mastered"] += state["box"] == MASTERED
    return {"session": progress["session"], "total": len(deck["cards"]), "boxes": boxes,
            "exam_areas": areas, "due": due, "new": new, "mastered": boxes[str(MASTERED)],
            "flagged": flagged, "sections": sections, "area_counts": area_counts}
