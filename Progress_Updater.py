#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as kungfupanda        # pandas
from os import listdir              # for file retrieval
from os.path import isfile, join

import re                           # for regex file name matching
from typing import List             # misc.


# # Notebook for Updating Stats and Links on README
# This is just a helper file I use to automatically link my solution files to the [README.md](README.md) page, formatting the links and details into markdown tables and calculating "solved" stats in the process. Just makes my life easier and I find it satisfying seeing the links lol. 
# 
# Just something I whipped up for fun. :)

# In[ ]:


readme_path             = '../'
leetcodePathFromReadme  = 'my-submissions/'
leetcodePathReference   = join(readme_path, leetcodePathFromReadme)
leetcodeFiles           = [x for x in listdir(leetcodePathReference) if isfile(join(leetcodePathReference, x))]

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

# In[ ]:


# Categories besides those in lists
categories = set(['Daily', 'Weekly Premium', 'Contest', 'Favourite'])


# In[ ]:


def addCase(level:      str, 
            number:     int, 
            title:      str, 
            category:   str,
            language:   str,
            path:       str) :

    # Level, Number, Title, Python, Java, MySQL, Other
    output = [level, number, title, category, '', '', '', '', '']
    path = f'[{language}](<{path}>)'
    
    match language.lower() :
        case 'python' | 'py':
            output[4] = path
        case 'java':
            output[5] = path
        case 'mysql' | 'sql' :
            output[6] = path
        case 'c' :
            output[7] = path
        case _:
            output[8] = path

    return output


# In[ ]:


def updateLanguage(orig, language, path) :  
    index = -1  
    match language.lower() :
        case 'python' | 'py':
            index = 4
        case 'java':
            index = 5
        case 'mysql' | 'sql' :
            index = 6
        case 'c' :
            index = 7
        case _:
            index = 8

    path = f'[{language}](<{path}>)'
    orig[index] = f'{orig[index]}, {path}' if not orig[index] == '' \
                                           else path

    return orig


# In[ ]:


# Update the category of a question e.g. adding 'Daily' or 'Weekly Premium' to the box
def updateCategory(orig, category) : 
    if category.lower() in orig[3].lower() :
        return orig

    orig[3] = f'{orig[3]}, {category}' if not orig[3] == '' \
                                       else category
    return orig


# # Retrieving Question Topics and Details from PICKLE File

# In[ ]:


import pickle           # picke is used to pull the stored dict

question_data_folder    = 'question_data/'
question_details_file   = 'leetcode_question_details.pkl'
question_topics_file    = 'leetcode_question_topics.pkl'


# In[ ]:


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

# In[ ]:


easyQuestions   = [] 
mediumQuestions = []
hardQuestions   = []

questionsVisited = set()

counter = {}
moreThanOnce = 0


# In[ ]:


# Parse one leetcode answer file in the submissions folder
def parseCase(leetcodeFile: str, altTitle: str, subFolderPath: str, contest: bool) -> bool:
    level       = leetcodeFile[0].lower()
    number      = int(re.sub("[^0-9]", "", leetcodeFile.split(' ')[0]))  # Strips non-numeric chars and any that
                                                                         # follow the question number
                                                                         # e.g. 'e123 v1.py' becomes 123
    if number in questionDetailsDict :
        title   = f'[{questionDetailsDict[number][0]}](<https://leetcode.com/problems/{questionDetailsDict[number][1]}>)'
    else :
        title   = f'Question {number}'
    category    = ''
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
        category = 'Contest'
    else :
        for cat in categories :
            if cat.lower() in leetcodeFile.lower() :
                category = cat
                break

    counter[(level, language)] = counter.get((level, language), 0) + 1  # For later reference

    if number in questionsVisited :                                     # If solution already found for this question
        global moreThanOnce
        moreThanOnce += 1

        match level :
            case 'e' :
                for i in range(len(easyQuestions)) :
                    if easyQuestions[i][1] == number :
                        easyQuestions[i] = updateLanguage(easyQuestions[i], language, path)
                        break
            case 'm' :
                for i in range(len(mediumQuestions)) :
                    if mediumQuestions[i][1] == number :
                        mediumQuestions[i] = updateLanguage(mediumQuestions[i], language, path)
                        break
            case 'h' :
                for i in range(len(hardQuestions)) :
                    if hardQuestions[i][1] == number :
                        hardQuestions[i] = updateLanguage(hardQuestions[i], language, path)
                        break
        
        # Assign a category
        if category != '' :
            match level :
                case 'e' :
                    for i in range(len(easyQuestions)) :
                        if easyQuestions[i][1] == number :
                            easyQuestions[i] = updateCategory(easyQuestions[i], category)
                            break
                case 'm' :
                    for i in range(len(mediumQuestions)) :
                        if mediumQuestions[i][1] == number :
                            mediumQuestions[i] = updateCategory(mediumQuestions[i], category)
                            break
                case 'h' :
                    for i in range(len(hardQuestions)) :
                        if hardQuestions[i][1] == number :
                            hardQuestions[i] = updateCategory(hardQuestions[i], category)
                            break

        return True

    questionsVisited.add(number)

    match level :
        case 'e' :
            easyQuestions.append(addCase('Easy', number, title, category, language, path))
        case 'm' :
            mediumQuestions.append(addCase('Medium', number, title, category, language, path))
        case 'h' :
            hardQuestions.append(addCase('Hard', number, title, category, language, path))

    return True


# In[ ]:


# Parsing primary files
for leetcodeFile in leetcodeFiles :
    parseCase(leetcodeFile, '', '', False)


# In[ ]:


# Parsing contest files & folforders

for leetcodeContestFile in contestLeetcodeFiles :
    contestFolder, leetcodeFile = leetcodeContestFile
    parseCase(leetcodeFile, contestFolder, contestFolder, True)


# In[ ]:


print(easyQuestions)
print(mediumQuestions)
print(hardQuestions)


# In[ ]:


# Sorting by question number
easyQuestions   = sorted(easyQuestions,   key=lambda x: x[1])
mediumQuestions = sorted(mediumQuestions, key=lambda x: x[1])
hardQuestions   = sorted(hardQuestions,   key=lambda x: x[1])


# # List-Based Categories
# Updating `Category` columns based on the lists in the `Lists` directory.

# In[ ]:


listsDir = 'Lists/'

listFileNames = [x for x in listdir(listsDir) if isfile(join(listsDir, x)) 
                                                 and not x.startswith('.')
                                                 and not x == 'README.md']
print(listFileNames)


# In[ ]:


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
    print(f'{fileName}: ', len(output), output)
    
    return output
    


# In[ ]:


listData = {}
for file in listFileNames :
    listData[file] = getList(file, join(listsDir, file))

listDataMerged          = {}
itemsPerListData        = {}    # Record of how many questions are in each list
itemsPerListDataCount   = {}    # Counting how many found in completed questions

for listName, val in listData.items() :
    itemsPerListDataCount[listName] = 0
    itemsPerListData[listName] = len(val)
    for question in val :
        if question in listDataMerged :
            listDataMerged[question] += f', {listName}'
        else :
            listDataMerged[question] = listName

print(listDataMerged)

listData = None # Free up memory


# In[ ]:


def updateListCount(lists: str) -> None :
    lists = lists.split(', ')
    for l in lists :
        itemsPerListDataCount[l] += 1


# In[ ]:


def updateQuestionTypeWithLists(listData: dict[int, str], questions: List[List[str]]) -> None :
    for i in range(len(questions)) :
        if questions[i][1] in listData :
            questions[i] = updateCategory(questions[i], listData[questions[i][1]])
            updateListCount(listData[questions[i][1]])


# In[ ]:


updateQuestionTypeWithLists(listDataMerged, easyQuestions)
updateQuestionTypeWithLists(listDataMerged, mediumQuestions)
updateQuestionTypeWithLists(listDataMerged, hardQuestions)

print([f'{x}: {itemsPerListDataCount.get(x)}/{itemsPerListData.get(x)}' for x in itemsPerListData])


# # DataFrames
# Conversion into DataFrames and declaration of respective column headers occurs here.

# In[ ]:


columns = ['Level', 
           '#', 
           'Title', 
           'Category',
           'Python', 
           'Java', 
           'MySQL', 
           'C',
           'Other'
           ]
typeClarification = {'Level': 'str', 
                     '#': 'int', 
                     'Title': 'str', 
                     'Category': 'str',
                     'Python': 'str', 
                     'Java': 'str', 
                     'MySQL': 'str', 
                     'C': 'str',
                     'Other': 'str'
                     }

dfEasy      = kungfupanda.DataFrame(data=easyQuestions, columns=columns)
dfMedium    = kungfupanda.DataFrame(data=mediumQuestions, columns=columns)
dfHard      = kungfupanda.DataFrame(data=hardQuestions, columns=columns)

dfEasy      = dfEasy.astype(typeClarification)
dfMedium    = dfMedium.astype(typeClarification)
dfHard      = dfHard.astype(typeClarification)


# In[ ]:


# Helper method for outputing just to make code cleaner
def subLevel(level: str) -> str :
    match level.lower() :
        case 'e' :
            return 'Easy'
        case 'm' :
            return 'Medium'
        case 'h' :
            return 'Hard'
        case _ :
            return 'Unknown'


# In[ ]:


print(counter, sum(counter.values()))
print(len(questionsVisited))
print(moreThanOnce)

rows = ['e', 'm', 'h']
columns = sorted(list(set([x[1] for x in counter.keys()])))

# Initialization of stats table + column header initialization
statsMatrix     = [[None] * (len(columns) + 2 + 1)] * (len(rows) + 2)
statsMatrix[0]  = [''] + \
                  [f'**{x.title()}**' for x in columns] + \
                  ['**Total**', '**Total Unique**']


# ## Stats by Group Parsing
# Going row by row to calculate the respective values :v

# In[ ]:


temp = [easyQuestions, mediumQuestions, hardQuestions] # For summing number of unique question later

for i in range(1, len(rows) + 1) :
    statsMatrix[i] = [f'**{subLevel(rows[i - 1])}**'] \
                     + [counter.get((rows[i - 1], columns[j]), 0) for j in range(len(columns))] \
                     + [f'*{sum([counter.get((rows[i - 1], x), 0) for x in columns])}*'] \
                     + [f'*{len(temp[i - 1])}*']


# Total sums at bottom for each language and TOTAL TOTAL
# Total including double counts for languages
''' Line by line:   Row Header
                    Sum for each language
                    Total everything
                    Total unique everything
'''
statsMatrix[-1] = ['**Total**'] \
                  + [f'*{sum([counter.get((x, y), 0) for x in rows])}*' for y in columns] \
                  + [f'**{sum(counter.values())}**'] \
                  + [f'**{sum([len(x) for x in temp])}**']
temp = None


# In[ ]:


# Conversion to DataFrame
dfColumns   = statsMatrix[0]
statsMatrix = [statsMatrix[i] for i in range(1, len(statsMatrix))]

statsMatrixDf = kungfupanda.DataFrame(data=statsMatrix, columns=dfColumns)
print(statsMatrixDf.to_markdown(index=False))


# # Counts per List
# These are for lists such as my favourites, the Neetcode150, etc.

# In[ ]:


# Get alternate names
def getAlternateNames() -> dict[str, str] :
    output = {}
    with open(join(listsDir, '.AltNames'), 'r') as file :
        lines = file.readlines()
        for line in lines :
            line = line.strip()
            if len(line) == 0 :
                continue
            splitLine = line.split('=')
            output[splitLine[0]] = ' '.join(splitLine[1:])
    print(output)
    return output


# In[ ]:


# No. Completed / No. Total
print([f'{x}: {itemsPerListDataCount.get(x)}/{itemsPerListData.get(x)}' for x in itemsPerListData])

altNames = getAlternateNames()

listStatOutputs = []
for key in itemsPerListData :
    altName = altNames.get(key, key)
    if altName != key :
        altName = f'{altName} ({key})'
    listStatOutputs.append(f'- **{altName}**: {itemsPerListDataCount.get(key)}/{itemsPerListData.get(key)}')

print(listStatOutputs)


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


readmePath = join(readme_path, 'README.md')

with open(readmePath, 'w') as file :
    file.write('# LeetCode Records\n\n')

    file.write('Profile: [Zanger](https://leetcode.com/u/Zanger/)\n\n')

    file.write('> *Note: if there are multiple files, it\'s likely a case of me having multiple solutions.*\n\n')

    file.write('## Stats by Language and Level\n\n')
    file.write(statsMatrixDf.to_markdown(index=False))
    file.write(f'\n\nQuestions done in multiple languages and/or multiple ways:\t{moreThanOnce}\n<br>')
    file.write(f'\nUnique questions done:\t\t**{int(re.sub("[^0-9]", "", statsMatrix[len(statsMatrix) - 1][len(statsMatrix[0]) - 2])) - moreThanOnce}**')

    file.write('\n\n\n')

    file.write('## Category Notes\n')
    file.write('1. **Daily** - Daily challenge questions that were done on the day of\n')
    file.write('2. **Weekly Premium** - Weekly premium questions that were done on week of\n')
    file.write('3. **Contest** - Questions that were done during a live contest\n')
    # file.write('4. **Favourite** - Questions that I liked and wanted to keep a record of\n')
    file.write('\n')

    file.write('## Additional Categories Stats\n')
    file.write('\n'.join(listStatOutputs))
    file.write('\n\n')



    file.write('## Easy\n')
    file.write(dfEasy.to_markdown(index=False))

    file.write('\n\n## Medium\n')
    file.write(dfMedium.to_markdown(index=False))

    file.write('\n\n## Hard\n')
    file.write(dfHard.to_markdown(index=False))

