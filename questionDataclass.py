

class questionDataclass: 
    def __init__(self,
                 *,
                 questionNo:int=-1,
                 acRate:float=None,
                 difficulty:str=None,
                 isFavor:bool=False,
                 paidOnly:bool=False,
                 title:str=None,
                 slug:str=None,
                 url:str=None,
                 topics:list=None,
                 hasSolution:bool=None,
                 hasVideoSolution:bool=None):
        self.questionNo = questionNo
        self.acRate = acRate
        self.difficulty = difficulty
        self.isFavor = isFavor
        self.paidOnly = paidOnly
        self.title = title
        self.slug = slug
        self.url = 'https://leetcode.com/problems/' + slug
        self.topics = topics
        self.hasSolution = hasSolution
        self.hasVideoSolution = hasVideoSolution


    def __str__(self):
        return f"questionNo: {self.questionNo}, acRate: {self.acRate}, difficulty: {self.difficulty}, isFavor: {self.isFavor}, paidOnly: {self.paidOnly}, title: {self.title}, slug: {self.slug}, url: {self.url}, topics: {self.topics}, hasSolution: {self.hasSolution}, hasVideoSolution: {self.hasVideoSolution}"
    
    def __repr__(self) -> str:
        return f"questionNo: {self.questionNo}, acRate: {self.acRate}, difficulty: {self.difficulty}, isFavor: {self.isFavor}, paidOnly: {self.paidOnly}, title: {self.title}, slug: {self.slug}, url: {self.url}, topics: {self.topics}, hasSolution: {self.hasSolution}, hasVideoSolution: {self.hasVideoSolution}"