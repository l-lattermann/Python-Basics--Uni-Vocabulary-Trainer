import json
import os

from trainer import storage


def test_missing_file_is_empty_progress(tmp_path):
    assert storage.load(tmp_path / "x.json") == {"schema": 1, "session": 0, "cards": {}, "current": None}


def test_save_round_trips_and_leaves_no_temp_file(tmp_path):
    path = tmp_path / "sub" / "deck.json"
    progress = {"schema": 1, "session": 3, "cards": {"a": {"box": 2}}, "current": None}
    storage.save(path, progress)
    assert storage.load(path) == progress
    assert [p.name for p in path.parent.iterdir()] == ["deck.json"]


def test_save_is_atomic(tmp_path, monkeypatch):
    path = tmp_path / "deck.json"
    storage.save(path, {"schema": 1, "session": 1, "cards": {}, "current": None})
    calls = []
    monkeypatch.setattr(os, "fsync", lambda fd: calls.append(fd))

    def crash(src, dst):
        raise OSError("disk gone")
    monkeypatch.setattr(os, "replace", crash)
    try:
        storage.save(path, {"schema": 1, "session": 2, "cards": {}, "current": None})
    except OSError:
        pass
    assert calls
    assert json.loads(path.read_text())["session"] == 1


def test_backup_keeps_newest_20(tmp_path):
    path = tmp_path / "deck.json"
    assert storage.backup(path) is None
    made = []
    for session in range(25):
        storage.save(path, {"schema": 1, "session": session, "cards": {}, "current": None})
        made.append(storage.backup(path))
    kept = sorted((tmp_path / "backups" / "deck").iterdir())
    assert kept == made[5:]
    assert json.loads(kept[-1].read_text())["session"] == 24
    assert json.loads(kept[0].read_text())["session"] == 5
