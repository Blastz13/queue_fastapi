from fastapi import Depends, WebSocket, WebSocketDisconnect, APIRouter
from sqlalchemy.orm import Session

from db import get_db
from chat.consumers import ConnectionChatManager
from queue_room.models import User
from user.jwt_handler import decode_jwt
from mongo_db import database
from . import schemas

chat_router = APIRouter(prefix="/chat", tags=["Chat"])

manager = ConnectionChatManager()


def message_serializer(data) -> dict:
    return {
        "id": str(data["_id"]),
        "message": data["message"],
        "user_id": data["user_id"],
        "username": data["username"]
    }


@chat_router.websocket("/ws/{queue_room_id}/{client_token}")
async def websocket_endpoint(websocket: WebSocket, queue_room_id: int, client_token: str, db: Session = Depends(get_db)):
    user = decode_jwt(client_token)
    db_user = db.query(User).get(user["user_id"])
    await manager.connect(websocket, queue_room_id, db_user.id)
    collection = database[str(queue_room_id)]
    try:
        while True:
            data = await websocket.receive_text()
            await collection.insert_one({"message": data, "user_id": user["user_id"], "username": db_user.username})
            await manager.send_personal_message({"message": data, "user_id": user["user_id"],
                                                 "username": db_user.username, "is_own_message": True,
                                                 "action": "messageChat"}, websocket)
            await manager.broadcast({"message": data, "user_id": user["user_id"],
                                     "username": db_user.username, "is_own_message": False, "action": "messageChat"},
                                    queue_room_id, user["user_id"], websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, queue_room_id)


@chat_router.get("/{queue_id}", response_model=list[schemas.MessageRead])
async def get_all_chat_rooms(queue_id: int):
    collection = database[str(queue_id)]
    messages = []
    async for document in collection.find().sort("_id", -1).limit(20):
        messages.append(message_serializer(document))
    return messages
