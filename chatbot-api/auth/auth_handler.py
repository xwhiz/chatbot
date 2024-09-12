import time
from typing import Dict

from fastapi import HTTPException
import jwt
from decouple import config

JWT_SECRET = config("JWT_SECRET")
JWT_ALGORITHM = config("JWT_ALGORITHM")


def sign_jwt(dict: Dict, canExpire=True) -> Dict:
    payload = dict
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    if not canExpire:
        return {"access_token": token}

    return {"access_token": token, "expires": time.time() + 3600 * 24}


def decode_jwt(token: str) -> Dict:
    try:
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return decoded_token
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="Invalid token")
