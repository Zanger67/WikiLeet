



from typing import Set
from datetime import datetime


class question :
    def __init__(self,
                 questionNo: int,
                 *,
                 level: str,
                 title: str,
                 categories: Set[str] = set(),
                 date_done: datetime,
                 date_modified: datetime,
                 solution: str,
                 solutions: dict = {},
                 bytes: int = 0,
                 questionData: dict = {}) -> None :
        
        self.questionNo = questionNo

        if not level :
            if level in questionData :
                self.level = questionData[questionNo][]

