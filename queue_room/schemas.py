import datetime

from pydantic import BaseModel
from user.schemas import *


class QueueRoomRead(BaseModel):
    id: int
    title: str
    date_create: datetime.datetime
    users: list[UserIdRead]
    admins: list[UserIdRead]

    class Config:
        orm_mode = True


class QueueCreate(BaseModel):
    title: str

    class Config:
        orm_mode = True


class QueueUpdate(QueueCreate):
    pass


class QueueTicketRead(BaseModel):
    id: int
    date_create: datetime.datetime
    user: UserProfileRead
    queue_id: int
    status: str
    date_update_status: datetime.datetime

    class Config:
        orm_mode = True


class QueueTicketReadList(BaseModel):
    __root__: list[QueueTicketRead]

    class Config:
        orm_mode = True


class UserInfoQueueRoomRead(BaseModel):
    id: int
    username: str
    is_admin: bool
