#!/usr/bin/env python
# coding: utf-8

'''
WikiLeet markdown generator.

Parses a repo of LeetCode solution files and generates a wiki-like set of
markdown files: one page per question, grouping pages (by topic, difficulty,
recency, code length, daily/weekly challenges), and the primary README.md of
the repo that imported WikiLeet as a submodule.

Run as a script:

    python main.py [-r] [-n] [-g] [-user NAME] [-contest-dir DIR ...]

    -r     : Recompile every markdown file regardless of whether its source
             code files were modified or not
    -n     : Don't use the previously stored modification dates and don't
             store the new ones (in effect the same as `-r` but stateless).
             Primarily for use with GitHub Actions.
    -g     : Trace each file's creation/modification dates through the git
             log instead of the filesystem. GitHub Actions checkouts reset
             filesystem dates, so CI runs need this.
             WARNING: slow when run locally; fast on GitHub Actions.
    -user  : LeetCode username (overrides LEETCODE_USERNAME from .env)
    -contest-dir : Extra contest container dir(s) whose subfolders are each a
             contest. Repeatable and/or comma-separated for multiple. Folders
             named "contest"/"contests" anywhere in the repo are auto-detected
             on top of these.

Or drive the pipeline stage-by-stage from a notebook / another module (this
is exactly what main.ipynb does -- see `main()` for the canonical order):

    import main, env_config as config
    config.load_environment()
    config.init()
    main.main()
'''

import argparse
import calendar
import json
import pickle
import re
import subprocess
import sys

from collections import defaultdict
from datetime import datetime, timedelta
from functools import cache
from os import chdir, environ, listdir, mkdir, stat, walk
from os.path import abspath, basename, dirname, getctime, getmtime, isdir, isfile, join, relpath
from typing import Dict, List, NamedTuple, Set, Tuple

import pandas as kungfupanda                    # pandas for dataframe to markdown exports
from pandas import DataFrame
from tqdm.auto import tqdm                      # progress bars (notebook- and cli-aware)

import env_config as config
from questionDataclass import questionDataclass as Question


# ============================================================================ #
#  Run state
# ============================================================================ #

# When True, file creation/modification dates are traced through the git log
# instead of the filesystem (see the -g flag). Needed under GitHub Actions
# where the checkout resets every file's filesystem dates to "now".
USE_GIT_DATES = False

# README-relative path -> (creation, modification) datetimes bulk-parsed from
# the git log when USE_GIT_DATES is on. Filled by load_git_timestamps().
_git_file_times: Dict[str, Tuple[datetime, datetime]] = {}

# Date of the oldest tracked solution file -- daily/weekly challenges from
# before this date can't have been completed on time, so they are skipped.
# Stays at "now" (i.e. no relevant challenges) until git dates are parsed.
_oldest_file_date = datetime.now()


# ============================================================================ #
#  Constants
# ============================================================================ #

# Column headers for every generated question table
COLUMNS = [
            '#',
            'Title',
            'Level',
            'Cats',
            'Solution',
            'Languages',
            'Date Complete'
          ]

# A question number is the first run of 1-4 digits in a name that is NOT part of
# a longer digit run -- so "abc1234 x" -> 1234 and "abc123def345" -> 123, while a
# 5+ digit run like "abc12345" matches nothing (LeetCode numbers cap at 4 digits).
QUESTION_NO_PATTERN = re.compile(r'(?<!\d)\d{1,4}(?!\d)')

# Number-less solution files are often named generically ("main"/"solution")
# inside a folder named after the question -- e.g. "1234. Two Sum/Solution.java".
MAIN_SOLUTION_PATTERN = re.compile(r'main|solution', re.IGNORECASE)

# Grace periods for counting a solve as an on-time daily/weekly challenge
# (allows for late commits and timezone offsets vs. UTC)
DAILY_LEEWAY  = timedelta(days=1, hours=12)
WEEKLY_LEEWAY = timedelta(days=8)


@cache
def language_equivs() -> Dict[str, str] :
    '''File extension -> markdown code-block language name.'''
    with open(config.LANGUAGE_EQUIVS_PATH) as f :
        return json.load(f)


# ============================================================================ #
#  File creation/modification dates
# ============================================================================ #

def _parse_git_log_times(cmd: List[str]) -> Tuple[datetime, datetime] :
    '''
    Runs a `git log --format=%ct` command from the README's directory and
    returns the (creation, modification) datetimes of the file it targets.
    '''
    process = subprocess.Popen(cmd,
                               shell=False,
                               stdin=None,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               cwd=config.README_PATH)

    # One unix timestamp per commit touching the file (ignoring blank lines)
    commit_times = [line.decode('utf-8').strip()
                    for line in process.stdout.readlines()
                    if line.strip()]

    try :
        creation_date = datetime.fromtimestamp(int(min(commit_times)))
        modified_date = datetime.fromtimestamp(int(max(commit_times)))
    except ValueError as ve :
        print(f'Error in parsing git log dates via {cmd}')
        print(f'{commit_times}')
        print(ve)
        sys.exit(1)

    return (creation_date, modified_date)


@cache
def _git_history_times(path: str) -> Tuple[datetime, datetime] :
    '''
    Creation/modification dates of a single file traced through the git log.

    WARNING: slow locally relative to the filesystem dates; prefer running
    without the `-g` flag when local filesystem dates are trustworthy.
    '''
    path = path[path.find('/') + 1:]        # script-relative -> repo-relative
    cmd = 'git log --follow --format=%ct --reverse --'.split() + [path]
    return _parse_git_log_times(cmd)


@cache
def _filesystem_times(path: str) -> Tuple[datetime, datetime] :
    '''Creation/modification dates of a file per the filesystem metadata.'''
    creation_date     = datetime.fromtimestamp(int(getctime(path)))
    modification_date = datetime.fromtimestamp(int(getmtime(path)))

    # Metadata occasionally reports creation after modification; normalize
    if creation_date > modification_date :
        return (modification_date, creation_date)
    return (creation_date, modification_date)


def get_file_times(path: str) -> Tuple[datetime, datetime] :
    '''
    Returns the (creation, modification) datetimes of a file, preferring the
    bulk git-log results when they were parsed (the `-g` flag).
    '''
    # Bulk git results are keyed by README-relative paths while `path` is
    # script-relative -- strip the leading '../'
    readme_path = path if '../' not in path else path[path.find('../') + len('../'):]
    if readme_path in _git_file_times :
        return _git_file_times[readme_path]

    if USE_GIT_DATES :
        return _git_history_times(path)
    return _filesystem_times(path)


# ============================================================================ #
#  Submission file discovery
# ============================================================================ #

# Files with these extensions hold notes/context for a question rather than a
# solution; files with no extension at all are treated the same way.
CONTEXT_EXTENSIONS = ('.txt', '.md')


def _is_code_file(file_name: str) -> bool :
    return ('.' in file_name
            and not file_name.endswith(CONTEXT_EXTENSIONS)
            and not file_name.endswith('.gitignore'))


def _is_context_file(file_name: str) -> bool :
    return ((file_name.endswith(CONTEXT_EXTENSIONS) or '.' not in file_name)
            and not file_name.endswith('.gitignore'))


class SubmissionFiles(NamedTuple) :
    '''Every repo file relevant to the generator, keyed by path from the README.'''
    code_files:     List[str]                   # solution file paths (from the README)
    contest_files:  List[Tuple[str, str]]       # (contest name, solution path from README)
    context_files:  List[str]                   # notes file paths (from the README)


# Non-dot directory names never descended into during the repo-wide scan
# (every dot-directory -- .git, .github, .readme_updater, .vscode, ... -- is
# skipped separately by the leading-dot check in discover_submission_files).
_PRUNE_DIR_NAMES = {'__pycache__'}

# Folders with either of these exact names are auto-detected as contest
# containers anywhere in the repo (in addition to any passed via --contest-dir).
CONTEST_DIR_NAMES = ('contest', 'contests')


def _collect_contest_dir(container_dir:  str,
                         repo_root:      str,
                         contest_files:  List[Tuple[str, str]],
                         context_files:  List[str]) -> None :
    '''
    Records every solution under one contest container: each immediate subfolder
    is a distinct contest (its folder name is the contest title) and the code
    files directly inside it are that contest's solutions. Appends (contest name,
    readme path) code entries and any notes files' readme paths in place.
    '''
    for folder in listdir(container_dir) :
        folder_dir = join(container_dir, folder)
        if folder.startswith('.') or not isdir(folder_dir) :
            continue
        for name in listdir(folder_dir) :
            if not isfile(join(folder_dir, name)) :
                continue
            readme_path = relpath(join(folder_dir, name), repo_root).replace('\\', '/')
            if _is_code_file(name) :
                contest_files.append((folder, readme_path))
            elif _is_context_file(name) :
                context_files.append(readme_path)


def discover_submission_files() -> SubmissionFiles :
    '''
    Scans the whole parent repo for solution and context files, keyed by their
    path from the README. Every code file whose name (or, for `main`/`solution`
    files, whose parent folder) carries a question number counts as a solution --
    regardless of whether it lives in a dedicated submissions folder.

    Contests come from *contest container* directories, whose immediate subfolders
    are the individual contests. A directory is a container if its name is
    verbatim `contest`/`contests` (auto-detected anywhere in the repo) or if it
    was registered via `--contest-dir` (config.CONTEST_DIRS, which may list
    several). Container subfolders are handled here and pruned from the generic
    walk, so no file is parsed twice.

    Every dot-directory (`.git/`, `.github/`, `.readme_updater/`, ...), the
    generator's own folder, the markdowns folder, and `__pycache__/` are skipped.
    '''
    repo_root     = abspath(config.README_PATH)
    pruned_fixed  = {abspath(config.SCRIPT_DIR), abspath(config.MARKDOWN_DIR)}
    extra_contest = {abspath(join(repo_root, d)) for d in config.CONTEST_DIRS}
    extra_contest.discard(repo_root)            # the repo root itself is never a container

    code_files    = []
    contest_files = []
    context_files = []
    for dir_path, dir_names, file_names in walk(repo_root) :
        is_container = (basename(dir_path) in CONTEST_DIR_NAMES and abspath(dir_path) != repo_root) \
                       or abspath(dir_path) in extra_contest

        if is_container :
            # Every subfolder here is a contest; collect them and stop descending
            # (their files are contest solutions, not generic ones). Files sitting
            # directly in the container still fall through as generic solutions.
            _collect_contest_dir(dir_path, repo_root, contest_files, context_files)
            dir_names[:] = []
        else :
            # Prune dot-dirs, __pycache__, and the generator/markdowns folders in
            # place; contest containers are left in so walk() descends and detects
            # them on the next iteration.
            dir_names[:] = [d for d in dir_names
                            if not d.startswith('.')
                            and d not in _PRUNE_DIR_NAMES
                            and abspath(join(dir_path, d)) not in pruned_fixed]

        for name in file_names :
            readme_path = relpath(join(dir_path, name), repo_root).replace('\\', '/')
            if _is_code_file(name) :
                code_files.append(readme_path)
            elif _is_context_file(name) :
                context_files.append(readme_path)

    code_files.sort()
    contest_files.sort()
    context_files.sort()

    print(f'Total of {len(code_files)} code files found.')
    print(f'Total of {len(contest_files)} contest files found.')
    print(f'Total of {len(context_files)} context files found.')

    return SubmissionFiles(code_files, contest_files, context_files)


def load_git_timestamps(files: SubmissionFiles) -> None :
    '''
    Bulk-parses every submission file's creation/modification dates from the
    git log (the `-g` flag), populating `_git_file_times` for get_file_times()
    and `_oldest_file_date` for the daily/weekly challenge matching.

    WARNING: DO NOT USE LOCALLY -- parsing the git log per file can take 10+
    minutes for ~700 files locally, while GitHub Actions does it in ~10s.
    Local runs get the same dates far faster from the filesystem metadata.
    '''
    global _oldest_file_date

    paths = (list(files.context_files)
             + list(files.code_files)
             + [readme_path for _, readme_path in files.contest_files])

    print('Beginning parsing of git logs for file creation and modification dates...')
    cmd = 'git log -M --format=%ct --reverse --'.split()
    oldest_date = datetime.now()

    for readme_path in tqdm(paths) :
        _git_file_times[readme_path] = _parse_git_log_times(cmd + [readme_path])
        oldest_date = min(oldest_date, _git_file_times[readme_path][0])

    _oldest_file_date = oldest_date.replace(hour=0, minute=0, second=0, microsecond=0)


# ============================================================================ #
#  Question records
# ============================================================================ #
# Each parsed question lives in the `question_data` dict as a plain dict of
# details (dates, categories, solution file paths per language, ...) keyed by
# its official LeetCode question number.

def _difficulty_name(level: str) -> str :
    match level[0].lower() :
        case 'e' :
            return 'Easy'
        case 'm' :
            return 'Medium'
        case 'h' :
            return 'Hard'
    return 'Unknown'


def _file_size(path: str) -> int :
    try :
        return stat(path).st_size
    except FileNotFoundError as fnfe :
        print(fnfe)
        return 0


def create_question_entry(*,
                          number:        int,
                          title:         str,
                          level:         str,
                          categories:    Set[str],
                          language:      str,
                          readme_path:   str,
                          file_times:    Tuple[datetime, datetime],
                          file_size:     int,
                          contest_title: str = None,
                          contest_q_no:  str = None) -> dict :
    '''Builds the record for a question not encountered before.'''
    creation_date, modification_date = file_times

    return {
        'level':            _difficulty_name(level),
        'number':           number,
        'title':            title,
        'categories':       categories or set(),
        'contestTitle':     contest_title,
        'contestQNo':       contest_q_no,
        'date_done':        creation_date,         # first time completed
        'date_modified':    modification_date,     # most recent update
        'solution':         '',                    # generated markdown file name
        'solutions':        {language: [readme_path]},
        'languages':        {language},
        'bytes':            file_size,
    }


def update_question_entry(entry: dict,
                          *,
                          language:      str,
                          categories:    Set[str],
                          readme_path:   str,
                          file_times:    Tuple[datetime, datetime],
                          file_size:     int,
                          contest_title: str = None,
                          contest_q_no:  str = None) -> dict :
    '''Folds another solution file into an already-encountered question.'''
    entry['languages'].add(language)

    if contest_title :
        entry['contestTitle'] = contest_title
    if contest_q_no :
        entry['contestQNo'] = contest_q_no
    if categories :
        entry['categories'] |= categories

    creation_date, modification_date = file_times
    entry['date_done']     = min(entry['date_done'], creation_date)
    entry['date_modified'] = max(entry['date_modified'], modification_date)

    entry['solutions'].setdefault(language, []).append(readme_path)
    entry['bytes'] += file_size

    return entry


def _first_question_number(text: str) :
    '''First 1-4 digit question number in `text`, or None (see QUESTION_NO_PATTERN).'''
    match = QUESTION_NO_PATTERN.search(text)
    return int(match.group()) if match else None


def _resolve_question_number(readme_path: str) :
    '''
    The question number for a code file.

    Normally the first 1-4 digit run in the file name. For number-less files
    named like "main"/"solution", falls back to the first number in the file's
    immediate parent folder (one level up only) -- e.g.
    "1234. Two Sum/Solution.java" resolves to 1234. None if neither has one.
    '''
    parts     = readme_path.replace('\\', '/').split('/')
    file_name = parts[-1]

    number = _first_question_number(file_name)
    if number is not None :
        return number

    if MAIN_SOLUTION_PATTERN.search(file_name) and len(parts) >= 2 :
        return _first_question_number(parts[-2])    # immediate parent folder only

    return None


def parse_case(readme_path:         str,
               question_data:       dict,
               file_latest_times:   dict,
               reprocess_markdown:  Set[int],
               question_details:    Dict[int, Question],
               *,
               contest:             str = None) -> bool :
    '''
    Parses one solution file (given by its path from the README) into
    `question_data`, creating or updating the question's record. Questions whose
    files are newer than the stored history in `file_latest_times` are queued in
    `reprocess_markdown`. Returns False for files with no resolvable question
    number (they are silently skipped -- most repo files are not solutions).
    '''
    path      = readme_path.replace('\\', '/')
    file_name = path.rsplit('/', 1)[-1]

    number = _resolve_question_number(path)
    if number is None :
        return False

    # Difficulty and title come solely from the official question data submodule
    if number in question_details :
        details = question_details[number]
        level   = details.level
        title   = f'[{details.title}](<https://leetcode.com/problems/{details.slug}>)'
    else :
        level = 'Unknown'
        title = f'Question {number}'

    script_path = join(config.README_PATH, path)
    file_times  = get_file_times(script_path)

    if path not in file_latest_times or max(file_times) > file_latest_times[path] :
        reprocess_markdown.add(number)
        file_latest_times[path] = max(file_times)

    categories = set()
    language   = file_name[file_name.rfind('.') + 1:]

    # Contest-folder files may carry their in-contest question number (q1-q4)
    contest_q_no = None
    if contest :
        in_contest_no = re.findall(r'q\d{1}', file_name)
        if in_contest_no :
            contest_q_no = in_contest_no[0]
        categories.add('Contest')

    if number in question_data :
        update_question_entry(question_data[number],
                              language=language,
                              categories=categories,
                              readme_path=path,
                              file_times=file_times,
                              file_size=_file_size(script_path),
                              contest_title=contest,
                              contest_q_no=contest_q_no)
    else :
        question_data[number] = create_question_entry(number=number,
                                                      title=title,
                                                      level=level,
                                                      categories=categories,
                                                      language=language,
                                                      readme_path=path,
                                                      file_times=file_times,
                                                      file_size=_file_size(script_path),
                                                      contest_title=contest,
                                                      contest_q_no=contest_q_no)
    return True


def parse_context_files(context_files:      List[str],
                        question_data:      dict,
                        file_latest_times:  dict,
                        reprocess_markdown: Set[int]) -> None :
    '''
    Attaches notes files (.txt/.md, matched by question number in the file
    name) to their question's record for inclusion in its markdown.
    '''
    for readme_path in context_files :
        readme_path = readme_path.replace('\\', '/')
        base_name   = readme_path.rsplit('/', 1)[-1]

        number = _first_question_number(base_name)
        if number is None or number not in question_data :
            continue

        question_data[number]['contextFile'] = readme_path

        script_path = join(config.README_PATH, readme_path)
        file_times  = get_file_times(script_path)
        if readme_path not in file_latest_times or max(file_times) > file_latest_times[readme_path] :
            file_latest_times[readme_path] = max(file_times)
            reprocess_markdown.add(number)


def build_question_data(files:              SubmissionFiles,
                        question_details:   Dict[int, Question],
                        file_latest_times:  dict) -> Tuple[dict, Set[int]] :
    '''
    Parses every discovered submission file into one `question_data` dict.

    ### Returns :
    question_data : dict[int, dict]
        Each question's parsed details keyed by question number
    reprocess_markdown : Set[int]
        Questions with new/modified files whose markdowns need regenerating
    '''
    question_data      = {}
    reprocess_markdown = set()

    # Contest files take precedence: a contest solution is parsed here (with its
    # Contest tag) and its folder is pruned from the repo-wide code-file scan, so
    # the two never both process the same file.
    print('Parsing contest files...')
    for contest_name, readme_path in files.contest_files :
        parse_case(readme_path,
                   question_data,
                   file_latest_times,
                   reprocess_markdown,
                   question_details,
                   contest=contest_name)

    print('Parsing code files...')
    for readme_path in files.code_files :
        parse_case(readme_path,
                   question_data,
                   file_latest_times,
                   reprocess_markdown,
                   question_details)

    print('Parsing additional information/context files...')
    parse_context_files(files.context_files,
                        question_data,
                        file_latest_times,
                        reprocess_markdown)

    return question_data, reprocess_markdown


# ============================================================================ #
#  Stored data (question details, modification history)
# ============================================================================ #

def retrieve_question_details() -> Dict[int, Question] :
    '''
    Retrieves each question's official details (title, AC rate, difficulty,
    topics, ...) from the `.pkl` parsed from official LeetCode data by the
    question-data submodule, keyed by question number.
    '''
    if not isfile(config.QUESTION_DETAILS_PATH) :
        print('\nError in parsing official question data. leetcode.pkl not found. Exiting...')
        print()
        sys.exit(1)

    with open(config.QUESTION_DETAILS_PATH, 'rb') as fp :
        return pickle.load(fp)


def load_file_times() -> dict :
    '''Retrieves the pickled per-file modification times from previous runs.'''
    if isfile(config.HISTORY_PATH) :
        with open(config.HISTORY_PATH, 'rb') as fp :
            return pickle.load(fp)
    return {}


def save_file_times(file_latest_times: dict) -> None :
    '''Pickles each file's newest modification time for future runs.'''
    with open(config.HISTORY_PATH, 'wb') as fp :
        pickle.dump(file_latest_times, fp)


# ============================================================================ #
#  Daily and weekly challenges
# ============================================================================ #

def load_challenge_dates(data_path: str,
                         first_date: datetime = None) -> List[Tuple[datetime, int]] :
    '''
    Loads a challenge history json (dailies or weeklies) as a list of
    (date, question number) tuples sorted by date descending, skipping
    challenges older than `first_date` (default: the oldest tracked file).
    '''
    if not first_date :
        first_date = _oldest_file_date
    print('Oldest date found:', first_date)

    with open(data_path) as fp :
        challenges = json.load(fp)

    output = []
    for date_string, details in challenges.items() :
        date = datetime.strptime(date_string, '%Y-%m-%d')
        if date < first_date :
            continue
        output.append((date, int(details['question']['questionFrontendId'])))

    return sorted(output, key=lambda x: x[0], reverse=True)


def match_challenge_questions(question_data: dict,
                              challenges:    List[Tuple[datetime, int]],
                              *,
                              leeway:        timedelta,
                              category:      str) -> Dict[datetime, dict] :
    '''
    Matches solved questions against challenge dates: a question completed
    within `leeway` of its challenge date is tagged with `category` and
    included in the returned {challenge date: question entry} mapping.
    '''
    matched = {}
    for date, number in challenges :
        if number in question_data and question_data[number]['date_done'] <= date + leeway :
            matched[date] = question_data[number].copy()
            matched[date]['date_done'] = date
            question_data[number]['categories'].add(category)
    return matched


def build_daily_calendars(dailies: Dict[datetime, dict]) -> Tuple[str, str] :
    '''
    Renders the completed dailies as per-month markdown-table calendars where
    each completed day links to its question's markdown.

    ### Returns :
    (current month's calendar, all months' calendars)
    '''
    if not dailies :
        return ('', '')

    # {year: {month: {day: question entry}}}
    date_map = {}
    for date, question in dailies.items() :
        date_map.setdefault(date.year, {}).setdefault(date.month, {})[date.day] = question

    calendar.setfirstweekday(calendar.SUNDAY)

    earliest_date = min(dailies.keys())
    today         = datetime.now()
    outputs       = []

    for year in range(earliest_date.year, today.year + 1) :
        start_month = earliest_date.month if year == earliest_date.year else 1
        end_month   = today.month if year == today.year else 12

        for month in range(start_month, end_month + 1) :
            days_completed = date_map.get(year, {}).get(month)
            if not days_completed :
                continue

            # calendar.month() gives 'MONTH YEAR\nSu Mo ... Sa\n<day rows>'
            month_lines = calendar.month(year, month).split('\n')
            header      = f'### {month_lines[0].strip()}'
            day_names   = month_lines[1].split()

            # Link every completed day to its question's markdown
            weeks = [[(day if int(day) not in days_completed
                       else f'[{day}](<{days_completed[int(day)]["solution"]}>)')
                      for day in line.split()]
                     for line in month_lines[2:]]

            # Left-pad the first week so days align to their weekday columns
            if len(weeks[0]) < 7 :
                weeks[0] = [''] * (7 - len(weeks[0])) + weeks[0]
            if not weeks[-1] :
                weeks.pop()

            markdown_cal = kungfupanda.DataFrame(weeks, columns=day_names) \
                                      .to_markdown(index=False)

            # Right-align the day columns (tabulate only emits left alignment)
            col_alignments = sorted(re.findall(r':{1}-{1}-*', markdown_cal),
                                    key=len, reverse=True)
            for alignment in col_alignments :
                markdown_cal = markdown_cal.replace(alignment,
                                                    '-' * (len(alignment) - 1) + ':')

            outputs.append('\n'.join([header, markdown_cal, '\n']))

    return (outputs[-1], '\n'.join(outputs))


# ============================================================================ #
#  List-based categories (NeetCode150, Blind75, ...)
# ============================================================================ #

def get_list_file_names() -> List[str] :
    '''Question-list files present in the lists directory.'''
    list_file_names = [x for x in listdir(config.LISTS_DIR)
                       if isfile(join(config.LISTS_DIR, x))
                          and not x.startswith('.')
                          and not x == 'README.md']
    print(list_file_names)
    return list_file_names


def parse_list_file(file_path: str) -> Set[int] :
    '''
    Extracts the question numbers from a list file. Expected format:

        [Question #]. [Question Name]

        [Easy, Med., Hard]
        Topic1
        Topic2
        ...
    '''
    output = set()
    with open(file_path, 'r') as file :
        for line in file.readlines() :
            if re.match(r'\d{1,4}\.', line) :
                output.add(int(line[:line.find('.')]))
    return output


def apply_list_categories(question_data: dict,
                          *,
                          list_file_names: List[str] = None) -> Dict[str, Set[int]] :
    '''
    Tags every solved question that appears in a list file with that list's
    name as a category. Returns each list's question numbers by list name.
    '''
    if not list_file_names :
        list_file_names = get_list_file_names()

    list_data = {}
    for file_name in list_file_names :
        list_data[file_name] = parse_list_file(join(config.LISTS_DIR, file_name))
        for number in list_data[file_name] :
            if number in question_data :
                question_data[number]['categories'].add(file_name)

    return list_data


# ============================================================================ #
#  Topic groupings
# ============================================================================ #

def get_completed_topic_lists(question_data:    dict,
                              question_details: Dict[int, Question]) -> defaultdict :
    '''Groups the solved question numbers by their official related topics.'''
    completed_topic_lists = defaultdict(set)

    for number in question_data.keys() :
        # Shouldn't occur but just in case
        if number not in question_details :
            continue
        for topic in question_details[number].topics :
            completed_topic_lists[topic].add(number)

    return completed_topic_lists


# ============================================================================ #
#  DataFrame conversion
# ============================================================================ #

def build_question_rows(question_data: dict,
                        *,
                        sort_by:                    str = 'number',
                        include_date:               bool = False,
                        include_questions:          Set[int] = set(),
                        relative_folder_adjustment: int = 0,
                        include_markdown_folder:    bool = False) -> List[list] :
    '''One table row of display values per question, sorted by `sort_by`.'''
    rows = []

    for question in question_data.values() :
        # If a question filter was given, skip questions outside of it
        if include_questions and question['number'] not in include_questions :
            continue

        if sort_by == 'number' and include_markdown_folder :
            solution_path = join(config.MARKDOWN_PATH, question['solution'])
        else :
            solution_path = question['solution']
        solution_path = '../' * abs(relative_folder_adjustment) + solution_path

        title = question['title']
        if question['contestTitle'] and question['contestQNo'] :
            title = f'{question["contestTitle"]} - {question["contestQNo"]} - {title}'

        row = [question['number'],
               title,
               question['level'],
               ', '.join(sorted(question['categories'])),
               f'[solution](<{solution_path}>)',
               ', '.join(sorted(question['languages']))]

        if include_date :
            row.append(question['date_done'].strftime('%b %d, %Y'))

        rows.append(row)

    # question_data is usually keyed by question number (= row[0]), except for
    # challenge mappings which are keyed by date -- sort those by date instead
    if not question_data :
        pass
    elif sort_by == 'date_done' and isinstance(next(iter(question_data.keys())), datetime) :
        rows.sort(key=lambda row: datetime.strptime(row[-1], '%b %d, %Y'))
    else :
        rows.sort(key=lambda row: question_data.get(row[0])[sort_by])

    return rows


def question_dataframe(question_data: dict,
                       *,
                       sort_by:                    str = 'number',
                       include_date:               bool = False,
                       include_questions:          Set[int] = set(),
                       relative_folder_adjustment: int = 0,
                       include_markdown_folder:    bool = False) -> DataFrame :
    '''Converts question records into a display DataFrame (see build_question_rows).'''
    rows = build_question_rows(question_data,
                               sort_by=sort_by,
                               include_date=include_date,
                               include_questions=include_questions,
                               relative_folder_adjustment=relative_folder_adjustment,
                               include_markdown_folder=include_markdown_folder)

    # Protects against empty cases (e.g. if you have no daily files)
    if not rows :
        return kungfupanda.DataFrame()
    return kungfupanda.DataFrame(data=rows, columns=COLUMNS[:len(rows[0])])


def by_recent_dataframe(question_data: dict) -> DataFrame :
    '''Questions sorted by first-completion date, most recent first.'''
    return question_dataframe(question_data, sort_by='date_done', include_date=True).iloc[::-1]


def by_code_length_dataframe(question_data: dict) -> DataFrame :
    '''Questions sorted by total code size (bytes), largest first.'''
    return question_dataframe(question_data, sort_by='bytes', include_date=True).iloc[::-1]


# ============================================================================ #
#  Markdown generation -- individual questions
# ============================================================================ #

def write_question_markdown(number:           int,
                            question_data:    dict,
                            question_details: Dict[int, Question],
                            *,
                            export: bool = False) -> None :
    '''
    Names (and, when `export` is set, writes) the markdown page collecting a
    question's details, notes, and every solution file's code.
    '''
    entry = question_data[number]

    title = entry['title']
    # Titles matched to a LeetCode url are wrapped in a markdown link --
    # extract the bare title for the file name
    if '[' in title :
        title = title[title.find('[') + 1:title.find(']')]
    title = f'{number}. {title}'

    file_name         = f'_{title}.md'
    entry['solution'] = file_name

    if not export :
        return

    with open(join(config.MARKDOWN_DIR, file_name), 'w', encoding='utf-8') as f :
        f.write(f'# {number}. {entry["title"]}\n\n')

        f.write('*All prompts are owned by LeetCode. To view the prompt, click the title link above.*\n\n')

        if entry['contestTitle'] and entry['contestQNo'] :
            f.write(f'*Completed during {entry["contestTitle"]} ({entry["contestQNo"]})*\n\n')

        f.write('*[Back to top](<../README.md>)*\n\n')

        f.write('------\n\n')
        f.write(f'> *First completed : {entry["date_done"]:%B %d, %Y}*\n>\n')
        f.write(f'> *Last updated : {entry["date_modified"]:%B %d, %Y}*\n')

        f.write('\n------\n\n')

        if number not in question_details or len(question_details[number].topics) == 0 :
            topics = 'N/A'
        else :
            topics = ', '.join(f'[{topic}](<{join(config.TOPIC_FOLDER, topic)}.md>)'
                               for topic in question_details[number].topics)
        f.write(f'> **Related Topics** : **{topics}**\n>\n')

        acceptance_rate = 'Unknown' if number not in question_details \
                          else f'{round(question_details[number].acRate, 2)} %'
        f.write(f'> **Acceptance Rate** : **{acceptance_rate}**\n\n')
        f.write('------\n\n')

        # The question's notes file, quoted, if one was found
        if 'contextFile' in entry :
            with open(join(config.README_PATH, entry['contextFile']), 'r') as context_file :
                f.write('> ' + context_file.read().replace('\n', '\n> '))
            f.write('\n\n------\n\n')

        f.write('## Solutions\n\n')
        for solutions in entry['solutions'].values() :
            solutions.sort()
            for solution in solutions :
                name = solution[solution.find('/') + 1:]
                f.write(f'- [{name}](<{join(config.README_PATH, solution)}>)\n')

        for language, solutions in entry['solutions'].items() :
            if language.lower() in language_equivs() :
                language = language_equivs()[language.lower()]
            else :
                print()
                print(f'Lang equiv not found: {language = }')
            f.write(f'### {language}\n')

            for solution in solutions :
                base_name = solution[solution.rfind('/') + 1:]
                f.write(f'#### [{base_name}](<{join(config.README_PATH, solution)}>)\n')
                f.write(f'```{language}\n')
                with open(join(config.README_PATH, solution), 'r', encoding='utf-8') as solution_file :
                    file_data = solution_file.read()
                    # Trim vscode-leetcode plugin wrappers down to the code itself
                    if '# @lc code=start' in file_data :
                        lc_start = '# @lc code=start'
                        lc_end   = '# @lc code=end'
                        file_data = file_data[file_data.find(lc_start) + len(lc_start):
                                              file_data.rfind(lc_end)]
                    f.write(file_data)
                f.write('\n```\n\n')


def export_question_markdowns(question_data:      dict,
                              reprocess_markdown: Set[int],
                              question_details:   Dict[int, Question]) -> None :
    '''
    Writes the markdown page of every question queued in `reprocess_markdown`.
    Untouched questions still get their markdown file name assigned (other
    pages link to it) -- the file itself just isn't rewritten.
    '''
    if not isdir(config.MARKDOWN_DIR) :
        mkdir(config.MARKDOWN_DIR)

    for number in question_data.keys() :
        write_question_markdown(number,
                                question_data,
                                question_details,
                                export=number in reprocess_markdown)


# ============================================================================ #
#  Markdown generation -- grouping pages
# ============================================================================ #

def _write_listing_markdown(file_name: str,
                            header:    str,
                            details:   str,
                            df:        DataFrame,
                            *,
                            tail:      str = None) -> str :
    '''
    Writes one grouping page (header, blurb, question table, optional tail)
    into the markdowns folder. Returns the page's path from the README.
    '''
    with open(join(config.MARKDOWN_DIR, file_name), 'w', encoding='utf-8') as f :
        f.write(header)
        f.write('*[Back to top](<../README.md>)*\n\n')
        f.write(details)
        f.write(df.to_markdown(index=False))
        if tail :
            f.write(f'\n\n{tail}')

    return join(config.MARKDOWN_PATH, file_name)


def export_daily_markdown(question_data: dict) -> str :
    '''Generates the daily-challenges page (calendars + table). Returns its path.'''
    dailies = match_challenge_questions(question_data,
                                        load_challenge_dates(config.DAILIES_DATA_PATH),
                                        leeway=DAILY_LEEWAY,
                                        category='Daily')

    current_month, all_months = build_daily_calendars(dailies)

    details = 'Dates are for the date I completed the ' + \
              'question so due to the my time zone and how it lines up with ' + \
              'UTC, it may be off by a day.\n\n' + \
              current_month + '\n\n'

    return _write_listing_markdown('Daily_Questions.md',
                                   '# Daily Questions\n\n',
                                   details,
                                   by_recent_dataframe(dailies),
                                   tail=all_months)


def export_weekly_markdown(question_data: dict) -> str :
    '''Generates the weekly-premium-challenges page. Returns its path.'''
    weeklies = match_challenge_questions(question_data,
                                         load_challenge_dates(config.WEEKLIES_DATA_PATH),
                                         leeway=WEEKLY_LEEWAY,
                                         category='Weekly Premium')

    details = 'Dates are for the date I completed the ' + \
              'question so due to the my time zone and how it lines up with ' + \
              'UTC, it may be off by a day.\n\n'

    return _write_listing_markdown('Weekly_Questions.md',
                                   '# Weekly Premium Questions\n\n',
                                   details,
                                   by_recent_dataframe(weeklies))


def export_code_length_markdown(question_data: dict) -> str :
    '''Generates the questions-by-code-length page. Returns its path.'''
    return _write_listing_markdown('Questions_By_Code_Length.md',
                                   '# Questions By Code Length\n\n',
                                   'Calculations are based on the code files\'s byte sizes.\n\n',
                                   by_code_length_dataframe(question_data))


def export_recent_markdown(question_data: dict) -> str :
    '''Generates the most-recently-solved page. Returns its path.'''
    return _write_listing_markdown('Questions_By_Recent.md',
                                   '# Most Recently Solved Questions\n\n',
                                   'Calculations are based on the date of the first solve.\n\n',
                                   by_recent_dataframe(question_data))


def export_difficulty_markdowns(question_data: dict) -> Tuple[Tuple[int, str],
                                                              Tuple[int, str],
                                                              Tuple[int, str]] :
    '''
    Generates one page per difficulty (Easy.md, Medium.md, Hard.md).

    ### Returns :
    - Tuple[Easy, Medium, Hard]
        - Tuple[int, str] : (count, path from readme)
    '''
    grouped = {'Easy': {}, 'Medium': {}, 'Hard': {}}
    for number, entry in question_data.items() :
        if entry['level'] in grouped :
            grouped[entry['level']][number] = entry
        else :
            print(f'Error identifying level of {number = }')

    output = []
    for level, questions in grouped.items() :
        df   = question_dataframe(questions, include_date=True)
        path = join(config.MARKDOWN_PATH, f'{level}.md')

        with open(join(config.README_PATH, path), 'w', encoding='utf-8') as f :
            f.write(f'# {level} Questions ({len(questions)})\n\n')
            f.write('*[Back to top](<../README.md>)*\n\n')
            f.write('------\n\n')
            f.write(df.to_markdown(index=False))

        output.append((len(questions), path))

    return tuple(output)


# NOTE: Topic-based markdowns (and the large list markdowns in general) may
# suddenly show massive diffs after a regular question update. This is likely
# the dataframe.to_markdown method widening the whole table to fit a larger
# than before seen input.
def export_topic_markdowns(question_data:   dict,
                           topic_groupings: defaultdict) -> Tuple[str, List[Tuple[str, str]]] :
    '''
    Generates one page per related topic plus the Topics.md overview linking
    to all of them, ordered by completed-question count.

    ### Returns :
    (overview page's path from the README, [(topic, page's path), ...])
    '''
    topic_dataframes = [(topic,
                         len(questions),
                         question_dataframe(question_data,
                                            include_date=True,
                                            include_questions=questions,
                                            relative_folder_adjustment=-config.TOPIC_FOLDER.count('/')))
                        for topic, questions in topic_groupings.items()]
    topic_dataframes.sort(key=lambda x: x[1], reverse=True)

    if not isdir(config.TOPIC_MARKDOWN_DIR) :
        mkdir(config.TOPIC_MARKDOWN_DIR)

    topic_links = []
    with open(config.TOPICS_OVERVIEW_FILE, 'w', encoding='utf-8') as overview :
        overview.write('# Topics\n\n')
        overview.write('*[Back to top](<../README.md>)*\n\n')
        overview.write('------\n\n')

        for topic, count, df in topic_dataframes :
            file_name = f'{topic}.md'
            with open(join(config.TOPIC_MARKDOWN_DIR, file_name), 'w', encoding='utf-8') as f :
                url = f'https://leetcode.com/tag/{topic.replace(" ", "-")}/'
                f.write(f'# [{topic}](<{url}>) ({count} completed)\n\n')
                f.write('*[Back to top](<../../README.md>)*\n\n')
                f.write('------\n\n')
                f.write(df.to_markdown(index=False))

            readme_path = join(config.TOPIC_FOLDER, file_name)
            overview.write(f'- [{topic}](<{readme_path}>) ({count} completed)\n')
            topic_links.append((topic, readme_path))

    return config.TOPICS_OVERVIEW_PATH_FROM_README, topic_links


# ============================================================================ #
#  Markdown generation -- primary README
# ============================================================================ #

def export_primary_readme(df_questions:     DataFrame,
                          *,
                          additional_sorts: List[str] = [],
                          topic_links:      List[Tuple[str, str]] = []) -> None :
    '''
    Overwrites the parent repo's README.md with the profile header, links to
    every grouping page, and the full sorted question table.
    '''
    readme_path = join(config.README_PATH, 'README.md')
    print(readme_path)

    username        = config.USERNAME
    q_solved_header = f'{len(df_questions.index)} solved'

    with open(readme_path, 'w') as file :
        file.write(f'# **[LeetCode Records](https://leetcode.com/u/{username}/)** ({q_solved_header})\n\n')
        file.write('<!-- This readme was generated using [WikiLeet](<https://github.com/Zanger67/WikiLeet>) -->\n\n')
        file.write(f'> My LeetCode Profile: [{username}](https://leetcode.com/u/{username}/)\n')
        file.write('\n\n')

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
        file.write('\n\n')

        file.write('------\n\n')

        file.write('## Additional Categories Stats\n')
        for alt_sort in additional_sorts :
            file.write(alt_sort)
            file.write('\n\n')

        if topic_links :
            file.write('------\n\n')
            file.write(', '.join(f'[{topic}](<{join(config.MARKDOWN_PATH, link)}>)'
                                 for topic, link in topic_links))
            file.write('\n\n')
            file.write('------\n\n')

        file.write('\n\n')

        file.write('## Questions\n')
        file.write(df_questions.to_markdown(index=False))

        file.write('\n\n')
        file.write('<p align="right"><i>This README was generated using <a href="https://github.com/Zanger67/WikiLeet">WikiLeet</a></i></p>\n')


# ============================================================================ #
#  Pipeline
# ============================================================================ #

def main(*, recalculate_all: bool = False, no_record: bool = False) -> Tuple[dict, Set[int]] :
    '''
    Runs the full generation pipeline. main.ipynb runs these same stages one
    cell at a time.

    ### Parameters :
    recalculate_all : bool
        Regenerate every question's markdown regardless of whether its source
        files were modified or not
    no_record : bool
        Ignore the stored modification-time history and don't store the new
        one (in effect the same as recalculate_all, but stateless)
    '''
    # Stage 1: find all submission files, then (optionally, -g) date them
    # through the git log
    files = discover_submission_files()
    if USE_GIT_DATES :
        load_git_timestamps(files)

    # Stage 2: official question details + which files changed since last run
    question_details  = retrieve_question_details()
    file_latest_times = load_file_times() if not (recalculate_all or no_record) else {}

    # Stage 3: parse every file into per-question records
    question_data, reprocess_markdown = build_question_data(files,
                                                            question_details,
                                                            file_latest_times)

    # Stage 4: tag questions that appear in list files (NeetCode150, ...)
    print('Sorting questions to their lists...')
    apply_list_categories(question_data)

    # Stage 5: one markdown page per new/updated question
    print('Generating markdowns for each individual question...')
    export_question_markdowns(question_data, reprocess_markdown, question_details)

    # Stage 6: grouping pages. Challenge pages come first -- they also tag
    # questions with the Daily/Weekly Premium categories shown everywhere else
    print('Generating category lists...')
    additional_sorts = [
        f'- [Daily Questions](<{export_daily_markdown(question_data)}>)',
        f'- [Weekly Questions](<{export_weekly_markdown(question_data)}>)',
        f'- [Questions By Code Length](<{export_code_length_markdown(question_data)}>)',
        f'- [Questions By Recent](<{export_recent_markdown(question_data)}>)',
    ]
    export_difficulty_markdowns(question_data)

    topic_groupings = get_completed_topic_lists(question_data, question_details)
    overview_path, topic_links = export_topic_markdowns(question_data, topic_groupings)
    additional_sorts.append(f'- [Grouped by Topic](<{overview_path}>)')

    # Stage 7: the primary README
    print('Exporting primary README.md file...')
    df_questions = question_dataframe(question_data, include_markdown_folder=True)
    export_primary_readme(df_questions,
                          additional_sorts=additional_sorts,
                          topic_links=topic_links)

    print(f'Number of individual questions updated/added: {len(reprocess_markdown)}')

    # Stage 8: remember each file's modification time for the next run
    if not no_record :
        print('Pickling most recent modification times for future reference...')
        save_file_times(file_latest_times)

    print('All processes complete. Exiting...')
    return question_data, reprocess_markdown


# ============================================================================ #
#  CLI entry point
# ============================================================================ #

def parse_cli_args() -> argparse.Namespace :
    parser = argparse.ArgumentParser(description='WikiLeet markdown generator')

    parser.add_argument('-r',
                        help='Recompile all markdown files',
                        required=False,
                        action=argparse.BooleanOptionalAction)
    parser.add_argument('-n',
                        help="Don't use the previous modified dates and don't store them",
                        required=False,
                        action=argparse.BooleanOptionalAction)
    parser.add_argument('-norecord',
                        help="Don't use the previous modified dates and don't store them",
                        required=False,
                        action=argparse.BooleanOptionalAction)
    parser.add_argument('-g',
                        help="Use the git repo's log for determining if a file has been modified and created (WARNING SLOW)",
                        required=False,
                        action=argparse.BooleanOptionalAction)

    parser.add_argument('-user',
                        type=str,
                        default='',
                        help='LeetCode Username',
                        required=False)
    parser.add_argument('-contest-dir',
                        type=str,
                        action='append',
                        default=None,
                        help='Extra contest container dir(s) whose subfolders are each a '
                             'contest; repeatable and/or comma-separated. Folders named '
                             '"contest"/"contests" are auto-detected on top of these.',
                        required=False)

    return parser.parse_args()


if __name__ == '__main__' :
    # Ensure relative paths resolve from this script's location rather than
    # the calling location (e.g. `python someFolder/main.py` still works)
    chdir(dirname(abspath(__file__)))

    args = parse_cli_args()

    config.load_environment()

    # CLI overrides are applied to the environment before the config
    # resolves its values from it
    if args.user :
        environ['LEETCODE_USERNAME'] = args.user
    if args.contest_dir :
        # -contest-dir may be repeated and/or comma-separated -> flatten to one
        # comma-joined list the config parses into config.CONTEST_DIRS
        contest_dirs = [d.strip()
                        for item in args.contest_dir
                        for d in item.split(',')
                        if d.strip()]
        if contest_dirs :
            environ['CONTEST_DIRS'] = ','.join(contest_dirs)

    config.init()

    USE_GIT_DATES   = bool(args.g)
    no_record       = bool(args.n or args.norecord)
    recalculate_all = bool(args.r)

    print('Extra contest dirs'.ljust(20), config.CONTEST_DIRS or '(none)')
    print('No record'.ljust(20), 'on' if no_record else 'off')
    print('Recalculate'.ljust(20), 'on' if recalculate_all else 'off')
    print('Use Git dates'.ljust(20), 'on' if USE_GIT_DATES else 'off')
    print()

    main(recalculate_all=recalculate_all, no_record=no_record)
