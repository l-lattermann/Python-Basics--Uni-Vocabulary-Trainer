#!/usr/bin/env python3

import os
import re
import sys
from dataclasses import dataclass
import time
from pathlib import Path
import textwrap
import shutil
import shutil
import textwrap
import random
from typing import List, Literal, Tuple

# ___________ Variables ___________
terminal_width, terminal_height = shutil.get_terminal_size()
left_bound_text_box = max(terminal_width // 2 - 20, 0)
right_bound_text_box = max(terminal_width // 2 + 20, 0)
text_box_size = 100
vocab_total = 0


@dataclass
class Entry:
    question: str
    answer: str
    known: bool = None
    seen: bool = None
    important = None

    path_known = "src_and_data/known.txt"
    path_not_known = "src_and_data/not_known.txt"
    path_important = "src_and_data/important.txt"
    path_all = "src_and_data/vocabulary.txt"
    path_backup = "src_and_data/vocabulary_backup"

def clear():
    os.system('clear' if os.name == 'posix' else 'cls')

def clear_line():
    sys.stdout.write("\033[F\033[K")  # Move cursor up one line and clear the line
    sys.stdout.flush()  # Ensure the command is executed immediately

def print_formated(
        string: str, colour: Literal["WHITE", "CYAN", "BLUE", "GREEN", "RED"], 
        style: Literal["BOLD", "NORMAL"], 
        position: Literal["LEFT", "CENTER", "RIGHT"] = "LEFT"
        ):
    
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


    if string.startswith("Q:"):
        is_question = True
    else:
        is_question = False
    if string.startswith("A:"):
        is_answer = True
    else:
        is_answer = False

    # Wrap first (no styling yet)
    wrapped_lines = textwrap.wrap(string, width=text_box_size)

    # Compute indent once
    indent = " " * max(terminal_width // 2 - text_box_size // 2, 0)

    # Apply formatting line by line
    formatted_lines = []
    for i, line in enumerate(wrapped_lines):
        styled = line
        if is_question:
            styled = f"{STYLES['BOLD']}{UNDERLINE}{line}{RESET}" 
        elif is_answer:
            styled = f"{STYLES['BOLD']}{COLOURS['WHITE']}{line}{RESET}"
        else:
            styled = f"{STYLES[style]}{COLOURS[colour]}{line}{RESET}"
        formatted_lines.append(indent + styled)
    
    if is_question or is_answer:
        final_output = "\n\n".join(formatted_lines)
        final_output += "\n\n"  # Add extra space after answer
    else:
        final_output = "\n".join(formatted_lines) 

    if position == "LEFT":
        print(final_output)
    elif position == "CENTER":
        print(final_output.center(terminal_width))
    elif position == "RIGHT":
        terminal_width, _ = shutil.get_terminal_size()
        print(final_output.rjust(terminal_width-len(indent)))
   
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

def print_header(mode="Trainer", current=0, local_total=0):
    terminal_width, terminal_height = shutil.get_terminal_size()
    global vocab_total
    clear()
    offset_vertical = max(0, (terminal_height - 40) // 2)
    print("\n" * offset_vertical)
    
    # ANSI Colors
    CYAN = "\033[36m"
    BLUE = "\033[38;5;117m"
    GREEN = "\033[38;5;151m"
    RED = "\033[38;5;210m"
    RESET = "\033[0m"
    YELLOW = "\033[38;5;226m"


    # Modes
    if mode == "Known":
        mode = f"{GREEN}✅ Known Vocabulary ✅{RESET}"
    elif mode == "Not Known":
        mode = f"{RED}❌ Not Known Vocabulary ❌{RESET}"
    elif mode == "Unseen":
        mode = f"{BLUE}🆕 Unseen Vocabulary 🆕{RESET}"
    elif mode == "Important":
        mode = f"{YELLOW}⚠️  Important Vocabulary ⚠️{RESET}"
    
    print_formated("=-" * (text_box_size // 2), style="BOLD", colour="CYAN")
    print(f"{mode}".center(terminal_width))
    print_formated("=-" * (text_box_size // 2), style="BOLD", colour="CYAN")
    print(f"{CYAN}[q] = quit{RESET}".center(terminal_width))
    print(f"{CYAN}[e] = edit current entry{RESET}".center(terminal_width))
    print(f"{CYAN}[d] = delete this entry{RESET}".center(terminal_width))
    print(f"{CYAN}[m] = change mode [ important / known / unknown / unseen ]{RESET}".center(terminal_width))
    print_formated("=-" * (text_box_size // 2), style="BOLD", colour="CYAN")
    print("\n\n")

    target_pos = int(max(terminal_width/2 - text_box_size/2, 0))
    print_formated(f"Current: {current}/{local_total}    Total: {vocab_total}", colour="CYAN", style="NORMAL", position="RIGHT")
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
    important = [e for e in entries if e.important and e.seen]

    path = Path(Entry.path_known)
    with open(path, "w") as f:
        for e in known:
            f.write(f"{e.question}\n{e.answer}\n")

    path = Path(Entry.path_not_known)
    with open(path, "w") as f:
        for e in not_known:  
            f.write(f"{e.question}\n{e.answer}\n")

    path = Path(Entry.path_important)
    with open(path, "w") as f:
        for e in important:
            f.write(f"{e.question}\n{e.answer}\n")

    path = Path(Entry.path_all)
    with open(path, "w") as f:
        for e in entries:
            f.write(f"{e.question}\n{e.answer}\n")

def multi_line_input() -> str:
        terminal_width, _ = shutil.get_terminal_size()
        indent = " " * max(terminal_width // 2 - text_box_size // 2, 0)
        print_formated("Type '#' on a new line to finish.", style="NORMAL", colour="CYAN")
        new_question = ""
        while True:
            # Print the current input
            user_input = input(indent)
            clear_line()          
            if user_input == "#":
                break
            new_question += (" " + user_input.strip())
        # Normalize the input      
        new_question = new_question.strip()  # Remove leading/trailing whitespace
        new_question = re.sub(r'\s+', ' ', new_question)  # Normalize whitespace
        new_question = re.sub(r'\r\n|\r|\n', ' ', new_question) # Normalize line endings
        new_question = new_question.strip() # Remove leading/trailing whitespace
        return new_question

def entry_editor(entry: Entry) -> Entry:

    while True:
        print_formated("Do you want to edit this question? [y/n]", style="NORMAL", colour="CYAN")
        edit_confirm = input(" " * max(terminal_width // 2 - text_box_size // 2, 0)).strip().lower()
        clear_line()      
        if edit_confirm == "n":
            print_formated("Exiting editor...", style="NORMAL", colour="CYAN")
            time.sleep(1)
            return
        elif edit_confirm == "y":
            print_formated("Continuing to edit...", style="NORMAL", colour="CYAN")
            break


    # Edit current entry
    while True:
        # Get terminal size
        print_formated("Editing current entry...", style="NORMAL", colour="CYAN")
        while True:
            print_formated("Please enter the new question and answer in the format 'Q: question'", style="NORMAL", colour="CYAN")
            new_question = multi_line_input()
            if new_question[:2] == "Q:":
                break
            else:
                print_formated("❌ Invalid format. Question must start with 'Q:'. Please try again.", style="NORMAL", colour="RED")

        while True:       
            print_formated("Now enter the answer in the format 'A: answer'", style="NORMAL", colour="CYAN")
            new_answer = multi_line_input()
            if new_answer[:2] == "A:":
                break
            else:
                print_formated("❌ Invalid format. Answer must start with 'A:'. Please try again.", style="NORMAL", colour="RED")
        # Validate input

        
        print("\n\n")
        print_formated(f"New Question:", style="NORMAL", colour="CYAN")
        print_formated(f"{new_question}", style="NORMAL", colour="WHITE")
        print("\n")
        print_formated(f"New Answer: ", style="NORMAL", colour="CYAN")
        print_formated(f"{new_answer}", style="NORMAL", colour="WHITE")
        print("\n")

        while True:
            print_formated("Confirm update? [y/n]", style="NORMAL", colour="CYAN")
            confirm = input(" " * max(terminal_width // 2 - text_box_size // 2, 0)).strip().lower()
            clear_line()              
            if confirm == "y":
                entry.question = new_question
                entry.answer = new_answer
                print_formated("✅ Entry updated successfully.", style="NORMAL", colour="CYAN")
                return entry
            elif confirm == "n":
                print_formated(" ❌ Update cancelled", style="NORMAL", colour="CYAN")
                print_formated("Exit editor? [y/n]", style="NORMAL", colour="CYAN")
                exit_confirm = input(" " * max(terminal_width // 2 - text_box_size //  2, 0)).strip().lower()
                clear_line()                  
                if exit_confirm == "y":
                    print_formated("Exiting editor...", style="NORMAL", colour="CYAN")
                    time.sleep(1)
                    return
                elif exit_confirm == "n":
                    print_formated("Continuing to edit...", style="NORMAL", colour="CYAN")
                    break  
                    
            else:
                print_formated("❌ Invalid input.", style="NORMAL", colour="RED")
                time.sleep(1)

def run_trainer(all_vocab: List[Entry], label: Literal["Important", "Known", "Not Known", "Unseen"] = "Known") -> Tuple[List[Entry], str | None]:    
    CYAN = "\033[36m"
    BLUE = "\033[38;5;117m"
    GREEN = "\033[38;5;151m"
    RED = "\033[38;5;210m"
    RESET = "\033[0m"
    

    if label == "Known":
        entries = [e for e in all_vocab if e.known and e.seen and not e.important]
        if not entries:
            print_formated("No known entries found.", style="NORMAL", colour="CYAN")
            time.sleep(1)
            return (all_vocab, None)
    elif label == "Important":
        entries = [e for e in all_vocab if e.important and e.seen]
        if not entries:
            print_formated("No known entries found.", style="NORMAL", colour="CYAN")
            time.sleep(1)
            return (all_vocab, None)
    elif label == "Not Known":
        entries = [e for e in all_vocab if not e.known and e.seen and not e.important]
        if not entries:
            print_formated("No not known entries found.", style="NORMAL", colour="CYAN")
            time.sleep(1)
            return (all_vocab, None)
    elif label == "Unseen":
        entries = [e for e in all_vocab if not e.seen]
        if not entries:
            print_formated("No unseen entries found.", style="NORMAL", colour="CYAN")
            time.sleep(1)
            return (all_vocab, None)
    else:
        raise ValueError(f"Invalid label: {label}")
        return (all_vocab, None)
    
    exit_code = None # "q" | "m" | None
    i = 0
    while i < len(entries):
        entry = entries[i]
        current = i + 1
        total = len(entries)
        
        print_header(label, current, total)
        print_formated(entry.question, colour="WHITE", style="BOLD")
        terminal_width = shutil.get_terminal_size().columns
        input(" " * max(terminal_width // 2 - text_box_size // 2, 0))
        clear_line()      
        print_formated(entry.answer, colour="WHITE", style="BOLD")

        while True:
            terminal_width = shutil.get_terminal_size().columns
            print_formated("Not known? [ENTER]     Known? [#]     Mark 'Important' [i]", style="NORMAL", colour="CYAN")
            cmd = input(" " * max(terminal_width // 2 - text_box_size // 2, 0))
            clear_line()          

            if cmd == "":
                entry.known = False
                entry.seen = True
                print(f"❌ {CYAN}Marked as not known{RESET}".center(terminal_width))
                time.sleep(0.75)
                break
            elif cmd == "#":
                entry.known = True
                entry.seen = True
                print(f"✅ {CYAN}Marked as known.{RESET}".center(terminal_width))
                time.sleep(0.75)
                break
            elif cmd == "q":
                exit_code = "q"
                return all_vocab, exit_code
            elif cmd == "i":
                entry.known = False
                entry.seen = True
                entry.important = True
                print(f"✅ {CYAN}Marked as important.{RESET}".center(terminal_width))
                time.sleep(0.75)
                break
            elif cmd == "m":
                exit_code = "m"
                return all_vocab, exit_code
            elif cmd == "e":
                entry_editor(entry)
                continue  # Stay on current entry
            elif cmd == "d":
                while True:
                    print_formated("Are you sure you want to delete this entry? [y/n]", style="NORMAL", colour="CYAN")
                    confirm = input(" " * max(terminal_width // 2 - text_box_size // 2, 0)).strip().lower()
                    clear_line()                  
                    if confirm == "y":
                        if entry in entries:
                            entries.remove(entry)
                        if entry in all_vocab:
                            all_vocab.remove(entry)
                        print_formated("✅ Entry deleted successfully.", style="NORMAL", colour="CYAN")
                        time.sleep(0.75)
                        i -= 1  # offset next increment to skip forward
                        break
                    elif confirm == "n":
                        print_formated("❌ Deletion cancelled.", style="NORMAL", colour="RED")
                        time.sleep(0.75)
                        break
            break  # exit inner while after valid input

        i += 1  # advance to next entry
               
    result = (all_vocab, exit_code)
    return result

def create_vocab_backup():
    backup_path = Path(Entry.path_backup) / f"vocabulary_backup_{time.strftime('%d.%m.%Y-%H:%M:%S')}.txt"
    if os.path.exists(backup_path):
        i = 2 
        while True:
            backup_path = Path(Entry.path_backup) / f"vocabulary_backup_{time.strftime('%d.%m.%Y-%H:%M:%S')}_{i}.txt"
            if os.path.exists(backup_path):
                i += 1
            else:
                print(f"❌ Backup file already exists. Creating new backup at {backup_path.stem}")
                break
    os.makedirs(backup_path.parent, exist_ok=True)
    shutil.copy(Entry.path_all, backup_path)
    print(f"✅ Backup created at {backup_path.stem}")



def main():
    clear()

    # Create backup of vocabulary file
    if os.path.exists(Entry.path_all):
        create_vocab_backup()

    # Create known and not known files if they don't exist
    if not os.path.exists(Entry.path_known):
        with open(Entry.path_known, "w") as f:
            f.write("")
    if not os.path.exists(Entry.path_not_known):
        with open(Entry.path_not_known, "w") as f:
            f.write("")
    if not os.path.exists(Entry.path_important):
        with open(Entry.path_important, "w") as f:
            f.write("")

    # Load vocab
    all_path = Entry.path_all if os.path.exists(Entry.path_all) else prompt_for_file("No 'vocabulary.txt' found.")
    all_vocab = load_vocab_file(all_path)
    print(all_path)
    validate_format(all_vocab)
    global vocab_total

    vocab_total = len(all_vocab)

    known = []
    not_known = []

    # Load known vocab
    known_path = Path(Entry.path_known)
    if os.path.exists(known_path):
        known = load_vocab_file(known_path)
        # Set all known entries known:True and seen:True
        print(known_path)
        validate_format(known)
        known_question_set = {e.question for e in known}

    # Initialize sets
    known_question_set = set()
    not_known_question_set = set()
    important_question_set = set()
    
    # Load not known vocab
    not_known_path = Path(Entry.path_not_known)
    if os.path.exists(not_known_path):
        not_known = load_vocab_file(not_known_path)
        # Set all not known entries known:False and seen:True
        print(not_known_path)
        validate_format(not_known)
        not_known_question_set = {e.question for e in not_known}

    # Load not important vocab
    important_path = Path(Entry.path_important)
    if os.path.exists(important_path):
        important = load_vocab_file(important_path)
        # Set all not known entries known:False and seen:True
        print(important_path)
        validate_format(important)
        important_question_set = {e.question for e in important}

    # Set all entries in all_vocab that are not in known or not_known as unseen
    # And set known:False and seen:True
    for entry in all_vocab:
        if entry.question in known_question_set:
            entry.known = True
            entry.seen = True
        elif entry.question in not_known_question_set:
            entry.known = False
            entry.seen = True
        else:
            entry.known = False
            entry.seen = False
        if entry.question in important_question_set:
            entry.important = True

    while True:
        # Important first
        # Shuffle not known entries
        random.shuffle(all_vocab)
        all_vocab, exit_code = run_trainer(all_vocab, label="Important")
        if exit_code == "q":
            save_vocab(all_vocab)   
            break
        # Unseen entries 
        # Shuffle unseen entries
        random.shuffle(all_vocab)
        all_vocab, exit_code = run_trainer(all_vocab, label="Unseen")
        if exit_code == "q":
            save_vocab(all_vocab)
            break
        # Not known first
        # Shuffle not known entries
        random.shuffle(all_vocab)
        all_vocab, exit_code = run_trainer(all_vocab, label="Not Known")
        if exit_code == "q":
            save_vocab(all_vocab)   
            break
        # Seen entries
        # Shuffle seen entries
        random.shuffle(all_vocab)
        all_vocab, exit_code = run_trainer(all_vocab, label="Known")
        if exit_code == "q":
            save_vocab(all_vocab)
            break


    save_vocab(all_vocab)
    print("\n\n")
    print_formated("=-" * (text_box_size // 2), style="BOLD", colour="CYAN")
    print_formated("🎉 Good Job! 🎉 Press Enter to exit...", style="NORMAL", colour="CYAN", position="CENTER")
    print_formated("=-" * (text_box_size // 2), style="BOLD", colour="CYAN")
    print("\n\n\n\n")
    time.sleep(1)

if __name__ == "__main__":
    main()
