import json

from starlette.websockets import WebSocket

from db import SessionLocal
from queue_room.models import QueueTicket
from queue_room.schemas import QueueTicketRead


class ConnectionChatManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = {}
        self.db = SessionLocal()

    def is_current_user_access(self, queue_room_id: int, user_id: int):
        # return self.db.query(User).get(user_id) in self.db.query(Queue).get(queue_room_id).users
        return True

    async def connect(self, websocket: WebSocket, queue_room_id: int, user_id: int):
        await websocket.accept()
        if self.is_current_user_access(queue_room_id, user_id):
            if queue_room_id not in self.active_connections.keys():
                self.active_connections[queue_room_id] = []
            self.active_connections[queue_room_id].append(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_json(message)

    def disconnect(self, websocket: WebSocket, queue_room_id: int):
        self.active_connections[queue_room_id].remove(websocket)

    async def broadcast(self, message: str, queue_room_id: int, user_id: int, websocket: WebSocket = None):
        if self.is_current_user_access(queue_room_id, user_id):
            for connection in self.active_connections[queue_room_id]:
                if websocket is not None:
                    if connection != websocket:
                        await connection.send_json(message)
                else:
                    await connection.send_json(message)

    async def broadcast_update_current_queue(self, queue_id, user_id):
        payload = {"data": None}
        db_queue_ticket = QueueTicket.get_current_queue_ticket(queue_id, user_id)
        if db_queue_ticket:
            temp = QueueTicketRead.from_orm(db_queue_ticket).dict()
            payload["data"] = json.loads(json.dumps(temp, default=str))
        payload["action"] = "updateCurrentQueue"
        await self.broadcast(message=payload, queue_room_id=queue_id, user_id=user_id)

    async def broadcast_update_list_queue(self, queue_id, user_id):
        payload = {}
        temp = []
        for obj in QueueTicket.get_current_queue(queue_id, user_id):
            temp.append(QueueTicketRead.from_orm(obj).dict())
        payload["data"] = json.loads(json.dumps(temp, default=str))
        payload["action"] = "updateListQueue"
        await self.broadcast(message=payload, queue_room_id=queue_id, user_id=user_id)
