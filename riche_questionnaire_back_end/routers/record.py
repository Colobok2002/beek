from typing import Dict, Optional, Union
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from uuid import uuid4
from sqlalchemy.orm import Session

from riche_questionnaire_back_end.db import get_db
from riche_questionnaire_back_end.models.survey_models import (
    AnswerOption,
    CustomerAction,
    Question,
)

# Пример простой БД в памяти для хранения данных
database = {}


# Модель для передаваемых данных
class DataIn(BaseModel):
    data: str


records_router = APIRouter()


@records_router.post("/create-record")
async def create_record(data_in: DataIn, db: Session = Depends(get_db)):
    """_summary_

    Args:
        data_in (DataIn): _description_
        db (Session, optional): _description_. Defaults to Depends(get_db).

    Returns:
        _type_: _description_
    """
    record_id = str(uuid4())
    database[record_id] = data_in.data
    return {"uuid": record_id}


@records_router.get("/read-record")
async def read_record(record_id: str) -> DataIn:
    """_summary_

    Args:
        record_id (str): _description_

    Raises:
        HTTPException: _description_

    Returns:
        _type_: _description_
    """
    if record_id not in database:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    return {"data": database[record_id]}


class Question(BaseModel):
    question: str
    answers: Dict[int, str]


class Survey(BaseModel):
    name: str
    id: Optional[Union[int, str]] = None
    data: Dict[int, Question]


data = {
    "name": "Тестовый опрос",
    "id": "BigInteger | None",
    "data": {
        1: {
            "question": "Назовите ваш имя",
            "ansvers": {
                1: "Илья",
                2: "Вадим",
                3: "Миша",
            },
        },
        2: {
            "question": "Назовите ваш пол",
            "ansvers": {
                1: "М",
                2: "Ж",
            },
        },
    },
}


@records_router.post("/create-survey")
async def create_survey(survey: Survey, db: Session = Depends(get_db)):
    """Функция создания нового опроса

    Args:
        survey (Survey): _description_

    Raises:
        HTTPException: _description_

    Returns:
        int: id_new_surveu
    """
    survey_exists = (
        db.query(CustomerAction).filter(CustomerAction.name == survey.name).first()
    )
    if survey_exists:
        raise HTTPException(
            status_code=400, detail="Survey with this name already exists"
        )

    new_survey = CustomerAction(name=survey.name)
    db.add(new_survey)
    db.commit()
    db.refresh(new_survey)

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
async def create_survey(survey_id: int, db: Session = Depends(get_db)):
    """Функция создания нового опроса

    Args:
        survey (Survey): _description_

    Raises:
        HTTPException: _description_

    Returns:
        int: id_new_surveu
    """

    survey_id = db.query(CustomerAction).get(survey_id)
    if not (survey_id):
        return JSONResponse(
            status_code=200, content={"status": False, "message": "Опросник не найде"}
        )
    return JSONResponse(status_code=200, content={"status": True, "data": data})


@records_router.get("/customer_actions_with_question_and_answer")
async def get_customer_actions_with_question_and_answer_route(
    db: Session = Depends(get_db),
):

    result = (
        db.query(CustomerAction)
        .join(Question, CustomerAction.id == Question.customer_id)
        .all()
    )

    return JSONResponse(status_code=200, content={"customer_id": result.customer_id})


# ======================================
