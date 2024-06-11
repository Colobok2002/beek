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
async def create_survey(survey: SurveyValid, db: Session = Depends(get_db)):
    """Функция создания нового опроса и проверка изменений"""

    # Если есть ID опроса, то обновляем существующий опрос
    if survey.id:
        existing_survey = db.query(CustomerAction).get(survey.id)
        if existing_survey:
            # Существующие вопросы для удаления тех, которые больше не нужны
            existing_questions = db.query(Question).filter(Question.customer_id == survey.id).all()
            existing_question_ids = {q.id for q in existing_questions}

            # Новый набор вопросов
            new_question_ids = set()

            # Проверяем и обновляем вопросы
            for question_order, question_data in survey.data.items():
                if question_data.id:
                    existing_question = db.query(Question).get(question_data.id)
                    if existing_question:
                        existing_question.text = question_data.question
                        existing_question.ordering = question_order
                        db.commit()
                        new_question_ids.add(existing_question.id)
                    else:
                        # Создаем новый вопрос, если не найден
                        new_question = Question(
                            customer_id=existing_survey.id,
                            text=question_data.question,
                            ordering=question_order,
                        )
                        db.add(new_question)
                        db.commit()
                        db.refresh(new_question)
                        question_data.id = new_question.id
                        new_question_ids.add(new_question.id)
                else:
                    # Создаем новый вопрос, если ID нет
                    new_question = Question(
                        customer_id=existing_survey.id,
                        text=question_data.question,
                        ordering=question_order,
                    )
                    db.add(new_question)
                    db.commit()
                    db.refresh(new_question)
                    question_data.id = new_question.id
                    new_question_ids.add(new_question.id)

                # Существующие ответы для удаления тех, которые больше не нужны
                existing_answers = db.query(AnswerOption).filter(AnswerOption.question_id == question_data.id).all()
                existing_answer_ids = {a.id for a in existing_answers}

                # Новый набор ответов
                new_answer_ids = set()

                # Проверяем и обновляем варианты ответов
                for ans_order, ans_data in question_data.answers.items():
                    if ans_data.id:
                        existing_answer = db.query(AnswerOption).get(ans_data.id)
                        if existing_answer:
                            existing_answer.text = ans_data.answer
                            existing_answer.ordering = ans_order
                            db.commit()
                            new_answer_ids.add(existing_answer.id)
                        else:
                            # Создаем новый вариант ответа, если не найден
                            new_answer = AnswerOption(
                                question_id=question_data.id,
                                text=ans_data.answer,
                                ordering=ans_order,
                            )
                            db.add(new_answer)
                            db.commit()
                            db.refresh(new_answer)
                            ans_data.id = new_answer.id
                            new_answer_ids.add(new_answer.id)
                    else:
                        # Создаем новый вариант ответа, если ID нет
                        new_answer = AnswerOption(
                            question_id=question_data.id,
                            text=ans_data.answer,
                            ordering=ans_order,
                        )
                        db.add(new_answer)
                        db.commit()
                        db.refresh(new_answer)
                        ans_data.id = new_answer.id
                        new_answer_ids.add(new_answer.id)

                # Удаление старых ответов, которые больше не нужны
                for answer in existing_answers:
                    if answer.id not in new_answer_ids:
                        db.delete(answer)
                        db.commit()

            # Удаление старых вопросов, которые больше не нужны
            for question in existing_questions:
                if question.id not in new_question_ids:
                    db.delete(question)
                    db.commit()

            return JSONResponse(status_code=200, content={"change": True})

    # Если ID опроса нет, то создаем новый опрос
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
        question_data.id = new_question.id

        for ans_order, ans_data in question_data.answers.items():
            new_answer = AnswerOption(
                question_id=new_question.id,
                text=ans_data.answer,
                ordering=ans_order,
            )
            db.add(new_answer)
            db.commit()
            db.refresh(new_answer)
            ans_data.id = new_answer.id

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
