# Wiki Leet

> [Click here for a sample repo (my LeetCode repo)](https://github.com/Zanger67/leetcode)

WikiLeet is a program that takes your local LeetCode submissions and organizes them into a navigatable wiki-like set of markdown files giving you an aesthetically pleasing README to view your journey. See the link above for my own LeetCode repo as an example.

Using GitHub actions, it will run everytime you commit a new submission to your linked repo, updating all the markdown links in the process. 


## Setup

1. In your repo on github.com, click on `Actions` and ensure that actions are enabled for this repo. Then in your repo create a folder 
2. Create a `.github/workflows/` folder/directory in your repo.
```
./project root
└── .github
    └── workflows
```
3. Create a `main.yml` file in this folder
```
./project root
└── .github
    └── workflows
        └── main.yml
```
4. Paste the following code into the file. Make sure to insert your own LeetCode username!

```yml
name: '[Updating markdown files]'

on:
    # Allows for munual runs of workflow
    workflow_dispatch:

    # Default whenever anything is pushed to the main branch (solutions are
    # detected anywhere in the repo now, not just under my-submissions/)
    push:
        branches:
            - main

permissions:
    contents: write

jobs:
    build:
        runs-on: ubuntu-latest
        
        steps:
            - name: Call and run markdown generator
              uses: Zanger67/WikiLeet@main
              with:
                # Insert your LeetCode username here!
                username: Zanger
```

<!-- Insert gif of it running and creating all the markdowns -->

## Additional Features

- Categories
  - The NeetCode150 and Blind75 lists have been added.
  - If you put "Daily" or "Weekly Premium" in the file's name, it will categorize them as such.

- Each question
    -   Contains a completion date, last attempted date, acceptance rate, related topics, languages used, etc.
    -   Each question has a markdown generated containing all solutions (if you have multiple) with all relevant details.
    -   If you create a `.txt` or `.md` file with a question number (e.g. `1234.py`), it will be inserted as a "summary" in the question's markdown. I personally use this to place my notes that I created while working on the problem. Click [here](https://github.com/Zanger67/leetcode/blob/main/markdowns/_3213.%20Construct%20String%20with%20Minimum%20Cost.md) for an example.

- Contests
  - A **contest container** is any directory whose immediate subfolders are individual contests. Each subfolder's questions are attributed to a contest named after that subfolder (e.g. `contests/Weekly Contest 400/200. two-sum.py` → the *Weekly Contest 400* contest).
  - Containers are found two ways, and both can contribute at once:
    - **Auto-detected:** any folder named verbatim `contest` or `contests`, located *anywhere* in the repo.
    - **User-specified:** additional containers (with any name) registered via the action's `contest-dir` input or the `-contest-dir` flag. Both accept **multiple** values — comma-separated (`contest-dir: 'comps/, weeklies/'`) or, for the CLI, by repeating `-contest-dir`.
  - Click [here](https://github.com/Zanger67/leetcode/tree/main/my-submissions) for an example.

- Auto-uploading submissions
  - Solution files are detected **anywhere in the repo**, not just in a dedicated folder. Any code file whose name contains the question number is picked up, using the **first 1-4 digit number** in the name (e.g. `abc1234 notes.java` → `1234`; a 5+ digit run like `abc12345.java` is ignored, and `abc123def345.java` → `123`).
  - Generically-named files like `main`/`solution` that have no number of their own take the question number from their **immediate parent folder** instead (e.g. `1234. Two Sum/Solution.java` → `1234`). Only that one folder level is checked.
  - Difficulty (Easy/Medium/Hard) always comes from the official LeetCode question data. Dot-directories (`.git/`, `.github/`, ...), the generated `markdowns/` folder, and this generator's own folder are skipped.
  - E.g. with the [vscode-leetcode](https://github.com/LeetCode-OpenSource/vscode-leetcode/tree/master) extension, you can set any folder as the file store location and the script will parse it all the same.

- Creation and modification dates
  - Default times are set based off of UTC commit times since that's what LeetCode goes off of.
  - These are tracked based off of your commit history by default. The script parses every file associated with a question up it's commit log finding the earliest and latest dates.
  - If ran manually, this can be done using the file creation and modification dates.
  - Warning: parsing the git commit history of each file is **slow** when done locally it seems but on GitHub actions, it's relatively fast. I'm not sure why this is, but to run locally look at the `flag` instructions for `-n` and `-g` in the [main.py](main.py) file's `main()`.


### Running Locally
The program can be ran locally once imported as a submodule via running `main.py` (all the functionality) or `main.ipynb` (a notebook wrapper that runs the same pipeline one stage at a time).

<!-- Insert instructions for submodule import and the run instructions -->

## About files and directories

| File / Directory                                                           | Details                                                                                                                                                                                                                                                      |
| :------------------------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`question_data/`](question_data/)                                         | Contains `.json` and `.pkl` files with question information such as AC rates, related topics, titles, etc. This is done to avoid constantly querying the Leetcode server and is automated within this repo. |
| [`user_data/`](user_data/)                                                 | A `.gitignore`d folder that will store the last modified date of each question so it doesn't unnecessarily reprocess questions that haven't changed. This only applies to local runs of the script.                                                                                                         |
| [`Lists/`](Lists/)                                                         | `.txt` files with lists such as the NeetCode150 and Blind75 (see the readme in this folder for more information).                                                                                                                                                   |
| [`.env`](.env.sample)                                                      | A config file template that you should edit with your own information, namely your LeetCode username.                                                                                                                                  |
| [`main.py`](main.py)                                                       | The main program that parses all your code and generates the markdowns (type `python main.py`; see its docstring for the flags).                                                                                                                             |
| [`main.ipynb`](main.ipynb)                                                 | A thin notebook wrapper around `main.py` for running the pipeline locally, one stage at a time.                                                                                                                                                              |
| [`env_config.py`](env_config.py)                                           | Loads the `.env` files and resolves every path the generator uses.                                                                                                                                                                                           |
| [`LeetCode Record - Publix.xlsx`](<LeetCode Record - Publix.xlsx>)         | The spreadsheet I use to track my progress with cumulative graphs and whatnot (extra)                                                                                                                                                                        |

## EXAMPLES

_[Click here to see my own repo as an example](https://github.com/Zanger67/leetcode)_

</br>

### My Repo's Homepage (the Primary README)

![Leetcode Repository Example](misc/eg_front_page.png?raw=true)

---

### A single question markdown which was generated from 2 solution files and a context file to add details

![Individual Question's Markdown Example](misc/eg_individual_question_markdown.png?raw=true)

---

### The pre-rendered markdown

![Markdown Code Example](misc/eg_markdown_code.png?raw=true)

---

![Spreadsheet Example](misc/spreadsheet_stats.png?raw=true)

<!-- ---

</br>
</br>

![Mediums Eg](misc/image.png?raw=true)

</br> -->

<!-- ---

</br>
</br>

_View of the actual markdown before being rendered_
![Markdown Code](misc/image-2.png?raw=true) -->

<!-- ---

</br>
</br>

_View of my stats spreadsheet that I used to track my progress_
![Stats from Excel Example](misc/image-3.png?raw=true) -->
## Characteristics to be Aware of
- In each new week, you may have a case where it shows a case of `+[# of questions solved] lines` `-[# of questions solved] lines`. This is likely the due to the AC rates being updated for the week.
- Occasionally, a lot of lines may be updated on the generalized files (`README.md`, `Mediums.md`, `Arrays.md`, etc.). If the question you add increases the width of a markdown file, it'll update the whole table width to match causing this. For instance, if my `Languages` column is usually just `py, java` but then for the first time I have a 3rd language for `py, java, js`, it'll udpate the column width so it "seems" like a lot of lines.


## Future Additions Planned
- Auto detection for Daily and Weekly Premium questions (e.g. commit time +/- 1 day)