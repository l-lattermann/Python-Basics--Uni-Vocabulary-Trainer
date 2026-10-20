import copy
import json

import pytest

from trainer import ROOT, deck

BASE = {
    "schema": 1,
    "id": "t",
    "title": "Test",
    "exam_areas": {"plan": {"title": "Plan", "weight": "25-30%"}},
    "sections": {"1": "One", "1.2": "One two"},
    "cards": [],
}
CARD = {"id": "c1", "type": "basic", "section": "1.2", "exam_area": "plan", "origin": "generated",
        "question": "Q?", "answer": "A."}


def check(*cards, **deck_fields):
    data = {**copy.deepcopy(BASE), **deck_fields, "cards": [{**CARD, **c} for c in cards]}
    return deck.validate(data, ROOT / "decks")


def test_sample_deck_loads_and_covers_every_type():
    data, warnings = deck.load(ROOT / "decks" / "sample.json")
    assert warnings == []
    types = [c["type"] for c in data["cards"]]
    assert {"basic", "mc", "order"} <= set(types)
    assert any(sum(o["correct"] for o in c.get("options", [])) > 1 for c in data["cards"])
    assert any("question_images" in c for c in data["cards"])


def test_valid_card_has_no_errors():
    assert check({}) == ([], [])


def test_all_errors_reported_at_once():
    errors, _ = check(
        {"id": "a", "type": "flash"},
        {"id": "a", "origin": "made-up"},
        {"id": "b", "section": "9"},
        {"id": "c", "exam_area": "nope"},
        {"id": "d", "addition": "extra"},
        {"id": "e", "questoin": "typo"},
        {"id": "f", "answer": 3},
    )
    assert errors == [
        "card a: unknown type 'flash'",
        "card a: duplicate id",
        "card a: unknown origin 'made-up'",
        "card b: unknown section '9'",
        "card c: unknown exam_area 'nope'",
        "card d: addition without addition_source",
        "card e: unknown field 'questoin'",
        "card f: answer must be str",
    ]


def test_missing_required_fields():
    data = copy.deepcopy(BASE)
    data["cards"] = [{"id": "x", "type": "basic"}]
    errors, _ = deck.validate(data, ROOT / "decks")
    assert {"card x: missing section", "card x: missing origin", "card x: missing question",
            "card x: missing answer", "card x: missing exam_area"} <= set(errors)


def test_exam_area_optional_without_exam_areas():
    data = copy.deepcopy(BASE)
    del data["exam_areas"]
    data["cards"] = [{k: v for k, v in CARD.items() if k != "exam_area"}]
    assert deck.validate(data, ROOT / "decks") == ([], [])
    data["cards"][0]["exam_area"] = "plan"
    assert deck.validate(data, ROOT / "decks")[0] == ["card c1: exam_area set but the deck has no exam_areas"]


def test_mc_structure():
    errors, _ = check(
        {"id": "one", "type": "mc", "options": [{"text": "only", "correct": True}]},
        {"id": "none", "type": "mc", "options": [{"text": "a", "correct": False}, {"text": "b", "correct": False}]},
        {"id": "bad", "type": "mc", "options": [{"text": "a", "correct": "yes"}, {"txt": "b", "correct": True}]},
        {"id": "basic", "options": []},
    )
    assert errors == [
        "card one: mc needs options: a list of at least 2",
        "card none: mc needs at least one correct option",
        "card bad: option 1: correct missing or not bool",
        "card bad: option 2: unknown field 'txt'",
        "card bad: option 2: text missing or not str",
        "card basic: options only belong on mc cards",
    ]


def test_order_structure():
    errors, _ = check({"id": "o", "type": "order", "items": ["a", "b"]}, {"id": "p", "type": "order"})
    assert errors == ["card o: order needs items: a list of at least 3 strings",
                      "card p: order needs items: a list of at least 3 strings"]


def test_images_must_exist():
    errors, _ = check({"question_images": [{"src": "media/sample/bounding-box.png", "alt": "box"},
                                           {"src": "media/sample/missing.png", "alt": "gone"},
                                           {"src": "../README.md", "alt": "outside"},
                                           {"src": "media/sample/bounding-box.png"}]})
    assert errors == ["card c1: question_images: image file not found: media/sample/missing.png",
                      "card c1: question_images: image file not found: ../README.md",
                      "card c1: question_images: image 4 needs exactly a string src and alt"]


def test_long_answer_and_explanation_warn():
    errors, warnings = check({"answer": "word " * 41, "explanation": "word " * 91})
    assert errors == []
    assert warnings == ["card c1: answer has 41 words (limit 40)",
                        "card c1: explanation has 91 words (limit 90)"]


def test_word_count_ignores_code():
    text = "Use `client.chat.completions.create` here.\n\n```python\n" + "x = 1\n" * 100 + "```\nDone now."
    assert deck.word_count(text) == 4
    assert check({"answer": "short " * 40 + "`" + "code " * 50 + "`"}) == ([], [])


def test_load_raises_with_every_error(tmp_path):
    data = {**copy.deepcopy(BASE), "id": "broken", "cards": [{**CARD, "type": "x"}, {**CARD, "origin": "y"}]}
    path = tmp_path / "broken.json"
    path.write_text(json.dumps(data))
    with pytest.raises(deck.DeckError) as info:
        deck.load(path)
    assert info.value.errors == ["card c1: unknown type 'x'", "card c1: duplicate id", "card c1: unknown origin 'y'"]


def test_deck_id_must_match_file_name(tmp_path):
    path = tmp_path / "other.json"
    path.write_text(json.dumps({**BASE, "cards": [CARD]}))
    with pytest.raises(deck.DeckError, match="does not match file name"):
        deck.load(path)
