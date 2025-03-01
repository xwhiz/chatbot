"""
LangGraph agent implementation for the chatbot.
This module provides an agentic workflow that can route queries to the appropriate
handler based on the query type (RAG, tool execution, or direct conversation).
"""

from typing import TypedDict, Optional, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.vectorstores import VectorStoreRetriever
import logging
import re

# Import tools from registry instead of defining them here
from tools import get_tool_by_name, get_tool_descriptions

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define the state type for the agent
class ChatState(TypedDict):
    messages: List[Dict[str, Any]]
    user_email: str
    chat_id: Optional[str]
    tool_results: List[Dict[str, Any]]
    rag_results: Optional[str]
    current_action: Optional[str]
    llm: Any
    retriever: Optional[Any]
    db: Optional[Any]

# Agent nodes
def query_router(state: ChatState):
    """
    Determine if the query should be handled by RAG, a tool, or direct conversation.
    """
    logger.info("Routing query")
    
    # Get the latest human message
    latest_message = None
    for message in reversed(state["messages"]):
        if message.get("sender") == "human":
            latest_message = message.get("message")
            break
    
    if not latest_message:
        logger.warning("No human message found in state")
        state["current_action"] = "direct"
        return "direct"
    
    # Use the LLM to classify the query
    llm = state["llm"]
    
    # Get tool descriptions for the prompt
    tool_descriptions = "\n".join([
        f"- {tool['name']}: {tool['description']}" 
        for tool in get_tool_descriptions()
    ])
    
    classification_prompt = f"""
    Determine how to process this user query. Choose exactly ONE option that best fits:
    
    Query: {latest_message}
    
    Available tools:
    {tool_descriptions}
    
    Options:
    - "rag": If the query is requesting information that should be retrieved from a knowledge base or documents
    - "time_tool": If the query is asking about current time, date, or day of week
    - "direct": If the query is general conversation that doesn't need tools or retrieval
    
    Output format: Return ONLY the classification string, nothing else.
    """
    
    try:
        # Use a low temperature for deterministic output
        query_type = llm.invoke(classification_prompt).strip().lower()
        
        # Clean up the result in case the LLM outputs extra text
        if "rag" in query_type:
            query_type = "rag"
        elif "time" in query_type or "date" in query_type or "day" in query_type:
            query_type = "time_tool"
        else:
            query_type = "direct"
            
        logger.info(f"Query classified as: {query_type}")
    except Exception as e:
        logger.error(f"Error classifying query: {e}")
        query_type = "direct"  # Default to direct if classification fails
    
    # Set the action in state
    state["current_action"] = query_type
    
    return query_type

def perform_rag_retrieval(state: ChatState):
    """
    Retrieve relevant information from the vector database.
    """
    logger.info("Performing RAG retrieval")
    
    # Get the latest human message
    latest_message = None
    for message in reversed(state["messages"]):
        if message.get("sender") == "human":
            latest_message = message.get("message")
            break
    
    if not latest_message:
        logger.warning("No human message found for RAG retrieval")
        state["rag_results"] = None
        return "generate_response"
    
    # Use the retriever to get relevant documents
    retriever = state["retriever"]
    if not retriever:
        logger.warning("No retriever available")
        state["rag_results"] = None
        return "generate_response"
    
    try:
        # Get relevant documents
        docs = retriever.get_relevant_documents(latest_message)
        
        if docs:
            # Format the retrieved information
            retrieved_content = "\n\n".join([doc.page_content for doc in docs])
            state["rag_results"] = retrieved_content
            logger.info(f"Retrieved {len(docs)} documents")
        else:
            state["rag_results"] = None
            logger.info("No relevant documents found")
    except Exception as e:
        logger.error(f"Error during RAG retrieval: {e}")
        state["rag_results"] = None
    
    return "generate_response"

def execute_time_tool(state: ChatState):
    """
    Execute time-related tools based on the query.
    """
    logger.info("Executing time tool")
    
    # Get the latest human message
    latest_message = None
    for message in reversed(state["messages"]):
        if message.get("sender") == "human":
            latest_message = message.get("message")
            break
    
    if not latest_message:
        logger.warning("No human message found for tool execution")
        return "generate_response"
    
    # Determine the specific time tool to use
    lower_message = latest_message.lower()
    
    tool_results = []
    
    # Use tools from registry instead of directly defining them
    if "time" in lower_message:
        time_tool = get_tool_by_name("get_current_time")
        if time_tool:
            result = time_tool()
            tool_results.append({"tool": "get_current_time", "result": result})
    
    if "date" in lower_message:
        date_tool = get_tool_by_name("get_current_date")
        if date_tool:
            result = date_tool()
            tool_results.append({"tool": "get_current_date", "result": result})
    
    if "day" in lower_message:
        day_tool = get_tool_by_name("get_day_of_week")
        if day_tool:
            result = day_tool()
            tool_results.append({"tool": "get_day_of_week", "result": result})
    
    # If no specific tool matched, default to current time
    if not tool_results:
        time_tool = get_tool_by_name("get_current_time")
        if time_tool:
            result = time_tool()
            tool_results.append({"tool": "get_current_time", "result": result})
    
    state["tool_results"] = tool_results
    logger.info(f"Executed tools: {[tr['tool'] for tr in tool_results]}")
    
    return "generate_response"

def generate_response(state: ChatState):
    """
    Generate the final response based on the agent's actions.
    """
    logger.info("Generating response")
    
    # Get the latest human message
    latest_message = None
    for message in reversed(state["messages"]):
        if message.get("sender") == "human":
            latest_message = message.get("message")
            break
    
    if not latest_message:
        logger.warning("No human message found for response generation")
        return END
    
    llm = state["llm"]
    current_action = state["current_action"]
    
    # Construct the prompt based on the current action
    if current_action == "rag" and state.get("rag_results"):
        # Use retrieved context in prompt
        prompt = f"""
        You are a helpful assistant. Answer based on the following retrieved documents:
        
        RETRIEVED INFORMATION:
        {state["rag_results"]}
        
        USER QUERY:
        {latest_message}
        
        Provide a comprehensive and accurate response based on the retrieved information.
        If the retrieved information doesn't fully answer the query, acknowledge that and provide
        the best answer you can with what's available.
        """
    elif current_action == "time_tool" and state.get("tool_results"):
        # Use tool results in prompt
        tool_outputs = "\n".join([f"{tr['tool']}: {tr['result']}" for tr in state["tool_results"]])
        prompt = f"""
        You are a helpful assistant. Based on the tool execution results:
        
        TOOL RESULTS:
        {tool_outputs}
        
        USER QUERY:
        {latest_message}
        
        Provide a natural and helpful response that incorporates the tool results.
        """
    else:
        # Direct conversation
        prompt = f"""
        You are a helpful assistant. Respond to the following query:
        
        USER QUERY:
        {latest_message}
        
        Provide a helpful, accurate, and concise response.
        """
    
    try:
        # Generate the response
        response = llm.invoke(prompt)
        
        # Add the response to the messages
        state["messages"].append({
            "sender": "assistant",
            "message": response,
        })
        
        logger.info("Response generated successfully")
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        # Add a fallback response
        state["messages"].append({
            "sender": "assistant",
            "message": "I apologize, but I encountered an error processing your request. Please try again.",
        })
    
    return END

def build_agent_graph():
    """
    Build and return the LangGraph for the agent.
    """
    workflow = StateGraph(ChatState)
    
    # Add nodes
    workflow.add_node("query_router", query_router)
    workflow.add_node("perform_rag_retrieval", perform_rag_retrieval)
    workflow.add_node("execute_time_tool", execute_time_tool)
    workflow.add_node("generate_response", generate_response)
    
    # Add conditional edges from router
    workflow.add_conditional_edges(
        "query_router",
        {
            "rag": "perform_rag_retrieval",
            "time_tool": "execute_time_tool",
            "direct": "generate_response"
        }
    )
    
    # Add remaining edges
    workflow.add_edge("perform_rag_retrieval", "generate_response")
    workflow.add_edge("execute_time_tool", "generate_response")
    
    # Set the entry point
    workflow.set_entry_point("query_router")
    
    return workflow.compile() 