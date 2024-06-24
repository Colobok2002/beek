from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Optional, Union, List
from sqlalchemy.orm import Session
from pydantic import BaseModel

from uuid import uuid4

from riche_questionnaire_back_end.db import get_db
from riche_questionnaire_back_end.models.survey_models import (
    AnswerOption,
    CustomerAction,
    Question,
    SurveyResponse,
)


records_router = APIRouter()
# app = FastAPI()


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
    type: str
    data: Dict[int, QuestionValid]


class AnswerItem(BaseModel):
    question_id: Union[int, str]
    answer_id: Union[int, str]


class AnswerData(BaseModel):
    answers: List[AnswerItem]
    response_uuid: str


data = {
    "name": "Тестовый опрос",
    "id": 3,
    "data": {
        "1": {
            "question": "Назовите ваш пол этот теперь первый",
            "answers": {"1": {"answer": "М"}, "2": {"answer": "Ж"}},
        },
        "2": {
            "id": 2,
            "question": "Назовите ваш имя (Изм вопрос)",
            "answers": {
                "1": {"answer": "Илья"},
                "2": {"answer": "Вадим"},
                "3": {"answer": "Миша"},
            },
        },
        "3": {
            "question": "Новый вопрос",
            "answers": {"1": {"answer": "М"}, "2": {"answer": "Ж"}},
        },
    },
}


@records_router.post("/create-survey")
async def create_survey(survey: SurveyValid, db: Session = Depends(get_db)):
    """Функция создания нового опроса и проверка изменений"""

    if survey.id:
        existing_survey = db.query(CustomerAction).get(survey.id)
        if existing_survey:
            existing_survey.name = survey.name
            existing_survey.type = survey.type
            db.commit()

            existing_questions = (
                db.query(Question).filter(Question.customer_id == survey.id).all()
            )
            new_question_ids = set()
            for question_order, question_data in survey.data.items():
                if question_data.id:
                    existing_question = db.query(Question).get(question_data.id)
                    if existing_question:
                        existing_question.text = question_data.question
                        existing_question.ordering = question_order
                        new_question_ids.add(existing_question.id)
                    else:
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

                existing_answers = (
                    db.query(AnswerOption)
                    .filter(AnswerOption.question_id == question_data.id)
                    .all()
                )
                new_answer_ids = set()

                for ans_order, ans_data in question_data.answers.items():
                    if ans_data.id:
                        existing_answer = db.query(AnswerOption).get(ans_data.id)
                        if existing_answer:
                            existing_answer.text = ans_data.answer
                            existing_answer.ordering = ans_order
                            db.commit()
                            new_answer_ids.add(existing_answer.id)
                        else:
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

                for answer in existing_answers:
                    if answer.id not in new_answer_ids:
                        db.delete(answer)

            for question in existing_questions:
                if question.id not in new_question_ids:
                    db.delete(question)

            db.commit()
            return JSONResponse(status_code=200, content={"change": True})

    new_survey = CustomerAction(name=survey.name, type=survey.type)
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
    survey_data_structure = {
        "name": survey_data.name,
        "id": survey_id,
        "type": survey_data.type,
        "data": {}
    }

    for question in survey_questions:
        answers = (
            db.query(AnswerOption).filter(AnswerOption.question_id == question.id).all()
        )
        answers_dict = {
            answer.ordering: {"answer": answer.text, "id": answer.id}
            for answer in answers
        }

        survey_data_structure["data"][question.ordering] = {
            "id": question.id,
            "question": question.text,
            "answers": answers_dict,
        }

    return JSONResponse(status_code=200, content=survey_data_structure)


data = {
    "name": "Тестовый опрос",
    "id": 3,
    "data": {
        "1": {
            "id": "1",
            "question": "Укажите пол",
            "answers": {
                "1": {"answer": "М", "id": "1", "selekted": False},
                "2": {"answer": "Ж", "id": "2", "selekted": True},
            },
        },
        "2": {
            "id": "2",
            "question": "Назовите ваше имя (Изм вопрос)",
            "answers": {
                "1": {"answer": "Илья", "id": "3"},
                "2": {"answer": "Вадим", "id": "4"},
                "3": {"answer": "Миша", "id": "5"},
            },
        },
        "3": {
            "id": "3",
            "question": "Новый вопрос",
            "answers": {
                "1": {"answer": "М", "id": "6"},
                "2": {"answer": "Ж", "id": "7"},
            },
        },
    },
}


@records_router.post("/submit-answers")
async def submit_answers(answer_data: AnswerData, db: Session = Depends(get_db)):
    """Функция для приема и сохранения ответов на опрос"""

    # dataAnsver = {
    #     "answers": [{"QuestionID": "Айди вопроса", "AnswerId": "Id ответа"}],
    #     "responsUUid": "Случайно генерируется во фронте",
    # }

    for answer in answer_data.answers:
        question = db.query(Question).get(answer.question_id)
        answer_option = db.query(AnswerOption).get(answer.answer_id)

        if not question:
            raise HTTPException(
                status_code=404, detail=f"Question ID {answer.question_id} not found"
            )
        if not answer_option:
            raise HTTPException(
                status_code=404, detail=f"Answer Option ID {answer.answer_id} not found"
            )

        new_response = SurveyResponse(
            response_uuid=answer_data.response_uuid,
            question_id=answer.question_id,
            answer_option_id=answer.answer_id,
        )
        db.add(new_response)

    db.commit()
    return JSONResponse(
        status_code=200, content={"message": "Ответы успешно отправлены!"}
    )


@records_router.get("/get-survey-with-answers")
async def get_survey_with_answers(response_uuid: str, db: Session = Depends(get_db)):
    """Функция получения данных опроса с ответами, включая отметку выбранных ответов"""

    # Пример структуры данных ответа:
    # data = {
    #     "name": "Тестовый опрос",
    #     "id": 3,
    #     "data": {
    #         "1": {
    #             "id": "1",
    #             "question": "Укажите пол",
    #             "answers": {
    #                 "1": {"answer": "М", "id": "1", "selected": False},
    #                 "2": {"answer": "Ж", "id": "2", "selected": True},
    #             },
    #         },
    #         "2": {
    #             "id": "2",
    #             "question": "Назовите ваше имя (Изм вопрос)",
    #             "answers": {
    #                 "1": {"answer": "Илья", "id": "3", "selected": False},
    #                 "2": {"answer": "Вадим", "id": "4", "selected": False},
    #                 "3": {"answer": "Миша", "id": "5", "selected": False},
    #             },
    #         },
    #         "3": {
    #             "id": "3",
    #             "question": "Новый вопрос",
    #             "answers": {
    #                 "1": {"answer": "М", "id": "6", "selected": False},
    #                 "2": {"answer": "Ж", "id": "7", "selected": False},
    #             },
    #         },
    #     },
    # }

    responses = db.query(SurveyResponse).filter(SurveyResponse.response_uuid == response_uuid).all()
    if not responses:
        raise HTTPException(status_code=404, detail="Ответы не найдены для данного UUID")

    survey_id = responses[0].question.customer_action.id
    survey_data = db.query(CustomerAction).get(survey_id)
    if not survey_data:
        raise HTTPException(status_code=404, detail="Опросник не найден в базе данных")

    survey_questions = db.query(Question).filter(Question.customer_id == survey_id).all()
    survey_data_structure = {"name": survey_data.name, "id": survey_id, "data": {}}

    for question in survey_questions:
        answers = db.query(AnswerOption).filter(AnswerOption.question_id == question.id).all()
        answers_dict = {
            answer.ordering: {
                "answer": answer.text,
                "id": answer.id,
                "selected": any(resp.answer_option_id == answer.id for resp in responses)
            } for answer in answers
        }

        survey_data_structure["data"][question.ordering] = {
            "id": question.id,
            "question": question.text,
            "answers": answers_dict,
        }

    return JSONResponse(status_code=200, content=survey_data_structure)
