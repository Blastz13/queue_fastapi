from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .jwt_handler import decode_jwt


class JwtBearer(HTTPBearer):
    def __init__(self, auto_Error: bool = True):
        super(JwtBearer, self).__init__(auto_error=auto_Error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(JwtBearer, self).__call__(request)
        print(self.verify_jwt(request))
        if credentials and self.verify_jwt(request):
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code=403, detail="Invalid or Expired token!")
            return credentials.credentials
        else:
            raise HTTPException(status_code=401, detail="Invalid or Expired token!")

    @classmethod
    def verify_jwt(cls, request: Request):
        is_token_valid = False
        scheme, _, param = request.headers.get("Authorization").partition(" ")
        payload = decode_jwt(param)
        if not payload.get("error"):
            is_token_valid = True
        return is_token_valid


async def get_current_user(token: str = Depends(JwtBearer())) -> dict:
    return decode_jwt(token)
