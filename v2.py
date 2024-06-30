#!/usr/bin/env python
# coding: utf-8

# In[328]:


import pandas as kungfupanda                    # pandas
from os import listdir                          # for file retrieval
from os.path import isfile, join

from typing import Set, Dict, List, Tuple       # misc.

from os.path import getmtime, getctime           # for file creation and modification times
from datetime import datetime
import time

from os import getenv                           # for environment variables
from dotenv import load_dotenv, find_dotenv     # / config purposes (.env file)
load_dotenv(find_dotenv(), override=True)

import re                                       # for regex file name matching
from typing import List                         # misc.


# In[329]:


readme_path             = getenv('README_PATH')
leetcodePathFromReadme  = getenv('QUESTIONS_PATH_FROM_README')
leetcodePathReference   = join(readme_path, leetcodePathFromReadme)
leetcodeFiles           = [x for x in listdir(leetcodePathReference) if isfile(join(leetcodePathReference, x))
                                                                     and not x.endswith('.txt')
                                                                     and not x.endswith('.md')
                                                                     and '.' in x]

# For later use when generating the individual readme files
additionalInfoFiles     = [x for x in listdir(leetcodePathReference) if isfile(join(leetcodePathReference, x))
                                                                     and (x.endswith('.txt') or x.endswith('.md') or '.' not in x)]

contestFolders          = [x for x in listdir(leetcodePathReference) if not isfile(join(leetcodePathReference, x))]
contestLeetcodeFiles    = []

for contestFolder in contestFolders :
    contestLeetcodeFiles.extend([(contestFolder, fileName) for fileName in listdir(join(leetcodePathReference, contestFolder)) 
                                                            if isfile(join(leetcodePathReference, contestFolder, fileName))])

leetcodeFiles.sort()
contestLeetcodeFiles.sort()


# Files for leetcode questions found
print(leetcodeFiles)
print(f'Total of {len(leetcodeFiles)} files found.')

# Files in contest folders found
print(contestLeetcodeFiles)
print(f'Total of {len(contestLeetcodeFiles)} contest files found.')


# ## Helper Methods
# 
# AddCase $\rightarrow$ takes information for a new question file and formats it accordingly for a row.
# 
# UpdateLanguage $\rightarrow$ if a question already has a solution, this is called instead to insert the new file link to the existing row details.

# In[330]:


# Categories besides those in lists
primary_categories = set(['Daily', 'Weekly Premium', 'Contest', 'Favourite'])


# In[331]:


def addCase(level:              str,
            number:             int, 
            title:              str, 
            categories:         Set[str],
            language:           str,
            notebook_path:      str,
            readme_path:        str) -> dict :

    creation_date = time.ctime(getctime(notebook_path))
    modification_date = time.ctime(getmtime(notebook_path))

    creation_date = datetime.strptime(creation_date, "%a %b %d %H:%M:%S %Y")
    modification_date = datetime.strptime(modification_date, "%a %b %d %H:%M:%S %Y")

    # print(f'{level}. {number}. {title}:\t')
    # print(f'{creation_date = }')
    # print(f'{modification_date = }')

    # I've sometimes encountered weird meta data issues so just as a precaution
    if modification_date < creation_date :
        creation_date, modification_date = modification_date, creation_date

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
                'date_done':            creation_date,          # First time completed
                'date_modified':        modification_date,      # Most recent date
                'solution':             '',
                'solutions':            {language: [readme_path]},
                'languages':            set([language])
             }
    
    # output = [level, number, title, category, '', '', '', '', '']
    # path = f'[{language}](<{path}>)'
    
    # match language.lower() :
    #     case 'python' | 'py':
    #         output[4] = path
    #     case 'java':
    #         output[5] = path
    #     case 'mysql' | 'sql' :
    #         output[6] = path
    #     case 'c' :
    #         output[7] = path
    #     case _:
    #         output[8] = path

    return output


# In[332]:


def updateQuestion(orig:               dict, 
                   *,
                   language:           str,
                   categories:         Set[str],
                   notebook_path:      str,
                   readme_path:        str) -> dict :  
    
    # Another question file found
    if language and language not in orig['languages'] :
        orig['languages'].add(language)

        if notebook_path and readme_path :
            creation_date = time.ctime(getctime(notebook_path))
            modification_date = time.ctime(getmtime(notebook_path))

            creation_date = datetime.strptime(creation_date, "%a %b %d %H:%M:%S %Y")
            modification_date = datetime.strptime(modification_date, "%a %b %d %H:%M:%S %Y")

            if modification_date < creation_date :
                creation_date, modification_date = modification_date, creation_date
            
            if creation_date < orig['date_done'] :
                orig['date_done'] = creation_date
            if modification_date > orig['date_modified'] :
                orig['date_modified'] = modification_date

            if language not in orig['solutions'] :
                orig['solutions'][language] = []
            orig['solutions'][language].append(readme_path)
    
    if categories :
        orig['categories'] |= categories

    return orig


# # Retrieving Question Topics and Details from PICKLE File

# In[333]:


import pickle           # picke is used to pull the stored dict

question_data_folder    = getenv('QUESTION_DATA_PATH')
question_details_file   = getenv('LEETCODE_QUESTION_DETAILS')
question_topics_file    = getenv('LEETCODE_QUESTION_TOPICS')


# In[334]:


if not isfile(join(question_data_folder, question_details_file)) or \
   not isfile(join(question_data_folder, question_topics_file)) :
    print('Rerunning json-to-pkl parse and export due to the file(s) not being found.')
    print()
    import parse_official_question_data
    
if not isfile(join(question_data_folder, question_details_file)) or \
   not isfile (join(question_data_folder, question_topics_file)) :
    print('\nError in parsing official question data. Exiting...')
    exit()
else : 
    print('\nFiles found. Importing now...\n')


# In[335]:


# schema: key=int(questionNumber)   val=(title, titleSlug, paidOnly, difficulty, acRate)
with open(join(question_data_folder, question_details_file), 'rb') as fp:
    questionDetailsDict = pickle.load(fp)
    print('Question Details dictionary')
    print(questionDetailsDict)

# schema: key-int(questionNumber)   val=List[str](topics)
with open(join(question_data_folder, question_topics_file), 'rb') as fp:
    questionTopicsDict = pickle.load(fp)
    print('Question Topic dictionary')
    print(questionTopicsDict)


# # Parsing Files
# Question file parsing occurs here. It organizes it into 3 different lists, separated by difficulty and sorted by question number afterwards.

# In[336]:


questionData = {}

counter = {}
moreThanOnce = 0


# In[337]:


# Parse one leetcode answer file in the submissions folder
def parseCase(leetcodeFile:     str, # file name
              *,
              subFolderPath:    str = '',
              altTitle:         str = '',
              contest:          bool = False) -> bool:
    
    level       = leetcodeFile[0].lower()
    number      = int(re.sub("[^0-9]", "", leetcodeFile.split(' ')[0]))  # Strips non-numeric chars and any that
                                                                         # follow the question number
                                                                         # e.g. 'e123 v1.py' becomes 123
    if number in questionDetailsDict :
        title   = f'[{questionDetailsDict[number][0]}](<https://leetcode.com/problems/{questionDetailsDict[number][1]}>)'
    else :
        title   = f'Question {number}'
    categories  = set()
    language    = leetcodeFile[leetcodeFile.find('.') + 1:]
    path        = join(leetcodePathFromReadme, subFolderPath, leetcodeFile).replace("\\", "/")

    if len(altTitle) > 0 :
        title = altTitle

    # Question is from a contest folder
    if contest :
        temp = re.findall('q\d{1}', leetcodeFile)                       # Checking if file name has a question number (e.g. q1 of the contest)
        if not len(temp) == 0 :
            title += ' - ' + temp[0]
        print(title)

    if contest :
        categories.add('Contest')
    else :
        for cat in primary_categories :
            if cat.lower() in leetcodeFile.lower() :
                categories.add(cat)

    counter[(level, language)] = counter.get((level, language), 0) + 1  # For later reference

    if number in questionData :                                     # If solution already found for this question
        global moreThanOnce
        moreThanOnce += 1

        questionData[number] = updateQuestion(questionData[number], 
                                              language=language, 
                                              categories=categories, 
                                              notebook_path=join(readme_path, path), 
                                              readme_path=path)
        return True
    
    questionData[number] = addCase(level=level, 
                                   number=number, 
                                   title=title,
                                   categories=categories, 
                                   language=language, 
                                   notebook_path=join(readme_path, path), 
                                   readme_path=path)
    return True


# In[338]:


# Parsing primary files
for leetcodeFile in leetcodeFiles :
    parseCase(leetcodeFile=leetcodeFile)


# In[339]:


# Parsing contest files & folforders

for leetcodeContestFile in contestLeetcodeFiles :
    contestFolder, leetcodeFile = leetcodeContestFile
    parseCase(leetcodeFile=leetcodeFile, 
              altTitle=contestFolder, 
              subFolderPath=contestFolder, 
              contest=True)


# In[340]:


# print(easyQuestions)
# print(mediumQuestions)
# print(hardQuestions)
print(questionData)


# In[341]:


# Sorting by question number
# easyQuestions   = sorted(easyQuestions,   key=lambda x: x[1])
# mediumQuestions = sorted(mediumQuestions, key=lambda x: x[1])
# hardQuestions   = sorted(hardQuestions,   key=lambda x: x[1])


# # Sort TXT Context
# If .txt notes are placed, this adds them to their respective entry.

# In[342]:


for fileName in additionalInfoFiles :
    print(f'Context file found: {fileName}')

    number      = int(re.sub("[^0-9]", "", fileName.split(' ')[0]))
    if number not in questionData :
        print(f'Error. No question solution found for {fileName = }')
        continue
    
    questionData[number]['contextFile'] = fileName
    print(f'{questionData[number] = }')


# # List-Based Categories
# Updating `Category` columns based on the lists in the `Lists` directory.

# In[343]:


listsDir = getenv('LISTS_LOCATION')

listFileNames = [x for x in listdir(listsDir) if isfile(join(listsDir, x)) 
                                                 and not x.startswith('.')
                                                 and not x == 'README.md']
print(listFileNames)


# In[344]:


''' Format for lists file is as follows:

        [Question #]. [Question Name]

        [Easy, Med., Hard]
        Topic1
        Topic2
        Topic3
        ...
'''

def getList(fileName, filePath) -> set[int] :
    output = set() # can change to dict later if we want to output category info

    count = 0
    with open(filePath, 'r') as file :
        lines = file.readlines()
        for line in lines :
            if re.match(r'\d{1,4}\.', line) :
                count += 1
                output.add(int(line[:line.find('.')]))
    # print(f'{fileName}: ', len(output), output)
    
    return output
    


# In[345]:


listData = {}
for file in listFileNames :
    listData[file] = getList(file, join(listsDir, file))
    for q in listData[file] :
        if q in questionData :
            questionData[q]['categories'].add(file)
            # print(questionData[q])
            
print(listData)

# listDataMerged          = {}
# itemsPerListData        = {}    # Record of how many questions are in each list
# itemsPerListDataCount   = {}    # Counting how many found in completed questions

# for listName, val in listData.items() :
#     itemsPerListDataCount[listName] = 0
#     itemsPerListData[listName] = len(val)
#     for question in val :
#         if question in listDataMerged :
#             listDataMerged[question] += f', {listName}'
#         else :
#             listDataMerged[question] = listName

# print(listDataMerged)

# listData = None # Free up memory


# In[346]:


# def updateListCount(lists: str) -> None :
#     lists = lists.split(', ')
#     for l in lists :
#         itemsPerListDataCount[l] += 1


# In[347]:


# def updateQuestionTypeWithLists(listData: dict[int, str], questions: List[List[str]]) -> None :
#     for i in range(len(questions)) :
#         if questions[i][1] in listData :
#             questions[i] = updateCategory(questions[i], listData[questions[i][1]])
#             updateListCount(listData[questions[i][1]])


# In[348]:


# updateQuestionTypeWithLists(listDataMerged, easyQuestions)

# print([f'{x}: {itemsPerListDataCount.get(x)}/{itemsPerListData.get(x)}' for x in itemsPerListData])


# In[ ]:





# # DataFrames
# Conversion into DataFrames and declaration of respective column headers occurs here.

# In[349]:


dataframe_array = []

for question in questionData.values() :
    currentRow = [question['number'],
                  question['title'], 
                  question['level'], 
                  ', '.join(list(question['categories'])), 
                  question['solution'], 
                  ', '.join(list(question['languages']))]
    dataframe_array.append(currentRow)
    print(currentRow)

dataframe_array.sort(key=lambda x: x[0])


# In[350]:


columns = [ 
            '#',
            'Title', 
            'Level',
            'Cats',
            'Solution',
            'Languages'
          ]
typeClarification = {
                      '#':         int,
                      'Title':     str, 
                      'Level':     str,
                      'Cats':      str,
                      'Solution':  str,
                      'Languages': str
                    }

dfQuestions   = kungfupanda.DataFrame(data=dataframe_array, columns=columns)
dfQuestions   = dfQuestions.astype(typeClarification)
print(dfQuestions)

# for question in questionData.values() :
#     dfQuestions = dfQuestions.append(question, ignore_index=True)

# dfEasy      = kungfupanda.DataFrame(data=easyQuestions, columns=columns)
# dfMedium    = kungfupanda.DataFrame(data=mediumQuestions, columns=columns)
# dfHard      = kungfupanda.DataFrame(data=hardQuestions, columns=columns)

# dfEasy      = dfEasy.astype(typeClarification)
# dfMedium    = dfMedium.astype(typeClarification)
# dfHard      = dfHard.astype(typeClarification)


# In[351]:


# # Helper method for outputing just to make code cleaner
# def subLevel(level: str) -> str :
#     match level.lower() :
#         case 'e' :
#             return 'Easy'
#         case 'm' :
#             return 'Medium'
#         case 'h' :
#             return 'Hard'
#         case _ :
#             return 'Unknown'


# In[352]:


# print(counter, sum(counter.values()))
# print(len(questionsVisited))
# print(moreThanOnce)

# rows = ['e', 'm', 'h']
# columns = sorted(list(set([x[1] for x in counter.keys()])))

# # Initialization of stats table + column header initialization
# statsMatrix     = [[None] * (len(columns) + 2 + 1)] * (len(rows) + 2)
# statsMatrix[0]  = [''] + \
#                   [f'**{x.title()}**' for x in columns] + \
#                   ['**Total**', '**Total Unique**']


# ## Stats by Group Parsing
# Going row by row to calculate the respective values :v

# In[353]:


# temp = [easyQuestions, mediumQuestions, hardQuestions] # For summing number of unique question later

# for i in range(1, len(rows) + 1) :
#     statsMatrix[i] = [f'**{subLevel(rows[i - 1])}**'] \
#                      + [counter.get((rows[i - 1], columns[j]), 0) for j in range(len(columns))] \
#                      + [f'*{sum([counter.get((rows[i - 1], x), 0) for x in columns])}*'] \
#                      + [f'*{len(temp[i - 1])}*']


# # Total sums at bottom for each language and TOTAL TOTAL
# # Total including double counts for languages
# ''' Line by line:   Row Header
#                     Sum for each language
#                     Total everything
#                     Total unique everything
# '''
# statsMatrix[-1] = ['**Total**'] \
#                   + [f'*{sum([counter.get((x, y), 0) for x in rows])}*' for y in columns] \
#                   + [f'**{sum(counter.values())}**'] \
#                   + [f'**{sum([len(x) for x in temp])}**']
# temp = None


# In[354]:


# # Conversion to DataFrame
# dfColumns   = statsMatrix[0]
# statsMatrix = [statsMatrix[i] for i in range(1, len(statsMatrix))]

# statsMatrixDf = kungfupanda.DataFrame(data=statsMatrix, columns=dfColumns)
# print(statsMatrixDf.to_markdown(index=False))


# # Counts per List
# These are for lists such as my favourites, the Neetcode150, etc.

# In[355]:


# # Get alternate names
# def getAlternateNames() -> dict[str, str] :
#     output = {}
#     with open(join(listsDir, '.AltNames'), 'r') as file :
#         lines = file.readlines()
#         for line in lines :
#             line = line.strip()
#             if len(line) == 0 :
#                 continue
#             splitLine = line.split('=')
#             output[splitLine[0]] = ' '.join(splitLine[1:])
#     print(output)
#     return output


# In[356]:


# # No. Completed / No. Total
# print([f'{x}: {itemsPerListDataCount.get(x)}/{itemsPerListData.get(x)}' for x in itemsPerListData])

# altNames = getAlternateNames()

# listStatOutputs = []
# for key in itemsPerListData :
#     altName = altNames.get(key, key)
#     if altName != key :
#         altName = f'{altName} ({key})'
#     listStatOutputs.append(f'- **{altName}**: {itemsPerListDataCount.get(key)}/{itemsPerListData.get(key)}')

# print(listStatOutputs)


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

# In[357]:


readmePath = join(readme_path, 'README.md')
print(readmePath)
with open(readmePath, 'w') as file :
    file.write('# LeetCode Records\n\n')

    username = getenv('LEETCODE_USERNAME')
    file.write(f'Profile: [{username}](https://leetcode.com/u/{username}/)\n\n')

    file.write('> *Note: if there are multiple files, it\'s likely a case of me having multiple solutions.*\n\n')

    # file.write('## Stats by Language and Level\n\n')
    # file.write(statsMatrixDf.to_markdown(index=False))
    # file.write(f'\n\nQuestions done in multiple languages and/or multiple ways:\t{moreThanOnce}\n<br>')
    # file.write(f'\nUnique questions done:\t\t**{int(re.sub("[^0-9]", "", statsMatrix[len(statsMatrix) - 1][len(statsMatrix[0]) - 2])) - moreThanOnce}**')

    file.write('\n\n\n')

    file.write('## Category Notes\n')
    file.write('1. **Daily** - Daily challenge questions that were done on the day of\n')
    file.write('2. **Weekly Premium** - Weekly premium questions that were done on week of\n')
    file.write('3. **Contest** - Questions that were done during a live contest\n')
    # file.write('4. **Favourite** - Questions that I liked and wanted to keep a record of\n')
    file.write('\n')

    file.write('## Additional Categories Stats\n')
    # file.write('\n'.join(listStatOutputs))
    file.write('\n\n')

    file.write('## Questions\n')
    file.write(dfQuestions.to_markdown(index=False))



    # file.write('## Easy\n')
    # file.write(dfEasy.to_markdown(index=False))

    # file.write('\n\n## Medium\n')
    # file.write(dfMedium.to_markdown(index=False))

    # file.write('\n\n## Hard\n')
    # file.write(dfHard.to_markdown(index=False))


# In[ ]:




