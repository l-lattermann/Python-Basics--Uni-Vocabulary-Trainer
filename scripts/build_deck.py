"""Assemble decks/<id>.json from decks/<id>/meta.json and the card files in decks/<id>/cards/."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from trainer import deck  # noqa: E402


def section_key(path):
    """Sort card files by section number, numerically."""
    return [int(part) for part in path.stem.split(".") if part.isdigit()]


def main(deck_id):
    """Merge, validate and write the deck; exit non-zero if it does not validate."""
    source = ROOT / "decks" / deck_id
    built = json.loads((source / "meta.json").read_text(encoding="utf-8"))
    built["cards"] = [card for path in sorted((source / "cards").glob("*.json"), key=section_key)
                      for card in json.loads(path.read_text(encoding="utf-8"))]
    errors, warnings = deck.validate(built, ROOT / "decks")
    for line in warnings:
        print(f"warning: {line}")
    if errors:
        sys.exit("\n".join(errors))
    (ROOT / "decks" / f"{deck_id}.json").write_text(json.dumps(built, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{deck_id}: {len(built['cards'])} cards")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "ai-103")
