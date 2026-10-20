"""List card pairs within a module whose question and answer share most of their words.

python3 scripts/find_duplicates.py [ID] [--threshold 0.5]
"""
import argparse
import itertools
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STOP = set("a an and are as at be by can do does for from how in is it of on or that the this to what when which with you your".split())


def words(card):
    """Content words of a card's question and answer."""
    text = f"{card['question']} {card['answer']}".lower()
    return {w for w in re.findall(r"[a-z0-9][a-z0-9+.-]*", text) if w not in STOP}


def main():
    """Print likely duplicate pairs, most similar first."""
    parser = argparse.ArgumentParser()
    parser.add_argument("deck_id", nargs="?", default="ai-103")
    parser.add_argument("--threshold", type=float, default=0.5)
    args = parser.parse_args()

    modules = defaultdict(list)
    for path in (ROOT / "decks" / args.deck_id / "cards").glob("*.json"):
        for card in json.loads(path.read_text(encoding="utf-8")):
            modules[".".join(card["section"].split(".")[:2])].append((card, words(card)))

    pairs = []
    for cards in modules.values():
        for (a, wa), (b, wb) in itertools.combinations(cards, 2):
            if a["section"] != b["section"] and wa and wb:
                score = len(wa & wb) / len(wa | wb)
                if score >= args.threshold:
                    pairs.append((score, a, b))
    for score, a, b in sorted(pairs, key=lambda p: -p[0]):
        print(f"{score:.2f}  {a['id']}  {b['id']}\n      {a['question'][:100]}\n      {b['question'][:100]}")
    print(f"{len(pairs)} pairs")


if __name__ == "__main__":
    main()
