#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as kungfupanda
from os import listdir
from os.path import isfile, join
import pickle

from os import getenv                           # for environment variables
from dotenv import load_dotenv, find_dotenv     # / config purposes (.env file)
load_dotenv(find_dotenv(), override=True)


# # Leetcode Question Data Parsing
# 
# The `.json` file in this repository is pulled straight from Leetcode's GraphQL. This Notebook parses the data, extracting the relevant data, and stores the newly formed dictionaries it in `.pkl` files for the `Progress_Updater.ipynb` process to make use of later. 
# 

# In[ ]:


def parseLeetcodeQuestionJSON() -> None :
    QUESTION_DATA_FOLDER_PATH = getenv('QUESTION_DATA_PATH')
    print(f'{QUESTION_DATA_FOLDER_PATH = }')

    jsonFiles = [join(QUESTION_DATA_FOLDER_PATH, f) for f in listdir(QUESTION_DATA_FOLDER_PATH) 
                                                    if isfile(join(QUESTION_DATA_FOLDER_PATH, f)) and f.endswith('.json')]
    print(f'JSONs found:', jsonFiles)

    # There should only be one file
    dataFile = jsonFiles[0]
    print('File to use:\t', dataFile)


    questionList        = kungfupanda.read_json(dataFile)
    temp                = questionList.get('data').get('problemsetQuestionList')
    
    totalQuestionCount  = temp.get('total')
    questions           = temp.get('questions')

    questionDetails = {}
    questionTopics  = {}

    # frontendQuestionId : (title, titleSlug, paidOnly, difficulty, acRate)
    for question in questions :
        questionNo  = int(question.get('frontendQuestionId'))       # int
        title       = str(question.get('title'))                    # str
        titleSlug   = str(question.get('titleSlug'))                # str
        paidOnly    = bool(question.get('paidOnly'))                # bool
        difficulty  = str(question.get('difficulty'))               # str (Easy, Medium, Hard)
        acRate      = round(float(question.get('acRate')), 3)       # float - 3 decimal places

        questionDetails[questionNo] = (title, titleSlug, paidOnly, difficulty, acRate)

        topicList = []
        for topic in question.get('topicTags') :
            topicList.append(topic.get('name'))
        
        questionTopics[questionNo] = topicList

    print(f'Total questions found:\t{totalQuestionCount}')
    print(questionDetails)
    print(questionTopics)

    with open(join(QUESTION_DATA_FOLDER_PATH, 'leetcode_question_details.pkl'), 'wb') as fp:
        pickle.dump(questionDetails, fp)
        print('Question Details saved successfully to file')
        
    with open(join(QUESTION_DATA_FOLDER_PATH, 'leetcode_question_topics.pkl'), 'wb') as fp:
        pickle.dump(questionTopics, fp)
        print('Question Topics saved successfully to file')

