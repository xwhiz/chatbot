import json
from fastapi import (
    Body,
    FastAPI,
    Response,
    status,
    Request,
)
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from bson import ObjectId
from decouple import config
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
from langchain_core.vectorstores import VectorStoreRetriever

from ollama_inference import initialize_qa_chain
from lifespan import lifespan
from models import Chat
from auth import decode_jwt
from routers import auth, chats, documents, users, seed


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
        "/auth/can-create-admin-token",
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
app.include_router(users.router)
app.include_router(seed.router)


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


async def get_retriever_for_user(user_email: str) -> VectorStoreRetriever:
    user = await app.database["users"].find_one(
        {"email": user_email}, {"accessible_docs": 1}
    )

    accessible_docs = user.get("accessible_docs", [])

    if "all" in accessible_docs:
        return app.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": 5,
                "score_threshold": 0.2,
            },
        )

    print("Accessible docs", accessible_docs)
    return app.vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": 5,
            "score_threshold": 0.2,
            "filter": rest.Filter(
                must=[
                    rest.FieldCondition(
                        key="metadata.document_id",  # Ensure the path to metadata is correct
                        match=rest.MatchAny(
                            any=accessible_docs,
                        ),
                    )
                ]
            ),
        },
    )


def get_context_string(length: int, chat: dict) -> str:
    pairs = []
    pair = []
    for message in chat["messages"]:
        if message['sender'] == 'human':
            pair = [f"Human: `{message['message']}`"]
        else:
            pair.append(f"Assistant: `{message['message']}")

        if len(pair) == 2:
            pairs.append(pair)
            pair = []

    context_pairs = []
    for pair in reversed(pairs):
        context_pairs.append(pair)
        if len(context_pairs) == length:
            break

    context_pairs.reverse()
    context_string = "\n".join([f"{a}\n{b}" for a, b in context_pairs])
    return context_string


async def generate_response(chat_id: str):
    chat = await app.database["chats"].find_one({"_id": ObjectId(chat_id)})
    if not chat:
        return
    

    user_email = chat["user_email"]
    user = await app.database["users"].find_one({"email": user_email})
    if not user:
        return

    prompt = ""
    if "prompt" in user:
        prompt = user["prompt"]

    context_length = 5
    context_string = get_context_string(context_length, chat)
    retriever = await get_retriever_for_user(chat["user_email"])
    qa_chain = initialize_qa_chain(app.llm, retriever, prompt, context_string)

    last_human_message = None
    for message in reversed(chat["messages"]):
        if message["sender"] == "human":
            last_human_message = message
            break

    if not last_human_message:
        return


    is_instructions = False
    if (
        "[NOTE]" in last_human_message["message"].upper()
        or "[TAKE NOTE]" in last_human_message["message"].upper()
        or "[TAKENOTE]" in last_human_message["message"].upper()
    ):
        is_instructions = True

        user["prompt"] += "\n" + last_human_message["message"].lower().replace(
            "[note]", ""
        ).replace("[take note]", "").replace("[takenote]", "")

        result = await app.database["users"].update_one(
            {"_id": ObjectId(user["_id"])}, {"$set": user}
        )

        if not result.acknowledged:
            yield f"data: {json.dumps({'chat_id': chat_id, 'partial_response': 'Unable to save your instructions. Please try again.'})}\n\n"
            return
        yield f"data: {json.dumps({'chat_id': chat_id, 'partial_response': 'Provided instructions has been saved.'})}\n\n"
        return

    if is_instructions:
        return

    print("Generating response for:", last_human_message["message"])
    print(retriever.invoke(last_human_message["message"]))

    try:
        stream = qa_chain.stream(last_human_message["message"])
    except Exception as e:
        print("Error in generating response:", e)

        print("Recreating Qdrant client")
        app.client = QdrantClient(path=config("VECTOR_DOC_DB_PATH"))
        stream = qa_chain.stream(last_human_message["message"])

    for chunk in stream:
        yield f"data: {json.dumps({'chat_id': chat_id, 'partial_response': chunk}).strip()}\n\n"


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


# A health endpoint
@app.get("/health")
async def health(response: Response):
    response.status_code = status.HTTP_200_OK
    return {"status": "ok"}
