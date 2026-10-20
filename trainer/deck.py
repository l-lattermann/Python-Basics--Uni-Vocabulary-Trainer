"""Load and validate decks."""
import json
import re
from pathlib import Path

TYPES = ("basic", "mc", "order")
ORIGINS = ("generated", "knowledge-check", "outline-gap")
IMAGE_FIELDS = ("question_images", "answer_images", "explanation_images", "addition_images")
CARD_FIELDS = {
    "id": str, "type": str, "section": str, "exam_area": str, "origin": str,
    "source_url": str, "tags": list, "question": str, "answer": str,
    "explanation": str, "addition": str, "addition_source": str,
    "options": list, "items": list,
    **dict.fromkeys(IMAGE_FIELDS, list),
}
REQUIRED = ("id", "type", "section", "origin", "question", "answer")
DECK_FIELDS = {"schema": int, "id": str, "title": str, "exam_areas": dict, "sections": dict, "cards": list}
MAX_WORDS = {"answer": 70, "explanation": 120}
CODE = re.compile(r"```.*?```|`[^`\n]*`", re.S)


class DeckError(Exception):
    """A deck that failed validation; carries every error."""

    def __init__(self, errors):
        super().__init__("\n".join(errors))
        self.errors = errors


def word_count(markdown):
    """Count words outside fenced code blocks and inline code."""
    return len(CODE.sub(" ", markdown).split())


def load(path):
    """Read and validate a deck file; return (deck, warnings) or raise DeckError."""
    path = Path(path)
    deck = json.loads(path.read_text(encoding="utf-8"))
    errors, warnings = validate(deck, path.parent)
    if isinstance(deck, dict) and deck.get("id") != path.stem:
        errors.insert(0, f"deck: id {deck.get('id')!r} does not match file name {path.stem!r}")
    if errors:
        raise DeckError(errors)
    return deck, warnings


def validate(deck, base):
    """Return (errors, warnings) for a parsed deck; image paths resolve against base."""
    if not isinstance(deck, dict):
        return ["deck: not a JSON object"], []
    errors = [f"deck: unknown field {key!r}" for key in deck.keys() - DECK_FIELDS.keys()]
    errors += [f"deck: {key} missing or not {kind.__name__}" for key, kind in DECK_FIELDS.items()
               if (key in deck or key != "exam_areas") and not isinstance(deck.get(key), kind)]
    if deck.get("schema") != 1:
        errors.append(f"deck: unsupported schema {deck.get('schema')!r}")
    exam_areas, sections = deck.get("exam_areas"), deck.get("sections")
    if not isinstance(deck.get("cards"), list) or not isinstance(sections, dict) or not isinstance(
            exam_areas, (dict, type(None))):
        return errors, []
    for key, area in (exam_areas or {}).items():
        if not isinstance(area, dict) or area.keys() != {"title", "weight"} or not all(
                isinstance(v, str) for v in area.values()):
            errors.append(f"deck: exam area {key!r} needs exactly a string title and weight")
    if not all(isinstance(v, str) for v in sections.values()):
        errors.append("deck: section titles must be strings")

    warnings, seen = [], set()
    for index, card in enumerate(deck["cards"]):
        if not isinstance(card, dict):
            errors.append(f"card #{index}: not an object")
            continue
        name = card["id"] if isinstance(card.get("id"), str) else f"#{index}"
        problems = card_errors(card, sections, exam_areas, base)
        if name in seen:
            problems.insert(0, "duplicate id")
        seen.add(name)
        errors += [f"card {name}: {problem}" for problem in problems]
        for key, limit in MAX_WORDS.items():
            if isinstance(card.get(key), str) and word_count(card[key]) > limit:
                warnings.append(f"card {name}: {key} has {word_count(card[key])} words (limit {limit})")
    return errors, warnings


def card_errors(card, sections, exam_areas, base):
    """List what is wrong with one card."""
    errors = [f"unknown field {key!r}" for key in card.keys() - CARD_FIELDS.keys()]
    required = REQUIRED + (("exam_area",) if exam_areas is not None else ())
    errors += [f"missing {key}" for key in required if key not in card]
    errors += [f"{key} must be {kind.__name__}" for key, kind in CARD_FIELDS.items()
               if key in card and not isinstance(card[key], kind)]
    ok = {key for key, kind in CARD_FIELDS.items() if isinstance(card.get(key), kind)}

    errors += [f"empty {key}" for key in ("question", "answer") if key in ok and not card[key].strip()]
    if "type" in ok and card["type"] not in TYPES:
        errors.append(f"unknown type {card['type']!r}")
    if "origin" in ok and card["origin"] not in ORIGINS:
        errors.append(f"unknown origin {card['origin']!r}")
    if "section" in ok and card["section"] not in sections:
        errors.append(f"unknown section {card['section']!r}")
    if "exam_area" in ok:
        if exam_areas is None:
            errors.append("exam_area set but the deck has no exam_areas")
        elif card["exam_area"] not in exam_areas:
            errors.append(f"unknown exam_area {card['exam_area']!r}")
    if "tags" in ok and not all(isinstance(tag, str) for tag in card["tags"]):
        errors.append("tags must be strings")
    if "addition" in card and "addition_source" not in card:
        errors.append("addition without addition_source")

    kind = card.get("type")
    if "options" in card and kind != "mc":
        errors.append("options only belong on mc cards")
    if "items" in card and kind != "order":
        errors.append("items only belong on order cards")
    if kind == "mc":
        errors += option_errors(card.get("options"))
    if kind == "order":
        items = card.get("items")
        if not isinstance(items, list) or len(items) < 3 or not all(isinstance(i, str) for i in items):
            errors.append("order needs items: a list of at least 3 strings")

    for key in IMAGE_FIELDS:
        if key in ok:
            errors += [f"{key}: {problem}" for problem in image_errors(card[key], base)]
    return errors


def option_errors(options):
    """List what is wrong with an mc card's options."""
    if not isinstance(options, list) or len(options) < 2:
        return ["mc needs options: a list of at least 2"]
    errors = []
    for number, option in enumerate(options, 1):
        if not isinstance(option, dict):
            errors.append(f"option {number} is not an object")
            continue
        errors += [f"option {number}: unknown field {key!r}" for key in option.keys() - {"text", "correct", "why"}]
        if not isinstance(option.get("text"), str):
            errors.append(f"option {number}: text missing or not str")
        if not isinstance(option.get("correct"), bool):
            errors.append(f"option {number}: correct missing or not bool")
        if "why" in option and not isinstance(option["why"], str):
            errors.append(f"option {number}: why must be str")
    if not any(isinstance(o, dict) and o.get("correct") is True for o in options):
        errors.append("mc needs at least one correct option")
    return errors


def image_errors(images, base):
    """List what is wrong with an image list; src must name a file under base."""
    errors = []
    for number, image in enumerate(images, 1):
        if not isinstance(image, dict) or image.keys() != {"src", "alt"} or not all(
                isinstance(v, str) for v in image.values()):
            errors.append(f"image {number} needs exactly a string src and alt")
            continue
        path = (Path(base) / image["src"]).resolve()
        if not path.is_relative_to(Path(base).resolve()) or not path.is_file():
            errors.append(f"image file not found: {image['src']}")
    return errors
