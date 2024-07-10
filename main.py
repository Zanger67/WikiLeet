#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as kungfupanda                    # pandas
from pandas import DataFrame

from os import listdir                          # for file retrieval and path calculations
from os.path import isfile, join
from os import stat

from os.path import isdir                       # for creation of topic markdown folder if 
from os import mkdir                            # not present

from os import getcwd                           # gets current working DIR for calculating git 
                                                # root of submissions folder 

from os import chdir                            # for changing the working directory to ensure
from os.path import abspath, dirname            # relative paths used are from this script's
import sys                                      # location rather than the calling location
                                                # e.g. if you call `python someFolder/main.py`
                                                #      then it will still work.

import subprocess

from os.path import getmtime, getctime          # retreiving file creation/modification times
from datetime import datetime
import time

from os import getenv                           # for environment variables
from dotenv import load_dotenv, find_dotenv     # for config purposes (.env file)

from typing import Set, Dict, List, Tuple       # misc. QOL imports
from collections import defaultdict
from icecream import ic                         # for debugging / outputs

import re                                       # for regex file name matching

import argparse                                 # For command line arguments when calling py script with flags
import pickle                                   # for saving/loading json records and file 
                                                # modification date history

from functools import cache                     # for redundancy protection


# # Script Configuration
# 1. Loads `env` variables for reference
# 2. If is a script run, denotes it as such for script flag references and ensures working directory is the script's location rather than the calling directory.

# In[ ]:


# loading env variables
load_dotenv(find_dotenv(), override=True)


# NOTE: if the script is being run from a jupyter notebook, then it should
# already be in the correct directory.
IS_NOTEBOOK = True
try:
    if 'ipykernel' not in sys.modules:
        print('Working directory being set to script location.')
        IS_NOTEBOOK = False
        chdir(dirname(abspath(__file__)))
    else :
        print('Working directory already set to script location. No need for adjustment')
except NameError:
    print('NameError')
    pass


# README_ABS_DIR will get confirmed in if name==main prior to running
README_ABS_DIR = getcwd().replace('\\', '/')
NOTEBOOK_ABS_DIR = README_ABS_DIR
print(f'{NOTEBOOK_ABS_DIR = }')
MAIN_DIRECTORY = NOTEBOOK_ABS_DIR[NOTEBOOK_ABS_DIR.rfind('/')+1:]


# In[ ]:


README_PATH                 = getenv('README_PATH')
LEETCODE_PATH_FROM_README   = getenv('QUESTIONS_PATH_FROM_README')
LEETCODE_PATH_REFERENCE     = join(README_PATH, LEETCODE_PATH_FROM_README)


# ## Helper Methods
# 
# AddCase $\rightarrow$ takes information for a new question file and formats it accordingly for a row.
# 
# UpdateLanguage $\rightarrow$ if a question already has a solution, this is called instead to insert the new file link to the existing row details.

# In[ ]:


# Categories besides those in lists
PRIMARY_CATEGORIES = set(['Daily', 'Weekly Premium', 'Contest', 'Favourite'])


# In[ ]:


_ALL_GIT_CM_TIMES = None
def getAllCTimesViaGit(paths: List[str]) -> Dict[str, Tuple[datetime, datetime]] :
    '''
    WARNING: SLOW

    To avoid having to constantly swap directories, this function parses all the ctimes and mtimes 
    in one block of time. This gets activated with the `-g` flag. Default otherwise is to use the 
    regular `getctime` and `getmtime` functions locally which is much much faster. This only exists 
    to compensate for the inability for ctime and mtime checking with git actions.
    '''
    print(f'pre ../: {getcwd() = }')

    chdir('../')

    cmd = r"git log --follow --format=%ct --reverse --".split()
    output = {}

    process = subprocess.Popen(['git', 'log', '--follow', '--format=%ct', '--reverse', '--', 'my-submissions/m1482.md'],
                                   shell=False,
                                #    shell=True,
                                   stdin=None,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)

    result = process.stdout.readlines()
    modifiedTimes = []
    if len(result) >= 1:
        for line in result:
            modifiedTimes.append(line.decode("utf-8").replace('\n', ''))
    print(f'{modifiedTimes = }')

    print(f'post ../: {getcwd() = }')
    print(f'{listdir(getcwd()) = }')

    for i, path in enumerate(paths) :
        # if not path.endswith('.md') :
        #     continue
        path = join(LEETCODE_PATH_FROM_README, path)
        print(f'{cmd + [path] = }')
        process = subprocess.Popen(cmd + [path],
                                   shell=False,
                                #    shell=True,
                                   stdin=None,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        result = process.stdout.readlines()
        modifiedTimes = []
        if len(result) >= 1:
            for line in result:
                modifiedTimes.append(line.decode("utf-8").replace('\n', ''))

        if modifiedTimes[-1] == '':
            modifiedTimes.pop()

        try :
            creationDate = datetime.strptime(time.ctime(int(modifiedTimes[0])), '%a %b %d %H:%M:%S %Y')
            modifiedDate = datetime.strptime(time.ctime(int(modifiedTimes[-1])), '%a %b %d %H:%M:%S %Y')
        except ValueError as ve:
            print(f'Error in parsing {path}')
            print(f'{modifiedTimes}')
            print(ve)
            exit()
        print((creationDate, modifiedDate))
        print()

        output[path] = (creationDate, modifiedDate)

    # Usually I'd avoid using global for this but this is a personal project so it should be fine.
    _ALL_GIT_CM_TIMES = output
    print(f'{output = }')
    
    chdir(MAIN_DIRECTORY)
    return output


# In[ ]:


@cache
def getCtimesMtimesGitHistory(path: str) -> Tuple[datetime, datetime] :
    path = path[path.find('/') + 1:]
    print('asdf git')
    chdir('../')
    cmd = r"git log --follow --format=%ct --reverse --".split() + [path]
    process = subprocess.Popen(cmd,
                               shell=True,
                               stdin=None,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    result=process.stdout.readlines()
    modifiedTimes = []
    if len(result) >= 1:
        for line in result:
            modifiedTimes.append(line.decode("utf-8").replace('\n', ''))

    print(modifiedTimes)
    
    # # print(f'{getcwd() = }')
    # modifiedTimes = subprocess.check_output(cmd)
    # modifiedTimes = modifiedTimes.decode('utf-8')
    # modifiedTimes = modifiedTimes.split('\n')
    # # print(f'{modifiedTimes = }')

    # Linebreak at last element can cause empty string
    if modifiedTimes[-1] == '':
        modifiedTimes.pop()

    creationDate = datetime.strptime(time.ctime(int(modifiedTimes[0])), '%a %b %d %H:%M:%S %Y')
    modifiedDate = datetime.strptime(time.ctime(int(modifiedTimes[-1])), '%a %b %d %H:%M:%S %Y')

    print(f'{creationDate, modifiedDate = }')

    chdir(MAIN_DIRECTORY)

    return (creationDate, modifiedDate)


# In[ ]:


USE_GIT_DATES = False

@cache
def getCtimeMtimesMain(path: str) -> Tuple[datetime, datetime] :
    '''
    Returns the a tuple containing the datetime objs of 
    (create date and time, modification date and time)

    @param useGitDates: bool = False
        If true, it will track the creation/modification dates of the file 
        according to the git history. This is mainly to counter the issue in 
        GitHub actions where the file creation date is the time of the action.
    '''
    
    if USE_GIT_DATES :
        return getCtimesMtimesGitHistory(path)
    
    # print('regular date called')
    creation_date = time.ctime(getctime(path))
    modification_date = time.ctime(getmtime(path))

    creation_date = datetime.strptime(creation_date, "%a %b %d %H:%M:%S %Y")
    modification_date = datetime.strptime(modification_date, "%a %b %d %H:%M:%S %Y")

    # I've sometimes encountered weird meta data issues so just as a precaution
    if creation_date > modification_date :
        return (modification_date, creation_date)
    
    return (creation_date, modification_date)


# In[ ]:


def getCtimeMtimes(path: str, *, preCalculated: Dict[str, Tuple[datetime, datetime]] = None) -> Tuple[datetime, datetime] :
    readme_path = path if ('../' not in path) else path[path.find('../') + len('../'):]
    print(f'{readme_path = }')
    if _ALL_GIT_CM_TIMES and readme_path in _ALL_GIT_CM_TIMES :
        return _ALL_GIT_CM_TIMES[readme_path]
    
    if preCalculated and readme_path in preCalculated :
        return preCalculated[readme_path]

    print('forced manual generation')
    return getCtimeMtimesMain(path)


# In[ ]:


def addCase(level:              str,
            number:             int, 
            title:              str, 
            categories:         Set[str],
            language:           str,
            notebook_path:      str,
            readme_path:        str,
            fileLatestTimes:    dict,
            contestTitle:       str=None,
            contestQNo:         str=None) -> dict :
    '''
    Takes the data found on a question not encountered before and 
    converts it into a callable dictionary with all the relevant 
    information

    ### Parameters (Required) :
    level : str
        Difficulty indicator of the question (e, m, h)
    number : int
        The official LeetCode question number
    title : str
        The title of the question (colloquial name)
    categories : Set[str]
        The categories the question falls under (e.g. Contest, Daily, etc.)
    language : str
        The programming language used to solve the question
    notebook_path : str
        The path from the main.py/ipynb script to the code file in question
    readme_path : str
        The path from the README.md file to be exported to the code file in question
    fileLatestTimes : dict
        A dictionary containing the latest modification times of all files
        in the repository
    
    ### Parameters (Optional) :
    contestTitle : str
        The title of the contest the question was a part of if applicable
    contestQNo : str
        The question number in the contest if applicable (e.g. q1, q2, etc.)

    ### Returns :
    output : dict
        A dictionary containing all the relevant information for the question
        to be used in the final output
    '''

    creation_date, modification_date = getCtimeMtimes(notebook_path)
    fileLatestTimes[readme_path] = modification_date

    try :
        fileSize = stat(notebook_path).st_size
    except FileNotFoundError as fnfe :
        fileSize = 0
        print(fnfe)
    

    if not categories :
        categories = set()

    if 'e' in level.lower() :
        level = 'Easy'
    elif 'm' in level.lower() : 
        level = 'Medium'
    elif 'h' in level.lower() :
        level = 'Hard'
    else :
        level = 'Unknown'

    output = {
                'level':                level,
                'number':               number,
                'title':                title, 
                'categories':           categories,
                'contestTitle':         contestTitle,
                'contestQNo':           contestQNo,
                'date_done':            creation_date,          # First time completed
                'date_modified':        modification_date,      # Most recent date
                'solution':             '',
                'solutions':            {language: [readme_path]},
                'languages':            set([language]),
                'bytes':                fileSize
             }

    return output


# In[ ]:


def updateQuestion(orig:               dict, 
                   *,
                   language:           str,
                   categories:         Set[str],
                   notebook_path:      str,
                   readme_path:        str,
                   fileLatestTimes:    dict,
                   contestTitle:       str=None,
                   contestQNo:         str=None) -> dict :
    '''
    Takes question data of a question that's already been encountered and 
    updates the relevant dictionary with the new information found. Similar 
    to addCase but for questions that have already been encountered.

    ### Parameters :
    orig : dict
        The original dictionary containing all the relevant information from previous encounters
    
    All other parameters are the same as addCase and are optional in order to update them.
        
    ### Returns :
    orig : dict
        The updated dictionary containing all the relevant information from previous encounters
    '''
    
    # Another question file found
    if language and language not in orig['languages'] :
        orig['languages'].add(language)

    if contestTitle :
        orig['contestTitle'] = contestTitle
        
    if contestQNo :
        orig['contestQNo'] = contestQNo
          
    if categories :
        orig['categories'] |= categories

    if notebook_path and readme_path :
        creation_date, modification_date = getCtimeMtimes(notebook_path)
        
        if creation_date < orig['date_done'] :
            orig['date_done'] = creation_date
        if modification_date > orig['date_modified'] :
            orig['date_modified'] = modification_date
            fileLatestTimes[readme_path] = modification_date

        if language not in orig['solutions'] :
            orig['solutions'][language] = []
        orig['solutions'][language].append(readme_path)

        try :
            fileSize = stat(notebook_path).st_size
        except FileNotFoundError as fnfe :
            fileSize = 0
            print(fnfe)
        orig['bytes'] += fileSize
  
    return orig


# # Pickle Processes
# 

# In[ ]:


@cache
def retrieveQuestionDetails() -> dict :
    '''
    Retrieves the question details (i.e. title, acRates, difficulties, etc.) from
    the relevant `.pkl` file containing parsed official LeetCode json data.

    ### Returns :
    questionDetailsDict : dict[int, details]
        A dictionary containing the question details matched to the question's assigned number
    '''
    
    question_data_folder    = getenv('QUESTION_DATA_PATH')
    question_details_file   = getenv('LEETCODE_QUESTION_DETAILS')

    if not isfile(join(question_data_folder, question_details_file)) :
        print('Rerunning json-to-pkl parse and export due to the file(s) not being found.')
        print()
        import parse_official_question_data
        
    if not isfile(join(question_data_folder, question_details_file)) :
        print('\nError in parsing official question data. Exiting...')
        print()
        exit()
    else : 
        print('\nFiles found. Importing now...\n')


    # schema: key=int(questionNumber)   val=(title, titleSlug, paidOnly, difficulty, acRate)
    with open(join(question_data_folder, question_details_file), 'rb') as fp:
        questionDetailsDict = pickle.load(fp)
        # print('Question Details dictionary')
        # print(questionDetailsDict)

    return questionDetailsDict


# In[ ]:


@cache
def retrieveQuestionTopics() -> dict :
    '''
    Retrieves the topics associated with each question (e.g. Array, LinkedList, 
    BST, etc.) from the relevant `.pkl` file containing parsed official LeetCode json data.

    ### Returns :
    questionDetailsDict : dict
        A dictionary containing the question details matched to the question's assigned number
    '''
    
    question_data_folder    = getenv('QUESTION_DATA_PATH')
    question_topics_file   = getenv('LEETCODE_QUESTION_TOPICS')

    if not isfile(join(question_data_folder, question_topics_file)) :
        print('Rerunning json-to-pkl parse and export due to the file(s) not being found.')
        print()
        import parse_official_question_data
        
    if not isfile(join(question_data_folder, question_topics_file)) :
        print('\nError in parsing official question data. Exiting...')
        print()
        exit()
    else : 
        print('\nFiles found. Importing now...\n')

    # schema: key-int(questionNumber)   val=List[str](topics)
    questionTopicsDict = None
    with open(join(question_data_folder, question_topics_file), 'rb') as fp:
        questionTopicsDict = pickle.load(fp)
        # print('Question Details dictionary')
        # print(questionTopicsDict)

    return questionTopicsDict


# In[ ]:


def writeRecentFileTimes(fileLatestTimes: dict) -> bool :
    '''Pickles the newly found most recent modification times of each question for reference in future runs'''
    
    history_path = join(getenv('USER_DATA_PATH'), getenv('FILE_MODIFICATION_NAME'))

    with open(history_path, 'wb') as fp:
        pickle.dump(fileLatestTimes, fp)

    return True


# In[ ]:


def getRecentFileTimes() -> dict :
    '''Retrieves the pickled data from previous cases of `writeRecentFileTimes()`'''
    
    history_path = join(getenv('USER_DATA_PATH'), getenv('FILE_MODIFICATION_NAME'))

    if isfile(history_path) :
        with open(history_path, 'rb') as fp:
            return pickle.load(fp)
        
    return {}


# # Parsing Files
# Question file parsing occurs here. It organizes it into 3 different lists, separated by difficulty and sorted by question number afterwards.

# In[ ]:


# Parse one leetcode answer file in the submissions folder
def parseCase(leetcodeFile:         str,  # file name
              questionData:         dict, # dictionary of question data
              fileLatestTimes:      dict,
              reprocessMarkdown:    set,
              *,
              questionDetailsDict:  dict = retrieveQuestionDetails(),
              subFolderPath:        str = '',
              altTitle:             str = '',
              contest:              str = None,
              contestQNo:           str = None) -> bool:

    path = join(LEETCODE_PATH_FROM_README, subFolderPath, leetcodeFile).replace("\\", "/")

    number      = int(re.search("\d{1,4}", leetcodeFile).group())   # Takes the first full number as the question
    level       = questionDetailsDict[number][3][0].lower()     # number and uses that as reference
                                                                # e.g. 'e123 v1.py' becomes 123

    creationtime, modificationtime = getCtimeMtimes(join(README_PATH, path))

    if path not in fileLatestTimes or max(creationtime, modificationtime) > fileLatestTimes[path] :
        reprocessMarkdown.add(number)
        fileLatestTimes[path] = max(creationtime, modificationtime)
        

    if number in questionDetailsDict :
        title   = f'[{questionDetailsDict[number][0]}](<https://leetcode.com/problems/{questionDetailsDict[number][1]}>)'
    else :
        title   = f'Question {number}'
    categories  = set()
    language    = leetcodeFile[leetcodeFile.rfind('.') + 1:]

    if len(altTitle) > 0 :
        title = altTitle + ' - ' + title

    # Question is from a contest folder
    if contest :
        temp = re.findall('q\d{1}', leetcodeFile)                       # Checking if file name has a question number (e.g. q1 of the contest)
        if not len(temp) == 0 :
            contestQNo = temp[0]

        categories.add('Contest')


    for cat in PRIMARY_CATEGORIES :
        if cat.lower() in leetcodeFile.lower() :
            categories.add(cat)

    if number in questionData :                                     # If solution already found for this question
        questionData[number] = updateQuestion(questionData[number], 
                                              language=language, 
                                              categories=categories, 
                                              notebook_path=join(README_PATH, path), 
                                              readme_path=path,
                                              contestTitle=contest,
                                              contestQNo=contestQNo,
                                              fileLatestTimes=fileLatestTimes)
        return True
    
    questionData[number] = addCase(level=level, 
                                   number=number, 
                                   title=title,
                                   categories=categories, 
                                   language=language, 
                                   notebook_path=join(README_PATH, path), 
                                   readme_path=path,
                                   contestTitle=contest,
                                   contestQNo=contestQNo,
                                   fileLatestTimes=fileLatestTimes)
    return True


# In[ ]:


@cache
def getCodeFiles() -> List[str] :
    return [x for x in listdir(LEETCODE_PATH_REFERENCE) if isfile(join(LEETCODE_PATH_REFERENCE, x))
                                                           and not x.endswith('.txt')
                                                           and not x.endswith('.md')
                                                           and '.' in x]

@cache
def getContestFolders() -> List[str] :
    return [x for x in listdir(LEETCODE_PATH_REFERENCE) if not isfile(join(LEETCODE_PATH_REFERENCE, x))]

@cache
def getContextFiles(contestFolders: List[str] = getContestFolders()) -> List[str] :
    output = [x for x in listdir(LEETCODE_PATH_REFERENCE) if isfile(join(LEETCODE_PATH_REFERENCE, x)) 
                                                             and (x.endswith('.txt') 
                                                                  or x.endswith('.md') 
                                                                  or '.' not in x)]
    for folder in contestFolders :
        output.extend([join(folder, y) for y in listdir(join(LEETCODE_PATH_REFERENCE, folder)) 
                                if isfile(join(LEETCODE_PATH_REFERENCE, folder, y))
                                   and (y.endswith('.txt') 
                                        or y.endswith('.md') 
                                        or '.' not in y)])
    return output

def getContestFiles(contestFolders: List[str]) -> List[Tuple[str, str]] :
    contestLeetcodeFiles    = []

    for contestFolder in contestFolders :
        contestLeetcodeFiles.extend([(contestFolder, fileName) for fileName in listdir(join(LEETCODE_PATH_REFERENCE, contestFolder)) 
                                                                if isfile(join(LEETCODE_PATH_REFERENCE, contestFolder, fileName))
                                                                    and not fileName.endswith('.txt')
                                                                    and not fileName.endswith('.md')
                                                                    and '.' in fileName])
    
    return contestLeetcodeFiles



# # Sort TXT Context
# If .txt notes are placed, this adds them to their respective entry.

# In[ ]:


def parseContextFiles(txtFiles: str, 
                      questionData: dict,
                      fileLatestTimes: dict, 
                      reprocessMarkdown: Set[int]) -> None:
    for fileName in txtFiles :
        print(f'Context file found: {fileName}')

        if '\\' in fileName :
            number = int(re.search("\d{1,4}", fileName[fileName.find('\\') + 1:]).group())
        elif '/' in fileName :
            number = int(re.search("\d{1,4}", fileName[fileName.find('/') + 1:]).group())
        else :
            number = int(re.search("\d{1,4}", fileName).group())
        if number not in questionData :
            print(f'Error. No question solution found for context file ({fileName = })')
            continue
        
        questionData[number]['contextFile'] = join(LEETCODE_PATH_FROM_README, fileName)
        path = join(LEETCODE_PATH_REFERENCE, fileName)
        
        creationtime, modificationtime = getCtimeMtimes(path)
        if path not in fileLatestTimes or max(creationtime, modificationtime) > fileLatestTimes[path] :
            fileLatestTimes[path] = max(creationtime, modificationtime)
            reprocessMarkdown.add(number)


# # List-Based Categories
# Updating `Category` columns based on the lists in the `Lists` directory.

# In[ ]:


LISTSDIR = getenv('LISTS_LOCATION')

@cache
def getLists() -> List[str] :

    listFileNames = [x for x in listdir(LISTSDIR) if isfile(join(LISTSDIR, x)) 
                                                    and not x.startswith('.')
                                                    and not x == 'README.md']
    print(listFileNames)

    return listFileNames


# In[ ]:


''' Format for lists file is as follows:

        [Question #]. [Question Name]

        [Easy, Med., Hard]
        Topic1
        Topic2
        Topic3
        ...
'''

@cache
def getList(fileName, filePath) -> set[int] :
    output = set() # can change to dict later if we want to output category info

    count = 0
    with open(filePath, 'r') as file :
        lines = file.readlines()
        for line in lines :
            if re.match(r'\d{1,4}\.', line) :
                count += 1
                output.add(int(line[:line.find('.')]))
    
    return output
    


# In[ ]:


def processListData(questionData: dict,
                    *,
                    listFileNames: List[str] = getLists()) -> dict :
    
    listData = {}
    for file in listFileNames :
        listData[file] = getList(file, join(LISTSDIR, file))
        for q in listData[file] :
            if q in questionData :
                questionData[q]['categories'].add(file)
                
    # print(listData)

    return listData


# # Question Topic Grouping
# Parses the questions in `questionData` and adds their numbers to appropriate lists so that they can be parsed into their own lists as well as counted.

# In[ ]:


def getCompletedQuestionsTopicLists(questionData: dict,
                                    *,
                                    questionTopicsDict: dict = retrieveQuestionTopics()) -> defaultdict :
    
    completedTopicLists = defaultdict(set)

    for question in questionData.keys() :
        if question not in questionTopicsDict :
            continue
        for topic in questionTopicsDict[question] :
            completedTopicLists[topic].add(question)

    return completedTopicLists


# # Individual Markdown Generation
# 

# In[ ]:


README_PATH                     = getenv('README_PATH')
QUESTIONS_FOLDER_FROM_README    = getenv('QUESTIONS_PATH_FROM_README')
QUESTIONS_FOLDER                = join(README_PATH, QUESTIONS_FOLDER_FROM_README)

MARKDOWN_PATH = getenv('QUESTION_MARKDOWNS_PATH_FROM_README')
MARKDOWN_TO_SUBMISSIONS = '../' * MARKDOWN_PATH.count('/') + QUESTIONS_FOLDER_FROM_README

QUESTION_DATA_FOLDER_PATH    = getenv('QUESTION_DATA_PATH')
QUESTION_TOPICS_FILE         = getenv('LEETCODE_QUESTION_TOPICS')
QUESTION_DETAILS_FILE        = getenv('LEETCODE_QUESTION_DETAILS')

import json
with open('question_data/language_equivs.json') as f :
    LANGUAGE_EQUIVS = json.load(f)


# In[ ]:


# MARKDOWN_TO_SUBMISSIONS
def generate_markdown(questionNo: int, 
                      questionData: dict,
                      *,
                      questionDetailsDict: dict = retrieveQuestionDetails(),
                      questionTopicsDict: dict = retrieveQuestionTopics(),
                      export: bool = False) -> str :
    if questionNo in questionData :
        questionData = questionData[questionNo]

    title = questionData["title"]

    # Only if title has already been modified and matched to a LeetCode url
    # E.g. some contest files will be unmatched
    if '[' in questionData["title"] :
        title = title[title.find('[') + 1:title.find(']')]

    title = f'{questionNo}. {title}'
    
    generate_file_name = f'_{title}.md'
    generate_path = join(README_PATH, MARKDOWN_PATH, generate_file_name)
    output_path = join(MARKDOWN_PATH, generate_file_name)
    
    questionData['solution'] = generate_file_name

    if not export :
        return generate_path

    with open(generate_path, 'w', encoding='utf-8') as f :
        f.write(f'# {questionNo}. {questionData["title"]}\n\n')

        date_done = questionData['date_done']
        date_modified = questionData['date_modified']
        
        f.write(f'*All prompts are owned by LeetCode. To view the prompt, click the title link above.*\n\n')
        
        if questionData['contestTitle'] and questionData['contestQNo']:
            f.write(f'*Completed during {questionData["contestTitle"]} ({questionData["contestQNo"]})*\n\n')

        f.write('*[Back to top](<../README.md>)*\n\n')

        f.write('------\n\n')
        f.write(f'> *First completed : {date_done:%B %d, %Y}*\n>\n')
        f.write(f'> *Last updated : {date_modified:%B %d, %Y}*\n')

        f.write('\n------\n\n')

        BY_TOPIC_FOLDER_PATH = getenv('TOPIC_MARKDOWN_PATH_IN_MARKDOWNS_FOLDER')
        tpcs = 'N/A' if questionNo not in questionTopicsDict or len(questionTopicsDict[questionNo]) == 0 \
                     else ', '.join([f'[{x}](<{join(BY_TOPIC_FOLDER_PATH, x)}.md>)' for x in questionTopicsDict[questionNo]])
        
        f.write(f'> **Related Topics** : **{tpcs}**\n>\n')

        acrate = 'Unknown' if questionNo not in questionDetailsDict else f'{questionDetailsDict[questionNo][4]} %'
        f.write(f'> **Acceptance Rate** : **{acrate}**\n\n')
        f.write('------\n\n')

        if 'contextFile' in questionData:
            with open(join(README_PATH, questionData['contextFile']), 'r') as contextFile:
                f.write('> ' + contextFile.read().replace('\n', '\n> '))
            f.write(f'\n\n------\n\n')
        

        f.write(f'## Solutions\n\n')
        for lang, solutions in questionData['solutions'].items() :
            solutions.sort()
            for solution in solutions :
                name = solution[solution.find('/') + 1:]
                f.write(f'- [{name}](<{join(README_PATH, solution)}>)\n')

        for lang, solutions in questionData['solutions'].items() :
            if lang.lower() in LANGUAGE_EQUIVS :
                lang = LANGUAGE_EQUIVS[lang.lower()]
            else :
                print()
                print(f'Lang equiv not found: {lang = }')
            f.write(f'### {lang}\n')
            for solution in solutions :
                name = solution.rfind('/') + 1
                f.write(f'#### [{solution[name:]}](<{join(README_PATH, solution)}>)\n')
                f.write(f'```{lang}\n')
                with open(join(README_PATH, solution), 'r', encoding='utf-8') as solutionFile:
                    fileData = solutionFile.read()
                    if '# @lc code=start' in fileData :
                        lcStart = '# @lc code=start'
                        lcEnd   = '# @lc code=end'
                        fileData = fileData[fileData.find(lcStart) + len(lcStart):fileData.rfind(lcEnd)]
                    f.write(fileData)
                f.write('\n```\n\n')

    return output_path


# In[ ]:


def processMarkdownGeneration(questionData: dict,
                              reprocessMarkdown: Set[int],
                              *,
                              questionDetailsDict: dict = retrieveQuestionDetails(),
                              questionTopicsDict: dict = retrieveQuestionTopics()) -> None :
    for questionNo, dta in questionData.items() :
        if questionNo in reprocessMarkdown :
            generate_markdown(questionNo, 
                              questionData, 
                              questionDetailsDict=questionDetailsDict, 
                              questionTopicsDict=questionTopicsDict,
                              export=True)
        else : # In order to assign the markdown paths
            generate_markdown(questionNo, 
                              questionData, 
                              questionDetailsDict=questionDetailsDict, 
                              questionTopicsDict=questionTopicsDict,
                              export=False)


# # DataFrames
# Conversion into DataFrames and declaration of respective column headers occurs here.

# In[ ]:


COLUMNS = [ 
            '#',
            'Title', 
            'Level',
            'Cats',
            'Solution',
            'Languages',
            'Date Complete'
          ]

TYPE_CLARIFICATION = {
                      '#':                  int,
                      'Title':              str, 
                      'Level':              str,
                      'Cats':               str,
                      'Solution':           str,
                      'Languages':          str,
                      'Date Complete':      str
                    }


# In[ ]:


def convertDataToMatrix(questionData: dict,
                        *,
                        sortBy:       str = 'number',
                        includeDate:  bool = False,
                        includeQuestions: set[int] = set(),
                        relativeFolderAdjustment: int = 0,
                        includeMarkdownFolder: bool = False) -> List[list] :
    dataframe_array = []

    for question in questionData.values() :
        # If it's not an empty set and the value isn't in there, skip
        if includeQuestions and question['number'] not in includeQuestions :
            continue

        if sortBy == 'number' and includeMarkdownFolder :
            solution_path = join(MARKDOWN_PATH, question['solution'])    
        else :
            solution_path = question['solution']
        
        solution_path = '../' * abs(relativeFolderAdjustment) + solution_path

        title_to_use = question['title']
        
        if question['contestTitle'] and question['contestQNo'] :
            title_to_use = f'{question["contestTitle"]} - {question["contestQNo"]} - {title_to_use}'

        currentRow = [question['number'],
                      title_to_use, 
                      question['level'], 
                      ', '.join(sorted(list(question['categories']))), 
                      f'[solution](<{solution_path}>)', 
                      ', '.join(sorted(list(question['languages'])))]
        
        if includeDate :
            currentRow.append(question['date_done'].strftime('%b %d, %Y'))
        
        dataframe_array.append(currentRow)

    dataframe_array.sort(key=lambda x: questionData.get(x[0])[sortBy])
    return dataframe_array


# In[ ]:


def convertQuestionDataToDataframe(questionData: dict,
                                   *,
                                   sortBy: str = 'number',
                                   includeDate:  bool = False,
                                   includeQuestions: set[int] = set(),
                                   relativeFolderAdjustment: int = 0,
                                   includeMarkdownFolder: bool = False) -> DataFrame :
    questionData = convertDataToMatrix(questionData, 
                                       sortBy=sortBy, 
                                       includeDate=includeDate, 
                                       includeQuestions=includeQuestions,
                                       relativeFolderAdjustment=relativeFolderAdjustment,
                                       includeMarkdownFolder=includeMarkdownFolder)
    
    dfQuestions   = kungfupanda.DataFrame(data=questionData, columns=COLUMNS[:len(questionData[0])])
    # dfQuestions   = dfQuestions.astype(TYPE_CLARIFICATION[:len(questionData[0])])

    return dfQuestions


# # List & Other Markdowns

# ## Sorted by Most Recent
# Using creation dates of code files only; not modification dates.

# In[ ]:


# NOTE: Reversed due to default sorting being in ascending order
def byRecentQuestionDataDataframe(questionData: dict) -> DataFrame :
    return convertQuestionDataToDataframe(questionData, sortBy='date_done', includeDate=True).iloc[::-1]


# ## Sorted by Amount of Code
# Questions with more files on the question and longer submissions will be prioritized.

# In[ ]:


def byCodeLengthDataDataframe(questionData: dict) -> DataFrame :
    return convertQuestionDataToDataframe(questionData, sortBy='bytes', includeDate=True).iloc[::-1]


# # Generation of Markdowns for Each Related Topic
# 

# In[ ]:


def questionTopicDataframes(questionData: dict,
                            *,
                            topicGroupings: defaultdict) -> List[Tuple[str, int, DataFrame]] : # [topic, number of questions, dataframe]
    if not topicGroupings :
        topicGroupings = getCompletedQuestionsTopicLists(questionData)
    
    output = []
    for topic, qs in topicGroupings.items() :
        output.append((topic, 
                       len(qs), 
                       convertQuestionDataToDataframe(questionData,
                                                      includeDate=True,
                                                      includeQuestions=qs,
                                                      relativeFolderAdjustment=-getenv('TOPIC_MARKDOWN_PATH_IN_MARKDOWNS_FOLDER').count('/'))))
        
    output.sort(key=lambda x: x[1], reverse=True)
    return output


# In[ ]:


TOPIC_FOLDER = getenv('TOPIC_MARKDOWN_PATH_IN_MARKDOWNS_FOLDER')

def topicBasedMarkdowns(questionData: dict,
                         *,
                         topicGroupings: defaultdict) -> List[Tuple[str, str]] :    # path of all outputs
                                                                                    # list[0]  = overall mardown
                                                                                    # list[1:] = order of count
                                                                                    # doesn't include markdown 'markdown/'
    if not topicGroupings :
        topicGroupings = getCompletedQuestionsTopicLists(questionData)

    topicDataframes = questionTopicDataframes(questionData=questionData, topicGroupings=topicGroupings)

    # For each topic case
    NOTEBOOK_PATH = join(README_PATH, MARKDOWN_PATH, TOPIC_FOLDER)

    # For the overal hosting markdown
    OVERALL_FILE_NOTEBOOK_PATH = join(README_PATH, MARKDOWN_PATH, 'Topics.md')
    OVERALL_FILE_README_PATH = join(MARKDOWN_PATH, 'Topics.md')

    if not isdir(NOTEBOOK_PATH) :
        mkdir(NOTEBOOK_PATH)

    output = [OVERALL_FILE_README_PATH]
    with open(OVERALL_FILE_NOTEBOOK_PATH, 'w', encoding='utf-8') as topic_file :
        topic_file.write('# Topics\n\n')
        topic_file.write('*[Back to top](<../README.md>)*\n\n')
        topic_file.write('------\n\n')

        for topic, cnt, df in topicDataframes :
            file_name = f'{topic}.md'
            notebook_path = join(NOTEBOOK_PATH, file_name)
            readme_path = join(TOPIC_FOLDER, file_name)
            with open(notebook_path, 'w', encoding='utf-8') as f :
                url = f'https://leetcode.com/tag/{topic.replace(" ", "-")}/'
                f.write(f'# [{topic}](<{url}>) ({cnt} completed)\n\n')
                f.write(f'*[Back to top](<../../README.md>)*\n\n')
                f.write('------\n\n')
                f.write(df.to_markdown(index=False))
        
            topic_file.write(f'- [{topic}](<{readme_path}>) ({cnt} completed)\n')
            output.append((topic, readme_path))

    # print(f'topic readme output: {output}')
    return output


# ## Exports

# ## Dailies, Recents, etc.

# In[ ]:


DAILY_URL = ''

def miscMarkdownGenerations(questionData:   dict,
                            *,
                            code_length:    bool = False,
                            recent:         bool = False,
                            daily:          bool = False) -> str : # output path
    df = None
    fileName = None
    header_data = None
    details = None

    # print(f'{code_length, recent = }')
    if code_length :
        df = byCodeLengthDataDataframe(questionData)
        fileName    = 'Questions_By_Code_Length.md'
        header_data = '# Questions By Code Length\n\n'
        details     = 'Calculations are based on the code files\'s byte sizes.\n\n'
    elif recent :
        df = byRecentQuestionDataDataframe(questionData)
        fileName    = 'Questions_By_Recent.md'
        header_data = '# Most Recently Solved Questions\n\n'
        details     = 'Calculations are based on the date of the first solve.\n\n'
    elif daily :
        dailyQuestionData = {}
        for qNo, qData in questionData.items() :
            if 'Daily' in qData['categories'] :
                dailyQuestionData[qNo] = qData
        df = byRecentQuestionDataDataframe(dailyQuestionData)
        fileName    = 'Daily_Questions.md'
        # header_data = f'# [Daily Questions](<{DAILY_URL}>)\n\n'
        header_data = f'# Daily Questions\n\n'
        details     = 'Dates are for the date I completed the ' + \
                      'question so due to the my time zone and how it lines up with ' + \
                      'UTC, it may be off by a day.\n\n'
    else :
        print('Error. No markdown generation specified.')
        print()
        return ''

    # print(f'{fileName = }')

    output_path = join(MARKDOWN_PATH, fileName)
    readme_path = join(README_PATH, MARKDOWN_PATH, fileName)

    with open(readme_path, 'w', encoding='utf-8') as f :
        f.write(header_data)
        f.write(f'*[Back to top](<../README.md>)*\n\n')
        f.write(details)
        f.write(df.to_markdown(index=False))

    return output_path


# # Outputing to README File
# Takes all the above and overwrites the current [README.md](README.md) file with the data calculated above.
# 
# Inputs values in order of:
# - Profile link
# - Stats
# - Stat clarification
# - Question link tables Easy-Medium-Hard
# 
# Uses the built-in DataFrame `.to_markdown()` for outputting.

# In[ ]:


def exportPrimaryReadme(dfQuestions:        DataFrame,
                        *,
                        additionalSorts:    List[str] = [],
                        topicLinks:         List[Tuple[str, str]] = []) -> None :
    readmePath = join(README_PATH, 'README.md')
    print(readmePath)
    with open(readmePath, 'w') as file :
        username = getenv('LEETCODE_USERNAME')
        file.write(f'# **[LeetCode Records](https://leetcode.com/u/{username}/)** ({len(dfQuestions.index)} solved)\n\n')

        file.write(f'> My LeetCode Profile: [{username}](https://leetcode.com/u/{username}/)\n\n')

        file.write('## About this Repo\n\n')
        file.write('This repo is a collection of my LeetCode solutions, primarily written in Python, Java, and C. ' + 
                   'On any page, `click the main title` to be redirected to the official `LeetCode` page for the ' + 
                   'question, topic, list, etc. See the `Additional Categories` section for pages that group' + 
                   ' questions by different criteria -- e.g. by their *related topics*.')
        file.write('\n\n\n')

        file.write('------\n\n')

        file.write('## Category Notes\n')
        file.write('1. **Daily** - Daily challenge questions that were done on the day of\n')
        file.write('2. **Weekly Premium** - Weekly premium questions that were done on week of\n')
        file.write('3. **Contest** - Questions that I completed during a live contest\n')
        # file.write('4. **Favourite** - Questions that I liked and wanted to keep a record of\n')
        file.write('\n\n')

        file.write('------\n\n')

        file.write('## Additional Categories Stats\n')

        for altSorts in additionalSorts :
            file.write(altSorts)
            file.write('\n\n')
        
        if topicLinks :
            file.write('------\n\n')
            file.write(', '.join([f'[{topic}](<{join(MARKDOWN_PATH, link)}>)' for topic, link in topicLinks[1:]]))       
            file.write('\n\n')
            file.write('------\n\n')
        
        file.write('\n\n')

        file.write('## Questions\n')
        file.write(dfQuestions.to_markdown(index=False))


# In[ ]:


# recalculateAll: forces recalcualtion markdowns for each question irregardless if its
#                 source files have been modified or not
def main(*, recalculateAll: bool = False, noRecord: bool = False) -> None :
    leetcodeFiles           = getCodeFiles()
    additionalInfoFiles     = getContextFiles()             # For later use when generating the individual readme files

    contestFolders          = getContestFolders()
    contestLeetcodeFiles    = getContestFiles(contestFolders)

    if USE_GIT_DATES :
        getAllCTimesViaGit(additionalInfoFiles + leetcodeFiles + [join(x[0], x[1]) for x in contestLeetcodeFiles])

    questionDetailsDict     = retrieveQuestionDetails()
    questionTopicsDict      = retrieveQuestionTopics()

    leetcodeFiles.sort()
    contestLeetcodeFiles.sort()


    # Files for leetcode questions found
    # print(leetcodeFiles)
    print(f'Total of {len(leetcodeFiles)} files found.')

    # Files in contest folders found
    # print(contestLeetcodeFiles)
    print(f'Total of {len(contestLeetcodeFiles)} contest files found.')

    # print(questionDetailsDict)


    # Parsing primary files
    fileLatestTimes = getRecentFileTimes() if (not recalculateAll and not noRecord) else {}

    reprocessMarkdown = set()
    questionData = {}

    # print(f'{fileLatestTimes = }')

    for leetcodeFile in leetcodeFiles :
        parseCase(leetcodeFile=leetcodeFile,
                  questionData=questionData,
                  fileLatestTimes=fileLatestTimes, 
                  reprocessMarkdown=reprocessMarkdown,
                  questionDetailsDict=questionDetailsDict)
        
    # Parsing contest files & folforders
    for leetcodeContestFile in contestLeetcodeFiles :
        contestFolder, leetcodeFile = leetcodeContestFile
        parseCase(leetcodeFile=leetcodeFile,
                  questionData=questionData,
                  fileLatestTimes=fileLatestTimes,
                  reprocessMarkdown=reprocessMarkdown, 
                  subFolderPath=contestFolder, 
                  questionDetailsDict=questionDetailsDict,
                  contest=contestFolder)
        

    parseContextFiles(txtFiles=additionalInfoFiles, 
                      questionData=questionData,
                      fileLatestTimes=fileLatestTimes,
                      reprocessMarkdown=reprocessMarkdown)
    
    processListData(questionData=questionData)

    processMarkdownGeneration(questionData=questionData, 
                              reprocessMarkdown=reprocessMarkdown, 
                              questionDetailsDict=questionDetailsDict, 
                              questionTopicsDict=questionTopicsDict)
    
    # Produces a markdown where questions are sorted by the amount of code
    # written for the question
    # code_length_md_path = exportCodeLengthMarkdown(questionData)
    byCodeLength        = miscMarkdownGenerations(questionData, code_length=True)
    byRecentlySolved    = miscMarkdownGenerations(questionData, recent=True)
    dailyQuestions      = miscMarkdownGenerations(questionData, daily=True)
    altSorts            = [f'- [Daily Questions](<{dailyQuestions}>)',
                           f'- [Questions By Code Length](<{byCodeLength}>)',
                           f'- [Questions By Recent](<{byRecentlySolved}>)']
    

    completedQsTopicGroupings = getCompletedQuestionsTopicLists(questionData)
    topicMarkdownLinks = topicBasedMarkdowns(questionData, topicGroupings=completedQsTopicGroupings)
    altSorts.append(f'- [Grouped by Topic](<{topicMarkdownLinks[0]}>)')
    # print(topicMarkdownLinks)


    dfQuestions = convertQuestionDataToDataframe(questionData, includeDate=False, includeMarkdownFolder=True)
    exportPrimaryReadme(dfQuestions, additionalSorts=altSorts, topicLinks=topicMarkdownLinks)

    print(f'Number of individual questions updated/added: {len(reprocessMarkdown)}')

    if not noRecord :
        writeRecentFileTimes(fileLatestTimes)           # restore for next use

    # print(len(questionData))

    return questionData, reprocessMarkdown


# In[ ]:


if __name__ == '__main__' :
    '''
    ### Flags
    `-r` : 
        Recalculate all markdown files irregardless of whether there are modified or new code files for that question or not
    `-n` :
        Don't use the previous modified dates and don't store them (in effect, the same as `-r` but it doesn't save the 
        new modification dates). Primarily for use with GitHub actions.
    `-g` :
        Uses the repository's git log history for each file to trace the creation and last modification dates of each file 
        rather than use the default `getctime()` and `getmtime()` of each file. GitHub actions seem to default the ctime 
        and mtimes to time.now due to not tracking the actual mtime ctime metadata.

        WARNING: Only for use with GitHub actions as this ends up being very slow due to low subprocess speends.
    '''
    recalcaulateAll = False
    noRecord = False

    if not IS_NOTEBOOK :
        parser = argparse.ArgumentParser()

        parser.add_argument("-r", 
                            help="Recompile all markdown files", 
                            required=False, 
                            action=argparse.BooleanOptionalAction)
        
        parser.add_argument("-n", 
                            help="Don't use the previous modified dates and don't store them", 
                            required=False, 
                            action=argparse.BooleanOptionalAction)
        parser.add_argument("-norecord", 
                            help="Don't use the previous modified dates and don't store them", 
                            required=False, 
                            action=argparse.BooleanOptionalAction)
        parser.add_argument("-g", 
                            help="Use Git repo's dates for determining if a file has been modified and created (WARNING SLOW)", 
                            required=False, 
                            action=argparse.BooleanOptionalAction)
        
        recalcaulateAll = parser.parse_args().r
        noRecord = parser.parse_args().norecord or parser.parse_args().n

        USE_GIT_DATES = parser.parse_args().g

    README_ABS_DIR = README_ABS_DIR[:README_ABS_DIR.rindex('/')]
    print(README_ABS_DIR, '\n')

    print('No record'.ljust(20), 'on' if noRecord else 'off')
    print('Recalculate'.ljust(20), 'on' if recalcaulateAll else 'off')
    print('Use Git dates'.ljust(20), 'on' if USE_GIT_DATES else 'off')
    print()


    main(recalculateAll=recalcaulateAll, noRecord=noRecord)

