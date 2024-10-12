from fastapi import APIRouter, Header, Response, status, Request
from models import User
from typing import Annotated
from auth import decode_jwt
from utils import hash_password

router = APIRouter(prefix="/seed", tags=["Seed"])


@router.post("/create-admin")
async def create_admin(
    authorization: Annotated[str, Header()], request: Request, response: Response
):
    app = request.app
    token = authorization.split(" ")[1]

    tokenPayload = decode_jwt(token)

    if "canCreateAdmin" not in tokenPayload:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"success": False, "message": "Unauthorized"}

    if not tokenPayload["canCreateAdmin"]:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"success": False, "message": "Unauthorized"}

    # remove current admin if there is any
    await app.database["users"].delete_many({"role": "admin"})

    # create new admin
    password = "admin"
    hashed_password = hash_password(password)

    admin = User(
        name="Admin", email="admin@chatbot.com", password=hashed_password, role="admin"
    )

    result = await app.database["users"].insert_one(admin.model_dump())

    if not result:
        return {"success": False, "message": "Could not create admin"}

    if not result.acknowledged:
        return {"success": False, "message": "Could not create admin"}

    return {"message": "Admin created successfully"}
