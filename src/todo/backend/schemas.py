from pydantic import BaseModel
from datetime import datetime

class TaskBase(BaseModel):
    name: str

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    name: str | None = None
    status: str | None = None

class Task(TaskBase):
    id: int
    status: str
    created_at: datetime

    class Config:
        orm_mode = True
