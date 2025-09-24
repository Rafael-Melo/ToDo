from pydantic import BaseModel
from datetime import datetime

# -------- Tasks --------
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

# -------- Users --------
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int

    class Config:
        from_attributes = True


# -------- Auth --------
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"