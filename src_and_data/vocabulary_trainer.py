#!/usr/bin/env python3

import os
import sys
from dataclasses import dataclass
from turtle import mode
from typing import List
import time

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
    print("\n" * 3)
    
    # ANSI Colors
    CYAN = "\033[36m"
    BLUE = "\033[38;5;117m"
    GREEN = "\033[38;5;151m"
    RED = "\033[38;5;210m"
    RESET = "\033[0m"


    # Modes
    if mode == "Known":
        mode = f"{GREEN}✅ Known Vocabulary ✅{RESET}"
    elif mode == "Not Known":
        mode = f"{RED}❌ Not Known Vocabulary ❌{RESET}"
    elif mode == "Unseen":
        mode = f"{BLUE}🆕 Unseen Vocabulary 🆕{RESET}"

    print(f"{mode}\n")
    print(f"{CYAN}# = mark known{RESET}")
    print(f"{CYAN}Enter = show answer (mark unknown){RESET}")
    print(f"{CYAN}q = quit{RESET}")
    print(f"{CYAN}m = change mode [ known / unknown / unseen ]{RESET}\n")

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
        while True:
            cmd = input().strip().lower()
            if cmd == "#":
                print(f"{entry.answer}\n")
                if input("✔ Not known? ([ENTER] to confirm): ").strip() == "#":
                    entry.known = False
                    entry.seen = True
                    print("❌ Marked as not known.")
                    time.sleep(0.65)
                    break
                else:
                    entry.known = True
                    entry.seen = True
                    print("✅ Marked as known.")
                    time.sleep(0.65)
                    break
            elif cmd == "": 
                print(f"{entry.answer}\n")
                if input("✔ Known? (# to confirm): ").strip() == "#":
                    entry.known = True
                    entry.seen = True
                    print("✅ Marked as known.")
                    time.sleep(0.65)
                    break
                else:
                    entry.known = False
                    entry.seen = True
                    print("❌ Marked as not known.")
                    time.sleep(0.65)
                    break
            elif cmd == "q":
                return "q"
            elif cmd == "m":
                return "m" 
            
            # Move cursor up one line and clear the line
            sys.stdout.write("\033[F\033[K")
            sys.stdout.flush()


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
        # Not known first
        if not_known:
            res = run_trainer(not_known, label="Not Known")
            if res == "q":
                save_vocab(not_known + known)
                break
                

        # Unseen entries
        seen_qs = {e.question for e in known + not_known}
        unseen = [e for e in all_vocab if e.question not in seen_qs]
        if unseen:
            res = run_trainer(unseen, label="Unseen")
            if res == "q":
                save_vocab(known + not_known)
                break
        
        # Known entries
        if known:
            res = run_trainer(known, label="Known")
            if res == "q":
                save_vocab(known + not_known)
                break

    save_vocab(known + not_known + unseen)
    input("🎉 All done. Press Enter to exit...")

if __name__ == "__main__":
    main()
