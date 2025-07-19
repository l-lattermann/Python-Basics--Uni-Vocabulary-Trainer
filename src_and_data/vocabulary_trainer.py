#!/usr/bin/env python3

import os
import sys
from dataclasses import dataclass
from typing import List
import time
from pathlib import Path
import textwrap

# ___________ Variables ___________
global_terminal_width = 80  # Default terminal width, can be adjusted

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

def print_header(mode="Trainer", current=0, total=0):
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

    print(f"{mode}\n".center(global_terminal_width))
    print(f"{CYAN}[q] = quit{RESET}".center(global_terminal_width))
    print(f"{CYAN}[m] = change mode [ known / unknown / unseen ]{RESET}\n".center(global_terminal_width))
    print(f"{CYAN}Q: {current}/{total}{RESET}")
    print(f"{CYAN}[ENTER] -> show answer{RESET}")

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

    path = Path("src_and_data") / Entry.path_known
    with open(path, "w") as f:
        for e in known:
            f.write(f"{e.question}\n{e.answer}\n")

    path = Path("src_and_data") / Entry.path_not_known
    with open(path, "w") as f:
        for e in not_known:  
            f.write(f"{e.question}\n{e.answer}\n")

def print_formated(string: str):
    BOLD = "\033[1m"
    RESET = "\033[0m"

    width = global_terminal_width 
    wrapped_string = textwrap.fill(string, width=width)  # or 70, 100, etc.
    print(f"{BOLD}{wrapped_string}{RESET}")

def run_trainer(entries: List[Entry], label="Trainer") -> str:
    CYAN = "\033[36m"
    BLUE = "\033[38;5;117m"
    GREEN = "\033[38;5;151m"
    RED = "\033[38;5;210m"
    RESET = "\033[0m"

    for i, entry in enumerate(entries):
        current = i + 1
        total = len(entries)
        print_header(label, current, total)
        print_formated(entry.question)
        input()
        print_formated(entry.answer)
        while True:
            cmd = input(f"{CYAN}Not known? [ENTER]     Known? [#]{RESET}\n").strip().lower()
            if cmd == "":
                    entry.known = False
                    entry.seen = True
                    print(f"❌ {CYAN} Marked as not known {RESET}".center(global_terminal_width)) 
                    time.sleep(0.75)
                    break
            elif cmd == "#": 
                    entry.known = True
                    entry.seen = True
                    print(f"✅ {CYAN}Marked as known.{RESET}".center(global_terminal_width))
                    time.sleep(0.75)
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

    if os.path.exists(Path("src_and_data") / Entry.path_known):
        known = load_vocab_file(Path("src_and_data") / Entry.path_known)
        # Set all known entries known:True and seen:True
        validate_format(known)
        for e in known:
            e.known = True
            e.seen = True

    if os.path.exists(Path("src_and_data") / Entry.path_not_known):
        not_known = load_vocab_file(Path("src_and_data") / Entry.path_not_known)
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
        # Drop entrys that have changed category
        not_known = [entry for entry in not_known if not entry.known]

        # Unseen entries 
        seen_qs = {e.question for e in known + not_known}
        unseen = [e for e in all_vocab if e.question not in seen_qs]
        if unseen:
            res = run_trainer(unseen, label="Unseen")
            if res == "q":
                save_vocab(known + not_known)
                break
        # Drop unseen entries that have been seen
        unseen = [entry for entry in unseen if not entry.seen]
        
        # Known entries
        if known:
            res = run_trainer(known, label="Known")
            if res == "q":
                save_vocab(known + not_known)
                break
        # Drop entries that have changed category
        known = [entry for entry in known if entry.known]


    save_vocab(known + not_known + unseen)
    input("🎉 All done. Press Enter to exit...")

if __name__ == "__main__":
    main()
