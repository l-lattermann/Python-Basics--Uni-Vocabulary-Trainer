"""Split the AI-103 deck's card cap over learning paths, modules and units; write decks/ai-103/budgets.json.

Learning paths get the exam weight of the areas they teach, modules within a path and
content units within a module get shares by word count. Knowledge checks get one card per
question, GitHub exercises a fixed few, introductions, summaries and exercise stubs none.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COURSE = Path.home() / "Documents/work/AI-103/ai-103"
TOTAL, GAPS, EXERCISE, MIN_CONTENT = 1000, 80, 3, 2  # GAPS is reserved up front; the gaps get what is left
PATH_WEIGHT = {"1": 30, "2": 30, "3": 12.5, "4": 25}  # plan + genai, text, vision + extraction


def kind(title):
    """Classify a unit by its title."""
    if re.match(r"(Introduction|Summary|Exercise\b)", title):
        return "skip"
    if title.startswith("Übung"):
        return "exercise"
    if re.match(r"(Knowledge check|Module assessment)", title):
        return "kc"
    return "content"


def split(total, weights):
    """Share an integer total by weights, largest remainders first."""
    raw = [total * w / sum(weights) for w in weights]
    shares = [int(r) for r in raw]
    for i in sorted(range(len(raw)), key=lambda i: raw[i] - shares[i], reverse=True)[:total - sum(shares)]:
        shares[i] += 1
    return shares


def units():
    """Yield (path, module, section, title, file) from the course index."""
    module = None
    for line in (COURSE / "00-index.md").read_text(encoding="utf-8").splitlines():
        if m := re.match(r"^### (\d+)\.(\d+) ", line):
            module = f"{m[1]}.{m[2]}"
        elif module and (m := re.match(r"^(\d+)\. \[(.+?)\]\((.+?)\)", line)):
            yield module.split(".")[0], module, f"{module}.{m[1]}", m[2], COURSE / m[3]


def main():
    """Compute and write the budgets."""
    plan = {}
    for path, module, section, title, file in units():
        text = file.read_text(encoding="utf-8")
        entry = {"title": title, "file": str(file), "kind": kind(title), "words": len(text.split()), "budget": 0}
        if entry["kind"] == "kc":
            entry["budget"] = len(re.findall(r"^\d+\.\s*$", text, re.M))
        elif entry["kind"] == "exercise":
            entry["budget"] = EXERCISE
        plan.setdefault(path, {}).setdefault(module, {})[section] = entry

    paths = sorted(plan)
    for path, path_total in zip(paths, split(TOTAL - GAPS, [PATH_WEIGHT[p] for p in paths])):
        modules = plan[path]
        content_words = {m: sum(u["words"] for u in us.values() if u["kind"] in ("content", "exercise"))
                         for m, us in modules.items()}
        for module, module_total in zip(modules, split(path_total, list(content_words.values()))):
            content = {s: u for s, u in modules[module].items() if u["kind"] == "content"}
            free = module_total - sum(u["budget"] for u in modules[module].values())
            free = max(free, MIN_CONTENT * len(content))
            for (section, unit), share in zip(content.items(), split(free, [u["words"] for u in content.values()])):
                unit["budget"] = max(share, MIN_CONTENT)

    course = sum(u["budget"] for p in plan.values() for m in p.values() for u in m.values())
    out = {"total": TOTAL, "gaps": TOTAL - course, "units": {s: u for p in plan.values() for m in p.values() for s, u in m.items()}}
    (ROOT / "decks/ai-103/budgets.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    for path in paths:
        for module, us in plan[path].items():
            print(module, sum(u["budget"] for u in us.values()), " ".join(f"{s.split('.')[-1]}:{u['budget']}" for s, u in us.items()))
    print("course", course, "+ gaps", out["gaps"])


if __name__ == "__main__":
    main()
