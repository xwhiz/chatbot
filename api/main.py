import json
import logging
from fastapi import (
    Body,
    FastAPI,
    Response,
    status,
    Request,
    Depends,
    HTTPException,
    Header,
)
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from bson import ObjectId
from decouple import config
from langchain_ollama import ChatOllama
from typing import Optional
import asyncio

from model_inference import initialize_qa_chain
from lifespan import lifespan
from models import Chat
from auth import decode_jwt
from routers import auth, chats, documents, users, seed
from agent_integration import generate_agentic_response, generate_streaming_response


app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Configure logger
logger = logging.getLogger(__name__)


@app.middleware("http")
async def verify_token(request, call_next):
    allowed_paths = [
        "/auth/register",
        "/auth/login",
        "/auth/can-create-admin-token",
        "/seed/create-admin",
        "/docs",
        "/openapi.json",
        "/health",
    ]
    
    # Check if the path matches any allowed paths (even with additional parameters)
    for allowed_path in allowed_paths:
        if request.url.path.startswith(allowed_path):
            response = await call_next(request)
            return response

    # if request is options, we don't need to verify the token
    if request.method == "OPTIONS":
        response = await call_next(request)
        return response

    # Look for token in query params first (for backward compatibility)
    token = None
    if "token" in request.query_params:
        token = request.query_params["token"]
    else:
        # If not in query params, check Authorization header
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


async def verify_user_access(chat_id: str, request: Request):
    """
    Verify that the user has access to the specified chat.
    """
    try:
        # Get the chat
        chat = await app.database["chats"].find_one({"_id": ObjectId(chat_id)})
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat not found",
            )
        
        # Get user from token payload
        payload = request.state.payload
        user_email = payload.get("email")
        user_role = payload.get("role")
        
        # Admin can access all chats
        if user_role == "admin":
            return chat
        
        # Regular users can only access their own chats
        if chat["user_email"] != user_email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this chat",
            )
        
        return chat
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error verifying access: {str(e)}",
        )


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


# Legacy function kept for reference
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


# For backward compatibility with old frontend
async def generate_response(chat_id: str):
    """
    Legacy function wrapper that calls the new agentic response generator.
    This returns an async generator for streaming responses.
    """
    try:
        # Get the full response from the agentic generator
        full_response = await generate_agentic_response(app, chat_id)
        
        if not full_response:
            yield f"data: {json.dumps({'chat_id': chat_id, 'partial_response': 'No response generated.'})}\n\n"
            return
        
        # Simulate streaming by breaking the response into chunks
        chunk_size = 20  # characters per chunk
        
        # Initial empty message to trigger the client
        yield f"data: {json.dumps({'chat_id': chat_id, 'partial_response': ''})}\n\n"
        await asyncio.sleep(0.05)
        
        # Stream the response in chunks
        for i in range(0, len(full_response), chunk_size):
            chunk = full_response[i:i+chunk_size]
            # Send accumulated text for backward compatibility
            accumulated_text = full_response[:i+chunk_size]
            yield f"data: {json.dumps({'chat_id': chat_id, 'partial_response': accumulated_text})}\n\n"
            await asyncio.sleep(0.05)  # Small delay to simulate streaming
        
        # Signal completion
        yield f"data: {json.dumps({'chat_id': chat_id, 'is_complete': True})}\n\n"
    
    except Exception as e:
        logger.error(f"Error generating streaming response for chat {chat_id}: {e}")
        error_message = "I apologize, but I encountered an error processing your request. Please try again."
        yield f"data: {json.dumps({'chat_id': chat_id, 'partial_response': error_message})}\n\n"
        yield f"data: {json.dumps({'chat_id': chat_id, 'is_complete': True})}\n\n"


# Replace these endpoints with the original version
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

    # Verify user has access to the chat
    await verify_user_access(chat_id, request)

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


async def get_retriever_for_user(user_email: str):
    """
    Get a retriever configured for the specific user.
    """
    try:
        user = await app.database["users"].find_one(
            {"email": user_email}, {"accessible_docs": 1}
        )

        if not user:
            return None

        accessible_docs = user.get("accessible_docs", [])

        if "all" in accessible_docs:
            return app.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={
                    "k": 5,
                    "score_threshold": 0.2,
                },
            )

        return app.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": 5,
                "score_threshold": 0.2,
                "filter": {"metadata.document_id": {"$in": accessible_docs}},
            },
        )
    except Exception as e:
        app.logger.error(f"Error getting retriever for user {user_email}: {e}")
        return None