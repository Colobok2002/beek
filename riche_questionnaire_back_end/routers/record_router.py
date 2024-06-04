from fastapi import HTTPException
from pydantic import BaseModel
from uuid import uuid4

# Пример простой БД в памяти для хранения данных
database = {}

# Модель для передаваемых данных
class DataIn(BaseModel):
    data: str

async def create_record(data_in: DataIn):
    record_id = str(uuid4())
    database[record_id] = data_in.data
    return {"uuid": record_id}

async def read_record(record_id: str):
    if record_id not in database:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    return {"data": database[record_id]}