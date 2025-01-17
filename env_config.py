# Categories besides those in lists
from datetime import datetime
import json
from ntpath import join
from os import getenv


PRIMARY_CATEGORIES = set(['Daily', 'Weekly Premium', 'Contest', 'Favourite'])
_oldest_date = datetime.now()
# _oldest_date = datetime(2024, 7, 23)

README_PATH, LEETCODE_PATH_FROM_README, LEETCODE_PATH_REFERENCE = None, None, None

QUESTION_DATA_FOLDER = None
SUBMODULE_DATA_PATH = None

HISTORY_PATH = None

DAILIES_DATA_PATH = None
WEEKLIES_DATA_PATH = None

LISTSDIR = None
README_PATH                     = None
QUESTIONS_FOLDER_FROM_README    = None
QUESTIONS_FOLDER                = None

MARKDOWN_PATH = None
MARKDOWN_TO_SUBMISSIONS = None


QUESTION_DATA_FOLDER_PATH    = None
QUESTION_TOPICS_FILE         = None
QUESTION_DETAILS_FILE        = None


BY_TOPIC_FOLDER_PATH = None



TOPIC_FOLDER = None

# For each topic case
NOTEBOOK_PATH = None

# For the overal hosting markdown
OVERALL_FILE_NOTEBOOK_PATH = None
OVERALL_FILE_README_PATH   = None

DIFFICULTY_MARKDOWNS_PATH = None
DAILY_URL = None
