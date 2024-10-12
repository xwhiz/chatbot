from fastapi import APIRouter, Response, status, Body, Request
from models.user import User
from utils import hash_password
from auth import sign_jwt

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register")
async def register(user: User, request: Request, response: Response):
    app = request.app

    if user.role == "admin":
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {
            "success": False,
            "message": "Cannot create admin user",
        }

    fetched_user = await app.database["users"].find_one({"email": user.email})
    if fetched_user:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {
            "success": False,
            "message": "User already exists, try logging in instead",
        }

    user.password = hash_password(user.password)
    user.accessible_docs = ["all"]
    result = await router.database["users"].insert_one(user.model_dump())

    if not result:
        return {"success": False, "message": "Could not create user"}

    if not result.acknowledged:
        return {"success": False, "message": "Could not create user"}

    response.status_code = status.HTTP_201_CREATED
    return {
        "success": True,
        "message": "User created successfully",
        "data": sign_jwt(
            {
                "name": user.name,
                "email": user.email,
                "role": user.role,
            }
        ),
    }


@router.post("/login")
async def login_user(
    request: Request,
    response: Response,
    email: str = Body(...),
    password: str = Body(...),
):
    app = request.app
    user = await app.database["users"].find_one({"email": email})

    if not user:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"success": False, "message": "Invalid credentials"}

    if not user["password"] == hash_password(password):
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"success": False, "message": "Invalid credentials"}

    return {
        "success": True,
        "message": "User logged in successfully",
        "data": sign_jwt(
            {
                "name": user["name"],
                "email": user["email"],
                "role": user["role"],
            }
        ),
    }


@router.post("change-name")
async def change_name(request: Request, response: Response):
    app = request.app

    payload = request.state.payload
    body = await request.json()

    if "name" not in body:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"success": False, "message": "Name is required"}

    if "password" not in body:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"success": False, "message": "Password is required"}

    user = await app.database["users"].find_one({"email": payload["email"]})

    if not user:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"success": False, "message": "User not found"}

    if not user["password"] == hash_password(body["password"]):
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"success": False, "message": "Invalid credentials"}

    new_name = body["name"]

    result = await app.database["users"].update_one(
        {"email": payload["email"]}, {"$set": {"name": new_name}}
    )

    if not result:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"success": False, "message": "Could not update name"}

    if not result.acknowledged:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"success": False, "message": "Could not update name"}

    return {"success": True, "message": "Name updated successfully"}


@router.post("/change-password")
async def change_password(request: Request, response: Response):
    app = request.app
    payload = request.state.payload
    body = await request.json()

    if "currentPassword" not in body:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"success": False, "message": "Old password is required"}

    if "newPassword" not in body:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"success": False, "message": "New password is required"}

    user = await app.database["users"].find_one({"email": payload["email"]})

    if not user:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"success": False, "message": "User not found"}

    if not user["password"] == hash_password(body["currentPassword"]):
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"success": False, "message": "Invalid credentials"}

    new_password = hash_password(body["newPassword"])

    result = await app.database["users"].update_one(
        {"email": payload["email"]}, {"$set": {"password": new_password}}
    )

    if not result:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"success": False, "message": "Could not update password"}

    if not result.acknowledged:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"success": False, "message": "Could not update password"}

    return {"success": True, "message": "Password updated successfully"}
