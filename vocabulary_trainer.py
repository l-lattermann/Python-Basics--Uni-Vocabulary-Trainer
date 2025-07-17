#!/usr/bin/env python3

import os
import re
import random

def clear():
    os.system('clear')

def load_vocab_file(path: str) -> list[str]:
    with open(path, "r") as f:
        return f.read().splitlines()

def validate_format(lines: list[str]) -> None:
    for i in range(len(lines) - 1):
        tag1, tag2 = lines[i][:2], lines[i+1][:2]
        if tag1 == tag2:
            print("❌ Format error: Expected alternating Q:/A: lines.")
            print(f"Line {i+1}: {lines[i]}\nLine {i+2}: {lines[i+1]}\n")
            exit(1)

def build_vocab_dict(lines: list[str]) -> dict[str, str]:
    return {lines[i]: lines[i+1] for i in range(0, len(lines)-1, 2)}

def prompt_for_vocab_file() -> str:
    print("Copy-paste the file path of your vocabulary file below:\n")
    while True:
        path = input("File path: ").strip().strip("'")
        if os.path.exists(path):
            return path
        print("Invalid path. Try again.\n")

def main():
    clear()
    print("📘 Vocabulary Trainer\n")
    default_file = "vocabulary.txt"
    
    # Load file
    if os.path.exists(default_file):
        vocab_path = default_file
    else:
        vocab_path = prompt_for_vocab_file()

    print(f"\n📂 Loading vocabulary from: {vocab_path}\n")
    lines = load_vocab_file(vocab_path)
    validate_format(lines)
    vocab = build_vocab_dict(lines)
    
    keys = list(vocab.keys())
    random.shuffle(keys)

    # Load not-known entries if they exist
    default_file = "not_known.txt"
    if os.path.exists(default_file):
        vocab_path = default_file
    else:
        print("\nℹ️ No 'not_known.txt' file found. You can create one by marking entries as not known during the session.\n")
        vocab_path = prompt_for_vocab_file()

    print(f"\n📂 Loading vocabulary from: {vocab_path}\n")
    lines = load_vocab_file(vocab_path)
    validate_format(lines)
    not_known = build_vocab_dict(lines)

    # Start with not-known entries if they exist
    not_known_copy = not_known.copy()
    if not_known:
        print("🔁 Starting with not-known entries:\n")
        for nq in not_known:
            clear()
            print("\n"*15)
            print("# = mark as known | q = quit ")
            print("Not-known:\n")
            print(f"{nq}\n")
            inp = input()
            print(f"{not_known[nq]}\n")
            inp2 = input()
            if inp.strip() == "#" or inp2.strip() == "#":
                not_known_copy.pop(nq)
            elif inp.strip() == "q" or inp2.strip() == "q":
                print("Exiting...")
                # Create file with not-known entries
                if not_known:
                    with open("not_known.txt", "w") as f:
                        for nq in not_known_copy:
                            f.write(f"{nq}\n{not_known_copy[nq]}\n")
                    print("📄 Not-known entries saved to 'not_known.txt'.\n")
                exit(0)
        not_known = not_known_copy # Reset not_known to the updated copy
         # Create file with not-known entries
        if not_known:
            with open("not_known.txt", "w") as f:
                for nq in not_known_copy:
                    f.write(f"{nq}\n{not_known_copy[nq]}\n")
            print("📄 Not-known entries saved to 'not_known.txt'.\n")
                
            
    for question in keys:
        clear()
        print("\n"*15)
        print("↩ Enter = show answer | # = mark as not known | r = repeat not-known | q = quit\n")
        print(f"{question}\n")
        cmd = input().strip().lower()

        if cmd == "":
            print(f"{vocab[question]}\n")
            temp_cmd = input()
            if temp_cmd == "#":
                not_known[question] = vocab[question]
        elif cmd == "#":
            print(f"{vocab[question]}\n")
            not_known[question] = vocab[question]
            input()
        elif cmd == "q":
            # Create file with not-known entries
            if not_known:
                with open("not_known.txt", "a") as f:
                    for nq in not_known:
                        f.write(f"{nq}\n{not_known[nq]}\n")
                print("📄 Not-known entries saved to 'not_known.txt'.\n")

            break
        elif cmd == "r":
            if not not_known:
                print("ℹ️ No not-known entries.\n")
                input("Press Enter to continue...")
                continue
            print("🔁 Repeating not-known entries:\n")
            for nq in not_known:
                print(f"{nq}\n")
                input()
                print(f"{not_known[nq]}\n")
                input()
            continue

    # Create file with not-known entries
    if not_known:
        with open("not_known.txt", "a") as f:
            for nq in not_known:
                f.write(f"{nq}\n{not_known[nq]}\n")
        print("📄 Not-known entries saved to 'not_known.txt'.\n")

    input("🎉 Done! Press Enter to exit...")

if __name__ == "__main__":
    main()