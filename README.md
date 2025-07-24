# Vocabulary Trainer for Mac/Linux [BETA]

This vocabulary trainer was primarily developed for macOS. You can launch it conveniently via the provided .command script. On Windows, the trainer can be run manually by executing the Python script directly.

The main use case is to send a coursebook text to ChatGPT and ask it to format the output as vocabulary flashcards. The script helps you manage, review, and update the vocabulary efficiently. *Copy-paste that output to the vocabulary.txt file (reformat it if needed, specs below) and start learning!
Vocabualry backups are saved in the backup folder on every start. So there is no chance of loosing your vocabulary set

#### Exemplary ChatGPT promt
```txt
I will give you a text. Your task is to extract and format vocabulary card–style Q&A pairs.

Step 1: Perform Named Entity Recognition (NER) to identify all relevant entities—such as names, concepts, and ideas.

Step 2: Create a question for each identified entity. Use the following format:
Q: <question>? [<topic> or <chapter name>]
A: <answer>

Formatting rules:
– Do not insert line breaks inside answers, even when using numbering or bullet points.
– Example:

Q: What are the three core activities in the UX design process? [UX Design Process]
A: According to Jonas (2006), the UX design process includes: (1) analysis – understanding the current state, (2) projection – generating ideas, and (3) synthesis – developing and implementing concrete design solutions. These activities span the broader macroprocess.

Q: What is the polar coordinate system used for in robotics? [Coordinate Systems in Robotics]
A: The polar coordinate system is used in 2D space to represent points by their distance *r* from the origin and angle *φ*, making it suitable for describing planar rotations.
```


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
| `vocabulary_backup/`         | Backup folder for vocabulary file backup in case something bugs out         |
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
d = delete
```

4.	All entries marked as not known will be saved to not_known.txt and can be reviewed separately.

### Setup: macOS / Linux
Open a terminal and copy paste these commands and hit enter.

#### Install brew
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
eval "$(/opt/homebrew/bin/brew shellenv)"
brew --version
```

#### Intall python
```bash
brew install pyenv
pyenv install 3.10.13
pyenv global 3.10.13
```
#### Intsall the project

1. Open Terminal.
2. Clone or download this repository.
3. Navigate to the folder:
4. Make the command file executable
5. Run the start_vocabtrainer.command script

```bash
git clone https://github.com/l-lattermann/uni-vocabulary-trainer.git
cd /uni-vocabulary-trainer
chmod +x ./src_and_data/vocabulary_trainer.py
./start_vocabtrainer.command
```
