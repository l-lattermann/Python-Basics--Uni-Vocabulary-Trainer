import random

import pytest

from trainer import scheduler as s


class NoShuffle:
    @staticmethod
    def shuffle(ids):
        pass


def make_deck(count, **fields):
    return {"cards": [{"id": f"c{i:03}", "section": "1.2", "exam_area": "plan", "origin": "generated", **fields}
                      for i in range(count)]}


def progress(session=0, **cards):
    return {"schema": 1, "session": session, "cards": {k: {**s.NEW_CARD, **v} for k, v in cards.items()},
            "current": None}


def scheduled(box, due):
    return {"box": box, "due": due, "reviews": 1}


def start(deck, prog, mode="mixed", flt=None):
    return s.start(deck, prog, mode, flt or {}, NoShuffle)


# box moves, intervals, lapses

def test_new_card_correct_goes_to_box_1():
    deck, prog = make_deck(1), progress()
    start(deck, prog, "new")
    state = s.rate(prog, "c000", True)
    assert state == {**s.NEW_CARD, "box": 1, "due": 2, "reviews": 1}
    assert prog["current"]["pending"] == []


@pytest.mark.parametrize("box", [1, 2, 3])
def test_correct_moves_up_one_box_with_its_interval(box):
    deck, prog = make_deck(1), progress(9, c000=scheduled(box, 10))
    start(deck, prog, "review")
    state = s.rate(prog, "c000", True)
    assert state["box"] == box + 1
    assert state["due"] == 10 + s.INTERVALS[box + 1]


def test_box_4_correct_is_mastered_and_never_due():
    deck, prog = make_deck(1), progress(9, c000=scheduled(4, 10))
    start(deck, prog, "review")
    state = s.rate(prog, "c000", True)
    assert (state["box"], state["due"]) == (5, None)
    assert s.build(deck, prog, "mixed", {}) == []
    assert s.build(deck, prog, "review", {}) == []


def test_wrong_drops_to_box_1_and_counts_a_lapse():
    deck, prog = make_deck(1), progress(9, c000={**scheduled(3, 10), "lapses": 2})
    start(deck, prog, "review")
    state = s.rate(prog, "c000", False)
    assert (state["box"], state["due"], state["lapses"], state["reviews"]) == (1, 11, 3, 2)
    assert prog["current"]["pending"] == ["c000"]


def test_wrong_on_a_new_card_is_no_lapse():
    deck, prog = make_deck(1), progress()
    start(deck, prog, "new")
    state = s.rate(prog, "c000", False)
    assert (state["box"], state["due"], state["lapses"]) == (1, 2, 0)


def test_every_session_counts():
    deck, prog = make_deck(2), progress(4)
    assert start(deck, prog, "new")["number"] == 5
    assert start(deck, prog, "new")["number"] == 6
    assert prog["session"] == 6


# re-queue within a session

def test_later_ratings_only_count_reviews():
    deck, prog = make_deck(1), progress(9, c000=scheduled(2, 10))
    start(deck, prog, "review")
    s.rate(prog, "c000", False)
    s.rate(prog, "c000", False)
    assert prog["current"]["pending"] == ["c000"]
    state = s.rate(prog, "c000", True)
    assert (state["box"], state["due"], state["lapses"], state["reviews"]) == (1, 11, 1, 4)
    assert prog["current"]["pending"] == []


def test_rating_a_card_not_pending_is_refused():
    deck, prog = make_deck(2), progress()
    start(deck, prog, "new")
    s.rate(prog, "c000", True)
    with pytest.raises(ValueError):
        s.rate(prog, "c000", True)
    with pytest.raises(ValueError):
        s.rate(prog, "nope", True)


def test_duplicate_seq_is_ignored():
    deck, prog = make_deck(2), progress()
    start(deck, prog, "new")
    assert s.rate(prog, "c000", False, seq=1)["reviews"] == 1
    assert s.rate(prog, "c000", False, seq=1) is None
    assert prog["cards"]["c000"]["reviews"] == 1
    assert s.rate(prog, "c000", True, seq=2)["reviews"] == 2


# modes

def test_mixed_caps_new_cards_at_15_when_enough_are_due():
    deck = make_deck(100)
    prog = progress(9, **{f"c{i:03}": scheduled(1, 10) for i in range(60)})
    ids = s.build(deck, prog, "mixed", {})
    assert len(ids) == 50
    assert sum(prog["cards"].get(i) is None for i in ids) == 15


def test_mixed_fills_up_with_new_cards():
    deck = make_deck(100)
    prog = progress(9, **{f"c{i:03}": scheduled(1, 10) for i in range(10)})
    ids = s.build(deck, prog, "mixed", {})
    assert len(ids) == 50
    assert sum(i in prog["cards"] for i in ids) == 10


def test_mixed_with_few_new_cards_takes_more_due():
    deck = make_deck(100)
    prog = progress(9, **{f"c{i:03}": scheduled(1, 10) for i in range(97)})
    ids = s.build(deck, prog, "mixed", {})
    assert len(ids) == 50
    assert sum(i not in prog["cards"] for i in ids) == 3


def test_mixed_takes_most_overdue_first_and_new_in_deck_order():
    deck = make_deck(70)
    cards = {f"c{i:03}": scheduled(1, 10 - i % 5) for i in range(40)}
    prog = progress(9, **cards)
    ids = s.build(deck, prog, "mixed", {}, NoShuffle)
    due, new = ids[:35], ids[35:]
    assert [cards[i]["due"] for i in due] == sorted(cards[i]["due"] for i in due)
    assert max(cards[i]["due"] for i in due) <= min(c["due"] for k, c in cards.items() if k not in due)
    assert new == [f"c{i:03}" for i in range(40, 55)]


def test_not_yet_due_cards_are_left_out():
    deck = make_deck(2)
    prog = progress(9, c000=scheduled(2, 10), c001=scheduled(2, 11))
    assert s.build(deck, prog, "review", {}) == ["c000"]


def test_new_mode_takes_up_to_50_new_cards_in_deck_order():
    deck = make_deck(60)
    prog = progress(0, c000=scheduled(1, 1))
    ids = s.build(deck, prog, "new", {}, NoShuffle)
    assert ids == [f"c{i:03}" for i in range(1, 51)]


def test_review_mode_only_due_and_may_be_short():
    deck = make_deck(10)
    prog = progress(9, c003=scheduled(1, 10), c004=scheduled(4, 2))
    assert sorted(s.build(deck, prog, "review", {})) == ["c003", "c004"]


def test_review_mode_caps_at_50():
    deck = make_deck(60)
    prog = progress(9, **{f"c{i:03}": scheduled(1, 10) for i in range(60)})
    assert len(s.build(deck, prog, "review", {})) == 50


def test_empty_review_reports_next_due_and_starts_nothing():
    deck = make_deck(4)
    prog = progress(9, c000=scheduled(3, 14), c001=scheduled(2, 12), c002={"box": 5, "reviews": 4})
    assert start(deck, prog, "review") is None
    assert prog["session"] == 9
    assert s.next_due_in(deck, prog, {}) == 2
    prog["session"] = 11
    assert start(deck, prog, "review")["number"] == 12


@pytest.mark.parametrize("mode", ["mixed", "review"])
def test_without_new_cards_sessions_skip_ahead_to_the_next_due(mode):
    deck = make_deck(3)
    prog = progress(9, c000=scheduled(3, 14), c001=scheduled(2, 12), c002={"box": 5, "reviews": 4})
    current = start(deck, prog, mode)
    assert (current["number"], current["pending"]) == (12, ["c001"])


def test_flagging_removes_a_card_from_the_current_session():
    deck, prog = make_deck(2), progress()
    start(deck, prog, "new")
    s.set_flag(prog, "c000", "typo")
    assert prog["current"]["pending"] == ["c001"]


def test_next_due_in_is_none_when_nothing_is_scheduled():
    assert s.next_due_in(make_deck(2), progress(3), {}) is None


def test_exam_mode_takes_all_mastered_cards():
    deck = make_deck(80)
    prog = progress(9, **{f"c{i:03}": {"box": 5} for i in range(60)}, c070=scheduled(1, 1))
    assert sorted(s.build(deck, prog, "exam", {})) == [f"c{i:03}" for i in range(60)]


def test_exam_ratings():
    deck = make_deck(2)
    prog = progress(9, c000={"box": 5, "reviews": 5}, c001={"box": 5, "reviews": 5})
    start(deck, prog, "exam")
    assert (s.rate(prog, "c000", True)["box"], prog["cards"]["c000"]["due"]) == (5, None)
    state = s.rate(prog, "c001", False)
    assert (state["box"], state["due"], state["lapses"]) == (1, 11, 1)


def test_sessions_are_shuffled():
    deck = make_deck(50)
    ids = s.build(deck, progress(), "new", {}, random.Random(1))
    assert sorted(ids) == [f"c{i:03}" for i in range(50)]
    assert ids != sorted(ids)


def test_bad_mode_and_filter_are_refused():
    deck, prog = make_deck(1), progress()
    with pytest.raises(ValueError):
        s.start(deck, prog, "cram", {})
    with pytest.raises(ValueError):
        s.start(deck, prog, "new", {"sektion": "1"})
    with pytest.raises(ValueError):
        s.start(deck, prog, "new", {"origins": "generated"})
    with pytest.raises(ValueError):
        s.start(deck, prog, "new", {"section": "1.2"})
    with pytest.raises(ValueError):
        s.start(deck, prog, "new", {"sections": "1.2"})
    with pytest.raises(ValueError):
        s.start(deck, prog, "new", {"sections": [1]})


# filters

def test_section_prefix_matches_whole_segments():
    deck = {"cards": [{"id": sec, "section": sec, "exam_area": "plan", "origin": "generated"}
                      for sec in ("1", "1.2", "1.2.3", "1.20", "1.20.1", "2.1.2")]}
    assert sorted(s.build(deck, progress(), "new", {"sections": ["1.2"]})) == ["1.2", "1.2.3"]
    assert sorted(s.build(deck, progress(), "new", {"sections": ["1"]})) == ["1", "1.2", "1.2.3", "1.20", "1.20.1"]


def test_several_sections_combine_with_or():
    deck = {"cards": [{"id": sec, "section": sec, "exam_area": "plan", "origin": "generated"}
                      for sec in ("1.2", "1.2.3", "1.20", "2.1.2", "3")]}
    assert sorted(s.build(deck, progress(), "new", {"sections": ["1.2", "2.1"]})) == ["1.2", "1.2.3", "2.1.2"]
    assert len(s.build(deck, progress(), "new", {"sections": []})) == 5


def test_exam_area_origin_and_star_filters():
    deck = {"cards": [
        {"id": "a", "section": "1", "exam_area": "plan", "origin": "generated"},
        {"id": "b", "section": "1", "exam_area": "genai", "origin": "knowledge-check"},
        {"id": "c", "section": "1", "exam_area": "vision", "origin": "outline-gap"},
    ]}
    prog = progress(0, c={"starred": True})
    assert sorted(s.build(deck, prog, "new", {"exam_areas": ["plan", "genai"]})) == ["a", "b"]
    assert sorted(s.build(deck, prog, "new", {"origins": ["knowledge-check", "outline-gap"]})) == ["b", "c"]
    assert s.build(deck, prog, "new", {"starred": True}) == ["c"]
    assert s.build(deck, prog, "new", {"exam_areas": ["plan"], "origins": ["outline-gap"]}) == []


def test_filter_applies_to_review_and_exam():
    deck = {"cards": [{"id": "a", "section": "1", "exam_area": "plan", "origin": "generated"},
                      {"id": "b", "section": "2", "exam_area": "plan", "origin": "generated"}]}
    prog = progress(5, a=scheduled(1, 1), b=scheduled(1, 1))
    assert s.build(deck, prog, "review", {"sections": ["2"]}) == ["b"]
    prog = progress(5, a={"box": 5}, b={"box": 5})
    assert s.build(deck, prog, "exam", {"sections": ["1"]}) == ["a"]


def test_flagged_cards_never_enter_sessions():
    deck = make_deck(4)
    prog = progress(9, c000={"flag": "wrong answer"}, c001={**scheduled(1, 1), "flag": ""},
                    c002={"box": 5, "flag": "typo"})
    for mode in ("mixed", "new", "review", "exam"):
        assert set(s.build(deck, prog, mode, {})) <= {"c003"}
    assert s.next_due_in(deck, prog, {}) is None


# undo

def test_undo_chain_back_to_session_start():
    deck = make_deck(3)
    prog = progress(9, c000=scheduled(2, 10), c001=scheduled(3, 10), c002=scheduled(1, 10))
    original = {k: dict(v) for k, v in prog["cards"].items()}
    start(deck, prog, "review")
    pending = list(prog["current"]["pending"])
    s.rate(prog, "c001", True)
    s.rate(prog, "c000", False)
    s.rate(prog, "c002", True)
    s.rate(prog, "c000", False)
    s.rate(prog, "c000", True)
    assert prog["current"]["pending"] == []

    assert s.undo(prog) == "c000"
    assert prog["cards"]["c000"]["reviews"] == 3 and prog["current"]["pending"] == ["c000"]
    assert s.undo(prog) == "c000"
    assert prog["cards"]["c000"]["reviews"] == 2 and prog["cards"]["c000"]["box"] == 1
    assert s.undo(prog) == "c002"
    assert prog["current"]["pending"] == ["c000", "c002"]
    assert s.undo(prog) == "c000"
    assert prog["cards"]["c000"] == original["c000"]
    assert s.undo(prog) == "c001"
    assert prog["cards"] == original
    assert prog["current"]["pending"] == pending
    assert prog["current"]["rated"] == {} and prog["current"]["history"] == []
    with pytest.raises(ValueError):
        s.undo(prog)


def test_undo_restores_a_new_card_and_keeps_star():
    deck, prog = make_deck(1), progress()
    start(deck, prog, "new")
    s.rate(prog, "c000", True)
    s.toggle_star(prog, "c000")
    s.undo(prog)
    assert prog["cards"]["c000"] == {**s.NEW_CARD, "starred": True}
    assert s.build(deck, prog, "new", {}) == ["c000"]


# star and flag

def test_star_and_flag_leave_boxes_alone():
    deck = make_deck(1)
    prog = progress(3, c000=scheduled(3, 5))
    assert s.toggle_star(prog, "c000") is True
    s.set_flag(prog, "c000", "answer is outdated")
    assert prog["cards"]["c000"] == {**s.NEW_CARD, **scheduled(3, 5), "starred": True, "flag": "answer is outdated"}
    s.set_flag(prog, "c000", None)
    assert s.toggle_star(prog, "c000") is False
    assert prog["cards"]["c000"] == {**s.NEW_CARD, **scheduled(3, 5)}
    assert s.toggle_star(progress(), "c000") is True


# stats and unknown ids

def test_stats():
    deck = {"exam_areas": {"plan": {}, "genai": {}}, "cards": [
        {"id": "a", "section": "1", "exam_area": "plan", "origin": "generated"},
        {"id": "b", "section": "1", "exam_area": "plan", "origin": "generated"},
        {"id": "c", "section": "1", "exam_area": "genai", "origin": "generated"},
        {"id": "d", "section": "1", "exam_area": "genai", "origin": "generated"},
    ]}
    prog = progress(4, b=scheduled(2, 5), c={"box": 5}, d={"flag": "x"}, gone=scheduled(1, 1))
    stats = s.stats(deck, prog)
    assert stats["boxes"] == {"0": 2, "1": 0, "2": 1, "3": 0, "4": 0, "5": 1}
    assert stats["exam_areas"]["plan"] == {"0": 1, "1": 0, "2": 1, "3": 0, "4": 0, "5": 0}
    assert stats["exam_areas"]["genai"]["5"] == 1
    assert (stats["due"], stats["new"], stats["mastered"], stats["flagged"], stats["total"]) == (1, 1, 1, 1, 4)
    assert stats["sections"] == {"1": {"total": 4, "due": 1, "new": 1, "mastered": 1}}
    assert stats["area_counts"] == {"plan": {"total": 2, "due": 1, "new": 1, "mastered": 0},
                                    "genai": {"total": 2, "due": 0, "new": 0, "mastered": 1}}


def test_unknown_ids_in_progress_are_ignored_and_kept():
    deck = make_deck(1)
    prog = progress(0, removed={"box": 3, "due": 1})
    start(deck, prog, "mixed")
    assert prog["current"]["pending"] == ["c000"]
    assert prog["cards"]["removed"] == {**s.NEW_CARD, "box": 3, "due": 1}
