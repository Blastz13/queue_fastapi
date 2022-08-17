from fastapi import HTTPException
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Session, joinedload

from db import Base, SessionLocal
import datetime

from queue_room.schemas import QueueUpdate

db = SessionLocal()


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    date_create = Column(DateTime, default=datetime.datetime.now())
    queues = relationship('Queue', secondary='queue_user', back_populates='users', cascade="all,delete")

    @classmethod
    def get(cls, id: int):
        return db.query(cls).get(id)

    @classmethod
    def get_or_404(cls, id: int):
        db_user = db.query(cls).get(id)
        if not db_user:
            raise HTTPException(status_code=404, detail="Not found")
        return db_user


class Queue(Base):
    __tablename__ = 'queue'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    date_create = Column(DateTime, default=datetime.datetime.now())
    chat_room = relationship("ChatRoom", uselist=False, backref="queue")
    join_token = relationship("JoinToken", uselist=False, backref="queue")
    admins = relationship('User', secondary='queue_admin', back_populates='queues', cascade="all, delete")
    users = relationship('User', secondary='queue_user', back_populates='queues', cascade="all, delete")

    @classmethod
    def all(cls):
        return db.query(cls).all()

    @classmethod
    def get(cls, id: int):
        return db.query(cls).get(id)

    @classmethod
    def get_or_404(cls, id: int):
        db_queue = db.query(cls).get(id)
        if not db_queue:
            raise HTTPException(status_code=404, detail="Not found")
        return db_queue

    def update(self, queue_update: QueueUpdate):
        for var, value in vars(queue_update).items():
            setattr(self, var, value)
        db.commit()
        return self

    def remove(self):
        db.delete(self)
        # db.query(QueueUser).filter(QueueUser.queue_id == self.id).delete(synchronize_session=False)
        # db.query(QueueAdmin).filter(QueueAdmin.queue_id == self.id).delete(synchronize_session=False)
        # db.query(JoinToken).filter(JoinToken.queue_id == self.id).delete(synchronize_session=False)
        db.commit()


class QueueTicket(Base):
    __tablename__ = 'queue_ticket'
    id = Column(Integer, primary_key=True)
    date_create = Column(DateTime, default=datetime.datetime.now())
    user_id = Column(Integer, ForeignKey('user.id'))
    queue_id = Column(Integer, ForeignKey('queue.id', ondelete='CASCADE'))
    user = relationship('User', backref='queue_ticket')
    status = Column(String, default="wait", nullable=False)
    date_update_status = Column(DateTime, default=datetime.datetime.now(), onupdate=datetime.datetime.now())

    @classmethod
    def get_current_queue_ticket(cls, queue_id, user_id):
        db_queue = Queue.get_or_404(queue_id)
        db_user = User.get(user_id)
        if db_user in db_queue.users:
            db_current_queue_ticket = db.query(QueueTicket).filter(QueueTicket.queue_id == queue_id) \
                .filter(QueueTicket.status == "in_process").options(joinedload(QueueTicket.user)).first()
            return db_current_queue_ticket
        else:
            raise HTTPException(status_code=403, detail="You are not the user of this queue")

    @classmethod
    def get_current_queue(cls, queue_id, user_id):
        db_queue = Queue.get_or_404(queue_id)
        db_user = User.get(user_id)
        if db_user in db_queue.users:
            db_queue_tickets = db.query(QueueTicket).filter(QueueTicket.queue_id == queue_id) \
                .filter(QueueTicket.status == "wait").order_by("id").all()
            return db_queue_tickets
        else:
            raise HTTPException(status_code=403, detail="You are not the user of this queue")


class QueueUser(Base):
    __tablename__ = "queue_user"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    queue_id = Column(Integer, ForeignKey('queue.id', ondelete='CASCADE'))


class QueueAdmin(Base):
    __tablename__ = "queue_admin"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    queue_id = Column(Integer, ForeignKey('queue.id', ondelete='CASCADE'))


class JoinToken(Base):
    __tablename__ = 'join_token'
    id = Column(Integer, primary_key=True)
    token = Column(String, unique=True, nullable=False)
    queue_id = Column(Integer, ForeignKey('queue.id'), nullable=False)
    date_create = Column(DateTime, default=datetime.datetime.now())

    @classmethod
    def get_or_404(cls, token: str):
        db_token = db.query(cls).filter(cls.token == token).first()
        if not db_token:
            raise HTTPException(status_code=404, detail="Not found")
        return db_token

    @classmethod
    def get_or_create(cls, token: str, queue_id: int):
        db_token = db.query(cls).filter(cls.queue_id == queue_id).first()
        if db_token is None:
            db_token = cls(token=token, queue_id=queue_id)
            db.add(db_token)
            db.commit()
            db.refresh(db_token)
            return db_token
        return db_token
