#!/usr/bin/env python3

import os
import random
import time
from dataclasses import dataclass
from typing import List

@dataclass
class Entry:
    question: str
    answer: str
    known: bool = False
    seen: bool = False

    path_known = "known.txt"
    path_not_known = "not_known.txt"
    path_all = "vocabulary.txt"

def clear():
    os.system('clear' if os.name == 'posix' else 'cls')

def validate_format(entries: list[Entry]):
    for entry in entries:
        q_marker = entry.question[:2]
        a_marker = entry.answer[:2]
        if q_marker != "Q:" or a_marker != "A:":
            raise ValueError(f"❌ Format error: Each entry must start with 'Q:' for question and 'A:' for answer. Found: {entry.question} / {entry.answer}")
            return       
    print("✅ Format validated successfully.")
            


def load_vocab_file(path: str) -> List[Entry]:
    with open(path, "r") as f:
        lines = f.read().splitlines()
    if len(lines) % 2 != 0:
        raise ValueError("❌ Format error: Vocabulary file must have even number of lines (Q/A pairs).")
    return [Entry(lines[i], lines[i+1]) for i in range(0, len(lines), 2)]

def print_header(mode="Trainer"):
    clear()
    print("\n" * 5)
    print(f"####### Vocabulary Trainer ({mode}) #######")
    print("# = known | Enter = show answer | q = quit | s = skip | r = repeat | k = repeat known\n")

def prompt_for_file(msg: str) -> str:
    print(msg)
    while True:
        path = input("File path: ").strip().strip("'")
        if os.path.exists(path):
            return path
        print("Invalid path. Try again.\n")

def save_vocab(entries: List[Entry]):
    known = [e for e in entries if e.known and e.seen]
    not_known = [e for e in entries if not e.known and e.seen]

    with open(Entry.path_known, "w") as f:
        for e in known:
            f.write(f"{e.question}\n{e.answer}\n")

    with open(Entry.path_not_known, "w") as f:
        for e in not_known:
            f.write(f"{e.question}\n{e.answer}\n")

def run_trainer(entries: List[Entry], label="Trainer") -> str:
    for entry in entries:
        print_header(label)
        print(f"{entry.question}\n")
        cmd = input().strip().lower()
        if cmd == "q":
            return "q"
        elif cmd == "s":
            break
        elif cmd == "r":
            return "r"
        elif cmd == "#":
            print(f"{entry.answer}\n")
            entry.known = True
            entry.seen = True
            input()
        elif cmd == "k":
            return "k"
        else: 
            print(f"{entry.answer}\n")
            if input("✔ Known? (# to confirm): ").strip() == "#":
                entry.known = True
                entry.seen = True
            else:
                entry.known = False
                entry.seen = True
    return "done"

def main():
    clear()

    # Load vocab
    all_path = Entry.path_all if os.path.exists(Entry.path_all) else prompt_for_file("No 'vocabulary.txt' found.")
    all_vocab = load_vocab_file(all_path)
    validate_format(all_vocab)

    known = []
    not_known = []

    if os.path.exists(Entry.path_known):
        known = load_vocab_file(Entry.path_known)
        # Set all known entries known:True and seen:True
        validate_format(known)
        for e in known:
            e.known = True
            e.seen = True
        
    if os.path.exists(Entry.path_not_known):
        not_known = load_vocab_file(Entry.path_not_known)
        # Set all not known entries known:False and seen:True
        validate_format(not_known)
        for e in not_known:
            e.known = False
            e.seen = True

    while True:
        # known first
        if not_known:
            res = run_trainer(not_known, label="Not Known")
            if res == "q":
                save_vocab(not_known + known)
                break
            elif res == "k":
                res = run_trainer(known, label="Known")
                if res == "q":
                    save_vocab(known + not_known)
                    break
            elif res == "r":
                res = run_trainer(not_known, label="Repeat Not Known")
                if res == "q":
                    save_vocab(known + not_known)
                    break

        # Unseen entries
        seen_qs = {e.question for e in known + not_known}
        unseen = [e for e in all_vocab if e.question not in seen_qs]
        if unseen:
            res = run_trainer(unseen, label="Unseen")
            if res == "q":
                save_vocab(known + not_known + unseen)
                break
            elif res == "r":
                res = run_trainer(known, label="Known")
                if res == "q":
                    save_vocab(known + not_known + unseen)
                    break
            elif res == "k":
                res = run_trainer(known, label="Not Known")
                if res == "q":
                    save_vocab(known + not_known + unseen)
                    break    



    save_vocab(known + not_known + unseen)
    input("🎉 All done. Press Enter to exit...")

if __name__ == "__main__":
    main()
