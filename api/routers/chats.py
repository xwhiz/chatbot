from fastapi import APIRouter, Response, status, Request
from bson import ObjectId


router = APIRouter(prefix="/chats", tags=["Chats"])


@router.post("/")
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

    user = await router.database["users"].find_one({"_id": ObjectId(user_id)})

    if not user:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"success": False, "message": "User not found"}

    user_email = user["email"]

    chats = (
        await router.database["chats"]
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


@router.get("/ids")
async def get_chat_ids(request: Request, response: Response):
    payload = request.state.payload
    user_email = payload["email"]

    chats = (
        await router.database["chats"]
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


@router.get("/{chat_id}")
async def get_chat(request: Request, response: Response, chat_id: str):
    chat = await router.database["chats"].find_one({"_id": ObjectId(chat_id)})

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


@router.delete("/{chat_id}")
async def delete_chat(request: Request, response: Response, chat_id: str):
    chat = await router.database["chats"].find_one({"_id": ObjectId(chat_id)})

    if not chat:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"success": False, "message": "Chat not found"}

    result = await router.database["chats"].delete_one({"_id": ObjectId(chat_id)})

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


@router.post("/count")
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

    user = await router.database["users"].find_one({"_id": ObjectId(user_id)})

    if not user:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"success": False, "message": "User not found"}

    user_email = user["email"]

    count = await router.database["chats"].count_documents({"user_email": user_email})

    return {
        "success": True,
        "message": "Chats count retrieved successfully",
        "data": count,
    }


@router.get("/all/minimal")
async def get_all_chats_minimal(request: Request, response: Response):
    # if it's admin, allow else return unauthorized
    payload = request.state.payload

    if payload["role"] != "admin":
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"success": False, "message": "Unauthorized"}

    chats = await router.database["chats"].find().to_list(length=1000)

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


@router.get("/{chat_id}")
async def get_single_chat(request: Request, response: Response, chat_id: str):
    # if it's admin, allow else return unauthorized
    payload = request.state.payload

    if payload["role"] != "admin":
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"success": False, "message": "Unauthorized"}

    chat = await router.database["chats"].find_one({"_id": ObjectId(chat_id)})

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
