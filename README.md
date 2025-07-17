# Vocabulary Trainer for Mac/Linux

[Can be run on Windows by running the vocabulary_trainer.py manually]
A simple terminal-based flashcard trainer for learning vocabulary. This Python script reads questions and answers from a text file and quizzes you interactively. Unknown entries are saved for focused repetition later. Vocabs are intentionally stored in .txt format, so copy-pasting and reformating them from Coursebooks or AI is easy.



## Features

- Loads vocabulary from `vocabulary.txt` or a custom path
- Supports alternating question (`Q:`) and answer (`A:`) lines
- Interactive controls
- Saves which vocabulary you have learn, not learned yet, and not seen yet



## Project Structure

| File / Folder                | Description                                                                |
|-----------------------------|-----------------------------------------------------------------------------|
| `vocabulary_trainer.py`     | Main Python script that runs the vocabulary quiz in the terminal.           |
| `vocabulary.txt`            | Default vocabulary file with alternating `Q:` and `A:` lines.               |
| `not_known.txt`             | Automatically generated file saving entries marked as not known.            |
| `known.txt`                 | Automatically generated file saving entries marked as known.                |
| `start_vocabtrainer.command`| macOS launcher script that opens Terminal and runs the quiz.                |

---


## File Format for vocabulary.txt
•	Exactly one line per question, prefixed by Q:

•	Followed immediately by one line per answer, prefixed by A:

•	No blank lines or extra whitespace

•	No repeated Q: or A: lines in a row

•	The number of lines in the file must be even (every Q: must be followed by A:).

•	Each line should start with either Q: or A: (no indentation or space before the prefix).

•	Do not add extra line breaks at the end of the file.


Example:
```txt
Q: What is the capital of France?
A: Paris
Q: What is the German word for ‘apple’?
A: Apfel
``` 

Avoid duplicate consecutive `Q:` or `A:` tags—this will raise a format error when the script validates input.



## Usage

1. Save your vocabulary in `vocabulary.txt`, or prepare a similar file and provide the path when prompted.
2. Double click the `start_vocabtrainer.command`
3.	Follow the on-screen instructions:

```txt
↩ Enter = show answer (mark as known)
# = mark as known
m = switch between modes [ known / unkown / unseen ]
q = quit
```

4.	All entries marked as not known will be saved to not_known.txt and can be reviewed separately.

### Setup: macOS / Linux

1. Open Terminal.
2. Clone or download this repository.
3. Navigate to the folder:
4. Make the command file executable
5. Run the start_vocabtrainer.command script

```bash
git clone https://github.com/l-lattermann/uni-vocabulary-trainer.git
cd /uni-vocabulary-trainer
chmod +x start_vocabtrainer.command
./start_vocabtrainer.command
```
