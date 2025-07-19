#!/usr/bin/env python3

import os
import sys
from dataclasses import dataclass
from typing import List
import time
from pathlib import Path
import textwrap
import shutil
import shutil
import textwrap
# ___________ Variables ___________
global terminal_width, terminal_height
terminal_width, terminal_height = shutil.get_terminal_size()

global left_bound_text_box, right_bound_text_box, text_box_size
left_bound_text_box = max(terminal_width // 2 - 20, 0)
right_bound_text_box = max(terminal_width // 2 + 20, 0)
text_box_size = 80

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
    terminal_width, terminal_height = shutil.get_terminal_size()
    left_bound_text_box = max(terminal_width // 2 - 20, 0)
    right_bound_text_box = max(terminal_width // 2 + 20, 0)

    clear()
    offset_vertical = max(0, (terminal_height - 40) // 2)
    print("\n" * offset_vertical)
    
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

    print(f"{mode}\n".center(terminal_width))
    print(f"{CYAN}[q] = quit{RESET}".center(terminal_width))
    print(f"{CYAN}[m] = change mode [ known / unknown / unseen ]{RESET}\n".center(terminal_width))
    target_pos = int(max(terminal_width/2 - text_box_size/2, 0))
    print(" " * target_pos + f"{CYAN}Q: {current}/{total}{RESET}")
    print(" " * target_pos + f"{CYAN}[ENTER] -> show answer{RESET}\n")

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


def print_formated(string: str, colour: str = "WHITE", style: str = "BOLD"):
    # Terminal dimensions
    terminal_width, _ = shutil.get_terminal_size()

    # Escape sequences
    STYLES = {
        "BOLD": "\033[1m",
        "NORMAL": "\033[0m"
    }

    COLOURS = {
        "WHITE": "\033[97m",
        "CYAN": "\033[36m",
        "BLUE": "\033[38;5;117m",
        "GREEN": "\033[38;5;151m",
        "RED": "\033[38;5;210m"
    }

    RESET = "\033[0m"
    UNDERLINE = "\033[4m"

    # Apply special formatting to questions
    if string.startswith("Q:"):
        string = f"{STYLES['BOLD']}{UNDERLINE}{string}{RESET}"

    # Wrap and indent
    wrapped_string = textwrap.fill(string, width=text_box_size)
    indent = " " * max(terminal_width // 2 - text_box_size // 2, 0)
    wrapped_string = wrapped_string.replace("\n", "\n" + indent)

    # Final print
    style_code = STYLES.get(style.upper(), "")
    colour_code = COLOURS.get(colour.upper(), "")
    print(indent + f"{style_code}{colour_code}{wrapped_string}{RESET}")

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
        print_formated(entry.question, colour="WHITE", style="BOLD")
        terminal_width = shutil.get_terminal_size().columns
        input(" " * max(terminal_width // 2 - text_box_size // 2, 0))
        print_formated(entry.answer, colour="WHITE", style="BOLD")
        while True:
            terminal_width = shutil.get_terminal_size().columns
            print_formated("Not known? [ENTER]     Known? [#]", style="NORMAL", colour="CYAN")
            cmd = input(" " * max(terminal_width // 2 - text_box_size // 2, 0))
            if cmd == "":
                    entry.known = False
                    entry.seen = True
                    print(f"❌ {CYAN} Marked as not known {RESET}".center(terminal_width)) 
                    time.sleep(0.75)
                    break
            elif cmd == "#": 
                    entry.known = True
                    entry.seen = True
                    print(f"✅ {CYAN} Marked as known.{RESET}".center(terminal_width))
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
    print(all_path)
    validate_format(all_vocab)

    known = []
    not_known = []

    # Load known vocab
    known_path = Path("src_and_data") / Entry.path_known
    if os.path.exists(known_path):
        known = load_vocab_file(known_path)
        # Set all known entries known:True and seen:True
        print(known_path)
        validate_format(known)
        for e in known:
            e.known = True
            e.seen = True

    # Load not known vocab
    not_known_path = Path("src_and_data") / Entry.path_not_known
    if os.path.exists(not_known_path):
        not_known = load_vocab_file(not_known_path)
        # Set all not known entries known:False and seen:True
        print(not_known_path)
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


    save_vocab(known + not_known)
    input("🎉 All done. Press Enter to exit...")

if __name__ == "__main__":
    main()
