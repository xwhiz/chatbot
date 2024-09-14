from fastapi import Body, FastAPI, Header, Response, status, Request
from typing import Annotated
from db_lifespan import db_lifespan
from fastapi.middleware.cors import CORSMiddleware
from bson import ObjectId

from models import User, Chat
from auth import sign_jwt, decode_jwt
from utils import hash_password

app = FastAPI(lifespan=db_lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def verify_token(request, call_next):
    allowed_paths = [
        "/auth/register",
        "/auth/login",
        "/seed/create-admin",
        "/docs",
        "/openapi.json",
    ]
    if request.url.path in allowed_paths:
        response = await call_next(request)
        return response

    # if request is options, we don't need to verify the token
    if request.method == "OPTIONS":
        response = await call_next(request)
        return response

    authorization = request.headers.get("Authorization")

    if not authorization:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)

    token = authorization.split(" ")[1]

    if token == "undefined":
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)

    payload = decode_jwt(token)

    if not payload:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)

    request.state.payload = payload

    return await call_next(request)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/auth/register")
async def register(user: User, response: Response):
    if user.role == "admin":
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {
            "success": False,
            "message": "Cannot create admin user",
        }

    u = await app.database["users"].find_one({"email": user.email})
    if u:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {
            "success": False,
            "message": "User already exists, try logging in instead",
        }

    user.password = hash_password(user.password)
    result = await app.database["users"].insert_one(user.model_dump())

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


@app.post("/auth/login")
async def login_user(
    response: Response, email: str = Body(...), password: str = Body(...)
):
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


@app.post("/seed/create-admin")
async def create_admin(authorization: Annotated[str, Header()], response: Response):
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


# create chat
@app.post("/add-message")
async def add_message(
    response: Response,
    message: str = Body(...),
    chat_id: str = Body(None),
    user_email: str = Body(...),
):
    if chat_id is None:
        # we need to create a new chat
        chat = Chat(
            title=message[:10],
            user_email=user_email,
            messages=[
                {
                    "sender": "human",
                    "message": message,
                }
            ],
        )

        result = await app.database["chats"].insert_one(chat.model_dump())

        if not result:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"success": False, "message": "Could not create chat"}

        if not result.acknowledged:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"success": False, "message": "Could not create chat"}

        response.status_code = status.HTTP_201_CREATED
        return {
            "success": True,
            "message": "Chat created successfully",
            "chat_id": str(result.inserted_id),
        }

    # we need to update an existing chat
    chat = await app.database["chats"].find_one({"_id": ObjectId(chat_id)})

    if not chat:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"success": False, "message": "Chat not found"}

    chat["messages"].append(
        {
            "sender": "human",
            "message": message,
        }
    )

    result = await app.database["chats"].update_one(
        {"_id": ObjectId(chat_id)}, {"$set": chat}
    )

    if not result:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"success": False, "message": "Could not update chat"}

    if not result.acknowledged:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"success": False, "message": "Could not update chat"}

    response.status_code = status.HTTP_200_OK
    return {"success": True, "message": "Chat updated successfully", "chat_id": chat_id}


@app.post("/generate-response")
async def bot_response(
    request: Request,
    response: Response,
):
    body = await request.json()
    chat_id = body.get("chat_id")

    if chat_id is None:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"success": False, "message": "Chat id is required"}

    chat = await app.database["chats"].find_one({"_id": ObjectId(chat_id)})

    if not chat:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"success": False, "message": "Chat not found"}

    message = {
        "sender": "ai",
        "message": "Response from the CHATBOT",
    }

    chat["messages"].append(message)

    result = await app.database["chats"].update_one(
        {"_id": ObjectId(chat_id)}, {"$set": chat}
    )

    if not result:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"success": False, "message": "Could not update chat"}

    if not result.acknowledged:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"success": False, "message": "Could not update chat"}

    response.status_code = status.HTTP_200_OK
    return {
        "success": True,
        "message": "Chat updated successfully",
        "chat_id": chat_id,
        "messageObject": message,
    }


@app.get("/chats/ids")
async def get_chat_ids(request: Request, response: Response):
    payload = request.state.payload
    user_email = payload["email"]

    chats = (
        await app.database["chats"]
        .find({"user_email": user_email})
        .to_list(length=1000)
    )

    chat_details = [
        {
            "id": str(chat["_id"]),
            "title": chat["title"],
        }
        for chat in chats
    ]

    return {
        "success": True,
        "message": "Chat ids retrieved successfully",
        "data": chat_details,
    }


@app.get("/chats/{chat_id}")
async def get_chat(request: Request, response: Response, chat_id: str):
    chat = await app.database["chats"].find_one({"_id": ObjectId(chat_id)})

    if not chat:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"success": False, "message": "Chat not found"}

    chat = {
        "_id": str(chat["_id"]),
        "title": chat["title"],
        "messages": chat["messages"],
        "user_email": chat["user_email"],
    }

    return {
        "success": True,
        "message": "Chat retrieved successfully",
        "data": chat,
    }


@app.delete("/chats/{chat_id}")
async def delete_chat(request: Request, response: Response, chat_id: str):
    chat = await app.database["chats"].find_one({"_id": ObjectId(chat_id)})

    if not chat:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"success": False, "message": "Chat not found"}

    result = await app.database["chats"].delete_one({"_id": ObjectId(chat_id)})

    if not result:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"success": False, "message": "Could not delete chat"}

    if not result.acknowledged:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"success": False, "message": "Could not delete chat"}

    return {
        "success": True,
        "message": "Chat deleted successfully",
    }


@app.get("/users/count")
async def get_users_count(request: Request, response: Response):
    # if it's admin, allow else return unauthorized
    payload = request.state.payload
    if payload["role"] != "admin":
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"success": False, "message": "Unauthorized"}

    count = await app.database["users"].count_documents({})

    return {
        "success": True,
        "message": "Users count retrieved successfully",
        "data": count,
    }


# i have two query parameters too for this method, page and limit use them to paginate the users
@app.get("/users")
async def get_users(
    request: Request, response: Response, page: int = 1, limit: int = 10
):
    # if it's admin, allow else return unauthorized
    payload = request.state.payload
    if payload["role"] != "admin":
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"success": False, "message": "Unauthorized"}

    users = (
        await app.database["users"]
        .find()
        .skip(page * limit)
        .limit(limit)
        .to_list(length=limit)
    )

    users = [
        {
            "_id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "created_at": user["created_at"],
        }
        for user in users
    ]

    return {
        "success": True,
        "message": "Users retrieved successfully",
        "data": users,
    }
