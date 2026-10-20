"""Assemble decks/<id>.json from decks/<id>/meta.json and the card files in decks/<id>/cards/.

python3 scripts/build_deck.py [ID]                  merge, validate and write the deck
python3 scripts/build_deck.py [ID] --only SECTION   validate one card file, write nothing
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from trainer import deck  # noqa: E402


def section_key(path):
    """Sort card files by section number, numerically."""
    return [int(part) for part in path.stem.split(".") if part.isdigit()]


def main():
    """Merge or check, validate, and exit non-zero on any error."""
    parser = argparse.ArgumentParser()
    parser.add_argument("deck_id", nargs="?", default="ai-103")
    parser.add_argument("--only", metavar="SECTION", help="validate decks/<id>/cards/SECTION.json alone")
    args = parser.parse_args()

    source = ROOT / "decks" / args.deck_id
    built = json.loads((source / "meta.json").read_text(encoding="utf-8"))
    paths = [source / "cards" / f"{args.only}.json"] if args.only else sorted(
        (source / "cards").glob("*.json"), key=section_key)
    built["cards"] = [card for path in paths for card in json.loads(path.read_text(encoding="utf-8"))]
    errors, warnings = deck.validate(built, ROOT / "decks")
    for line in warnings:
        print(f"warning: {line}")
    if errors:
        sys.exit("\n".join(errors))
    if args.only:
        print(f"{args.only}: {len(built['cards'])} cards ok")
        return
    (ROOT / "decks" / f"{args.deck_id}.json").write_text(
        json.dumps(built, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{args.deck_id}: {len(built['cards'])} cards")


if __name__ == "__main__":
    main()
