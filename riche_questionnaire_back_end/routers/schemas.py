
from pydantic import BaseModel
from typing import List, Union, Optional, Dict

class Answers(BaseModel):
    id: Optional[Union[int, str]] = None
    answer: str

class QuestionValid(BaseModel):
    id: Optional[Union[int, str]] = None
    question: str
    answers: Dict[int, Answers]

class SurveyValid(BaseModel):
    name: str
    id: Optional[Union[int, str]] = None
    data: Dict[int, QuestionValid]

class AnswerItem(BaseModel):
    question_id: Union[int, str]
    answer_id: Union[int, str]

class AnswerData(BaseModel):
    answers: List[AnswerItem]
    response_uuid: str
