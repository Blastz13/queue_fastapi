from fastapi import HTTPException, APIRouter, Depends

from werkzeug.security import generate_password_hash, check_password_hash

from sqlalchemy.orm import Session

from fastapi.encoders import jsonable_encoder

from queue_room.models import User
from user.jwt_handler import sign_jwt

from .schemas import *
from db import get_db

user_router = APIRouter(prefix="/auth", tags=["auth"])


@user_router.post('/signup')
async def sign_up(user: UserSignUp, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user is not None:
        raise HTTPException(status_code=400, detail="User with username already exists")
    db_user = User(username=user.username, password=generate_password_hash(user.password))
    db.add(db_user)
    db.commit()
    return jsonable_encoder(sign_jwt(db_user.id))


@user_router.post('/login')
async def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user is not None and check_password_hash(db_user.password, user.password):
        return jsonable_encoder(sign_jwt(db_user.id))
    else:
        raise HTTPException(status_code=400, detail="Invalid username or password")
