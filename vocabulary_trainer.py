#!/usr/bin/env python3

import os
import re
import random
from dataclasses import dataclass
import time

@dataclass
class Entry:
    question: str
    answer: str
    known: bool = False
    path_known = "not_known.txt"
    path_not_known = "known.txt"

def clear():
    os.system('clear')

def load_vocab_file(path: str) -> list[str]:
    with open(path, "r") as f:
        return f.read().splitlines()
def print_header(known_flag: bool = False) -> None:
    clear()
    print("\n" * 15)
    if known_flag:
        print("#######  Vocabulary Trainer (Known) #########\n")
    else:
        print("#######  Vocabulary Trainer (Not Known) #########\n")
    print("# = known | q = quit | s = skip | r = repeat the not-known\n")

def validate_format(entries: list[Entry]) -> Entry:
    for i in range(len(entries) - 1):
            print(f"❌ Format error at line {i+1}:\n{entries[i]}\n{entries[i+1]}\n")
            exit(1)

def prompt_for_file(prompt_msg="Provide file path:") -> str:
    print(prompt_msg)
    while True:
        path = input("File path: ").strip().strip("'")
        if os.path.exists(path):
            return path
        print("Invalid path. Try again.\n")

def save_vocab(entries: list[Entry]) -> None:
    not_known = {entry.question: entry.answers for entry in entries if not entry.known}
    known = {entry.question: entry.answers for entry in entries if entry.known}
    with open(Entry.path_known, "w") as f:
        for q, a in known.items():
            f.write(f"{q}\n{a}\n")
    with open(Entry.path_not_known, "w") as f:
        for q, a in not_known.items():
            f.write(f"{q}\n{a}\n")

def review_entries(vocab: list[Entry]) -> list[Entry]:
    updated = vocab.copy()
    for entry in vocab:
        clear()
        print("\n" * 15)
        print("#######  Repeating not-known #########\n")
        print("# = known | q = quit | s = skip\n")
        print(f"{entry.question}\n")
        i1 = input()
        print(f"{entry.answer}\n")
        i2 = input()

        if i1.strip() == "" or i2.strip() == "":
            entry.known = False
            print("❌ Marked as not known.\n")
            time.wait(20)
        if i1.strip() == "#" or i2.strip() == "#":
            entry.known = True
            print("✅ Marked as known.\n")
            time.wait(20)
        elif i1.strip() == "q" or i2.strip() == "q":
            save_vocab("not_known.txt", updated)
            exit(0)
        elif i1.strip() == "s" or i2.strip() == "s":
            break
    return updated

def run_trainer(vocab: list[Entry]) -> str:
    for entry in vocab:
        clear()
        print(f"{entry.question}\n")
        cmd = input()
        print(f"{entry.answer}\n")
        cmd = cmd.strip().lower()
        if cmd == "":
            entry.known = True
            print("✅ Marked as known.\n")
        elif cmd == "#":
            entry.known = False
            print("❌ Marked as not known.\n")
            time.sleep(2)
        elif cmd == "q":
            return cmd
        elif cmd == "s":
            return cmd
        elif cmd == "r":
            return cmd
        

def main():
    clear()
    print("📘 Vocabulary Trainer\n")

    all_path = "vocabulary.txt" if os.path.exists("vocabulary.txt") else prompt_for_file("📂 No 'vocabulary.txt' found.\n")
    known_path = Entry.path_known if os.path.exists(Entry.path_known) else: = None
    not_known_path = Entry.path_not_known if os.path.exists(Entry.path_not_known) else: = None

    if not all_path:
        print("❌ No vocabulary file provided. Exiting.\n")
        return
    else:
        print(f"📂 Using vocabulary file: {all_path}\n")
        all_vocab = load_vocab_file(all_path)
        all_vocab = validate_format(all_vocab)
    
    if not known_path:
        print("❌ No known vocabulary file provided. Continuing without.\n")
    else:
        print(f"📂 Using known vocabulary file: {known_path}\n")
        known_vocab = load_vocab_file(known_path)
        known_vocab = validate_format(known_vocab)

    if not not_known_path:
        print("❌ No not-known vocabulary file provided. Continuing without.\n")
    else:
        print(f"📂 Using not-known vocabulary file: {not_known_path}\n")
        not_known_vocab = load_vocab_file(not_known_path)
        not_known_vocab = validate_format(not_known_vocab)
    
    # Start with unknown vocabulary
    while True:
        if not_known_vocab:
            print_header()
            print("Starting with not-known vocabulary...\n")
            cmd_output = run_trainer(not_known_vocab)

            if cmd_output == "q":
                print("Exiting the trainer. Goodbye!\n")
                break
            elif cmd_output == "s":
                print("Skipping the current this training.\n")
            elif cmd_output == "r":
                print("Repeating the not-known vocabulary.\n")
                run_trainer(not_known_vocab)
        else:
            print("No not-known vocabulary found. Starting with known vocabulary...\n")
    
    # Save the updated not-known vocabulary
    save_vocab(not_known_vocab)
    print("✅ Not-known vocabulary file saved successfully.\n")

    # Start with unseen vocabulary
    unseen_vocab = set(all_vocab) - set(known_vocab) - set(not_known_vocab)
    while True:
        if unseen_vocab:
            print_header(unseen_flag=True)
            print("Starting with unseen vocabulary...\n")
            cmd_output = run_trainer(unseen_vocab)

            if cmd_output == "q":
                print("Exiting the trainer. Goodbye!\n")
                break
            elif cmd_output == "s":
                print("Skipping the current this training.\n")
            elif cmd_output == "r":
                print("Repeating the known vocabulary.\n")
                if not_known_vocab:
                    not_known_vocab = review_entries(not_known_vocab)
        

    # Save the updated vocabulary files
    save_vocab(known_vocab)
    save_vocab(not_known_vocab)
    print("✅ Vocabulary files saved successfully.\n")



    input("🎉 Done! Press Enter to exit...")

if __name__ == "__main__":
    main()