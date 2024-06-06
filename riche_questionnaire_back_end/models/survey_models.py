from sqlalchemy import Column, ForeignKey, Integer, String, Text, BigInteger
from sqlalchemy.orm import relationship
from ..db import Base


class CustomerAction(Base):
    __tablename__ = "survey_customer_actions"
    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(Text)

    questions = relationship("Question", back_populates="customer_action")


class Question(Base):
    __tablename__ = "survey_questions"
    id = Column(BigInteger, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("survey_customer_actions.id"))
    text = Column(Text)
    ordering = Column(Integer)

    customer_action = relationship("CustomerAction", back_populates="questions")
    answers = relationship("AnswerOption", back_populates="question")


class AnswerOption(Base):
    __tablename__ = "survey_answer_options"
    id = Column(BigInteger, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("survey_questions.id"))
    text = Column(Text)
    ordering = Column(Integer)

    question = relationship("Question", back_populates="answers")
