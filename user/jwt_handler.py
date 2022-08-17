import os
import time
import jwt

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")


def token_response(token: str):
    return {
        "access_token": token
    }


def sign_jwt(user_id: int):
    payload = {
        "user_id": user_id,
        "expires": time.time() + 600*600
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token_response(token)


def decode_jwt(token: str):
    try:
        decode_token = jwt.decode(token, JWT_SECRET, algorithms=JWT_ALGORITHM)
        return decode_token if decode_token["expires"] >= time.time() else None
    except Exception as e:
        return {"error": str(e)}
