import json
import threading
import urllib.error
import urllib.request

import pytest

from trainer import ROOT, deck
from trainer.server import Trainer, make_server


@pytest.fixture
def api(tmp_path):
    data, warnings = deck.load(ROOT / "decks" / "sample.json")
    server = make_server(Trainer(data, warnings, tmp_path / "sample.json"), 0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_address[1]}"

    def call(path, body=None, content_type="application/json"):
        request = urllib.request.Request(base + path, data=None if body is None else json.dumps(body).encode(),
                                         headers={"Content-Type": content_type})
        try:
            with urllib.request.urlopen(request) as response:
                raw = response.read()
                return response.status, json.loads(raw) if path.startswith("/api/") else raw
        except urllib.error.HTTPError as error:
            return error.code, json.loads(error.read())

    yield call
    server.shutdown()
    server.server_close()


def test_session_rate_undo(api, tmp_path):
    status, state = api("/api/state")
    assert status == 200
    assert state["deck"]["id"] == "sample" and state["current"] is None
    assert state["stats"]["new"] == 8

    status, session = api("/api/session", {"mode": "mixed", "filter": {}})
    assert session["number"] == 1 and len(session["cards"]) == 8
    first = session["cards"][0]
    assert first["progress"]["box"] == 0 and "question" in first

    status, rated = api("/api/rate", {"id": first["id"], "correct": True, "seq": 1}, "text/plain;charset=UTF-8")
    assert status == 200 and rated["progress"]["box"] == 1 and rated["pending"] == 7
    assert api("/api/rate", {"id": first["id"], "correct": True, "seq": 1})[1] == {"duplicate": True}
    saved = json.loads((tmp_path / "sample.json").read_text())
    assert saved["cards"][first["id"]]["box"] == 1

    status, state = api("/api/state")
    assert len(state["current"]["cards"]) == 7

    status, undone = api("/api/undo", {})
    assert undone["id"] == first["id"] and undone["card"]["progress"]["box"] == 0 and undone["pending"] == 8
    assert api("/api/undo", {}) == (400, {"error": "nothing to undo"})

    assert api("/api/star", {"id": first["id"]})[1] == {"id": first["id"], "starred": True}
    assert api("/api/flag", {"id": first["id"], "note": "typo"})[1] == {"id": first["id"], "flag": "typo"}
    assert api("/api/stats")[1]["flagged"] == 1
    assert api("/api/session", {"mode": "review"})[1] == {"empty": True, "next_due_in": None}


def test_errors_and_files(api):
    assert api("/api/session", {"mode": "cram"})[0] == 400
    assert api("/api/rate", {"id": "1.1-01", "correct": "yes"})[0] == 400
    assert api("/api/star", {"id": "nope"})[0] == 400
    assert api("/api/nope", {})[0] == 404
    assert b'src="/static/app.js"' in api("/")[1]
    assert api("/static/app.js")[1].startswith(b"import hljs")
    assert api("/media/sample/bounding-box.png")[1].startswith(b"\x89PNG")
    assert api("/media/../../README.md")[0] == 404
