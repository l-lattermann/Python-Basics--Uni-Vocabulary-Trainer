"""Local HTTP server: JSON API and static files."""
import json
import mimetypes
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

from . import ROOT, scheduler, storage

STATIC_DIR = ROOT / "trainer" / "static"
MEDIA_DIR = ROOT / "decks" / "media"


class Trainer:
    """One deck's progress behind a lock; every change is saved at once."""

    def __init__(self, deck, warnings, progress_path):
        self.deck = deck
        self.warnings = warnings
        self.path = Path(progress_path)
        self.progress = storage.load(self.path)
        self.cards = {card["id"]: card for card in deck["cards"]}
        self.lock = threading.Lock()

    def card(self, card_id):
        """Return a deck card with its progress state attached."""
        return {**self.cards[card_id], "progress": scheduler.state_of(self.progress, card_id)}

    def require_card(self, body):
        """Return the body's card id, or raise ValueError if the deck lacks it."""
        if body.get("id") not in self.cards:
            raise ValueError(f"unknown card {body.get('id')!r}")
        return body["id"]

    def state(self):
        """Deck meta, warnings, the unfinished session and stats."""
        with self.lock:
            current = self.progress["current"]
            if current and current["pending"]:
                current = {"number": current["number"], "mode": current["mode"], "filter": current["filter"],
                           "cards": [self.card(i) for i in current["pending"] if i in self.cards]}
            else:
                current = None
            return {"deck": {key: self.deck.get(key) for key in ("id", "title", "exam_areas", "sections")},
                    "warnings": self.warnings, "current": current,
                    "stats": scheduler.stats(self.deck, self.progress)}

    def stats(self):
        """Box, area, due, new, mastered and flagged counts."""
        with self.lock:
            return scheduler.stats(self.deck, self.progress)

    def start(self, body):
        """Start a session, abandoning any unfinished one."""
        flt = body.get("filter") or {}
        with self.lock:
            current = scheduler.start(self.deck, self.progress, body.get("mode"), flt)
            if current is None:
                return {"empty": True, "next_due_in": scheduler.next_due_in(self.deck, self.progress, flt)}
            storage.save(self.path, self.progress)
            return {"number": current["number"], "cards": [self.card(i) for i in current["pending"]]}

    def rate(self, body):
        """Record one answer; a repeated seq is acknowledged and ignored."""
        if not isinstance(body.get("correct"), bool):
            raise ValueError("correct must be true or false")
        with self.lock:
            state = scheduler.rate(self.progress, body.get("id"), body["correct"], body.get("seq"))
            if state is None:
                return {"duplicate": True}
            storage.save(self.path, self.progress)
            return {"id": body["id"], "progress": state, "pending": len(self.progress["current"]["pending"])}

    def undo(self):
        """Revert the latest rating and return the card it restored."""
        with self.lock:
            card_id = scheduler.undo(self.progress)
            storage.save(self.path, self.progress)
            return {"id": card_id, "card": self.card(card_id),
                    "pending": len(self.progress["current"]["pending"])}

    def star(self, body):
        """Toggle a card's star."""
        card_id = self.require_card(body)
        with self.lock:
            starred = scheduler.toggle_star(self.progress, card_id)
            storage.save(self.path, self.progress)
            return {"id": card_id, "starred": starred}

    def flag(self, body):
        """Flag a card with a note, or clear the flag with a null note."""
        card_id = self.require_card(body)
        if not isinstance(body.get("note"), (str, type(None))):
            raise ValueError("note must be a string or null")
        with self.lock:
            scheduler.set_flag(self.progress, card_id, body.get("note"))
            storage.save(self.path, self.progress)
            return {"id": card_id, "flag": body.get("note")}


class Handler(BaseHTTPRequestHandler):
    """Route requests to the trainer API or to files."""

    def do_GET(self):
        """Serve the API's read endpoints, the UI and deck media."""
        path = urlsplit(self.path).path
        trainer = self.server.trainer
        if path == "/api/state":
            self.send_json(trainer.state())
        elif path == "/api/stats":
            self.send_json(trainer.stats())
        elif path == "/":
            self.send_file(STATIC_DIR, "index.html")
        elif path.startswith("/static/"):
            self.send_file(STATIC_DIR, path[len("/static/"):])
        elif path.startswith("/media/"):
            self.send_file(MEDIA_DIR, path[len("/media/"):])
        else:
            self.send_json({"error": "not found"}, 404)

    def do_POST(self):
        """Run a state-changing API call; the body is JSON whatever its Content-Type."""
        path = urlsplit(self.path).path
        trainer = self.server.trainer
        routes = {"/api/session": trainer.start, "/api/rate": trainer.rate,
                  "/api/star": trainer.star, "/api/flag": trainer.flag}
        if path != "/api/undo" and path not in routes:
            self.send_json({"error": "not found"}, 404)
            return
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
            if not isinstance(body, dict):
                raise ValueError("body must be a JSON object")
            self.send_json(trainer.undo() if path == "/api/undo" else routes[path](body))
        except ValueError as error:
            self.send_json({"error": str(error)}, 400)

    def send_json(self, data, status=200):
        """Send a JSON response."""
        self.send_bytes(json.dumps(data, ensure_ascii=False).encode(), "application/json", status)

    def send_file(self, folder, relative):
        """Send a file from folder, refusing paths that leave it."""
        target = (folder / unquote(relative)).resolve()
        if not target.is_relative_to(folder.resolve()) or not target.is_file():
            self.send_json({"error": "not found"}, 404)
            return
        self.send_bytes(target.read_bytes(), mimetypes.guess_type(target.name)[0] or "application/octet-stream")

    def send_bytes(self, data, content_type, status=200):
        """Send a complete response body."""
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        """Keep the terminal free of access logs."""


def make_server(trainer, port):
    """Bind a threaded HTTP server for the trainer to 127.0.0.1."""
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.trainer = trainer
    return server
