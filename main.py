from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from chat.api import chat_router
from user.api import user_router
from queue_room.api import queue_router

app = FastAPI()
app.include_router(user_router)
app.include_router(chat_router)
app.include_router(queue_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
