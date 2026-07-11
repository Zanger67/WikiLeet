'''
Central configuration for the WikiLeet markdown generator.

This module owns two things:

1. `load_environment()` -- loads the `.env` config files. The `.env` sitting
   next to this file provides the defaults; a `.env` in the parent directory
   (the root of the repo that imported WikiLeet as a submodule) overrides it.

2. `init()` -- resolves every path/value the generator uses from those
   environment variables into module globals, so all other modules share one
   consistent view via `import env_config as config`.

Call order:

    config.load_environment()
    # ...optionally override variables in os.environ (e.g. CLI flags)...
    config.init()

Keeping these values as module globals (rather than locals threaded through
every call) means they are static and consistent everywhere, while still being
derived from the environment *after* any runtime overrides have been applied.

All relative paths are relative to this file's directory (the WikiLeet repo
root), which is also the expected working directory when the generator runs.
'''

from os import getenv
from os.path import abspath, dirname, isfile, join

from dotenv import load_dotenv


# Directory containing this file (alongside main.py, .env, question_data/, ...)
SCRIPT_DIR = dirname(abspath(__file__))


def load_environment() -> None :
    '''
    Loads `.env` variables for reference.
    1. Loads the default `.env` from this script's directory.
    2. If a `.env` exists in the parent directory (the repo that imported
       WikiLeet as a submodule), it overrides the defaults.
    '''
    print('Default .env activated from script directory (.readme_updater/)')
    load_dotenv(join(SCRIPT_DIR, '.env'), override=True)

    parent_env = abspath(join(SCRIPT_DIR, '..', '.env'))
    if isfile(parent_env) :
        print('.env found in ../ directory. Overriding default...')
        load_dotenv(parent_env, override=True)


# ============================================================================ #
#  Resolved configuration -- populated by init()
# ============================================================================ #

# LeetCode username used for profile links in the generated README
USERNAME                        = None

# Relative path from this script to the folder whose README.md we generate
# (i.e. the root of the repo that imported WikiLeet)
README_PATH                     = None

# Extra contest container dirs (relative to the README) registered via
# --contest-dir / the CONTEST_DIRS env var. Folders named "contest"/"contests"
# are auto-detected anywhere in the repo on top of these.
CONTEST_DIRS                    = []

# Question metadata (titles, AC rates, difficulties, topics, ...) parsed from
# official LeetCode data by the question-data submodule
SUBMODULE_DATA_PATH             = None
QUESTION_DETAILS_PATH           = None

# Daily / weekly-premium challenge history (date -> question) json files
DAILIES_DATA_PATH               = None
WEEKLIES_DATA_PATH              = None

# Pickled file-modification history so unchanged questions aren't regenerated
HISTORY_PATH                    = None

# Question lists (NeetCode150, Blind75, ...) used as extra categories
LISTS_DIR                       = None

# Mapping of file extensions to markdown code-block language names
LANGUAGE_EQUIVS_PATH            = None

# Where the individual question markdowns go -- relative to the README, and
# relative to here
MARKDOWN_PATH                   = None
MARKDOWN_DIR                    = None

# Topic-grouped markdowns: folder (relative to the markdowns folder), that
# folder relative to here, plus the overview file listing every topic
TOPIC_FOLDER                    = None
TOPIC_MARKDOWN_DIR              = None
TOPICS_OVERVIEW_FILE            = None
TOPICS_OVERVIEW_PATH_FROM_README = None


def init() -> None :
    '''
    Resolves all configuration globals from the environment. Must be called
    after `load_environment()` (and after any manual overrides of
    `os.environ`, e.g. from CLI flags).
    '''
    global USERNAME, README_PATH
    global CONTEST_DIRS
    global SUBMODULE_DATA_PATH, QUESTION_DETAILS_PATH
    global DAILIES_DATA_PATH, WEEKLIES_DATA_PATH
    global HISTORY_PATH, LISTS_DIR, LANGUAGE_EQUIVS_PATH
    global MARKDOWN_PATH, MARKDOWN_DIR
    global TOPIC_FOLDER, TOPIC_MARKDOWN_DIR
    global TOPICS_OVERVIEW_FILE, TOPICS_OVERVIEW_PATH_FROM_README

    USERNAME                        = getenv('LEETCODE_USERNAME')
    README_PATH                     = getenv('README_PATH')

    extra_contest_dirs              = getenv('CONTEST_DIRS', '') or ''
    CONTEST_DIRS                    = [d.strip()
                                       for d in extra_contest_dirs.split(',')
                                       if d.strip()]

    SUBMODULE_DATA_PATH             = getenv('SUBMODULE_DATA_PATH')
    QUESTION_DETAILS_PATH           = join(SUBMODULE_DATA_PATH,
                                           getenv('LEETCODE_QUESTION_DETAILS'))

    DAILIES_DATA_PATH               = join(SUBMODULE_DATA_PATH,
                                           getenv('DAILIES_FOLDER'),
                                           getenv('DAILIES_FILE'))
    WEEKLIES_DATA_PATH              = join(SUBMODULE_DATA_PATH,
                                           getenv('DAILIES_FOLDER'),
                                           getenv('WEEKLIES_FILE'))

    HISTORY_PATH                    = join(getenv('USER_DATA_PATH'),
                                           getenv('FILE_MODIFICATION_NAME'))

    LISTS_DIR                       = getenv('LISTS_LOCATION')
    LANGUAGE_EQUIVS_PATH            = join(getenv('QUESTION_DATA_PATH'),
                                           'language_equivs.json')

    MARKDOWN_PATH                   = getenv('QUESTION_MARKDOWNS_PATH_FROM_README')
    MARKDOWN_DIR                    = join(README_PATH, MARKDOWN_PATH)

    TOPIC_FOLDER                    = getenv('TOPIC_MARKDOWN_PATH_IN_MARKDOWNS_FOLDER')
    TOPIC_MARKDOWN_DIR              = join(MARKDOWN_DIR, TOPIC_FOLDER)
    TOPICS_OVERVIEW_FILE            = join(MARKDOWN_DIR, 'Topics.md')
    TOPICS_OVERVIEW_PATH_FROM_README = join(MARKDOWN_PATH, 'Topics.md')
