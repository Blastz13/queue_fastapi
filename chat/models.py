from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean

from db import Base
import datetime


class ChatRoom(Base):
    __tablename__ = 'chat_room'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    create_date = Column(DateTime, default=datetime.datetime.now())
    queue_id = Column(Integer, ForeignKey('queue.id'))
