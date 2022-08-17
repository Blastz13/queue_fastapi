import datetime

from pydantic import BaseModel, validator
from user.schemas import UserProfileRead


class ChatRoomCreate(BaseModel):
    title: str
    is_public: bool

    class Config:
        orm_mode = True


class ChatRoomRead(ChatRoomCreate):
    id: int
    create_date: datetime.datetime
    admins: list[UserProfileRead]
    users: list[UserProfileRead]
    is_public: bool

    class Config:
        orm_mode = True


class ChatRoomUpdate(ChatRoomCreate):
    pass


class ChatMessage(BaseModel):
    message: str
    user: UserProfileRead

    @validator('message')
    def validate_password(cls, value):
        if len(value) <= 0:
            raise ValueError('Message must not be empty')
        return value


class JoinTokenCreate(BaseModel):
    user_id: int
    chat_id: int


class JoinTokenRead(BaseModel):
    id: int
    token: str
    queue_id: int
    date_create: datetime.datetime

    class Config:
        orm_mode = True


class MessageRead(BaseModel):
    id: str
    message: str
    user_id: int
    username: str
