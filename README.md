# Leetcode Progress Updater

> [Click here for a sample repo (my LeetCode repo)](https://github.com/Zanger67/leetcode)

Heya! This repository contains the scripts I created to automatically take all my Leetcode solutions and convert them to a navigatable wiki of markdown files. See the link above for a live example.

If you'd like to use this for yourself, you can either import this repo as a submodule or use the template I've [created]. Instructions can be found at the bottom of this README.

<!-- To create a readme, input your information and the directory path and run [`main.ipynb`](main.ipynb). -->

<!-- Insert gif of it running and creating all the markdowns -->

## Additional Features

-   Automatically generates a README markdown with your solved count and links to each question.
    -   Each question is linked with a completion date, its topics, languages used, etc.
    -   Each question has a markdown generated containing all solutions (if you have multiple) with all relevant details.
-   Has the `Neetcode150` and `Blind75` lists already added.
-   Provides lists sorted and grouped by Completion Date, Daily Questions, and the official Topics.

-   If you are using the LeetCode [vscode-leetcode](https://github.com/LeetCode-OpenSource/vscode-leetcode/tree/master) extension, you can set the `my-submissions` as the file store location and the script will parse it all the same.

## How to Use

See [here](https://github.com/Zanger67/leetcode-template/tree/main) for the template repository and instructions on how to make use of it.

## Data Files

-   [`leetcode question list query.json`](<question_data/leetcode question list query.json>) - Direct query to Leetcode's GraphQL API for all question info including topics, acceptance rates, full names, etc.
-   `leetcode_question_details.pkl` & `leetcode_question_topics.pkl` - Binary file exports using the `pickle` `Python` package to export and save dictionaries for later use. -->

## About the files and directories

| File / Directory                                                           | Details                                                                                                                                                                                                                                                      |
| :------------------------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`question_data/`](question_data/)                                         | contains a `.json` and `.pkl` files with all the details pertaining to each question such as AC rates, related topics, titles, etc. This is done to avoid constantly querying the Leetcode server since questions won't change that significantly over time. |
| [`user_data/`](user_data/)                                                 | a `.gitignored` folder that will store the last modified date of each question so it doesn't unnecessarily reprocess questions that haven't changed.                                                                                                         |
| [`Lists/`](Lists/)                                                         | `.txt` files with the question numbers of each list (read the readme in this folder for more information).                                                                                                                                                   |
| [`.env.sample`](.env.sample)                                               | a config file template that you should edit with your own information (remove the `.sample` portion to leave it as `.env`).                                                                                                                                  |
| [`main.ipynb`](main.ipynb)                                                 | the main program that parses all your code and generates the markdowns.                                                                                                                                                                                      |
| [`main.py`](main.py)                                                       | the exported version of `main.ipynb` for easier running (type `python main.py`).                                                                                                                                                                             |
| [`parse_official_question_data.ipynb`](parse_official_question_data.ipynb) | a helper script that I use to reprocess the `.json` data (you can ignore).                                                                                                                                                                                   |
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
