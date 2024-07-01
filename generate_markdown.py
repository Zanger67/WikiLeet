#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from os.path import join, isfile
from os import listdir

from os import getenv                           # for environment variables
from dotenv import load_dotenv, find_dotenv     # / config purposes (.env file)
load_dotenv(find_dotenv(), override=True)

import pickle


# # Functions that take in a question's data and convert it to a markdown with all solutions

# In[ ]:


README_PATH                     = getenv('README_PATH')
QUESTIONS_FOLDER_FROM_README    = getenv('QUESTIONS_PATH_FROM_README')
QUESTIONS_FOLDER                = join(README_PATH, QUESTIONS_FOLDER_FROM_README)

MARKDOWN_PATH = getenv('QUESTION_MARKDOWNS_PATH_FROM_README')
MARKDOWN_TO_SUBMISSIONS = '../' * MARKDOWN_PATH.count('/') + QUESTIONS_FOLDER_FROM_README


# print(f'{README_PATH = }')
# print(f'{QUESTIONS_FOLDER_FROM_README = }')
# print(f'{QUESTIONS_FOLDER = }')

# print(f'{MARKDOWN_PATH = }')


# In[ ]:





# In[ ]:


LANGUAGE_EQUIVS = {
    'py': 'Python',
    'python': 'Python',
    'java': 'Java',
    'cpp': 'C++',
    'c': 'C',
    'sql': 'SQL',
    'mysql': 'SQL',
    'js': 'JavaScript',
    'javascript': 'JavaScript',
    'ts': 'TypeScript',
    'typescript': 'TypeScript',
    'go': 'Go',
    'rb': 'Ruby',
    'ruby': 'Ruby',
    'kt': 'Kotlin',
    'kotlin': 'Kotlin',
    'swift': 'Swift',
    'scala': 'Scala',
    'rs': 'Rust',
    'rust': 'Rust',
    'php': 'PHP',
    'cs': 'C#',
    'csharp': 'C#',
    'm': 'Objective-C',
    'objc': 'Objective-C',
    'r': 'R',
    'racket': 'Racket',
    'lua': 'Lua',
    'perl': 'Perl',
    'sh': 'Bash',
    'bash': 'Bash'
}


# In[ ]:


QUESTION_DATA_FOLDER_PATH    = getenv('QUESTION_DATA_PATH')
QUESTION_TOPICS_FILE    = getenv('LEETCODE_QUESTION_TOPICS')
question_details_file   = getenv('LEETCODE_QUESTION_DETAILS')


# In[ ]:


if not isfile(join(QUESTION_DATA_FOLDER_PATH, QUESTION_TOPICS_FILE) or 
              join(QUESTION_DATA_FOLDER_PATH, question_details_file)) :
    print('Rerunning json-to-pkl parse and export due to the file(s) not being found.')
    print()
    import parse_official_question_data
    
if not isfile(join(QUESTION_DATA_FOLDER_PATH, QUESTION_TOPICS_FILE) or
              join(QUESTION_DATA_FOLDER_PATH, question_details_file)) :
    print('\nError in parsing official question data. Exiting...')
    exit()
else : 
    print('\nFiles found. Importing now...\n')


# In[ ]:


# schema: key-int(questionNumber)   val=List[str](topics)
questionTopicsDict = None
with open(join(QUESTION_DATA_FOLDER_PATH, QUESTION_TOPICS_FILE), 'rb') as fp:
    questionTopicsDict = pickle.load(fp)
    print('Question Topic dictionary')
    print(questionTopicsDict)


# schema: key=int(questionNumber)   val=(title, titleSlug, paidOnly, difficulty, acRate)
questionDetailsDict = None
with open(join(QUESTION_DATA_FOLDER_PATH, question_details_file), 'rb') as fp:
    questionDetailsDict = pickle.load(fp)
    print('Question Details dictionary')
    print(questionDetailsDict)


# In[ ]:


questionData = v2.questionData

print(questionDetailsDict)

# MARKDOWN_TO_SUBMISSIONS
def generate_markdown(questionNo: int, questionData: dict) -> bool :
    if questionNo in questionData :
        questionData = questionData[questionNo]

    title = questionData["title"][questionData["title"].find('[') + 1:questionData["title"].find(']')]
    title = f'{questionNo}. {title}'

    print(f'{title = }')
    
    generate_file_name = f'_{title}.md'
    generate_path = join(README_PATH, MARKDOWN_PATH, generate_file_name)

    with open(generate_path, 'w') as f :
        f.write(f'# {questionNo}. {questionData["title"]}\n\n')

        date_done = questionData['date_done']
        date_modified = questionData['date_modified']
        
        f.write(f'*First added: {date_done:%B %d, %Y}*\n\n')
        f.write(f'*First added: {date_modified:%B %d, %Y}*\n\n\n')

        f.write(f'> *To see the question prompt, click the title.*\n\n')

        f.write(f'**Topics:** ' + ', '.join(questionTopicsDict[questionNo]) + '\n\n')
        acrate = questionDetailsDict[questionNo][4]
        f.write(f'**AC %:** ' + f'{str(acrate)}' + '\n\n\n')

        if 'contextFile' in questionData:
            with open(join(README_PATH, questionData['contextFile']), 'r') as contextFile:
                f.write(contextFile.read())
            f.write('\n\n')

        print(questionData['solutions'])
        

        f.write(f'## Solutions\n\n')
        for lang, solutions in questionData['solutions'].items() :
            solutions.sort()
            for solution in solutions :
                name = solution[solution.find('/') + 1:]
                f.write(f'- [{name}](<{join(README_PATH, solution)}>)\n')

        for lang, solutions in questionData['solutions'].items() :
            if lang.lower() in LANGUAGE_EQUIVS :
                lang = LANGUAGE_EQUIVS[lang.lower()]
            f.write(f'### {lang}\n')
            for solution in solutions :
                name = solution.rfind('/') + 1
                f.write(f'#### [{solution[name:]}](<{join(README_PATH, solution)}>)\n')
                f.write(f'```{lang}\n')
                with open(join(README_PATH, solution), 'r') as solutionFile:
                    f.write(solutionFile.read())
                f.write('\n```\n\n')


# In[ ]:


import random
for i in range(1, 10) :
    test_question = random.choice(list(questionData.keys()))
    generate_markdown(test_question, questionData[test_question])


# In[ ]:




