from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from uuid import uuid4
from sqlalchemy.orm import Session

from riche_questionnaire_back_end.db import get_db

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
