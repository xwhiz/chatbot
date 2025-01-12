from fastapi import APIRouter, Response, status, Request
from bson import ObjectId

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/")
async def get_users(
    request: Request, response: Response, page: int = 0, limit: int = 10
):
    app = request.app

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


@router.delete("/{user_id}")
async def delete_user_and_all_their_chats(
    request: Request, response: Response, user_id: str
):
    app = request.app
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


@router.get("/all-minimal")
async def get_all_users_minimal(request: Request, response: Response):
    app = request.app
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


@router.get("/count")
async def get_users_count(request: Request, response: Response):
    app = request.app
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


@router.delete("/{user_id}/{doc_id}")
async def remove_doc_access_for_user(
    request: Request, response: Response, user_id: str, doc_id: str
):
    app = request.app
    payload = request.state.payload

    if payload["role"] != "admin":
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"success": False, "message": "Unauthorized"}

    user = await app.database["users"].find_one({"_id": ObjectId(user_id)})

    if not user:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"success": False, "message": "User not found"}

    # if ["all"] is in accessible_docs, remove it
    if "all" in user["accessible_docs"]:
        user["accessible_docs"].remove("all")

        all_documents = await app.database["documents"].find().to_list(length=1000)
        all_documents = [str(doc["_id"]) for doc in all_documents]

        print(all_documents)

        user["accessible_docs"] = list(set(user["accessible_docs"] + all_documents))

    print(user["accessible_docs"])

    if doc_id not in user["accessible_docs"]:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"success": False, "message": "Document not accessible by user"}

    user["accessible_docs"].remove(doc_id)

    result = await app.database["users"].update_one(
        {"_id": ObjectId(user_id)}, {"$set": user}
    )

    if not result.acknowledged:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"success": False, "message": "Could not remove document access"}

    return {
        "success": True,
        "message": "Document access removed successfully",
    }


@router.put("/{user_id}/{doc_id}")
async def add_doc_access_for_user(
    request: Request, response: Response, user_id: str, doc_id: str
):
    app = request.app
    payload = request.state.payload

    if payload["role"] != "admin":
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"success": False, "message": "Unauthorized"}

    user = await app.database["users"].find_one({"_id": ObjectId(user_id)})

    if not user:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"success": False, "message": "User not found"}

    # if ["all"] is in accessible_docs, remove it
    if "all" in user["accessible_docs"]:
        user["accessible_docs"].remove("all")

        all_documents = await app.database["documents"].find().to_list(length=1000)
        all_documents = [str(doc["_id"]) for doc in all_documents]

        user["accessible_docs"] = list(set(user["accessible_docs"] + all_documents))

    if doc_id in user["accessible_docs"]:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"success": False, "message": "Document already accessible by user"}

    user["accessible_docs"].append(doc_id)

    result = await app.database["users"].update_one(
        {"_id": ObjectId(user_id)}, {"$set": user}
    )

    if not result.acknowledged:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"success": False, "message": "Could not add document access"}

    return {
        "success": True,
        "message": "Document access added successfully",
    }


@router.post("/prompt/{user_id}")
async def update_prompt(request: Request, response: Response, user_id: str):
    app = request.app
    payload = request.state.payload

    if payload["role"] != "admin":
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"success": False, "message": "Unauthorized"}

    user = await app.database["users"].find_one({"_id": ObjectId(user_id)})

    if not user:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"success": False, "message": "User not found"}

    body = await request.json()
    if "prompt" not in body:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"success": False, "message": "Missing prompt in request body"}

    prompt = body["prompt"]
    user["prompt"] = prompt

    result = await app.database["users"].update_one(
        {"_id": ObjectId(user_id)}, {"$set": user}
    )
    if not result.acknowledged:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"success": False, "message": "Could not update prompt"}

    response.status_code = status.HTTP_201_CREATED
    return {
        "success": True,
        "message": "Prompt updated successfully",
    }
