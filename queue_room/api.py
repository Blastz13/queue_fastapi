import json
from http.client import HTTPException
from uuid import uuid4

from fastapi import Depends, APIRouter
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload
from starlette.websockets import WebSocket, WebSocketDisconnect

from chat.models import ChatRoom
from chat.schemas import JoinTokenRead
from db import get_db

from user import schemas
from user.jwt_bearer import JwtBearer, get_current_user
from chat.api import manager
from .models import *
from .schemas import *

queue_router = APIRouter(prefix="", tags=["Queue Room"])


# @queue_router.websocket("/ws/{queue_id}/{client_token}")
# async def websocket_endpoint(websocket: WebSocket, queue_id: int, client_token: str):
#     await manager.connect(websocket, queue_id, client_token)
#     try:
#         while True:
#             await websocket.receive_text()
#             pass
#     except WebSocketDisconnect:
#         manager.disconnect(websocket, queue_id)


@queue_router.get("/queue_room/list", response_model=list[QueueRoomRead])
async def get_all_queues_room():
    db_queues = Queue.all()
    return db_queues


@queue_router.get("/queue_room/entered", response_model=list[QueueRoomRead], dependencies=[Depends(JwtBearer())])
async def get_entered_queues_room(user: get_current_user = Depends()):
    db_queues = User.get_or_404(user["user_id"]).queues
    return db_queues


@queue_router.post("/queue_room", response_model=QueueRoomRead, dependencies=[Depends(JwtBearer())])
async def create_queue_room(queue: QueueCreate, db: Session = Depends(get_db), user: get_current_user = Depends()):
    db_queue = Queue(title=queue.title)
    db.add(db_queue)
    db.commit()
    db.refresh(db_queue)

    db_queue_user = QueueUser(user_id=user["user_id"], queue_id=db_queue.id)
    db.add(db_queue_user)
    # db.commit()

    db_queue_admin = QueueAdmin(user_id=user["user_id"], queue_id=db_queue.id)
    db.add(db_queue_admin)
    # db.commit()

    db_chat_room = ChatRoom(title=db_queue.title, queue_id=db_queue.id)
    db.add(db_chat_room)
    db.commit()

    return db_queue


@queue_router.get("/queue_room/{queue_id}", response_model=QueueRoomRead, dependencies=[Depends(JwtBearer())])
async def get_queue_room(queue_id: int):
    db_chat_room = Queue.get_or_404(queue_id)
    return db_chat_room


@queue_router.get("/queue_room/generate_token/{queue_id}", response_model=JoinTokenRead, dependencies=[Depends(JwtBearer())])
async def generate_invitation_token_queue_room(queue_id: str, user: get_current_user = Depends()):
    db_user = User.get(user["user_id"])
    db_queue = Queue.get_or_404(queue_id)
    if db_user in db_queue.users:
        db_join_token = JoinToken.get_or_create(token=str(uuid4()), queue_id=db_queue.id)
        return db_join_token
    else:
        raise HTTPException(status_code=403, detail="You are not a member of this chat")


@queue_router.get("/queue_room/join_queue/{token}", response_model=QueueRoomRead, dependencies=[Depends(JwtBearer())])
async def join_in_queue_room(token: str, db: Session = Depends(get_db), user: get_current_user = Depends()):
    db_join_token = JoinToken.get_or_404(token)
    db_user = User.get(user["user_id"])
    db_queue_room = Queue.get_or_404(db_join_token.queue_id)
    db_queue_user = QueueUser(user_id=db_user.id, queue_id=db_queue_room.id)
    db.add(db_queue_user)
    db.commit()
    db.refresh(db_queue_user)
    return db_queue_room


@queue_router.put("/queue_room/{queue_id}", response_model=QueueRoomRead, dependencies=[Depends(JwtBearer())])
async def update_queue_room(chat_id: int, queue: QueueUpdate, user: get_current_user = Depends()):
    db_queue = Queue.get_or_404(chat_id)
    db_user = User.get(user["user_id"])
    if db_user in db_queue.admins:
        return db_queue.update(queue)
    else:
        raise HTTPException(status_code=403, detail="You are not the administrator of this chat")


@queue_router.delete("/queue_room/{queue_id}", status_code=204, dependencies=[Depends(JwtBearer())])
async def delete_queue_room(queue_id: int, user: get_current_user = Depends()):
    db_queue = Queue.get_or_404(queue_id)
    db_user = User.get(user["user_id"])
    if db_user in db_queue.admins:
        db_queue.remove()
        return {}
    else:
        raise HTTPException(status_code=403, detail="You are not the administrator of this chat")


@queue_router.delete("/queue_room/{queue_id}/leave", status_code=204, dependencies=[Depends(JwtBearer())])
async def leave_from_queue_room(queue_id: int, db: Session = Depends(get_db), user: get_current_user = Depends()):
    db.query(QueueUser).filter(QueueUser.queue_id == queue_id) \
        .filter(QueueUser.user_id == user["user_id"]).delete()
    db.commit()
    return {}


@queue_router.delete("/queue_room/{queue_id}/kick", status_code=204, dependencies=[Depends(JwtBearer())])
async def kick_from_queue_room(queue_id: int, target_user: schemas.UserIdRead, db: Session = Depends(get_db),
                              user: get_current_user = Depends()):
    db_queue = Queue.get_or_404(queue_id)
    db_user = User.get(user["user_id"])
    if db_user in db_queue.admins:
        db.query(QueueUser).filter(QueueUser.queue_id == queue_id) \
            .filter(QueueUser.user_id == target_user.id).delete()
        db.commit()
        return {}
    else:
        raise HTTPException(status_code=403, detail="You are not the administrator of this chat")


@queue_router.post("/{queue_id}/", response_model=QueueTicketRead, dependencies=[Depends(JwtBearer())])
async def add_to_queue(queue_id: int, db: Session = Depends(get_db), user: get_current_user = Depends()):
    db_queue = Queue.get_or_404(queue_id)
    db_user = User.get(user["user_id"])
    if db_user in db_queue.users:
        db_queue_ticket_wait = db.query(QueueTicket).filter(QueueTicket.queue_id == db_queue.id)\
                                .filter((QueueTicket.status == "wait") | (QueueTicket.status == "in_process"))
        if not db_queue_ticket_wait.filter(QueueTicket.user_id == db_user.id).all():
            if db_queue_ticket_wait.count() > 0:
                db_queue_ticket = QueueTicket(user_id=db_user.id, queue_id=db_queue.id)
            else:
                db_queue_ticket = QueueTicket(user_id=db_user.id, queue_id=db_queue.id, status="in_process")
            db.add(db_queue_ticket)
            db.commit()

            await manager.broadcast_update_current_queue(queue_id, user["user_id"])
            await manager.broadcast_update_list_queue(queue_id, user["user_id"])

            return db_queue_ticket
        else:
            raise HTTPException(status_code=400, detail="You already consist of queue")
    else:
        raise HTTPException(status_code=403, detail="You are not the user of this queue room")


@queue_router.put("/{queue_id}/", status_code=204, dependencies=[Depends(JwtBearer())])
async def update_status_in_queue(queue_id: int, db: Session = Depends(get_db),
                              user: get_current_user = Depends()):
    db_queue = Queue.get_or_404(queue_id)
    db_user = User.get(user["user_id"])
    if db_user in db_queue.users:
        db_queue_ticket = db.query(QueueTicket).filter(QueueTicket.queue_id == db_queue.id) \
                             .filter(QueueTicket.user_id == db_user.id).order_by(desc(QueueTicket.id)).first()

        if db_queue_ticket.status == "in_process":
            db_queue_ticket.status = "passed"
            db.commit()

            db_queue_ticket = db.query(QueueTicket).filter(QueueTicket.queue_id == db_queue.id) \
                .filter(QueueTicket.status == "wait").first()
            if db_queue_ticket:
                db_queue_ticket.status = "in_process"
                db.commit()

            await manager.broadcast_update_current_queue(queue_id, user["user_id"])
            await manager.broadcast_update_list_queue(queue_id, user["user_id"])

            return {}
    else:
        raise HTTPException(status_code=403, detail="You are not the user of this queue")


@queue_router.get("/queue/{queue_id}/current", response_model=QueueTicketRead, dependencies=[Depends(JwtBearer())])
async def get_current_queue_ticket(queue_id: int, user: get_current_user = Depends()):
    return QueueTicket.get_current_queue_ticket(queue_id, user["user_id"])


@queue_router.get("/queue/{queue_id}/", response_model=list[QueueTicketRead], dependencies=[Depends(JwtBearer())])
async def get_all_current_queue(queue_id: int, user: get_current_user = Depends()):
    return QueueTicket.get_current_queue(queue_id=queue_id, user_id=user["user_id"])


@queue_router.delete("/queue/{queue_id}/", status_code=200, dependencies=[Depends(JwtBearer())])
async def delete_from_queue(queue_id: int, db: Session = Depends(get_db), user: get_current_user = Depends()):
    db_queue = Queue.get_or_404(queue_id)
    db_user = User.get(user["user_id"])
    if db_user in db_queue.users:
        db_queue_ticket = db.query(QueueTicket).filter(QueueTicket.queue_id == queue_id)\
            .filter(QueueTicket.user_id == db_user.id).order_by(desc(QueueTicket.id)).first()
        db.delete(db_queue_ticket)
        db.commit()
        await manager.broadcast_update_list_queue(queue_id, user["user_id"])

        return {}
    else:
        raise HTTPException(status_code=403, detail="You are not the user of this queue")


@queue_router.get("/queue_room/{queue_id}/", response_model=UserInfoQueueRoomRead, dependencies=[Depends(JwtBearer())])
async def get_user_info_in_queue_room(queue_id: int, user: get_current_user = Depends()):
    db_queue = Queue.get_or_404(queue_id)
    db_user = User.get(user["user_id"])
    is_admin = False
    if db_user in db_queue.admins:
        is_admin = True
    return UserInfoQueueRoomRead(**dict(UserProfileRead.from_orm(db_user)), is_admin=is_admin)
