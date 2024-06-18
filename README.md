# Leetcode Progress Updater

Alright, I've been grinding for a while now. I need a break from doing questions. How should I do that. Walk? Nah it's raining. YouTube? Kinda bored of that. Plus, I've watched too many shorts recentlly. 

I know, let's create a way to keep track of all the questions done and code I've written for Leetcode. This totally isn't an addiction.

This is just a small program I whipped up to take the code files I saved for each question I've done on Leetcode and propogate a README with them, sorted by difficulty and question number, linking them to my solutions and the actual webpage. Also shows stats and different languages.

To create a readme, input your information and the directory path and run [`Progress_Updater.ipynb`](Progress_Updater.ipynb).


## Files to Note
### Runnable Files
- [`Progress_Updater.ipynb`](Progress_Updater.ipynb) - File to run to update your README.md file
- [`question_data/ParseQuestions.ipynb`](question_data/ParseQuestions.ipynb) - Parses the Leetcode JSON containing question data to match question numbers to names, difficulties, etc. 

### Config
- [`config`](config)

### Lists
- `.AltNames`
- `N150` - Neetcode 150 Questions
- `B75` - Blind 75 / Grind 75 Questions


### Data Files
- [`leetcode question list query.json`](<question_data/leetcode question list query.json>) - Direct query to Leetcode's GraphQL API for all question info including topics, acceptance rates, full names, etc.
- `leetcode_question_details.pkl` & `leetcode_question_topics.pkl` - Binary file exports using the `pickle` `Python` package to export and save dictionaries for later use.