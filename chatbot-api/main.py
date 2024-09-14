from datetime import datetime
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

from fastapi.responses import FileResponse, JSONResponse
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


# i have two query parameters too for this method, page and limit use them to paginate the users
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


@app.post("/chats/count")
async def get_chats_count(request: Request, response: Response):
    # if it's admin, allow else return unauthorized
    payload = request.state.payload
    if payload["role"] != "admin":
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"success": False, "message": "Unauthorized"}

    body = await request.json()
    user_id = body.get("user_id")

    if not user_id:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"success": False, "message": "User id is required"}

    user = await app.database["users"].find_one({"_id": ObjectId(user_id)})

    if not user:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"success": False, "message": "User not found"}

    user_email = user["email"]

    count = await app.database["chats"].count_documents({"user_email": user_email})

    return {
        "success": True,
        "message": "Chats count retrieved successfully",
        "data": count,
    }


@app.post("/chats")
async def get_chats(
    request: Request, response: Response, page: int = 0, limit: int = 10
):
    # if it's admin, allow else return unauthorized
    payload = request.state.payload
    if payload["role"] != "admin":
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"success": False, "message": "Unauthorized"}

    body = await request.json()
    user_id = body.get("user_id")

    if not user_id:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"success": False, "message": "User id is required"}

    user = await app.database["users"].find_one({"_id": ObjectId(user_id)})

    if not user:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"success": False, "message": "User not found"}

    user_email = user["email"]

    chats = (
        await app.database["chats"]
        .find({"user_email": user_email})
        .skip(page * limit)
        .limit(limit)
        .to_list(length=limit)
    )

    chats = [
        {
            "_id": str(chat["_id"]),
            "title": chat["title"],
            "user_email": chat["user_email"],
            "created_at": chat["created_at"],
        }
        for chat in chats
    ]

    return {
        "success": True,
        "message": "Chats retrieved successfully",
        "data": chats,
    }


@app.get("/chats/all/minimal")
async def get_all_chats_minimal(request: Request, response: Response):
    # if it's admin, allow else return unauthorized
    payload = request.state.payload

    if payload["role"] != "admin":
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"success": False, "message": "Unauthorized"}

    chats = await app.database["chats"].find().to_list(length=1000)

    chats = [
        {
            "_id": str(chat["_id"]),
            "created_at": chat["created_at"],
        }
        for chat in chats
    ]

    return {
        "success": True,
        "message": "Chats retrieved successfully",
        "data": chats,
    }


@app.get("/chats/{chat_id}")
async def get_single_chat(request: Request, response: Response, chat_id: str):
    # if it's admin, allow else return unauthorized
    payload = request.state.payload

    if payload["role"] != "admin":
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"success": False, "message": "Unauthorized"}

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


###########################################
# Documents


@app.get("/documents/count")
async def get_documents_count(request: Request, response: Response):
    # if it's admin, allow else return unauthorized
    payload = request.state.payload
    if payload["role"] != "admin":
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"success": False, "message": "Unauthorized"}

    count = await app.database["documents"].count_documents({})

    return {
        "success": True,
        "message": "Documents count retrieved successfully",
        "data": count,
    }


@app.get("/documents")
async def get_documents(
    request: Request, response: Response, page: int = 0, limit: int = 10
):
    # if it's admin, allow else return unauthorized
    payload = request.state.payload
    if payload["role"] != "admin":
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"success": False, "message": "Unauthorized"}

    documents = (
        await app.database["documents"]
        .find()
        .skip(page * limit)
        .limit(limit)
        .to_list(length=limit)
    )

    documents = [
        {
            "_id": str(document["_id"]),
            "title": document["title"],
            "created_at": document["created_at"],
        }
        for document in documents
    ]

    return {
        "success": True,
        "message": "Documents retrieved successfully",
        "data": documents,
    }


@app.post("/documents")
async def create_document(
    request: Request,
    response: Response,
    title: str = Form(...),
    file: UploadFile = File(...),
):
    # Check authorization
    payload = request.state.payload
    if payload["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )

    # Validate file type
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are allowed"
        )

    # Save file to disk
    file_location = f"uploaded_documents/{time.time()}{file.filename}"
    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())

    # Create document in MongoDB
    document = {
        "title": title,
        "file_path": file_location,
        "created_at": datetime.now(),
    }

    result = await app.database["documents"].insert_one(document)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Could not create document"
        )

    if not result.acknowledged:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Could not create document"
        )

    document = {
        "_id": str(result.inserted_id),
        "title": title,
        "file_path": file_location,
        "created_at": document["created_at"],
    }

    response.status_code = status.HTTP_201_CREATED
    return {
        "success": True,
        "message": "Document created successfully",
        "data": document,
    }


@app.get("/documents/{document_id}")
async def get_document(document_id: str, request: Request, response: Response):
    # Check authorization
    payload = request.state.payload
    if payload["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )

    # Fetch the document from MongoDB
    document = await app.database["documents"].find_one({"_id": ObjectId(document_id)})

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    # Get the file path from the document
    file_path = document.get("file_path")

    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="File path not found"
        )

    # Serve the file
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=document["title"] + ".pdf",
    )


@app.delete("/documents/{document_id}")
async def delete_document(document_id: str, request: Request, response: Response):
    # Check authorization
    payload = request.state.payload
    if payload["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )

    # Fetch the document from MongoDB
    document = await app.database["documents"].find_one({"_id": ObjectId(document_id)})

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    # Get the file path from the document
    file_path = document.get("file_path")

    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="File path not found"
        )

    # Delete the file from disk
    import os
    os.remove(file_path)

    # Delete the document from MongoDB
    result = await app.database["documents"].delete_one({"_id": ObjectId(document_id)})

    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Could not delete document"
        )

    if not result.acknowledged:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Could not delete document"
        )

    return {
        "success": True,
        "message": "Document deleted successfully",
    }
