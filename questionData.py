class questionData :
    def __init__(self, 
                 level:              str,
                 number:             int, 
                 title:              str, 
                 categories:         Set[str],
                 language:           str,
                 notebook_path:      str,
                 readme_path:        str,
                 fileLatestTimes:    dict,
                 contestTitle:       str=None,
                 contestQNo:         str=None) -> None :
        self.level = level
        self.number = number
        self.title = title
        self.categories = categories
        self.language = language
        self.notebook_path = notebook_path
        self.readme_path = readme_path
        
        # File latest times not kept due to it being a reference

        self.contestTitle = contestTitle
        self.contestQNo = contestQNo
