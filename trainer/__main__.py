"""Start the trainer: python3 -m trainer [--deck ID] [--port 8642]."""
import argparse
import sys

from . import ROOT, deck, storage
from .server import Trainer, make_server


def default_deck():
    """Pick the first deck alphabetically that is not the sample; the sample if it is alone."""
    ids = sorted(path.stem for path in (ROOT / "decks").glob("*.json"))
    return next((i for i in ids if i != "sample"), "sample")


def main():
    """Load the deck, back up its progress and serve until interrupted."""
    parser = argparse.ArgumentParser(prog="python3 -m trainer")
    parser.add_argument("--deck", default=default_deck(), help="deck id, the file name in decks/ without .json")
    parser.add_argument("--port", type=int, default=8642)
    args = parser.parse_args()

    path = ROOT / "decks" / f"{args.deck}.json"
    if not path.exists():
        sys.exit(f"No deck file {path}")
    try:
        data, warnings = deck.load(path)
    except deck.DeckError as error:
        sys.exit(f"Deck {path.name} does not load:\n{error}")
    for warning in warnings:
        print(f"warning: {warning}")

    progress_path = ROOT / "progress" / f"{args.deck}.json"
    storage.backup(progress_path)
    server = make_server(Trainer(data, warnings, progress_path), args.port)
    print(f"{data['title']}: http://127.0.0.1:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
