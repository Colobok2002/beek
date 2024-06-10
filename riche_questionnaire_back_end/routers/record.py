from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Optional, Union
from sqlalchemy.orm import Session
from pydantic import BaseModel
from uuid import uuid4

from riche_questionnaire_back_end.db import get_db
from riche_questionnaire_back_end.models.survey_models import (
    AnswerOption,
    CustomerAction,
    Question,
)



records_router = APIRouter()


class QuestionValid(BaseModel):
    question: str
    answers: Dict[int, str]


class SurveyValid(BaseModel):
    name: str
    id: Optional[Union[int, str]] = None
    data: Dict[int, QuestionValid]


data = {
    "name": "Тестовый опрос",
    "id": None,
    "data": {
        "1": {
            "question": "Назовите ваш имя",
            "answers": {"1": "Илья", "2": "Вадим", "3": "Миша"},
        },
        "2": {"question": "Назовите ваш пол", "answers": {"1": "М", "2": "Ж"}},
    },
}


@records_router.post("/create-survey")
async def create_survey(survey: SurveyValid = data, db: Session = Depends(get_db)):
    """Функция создания нового опроса

    Args:
        survey (Survey): _description_

    Raises:
        HTTPException: _description_

    Returns:
        int: id_new_surveu
    """

    if survey.id:
        return JSONResponse(status_code=200, content={"change": True})
    # survey_exists = (
    #     db.query(CustomerAction).filter(CustomerAction.name == survey.name).first()
    # )
    # if survey_exists:
    #     raise HTTPException(
    #         status_code=400, detail="Survey with this name already exists"
    #     )

    new_survey = CustomerAction(name=survey.name)
    db.add(new_survey)
    db.commit()

    for question_order, question_data in survey.data.items():
        new_question = Question(
            customer_id=new_survey.id,
            text=question_data.question,
            ordering=question_order,
        )
        db.add(new_question)
        db.commit()
        db.refresh(new_question)

        for ans_order, ans_text in question_data.answers.items():
            new_answer = AnswerOption(
                question_id=new_question.id, text=ans_text, ordering=ans_order
            )
            db.add(new_answer)
            db.commit()

    return JSONResponse(status_code=200, content={"id": new_survey.id})


@records_router.get("/get-survey")
async def get_survey(survey_id: int, db: Session = Depends(get_db)):
    """Функция получения данных из базы и создания опросника по структуре"""

    survey_data = db.query(CustomerAction).get(survey_id)
    if not survey_data:
        raise HTTPException(status_code=404, detail="Опросник не найден в базе данных")

    survey_questions = (
        db.query(Question).filter(Question.customer_id == survey_id).all()
    )

    survey_data_structure = {"name": survey_data.name, "id": survey_id, "data": {}}

    for question in survey_questions:
        answers = (
            db.query(AnswerOption).filter(AnswerOption.question_id == question.id).all()
        )
        answers_dict = {answer.ordering: answer.text for answer in answers}

        survey_data_structure["data"][question.ordering] = {
            "question": question.text,
            "answers": answers_dict,
        }

    if survey_data_structure["id"] is not None:
        pass

    return JSONResponse(status_code=200, content=survey_data_structure)
