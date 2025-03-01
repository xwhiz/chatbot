"""
Integration module to connect the LangGraph agent with the existing chatbot functionality.
This allows for a seamless transition from the current implementation to the agentic workflow.
"""

import logging
import json
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from bson import ObjectId

from agent_flow import build_agent_graph, ChatState
from model_inference.infer_model_chain import initialize_qa_chain

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize the agent graph
agent_graph = build_agent_graph()

def get_context_from_history(messages: List[Dict], max_pairs: int = 5):
    """
    Extract conversation context from message history.
    Enhanced version of the get_context_string function from main.py.
    """
    pairs = []
    pair = []
    
    for message in messages:
        if message['sender'] == 'human':
            pair = [f"Human: {message['message']}"]
        else:
            pair.append(f"Assistant: {message['message']}")

        if len(pair) == 2:
            pairs.append(pair)
            pair = []

    # Select most recent pairs, limited by max_pairs
    context_pairs = []
    for pair in reversed(pairs):
        context_pairs.append(pair)
        if len(context_pairs) == max_pairs:
            break

    context_pairs.reverse()
    context_string = "\n".join([f"{a}\n{b}" for a, b in context_pairs])
    return context_string

async def generate_agentic_response(app, chat_id: str):
    """
    Generate a response using the LangGraph agent.
    This replaces the generate_response function in main.py.
    """
    try:
        # Retrieve the chat from the database
        chat = await app.database["chats"].find_one({"_id": ObjectId(chat_id)})
        if not chat:
            logger.error(f"Chat not found: {chat_id}")
            return None

        user_email = chat["user_email"]
        
        # Get user information for custom prompt
        user = await app.database["users"].find_one({"email": user_email})
        if not user:
            logger.error(f"User not found: {user_email}")
            return None

        # Check for custom instructions
        if (
            len(chat["messages"]) > 0 and 
            chat["messages"][-1]["sender"] == "human" and
            (
                "[NOTE]" in chat["messages"][-1]["message"].upper() or
                "[TAKE NOTE]" in chat["messages"][-1]["message"].upper() or
                "[TAKENOTE]" in chat["messages"][-1]["message"].upper()
            )
        ):
            # Handle custom instructions
            instruction = chat["messages"][-1]["message"].lower()
            instruction = (
                instruction.replace("[note]", "")
                .replace("[take note]", "")
                .replace("[takenote]", "")
                .strip()
            )
            
            # Update user prompt
            current_prompt = user.get("prompt", "")
            new_prompt = f"{current_prompt}\n{instruction}" if current_prompt else instruction
            
            result = await app.database["users"].update_one(
                {"_id": ObjectId(user["_id"])}, {"$set": {"prompt": new_prompt}}
            )
            
            if not result or not result.acknowledged:
                logger.error(f"Failed to update user prompt for {user_email}")
                return "Unable to save your instructions. Please try again."
            
            return "Provided instructions have been saved."

        # Get custom prompt if available
        custom_prompt = user.get("prompt", "")
        
        # Get retriever for the user - use app.get_retriever_for_user directly
        # to avoid circular imports
        try:
            user_info = await app.database["users"].find_one(
                {"email": user_email}, {"accessible_docs": 1}
            )

            if not user_info:
                logger.warning(f"User not found when getting retriever: {user_email}")
                retriever = None
            else:
                accessible_docs = user_info.get("accessible_docs", [])

                if "all" in accessible_docs:
                    retriever = app.vector_store.as_retriever(
                        search_type="similarity",
                        search_kwargs={
                            "k": 5,
                            "score_threshold": 0.2,
                        },
                    )
                else:
                    logger.info(f"User {user_email} has access to documents: {accessible_docs}")
                    retriever = app.vector_store.as_retriever(
                        search_type="similarity",
                        search_kwargs={
                            "k": 5,
                            "score_threshold": 0.2,
                            "filter": {"metadata.document_id": {"$in": accessible_docs}},
                        },
                    )
        except Exception as e:
            logger.error(f"Error getting retriever for user {user_email}: {e}")
            retriever = None
        
        # Set up the initial state for the agent
        state = ChatState(
            messages=chat["messages"],
            user_email=user_email,
            chat_id=chat_id,
            tool_results=[],
            rag_results=None,
            current_action=None,
            llm=app.llm,
            retriever=retriever,
            db=app.database
        )
        
        # Execute the agent graph
        logger.info(f"Executing agent graph for chat {chat_id}")
        final_state = agent_graph.invoke(state)
        
        # The agent has already added its response to the messages
        updated_messages = final_state["messages"]
        
        # Update the chat in the database
        result = await app.database["chats"].update_one(
            {"_id": ObjectId(chat_id)},
            {"$set": {"messages": updated_messages}}
        )
        
        if not result or not result.acknowledged:
            logger.error(f"Failed to update chat {chat_id} with agent response")
            return None
        
        # Return the assistant's response
        for message in reversed(updated_messages):
            if message.get("sender") == "assistant":
                return message.get("message")
        
        return None
    
    except Exception as e:
        logger.error(f"Error generating agentic response for chat {chat_id}: {e}")
        return "I apologize, but I encountered an error processing your request. Please try again."

async def generate_streaming_response(app, chat_id: str) -> AsyncGenerator[str, None]:
    """
    Generate a streaming response using the LangGraph agent.
    This simulates streaming by breaking the response into chunks and using SSE formatting.
    """
    try:
        # Get the full response first
        full_response = await generate_agentic_response(app, chat_id)
        
        if not full_response:
            yield f"data: {json.dumps({'chat_id': chat_id, 'partial_response': 'No response generated.'})}\n\n"
            return
        
        # Simulate streaming by breaking the response into chunks
        # This is a placeholder until true streaming is implemented in LangGraph
        chunk_size = 20  # characters per chunk
        
        # Initial empty message to trigger the client
        yield f"data: {json.dumps({'chat_id': chat_id, 'partial_response': ''})}\n\n"
        await asyncio.sleep(0.05)
        
        # Stream the response in chunks
        for i in range(0, len(full_response), chunk_size):
            chunk = full_response[i:i+chunk_size]
            # For backward compatibility, send the full accumulated text so far, not just the new chunk
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