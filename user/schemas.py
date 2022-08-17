import datetime

from pydantic import BaseModel, validator


class UserSignUp(BaseModel):
    username: str
    password: str

    @validator('password')
    def validate_password(cls, value):
        if len(value) < 6:
            raise ValueError('Password must have a minimum length of 6 characters')
        return value

    class Config:
        orm_mode = True


class UserRead(BaseModel):
    id: int
    username: str
    password: str
    create_date: datetime.datetime

    class Config:
        orm_mode = True


class UserLogin(UserSignUp):
    pass


class UserProfileRead(BaseModel):
    id: int
    username: str

    class Config:
        orm_mode = True


class UserIdRead(BaseModel):
    id: int

    class Config:
        orm_mode = True
