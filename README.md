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
•	Questions must start with "Q:", Answers with "A:"

•	No repeated Q: or A: lines in a row

•	The number of lines in the file must be even (every Q: must be followed by A:).



Example:
```txt
Q: How are entities and attributes represented in Chen notation? [3.1 The Entity Relationship Model]
A:
	•	rectangle = entity
	•	oval = attribute
	•	underlined = primary key

In Chen notation, entities are drawn as rectangles and attributes as ovals connected to their respective entities. A primary key is indicated by underlining the corresponding attribute name.
 ______________   ______________   ______________
|  Attribute 1 | |  Attribute 2 | |  Attribute 3 |
|   (PK)       | |              | |              |
 --------------   --------------   --------------
         \             |             /
          \            |            /
           \           |           /
            \          |          /
             \         |         /
              \        |        /
               \       |       /
                \      |      /
                 \     |     /
                  ___________
                 |   Entity  |
                 |___________|
Q: What is the structure of Martin (crow’s foot) notation for entities? [3.1 The Entity Relationship Model]
A:
	•	rectangle = entity
	•	top = primary key
	•	bottom = other attributes

Martin notation (also known as crow’s foot notation) uses rectangles to represent entities. The entity name and primary key appear in the upper section of the rectangle, optionally marked with a key icon. Other attributes are listed in the lower section.

 +-----------------+
 |     Attribute 1 |  ← Primary key
 +-----------------+
 |     Attribute 2 |
 |     Attribute 3 |  ← Entity
 +-----------------+

``` 

### Highlighting text
You can also highlight text using ANSI codes by…
-	Embedding escape sequences like `\033[43;30m` before text and `\033[0m` after to reset formatting.
-	Using the format `\\033[<style>;<foreground>;<background>m` where style, text color, and background color are numeric codes.
-	Applying styles: 0 reset, 1 bold, 4 underline (optional, can be combined).
-	Color codes: foreground 30–37 (black–white), background 40–47 (black–white).

Example:
<pre style="font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace; white-space: pre-wrap; line-height: 1.3; font-size: 0.95em;">
Q: What do the cardinality notations N, C, CN, and CM represent in ER modeling? [3.2 Relationships and Cardinalities in ER]  
A:  

•	N   = 1*   <span style="color:yellow;">\033[43;30m</span>(mandatory)<span style="color:yellow;">\033[0m</span>
•	C   = 0..1 (optional)  
•	CN  = 0*   (optional)  
•	CM  = 0*   (optional)  

In ER modeling, <span style="color:yellow;">\033[42;97m</span>cardinality<span style="color:yellow;">\033[0m</span> notations describe how many instances of one entity can be associated with instances of another and whether the relationship is <span style="color:yellow;">\033[44;97m</span>optional<span style="color:yellow;">\033[0m</span>. “N” implies <span style="color:yellow;">\033[41;97m</span>mandatory<span style="color:yellow;">\033[0m</span> multiplicity (at least one), while “C” allows for omission. “CN” and “CM” both indicate an optional relationship to many, i.e., zero or more.  

---

Q: How is a 1:N and 1:CN relationship visually represented in Martin, UML, and Chen notation? [3.2 Relationships and Cardinalities in ER]  
A:  

•	Martin: line with crow’s foot
	1:N:  [ENTITY]-|-----------------|<[ENTITY]  

	1:CN  [ENTITY]-|----------------O|<[ENTITY]  

•	UML: 1 to +1..*
	1:N:  [ENTITY] 1_______________1..*[ENTITY]  

	1:CN  [ENTITY] 1______________0..1 [ENTITY]  

•	Chen: diamond with 1 and N
	1:N:  [ENTITY] 1-------<>--------N [ENTITY]  

	1:CN:     &lt;NOT POSSIBLE&gt;  

In Martin notation, the 1:N relationship is shown using a straight line from Entity 1 to a crow’s foot on Entity 2. In UML, it is written as 1 on the side of Entity 1 and 1..* (one to many) on Entity 2’s side. In Chen notation, a diamond symbol connects both entities with 1 and N as the <span style="color:yellow;">\033[45;97m</span>cardinalities<span style="color:yellow;">\033[0m</span>. All three represent that each instance of Entity 1 is associated with one or more instances of Entity 2.
</pre>
### Output

<!-- Put this directly in README.md (outside triple backticks) -->
<pre style="font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace; line-height:1.2;">Q: What do the cardinality notations N, C, CN, and CM represent in ER modeling? [3.2 Relationships and Cardinalities in ER]  
A:  

•	N   = 1*   <span style="background-color:yellow;color:black;">(mandatory)</span>
•	C   = 0..1 (optional)  
•	CN  = 0*   (optional)  
•	CM  = 0*   (optional)  

In ER modeling, <span style="background-color:lightgreen;color:black;">cardinality</span> notations describe how many instances of one entity can be associated with instances of another and whether the relationship is <span style="background-color:lightblue;color:black;">optional</span>. “N” implies <span style="background-color:red;color:white;">mandatory</span> multiplicity (at least one), while “C” allows for omission. “CN” and “CM” both indicate an optional relationship to many, i.e., zero or more.  

---

Q: How is a 1:N and 1:CN relationship visually represented in Martin, UML, and Chen notation? [3.2 Relationships and Cardinalities in ER]  
A:  

•	Martin: line with crow’s foot
	1:N:  [ENTITY]-|-----------------|<[ENTITY]  

	1:CN  [ENTITY]-|----------------O|<[ENTITY]  

•	UML: 1 to 1..*
	1:N:  [ENTITY] 1_______________1..*[ENTITY]  

	1:CN  [ENTITY] 1______________0..1 [ENTITY]  

•	Chen: diamond with 1 and N 
	1:N:  [ENTITY] 1-------<>--------N [ENTITY]  

	1:CN:     &lt;NOT POSSIBLE&gt;  

In Martin notation, the 1:N relationship is shown using a straight line from Entity 1 to a crow’s foot on Entity 2. In UML, it is written as 1 on the side of Entity 1 and 1..* (one to many) on Entity 2’s side. In Chen notation, a diamond symbol connects both entities with 1 and N as the <span style="background-color:violet;color:black;">cardinalities</span>. All three represent that each instance of Entity 1 is associated with one or more instances of Entity 2.
</pre>





## Usage

1. Save your vocabulary in `vocabulary.txt`, or prepare a similar file and provide the path when prompted.
2. Double click the `start_vocabtrainer.command`
3.	Follow the on-screen instructions:

```txt
↩ Enter = show answer (mark as known)
# = mark as known
m = switch between modes [ known / unkown / unseen ]
i = mark as important/unimportant
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
