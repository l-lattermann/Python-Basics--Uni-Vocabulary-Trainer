import re
import os
import shutil
# clear
os.system('cls' if os.name == 'nt' else 'clear')
os.system('cls' if os.name == 'nt' else 'clear')

text_box_size = 80

line_list = [
    "This is a line.",
    "",
    "This is another line.",
    "\n"
    "This is a third line.\n"
    "This is a fourth line.",
    "This is a fifth line.\n",
    "This is a sixth line.",

]
# ==============================================================================================================================

def multi_line_input() -> str:
        terminal_width, _ = shutil.get_terminal_size()
        indent = " " * max(terminal_width // 2 - text_box_size // 2, 0)
        print("Type '#' on a new line to finish.")
        new_question = ""
        while True:
            # Print the current input
            user_input = input(indent)    
            if user_input == "#":
                break
            new_question += " " + user_input + "\n"

        # Normalize the input      
        new_question = re.sub(r'\r\n', '\n', new_question) # Normalize line endings
        new_question = re.sub(r'\r{3,}|\n{3,}', '\n\n', new_question) # Normalize line endings
        new_question = new_question.strip()  # Remove leading/trailing whitespace
        new_question = re.sub(r"#$", "", new_question)
        return new_question
# ==============================================================================================================================

new_question = multi_line_input()
# ==============================================================================================================================

for a in new_question.splitlines():
     print(a)
print("_" * 50)
print()

# ==============================================================================================================================
string = new_question
text_box_size = 150  # Example width for text wrapping
# ==============================================================================================================================

import textwrap
# Wrap the text to fit within the specified width
wrapped_lines = []
for l in string.splitlines():
    if "•"  not in l:
        l = l.strip()
    wrapped_lines.extend(textwrap.wrap(l, width=text_box_size) if l.strip() != "" else [""])

for line in wrapped_lines:
    print(line)