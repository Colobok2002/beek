from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from .db import Base

class CustomerAction(Base):
    __tablename__ = 'customer_actions'
    id = Column(Integer, primary_key=True, index=True)
    # тут нужны поля для модели CustomerAction

class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True, index=True)
    # тут нужны  поля для модели Question

class AnswerOption(Base):
    __tablename__ = 'answer_options'
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey('questions.id'))
    # тут нужны поля для модели AnswerOption

# ниже метод для выполнения JOIN операции между таблицами "customer actions", "question" и "answer option"
def get_customer_actions_with_question_and_answer(session):
    return session.query(CustomerAction).\
        join(Question).join(AnswerOption).all()