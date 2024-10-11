from datetime import datetime
import json
import time
from fastapi import (
    Body,
    FastAPI,
    File,
    Form,
    HTTPException,
    Header,
    Response,
    UploadFile,
    status,
    Request,
)
from typing import Annotated
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from bson import ObjectId
from decouple import config
from qdrant_client import QdrantClient

from lifespan import lifespan
from utils import hash_password
from models import User, Chat
from auth import decode_jwt

from routers import auth, chats, documents

app = FastAPI(lifespan=lifespan)


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
        "/generate-response",
        "/health",
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


app.include_router(auth.router)
app.include_router(chats.router)
app.include_router(documents.router)


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


async def generate_response(chat_id: str):
    chat = await app.database["chats"].find_one({"_id": ObjectId(chat_id)})
    if not chat:
        return

    last_human_message = None
    for message in reversed(chat["messages"]):
        if message["sender"] == "human":
            last_human_message = message
            break

    if not last_human_message:
        return

    print("Generating response for:", last_human_message["message"])

    # # print(retriever.invoke(last_human_message["message"]))
    # print(ensemble_retriever.invoke(last_human_message["message"]))

    try:
        stream = app.qa_chain.stream(last_human_message["message"])
    except Exception as e:
        print("Error in generating response:", e)

        print("Recreating Qdrant client")
        app.client = QdrantClient(path=config("VECTOR_DOC_DB_PATH"))
        stream = app.qa_chain.stream(last_human_message["message"])

    for chunk in stream:
        yield f"data: {json.dumps({'chat_id': chat_id, 'partial_response': chunk}).strip()}\n\n"

    # stream = ollama.chat(
    #     model="llama3.1",
    #     messages=[{"role": "user", "content": last_human_message["message"]}],
    #     stream=True,
    # )

    # for chunk in stream:
    #     yield f"data: {json.dumps({'chat_id': chat_id, 'partial_response': chunk['message']['content']}).strip()}\n\n"

    # words = "This is a streaming response from the chatbot.".split()
    # for word in words:
    #     yield f"data: {json.dumps({'chat_id': chat_id, 'partial_response': word})}\n\n"
    #     await asyncio.sleep(0.05)  # Simulate delay between words


@app.get("/generate-response")
async def bot_response(chat_id: str, token: str):
    payload = decode_jwt(token)

    if not payload:
        return Response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=json.dumps({"success": False, "message": "Unauthorized"}),
        )

    if chat_id is None:
        return Response(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=json.dumps({"success": False, "message": "Chat id is required"}),
        )

    chat = await app.database["chats"].find_one({"_id": ObjectId(chat_id)})
    if not chat:
        return Response(
            status_code=status.HTTP_404_NOT_FOUND,
            content=json.dumps({"success": False, "message": "Chat not found"}),
        )

    return StreamingResponse(generate_response(chat_id), media_type="text/event-stream")


@app.post("/update-chat")
async def update_chat(request: Request):
    body = await request.json()
    chat_id = body.get("chat_id")
    full_message = body.get("full_message")

    if chat_id is None or full_message is None:
        return Response(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=json.dumps(
                {"success": False, "message": "Chat id and full message are required"}
            ),
        )

    message = {
        "sender": "ai",
        "message": full_message,
    }

    result = await app.database["chats"].update_one(
        {"_id": ObjectId(chat_id)}, {"$push": {"messages": message}}
    )

    if not result or not result.acknowledged:
        return Response(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=json.dumps({"success": False, "message": "Could not update chat"}),
        )

    return Response(
        status_code=status.HTTP_200_OK,
        content=json.dumps(
            {
                "success": True,
                "message": "Chat updated successfully",
                "chat_id": chat_id,
                "messageObject": message,
            }
        ),
    )


@app.delete("/users/{user_id}")
async def delete_user_and_all_their_chats(
    request: Request, response: Response, user_id: str
):
    payload = request.state.payload

    if payload["role"] != "admin":
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"success": False, "message": "Unauthorized"}

    user = await app.database["users"].find_one({"_id": ObjectId(user_id)})

    if not user:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"success": False, "message": "User not found"}

    result = await app.database["users"].delete_one({"_id": ObjectId(user_id)})

    # delete all the chats of the user
    await app.database["chats"].delete_many({"user_email": user["email"]})

    if not result:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"success": False, "message": "Could not delete user"}

    if not result.acknowledged:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"success": False, "message": "Could not delete user"}

    return {
        "success": True,
        "message": "User deleted successfully",
    }


@app.get("/users/all-minimal")
async def get_all_users_minimal(request: Request, response: Response):
    payload = request.state.payload

    if payload["role"] != "admin":
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"success": False, "message": "Unauthorized"}

    users = await app.database["users"].find().to_list(length=1000)

    users = [
        {
            "_id": str(user["_id"]),
            "created_at": user["created_at"],
        }
        for user in users
    ]

    return {
        "success": True,
        "message": "Users retrieved successfully",
        "data": users,
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


@app.get("/users")
async def get_users(
    request: Request, response: Response, page: int = 0, limit: int = 10
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


# A health endpoint
@app.get("/health")
async def health(response: Response):
    response.status_code = status.HTTP_200_OK
    return {"status": "ok"}
