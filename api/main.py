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
from langchain_ollama import ChatOllama

from model_inference import initialize_qa_chain
from lifespan import lifespan
from models import Chat
from auth import decode_jwt
from routers import auth, chats, documents, users, seed
from agent_integration import generate_agentic_response, generate_streaming_response, get_retriever_for_user


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

        if not result or not result.acknowledged:
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

    if not result or not result.acknowledged:
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
            pair.append(f"Assistant: `{message['message']}`")

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
    """
    Legacy function wrapper that calls the new agentic response generator.
    """
    return await generate_agentic_response(app, chat_id)


@app.get("/generate-response/{chat_id}")
async def get_response(chat_id: str):
    """
    Generate a response for a chat using the LangGraph agent.
    """
    return StreamingResponse(
        generate_streaming_response(app, chat_id),
        media_type="text/event-stream",
    )


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


@app.post("/change-model")
async def change_model(response: Response, request: Request):
    body = await request.json()
    model = body.get("model")
    if model is None:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"success": False, "message": "Model is required"}
    

    app.llm = ChatOllama(model=model)
    response.status_code = status.HTTP_200_OK
    return {"success": True, "message": f"Changed LLM model to {model}"}

# A health endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "ok"}
