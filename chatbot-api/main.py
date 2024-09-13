from fastapi import Body, FastAPI, Header, Response, status, Request
from typing import Annotated, Optional
from db_lifespan import db_lifespan
from fastapi.middleware.cors import CORSMiddleware

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
            "chat_id": chat.chat_id,
        }

    # we need to update an existing chat
    chat = await app.database["chats"].find_one({"chat_id": chat_id})

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
        {"chat_id": chat_id},
        {"$set": {"messages": chat["messages"]}},
    )

    if not result:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"success": False, "message": "Could not update chat"}

    if not result.acknowledged:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"success": False, "message": "Could not update chat"}

    response.status_code = status.HTTP_200_OK
    return {"success": True, "message": "Chat updated successfully", "chat_id": chat_id}


# I want this as a stream response from the bot
@app.get("/bot-response")
async def bot_response(response: Response, chat_id: str = Body(...)):
    chat = await app.database["chats"].find_one({"chat_id": chat_id})

    if not chat:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"success": False, "message": "Chat not found"}

    return {"success": True, "message": "Bot response", "data": chat["messages"]}


@app.get("/chats/ids")
async def get_chat_ids(request: Request, response: Response):
    payload = request.state.payload
    user_email = payload["email"]

    chats = (
        await app.database["chats"]
        .find({"user_email": user_email})
        .to_list(length=1000)
    )

    chat_ids = [chat["chat_id"] for chat in chats]

    return {
        "success": True,
        "message": "Chat ids retrieved successfully",
        "data": chat_ids,
    }
