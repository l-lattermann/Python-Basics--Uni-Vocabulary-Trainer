# Vocabulary Trainer for Mac/Linux

A simple terminal-based flashcard trainer for learning vocabulary. This Python script reads questions and answers from a text file and quizzes you interactively. Unknown entries are saved for focused repetition later.



## Features

- Loads vocabulary from `vocabulary.txt` or a custom path
- Supports alternating question (`Q:`) and answer (`A:`) lines
- Randomizes question order each session
- Interactive controls:
  - `Enter` — Show the answer
  - `#` — Mark as not known
  - `r` — Review only not-known entries
  - `q` — Quit the session
- Saves unknown entries to `not_known.txt` for targeted review



## Project Structure

| File / Folder                | Description                                                                 |
|-----------------------------|-----------------------------------------------------------------------------|
| `vocabulary_trainer.py`     | Main Python script that runs the vocabulary quiz in the terminal.           |
| `vocabulary.txt`            | Default vocabulary file with alternating `Q:` and `A:` lines.               |
| `not_known.txt`             | Automatically generated file saving entries marked as not known.            |
| `start_vocabtrainer.command`| macOS launcher script that opens Terminal and runs the quiz.                |

---


## File Format

vocabulary.txt files must alternate between `Q:` and `A:` lines. Example:
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
↩ Enter = show answer
# = mark as not known
r = repeat not-known
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
