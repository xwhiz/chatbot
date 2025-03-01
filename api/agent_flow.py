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
import json

# Import tools from registry instead of defining them here
from tools import get_day_date_time, get_tool_by_name

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
    custom_prompt: Optional[str]

class ActionType:
    RAG = "rag"
    TIME_TOOL = "time_tool"
    DIRECT = "direct"


def _get_context_from_history(messages: List[Dict], max_pairs: int = 5) -> str:
    message_pairs = []
    human_msg = None
    
    for message in messages:
        if message.get("sender") == "human":
            human_msg = message.get("message")
        elif message.get("sender") == "ai" and human_msg:
            message_pairs.append((human_msg, message.get("message")))
            human_msg = None
    
    context = ""
    context_pairs = message_pairs[-max_pairs:] if len(message_pairs) > max_pairs else message_pairs
    for human, ai in context_pairs:
        context += f"Human: {human}\nAssistant: {ai}\n\n"
    
    return context.strip()


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
        state["current_action"] = ActionType.DIRECT
        return state
    
    # Convert message to lowercase for pattern matching
    message_lower = latest_message.lower()
        
    # Check common RAG indicators (but verify with LLM as these can be ambiguous)
    # rag_indicators_found = False
    # for pattern in PATTERNS["rag_indicators"]:
    #     if re.search(pattern, message_lower):
    #         rag_indicators_found = True
    #         break
    
    # For ambiguous cases, use the LLM to classify
    llm = state["llm"]
    
    classification_prompt = f"""
    Determine the best way to process the user's query by assigning a confidence percentage to each available tool.

    Query: {latest_message}

    Context (if available):
    { _get_context_from_history(state['messages']) }

    RAG results from history (if available):
    {state.get('rag_results', 'No RAG results available')}

    Available tools:
    - "time_tool": Use this when the query requires the **current date, time, or any reasoning based on the present moment** (e.g., "What day is it?", "How many days until an event?").
    - "rag": Use this when the **query asks for factual knowledge that is NOT explicitly known to the model or current context** (e.g., "Who is [someone]?", "What are the details of [X]?").
    - "direct": Use this when the model **can confidently answer from its built-in knowledge OR the context already contains the answer** without requiring external retrieval.

    Guidelines:
    - You must rate each tool completely independent of others. The rating will show how relevant is the tool to the query of user with respect to the context and retrieved documents.
    - Scores must be in the range of 0 to 100.
    - Always return all three keys in the output, even if some scores are low.
    - OUTPUT MUST BE JUST THE THINGS I HAVE MENTIONED IN THE FOLLOWING TEXT. NO TEXT, EXPLANATIONS OR ANYTHING ELSE IS REQUIRED. ONLY THE THREE LINES OF OUTPUT.
    - Return output in this exact format:

    time_tool: <confidence_score>  
    rag: <confidence_score>  
    direct: <confidence_score>
    """

    
    try:
        response = llm.invoke(classification_prompt)
        if hasattr(response, 'content'):
            response = response.content
        else:
            response = str(response)
        
        logger.info(f"Classification response: {response}")
        ratings = response.split("\n")
        rating = {r.split(":")[0].strip(): int(r.split(":")[1].strip()) for r in ratings}

        query_type = "time_tool"
        for key, value in rating.items():
            if rating[query_type] < value:
                query_type = key

        if ActionType.RAG in query_type:
            query_type = ActionType.RAG
        elif ActionType.TIME_TOOL in query_type:
            query_type = ActionType.TIME_TOOL
        else:
            query_type = ActionType.DIRECT
            
        logger.info(f"Query classified as: {query_type}")
    except Exception as e:
        logger.error(f"Error classifying query: {e}")
        query_type = ActionType.DIRECT  # Default to direct if classification fails
    
    state["current_action"] = query_type
    return state

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
        return state
    
    # Use the retriever to get relevant documents
    retriever = state["retriever"]
    if not retriever:
        logger.warning("No retriever available")
        state["rag_results"] = None
        return state
    
    try:
        # Get relevant documents
        docs = retriever.get_relevant_documents(latest_message)
        
        if docs:
            # Format the docs into a string for the LLM
            context = "\n\n".join([f"Document: {doc.page_content}" for doc in docs])
            state["rag_results"] = context
            logger.info(f"Retrieved {len(docs)} relevant documents")
        else:
            logger.info("No relevant documents found")
            state["rag_results"] = None
    except Exception as e:
        logger.error(f"Error retrieving documents: {e}")
        state["rag_results"] = None
    
    return state

def execute_time_tool(state: ChatState):
    """
    Execute a time-related tool based on the query.
    """
    logger.info("Executing time tool")
    
    # Get the latest human message
    latest_message = None
    for message in reversed(state["messages"]):
        if message.get("sender") == "human":
            latest_message = message.get("message")
            break
    
    if not latest_message:
        logger.warning("No human message found for time tool")
        tool_result = "I couldn't understand your time-related query."
        state["tool_results"].append({
            "tool": "time",
            "result": tool_result
        })
        return state
    
    try:
        result = get_tool_by_name("get_day_date_time")()
        state["tool_results"].append({
            "tool": "time",
            "result": result
        })
        logger.info(f"Time tool result: {result}")
    except Exception as e:
        logger.error(f"Error executing time tool: {e}")
        state["tool_results"].append({
            "tool": "time",
            "result": "I encountered an error trying to get the time information."
        })
    
    return state

def generate_response(state: ChatState):
    """
    Generate a response based on the current state.
    """
    logger.info("Generating response")
    
    # Get the LLM from state
    llm = state["llm"]
    if not llm:
        logger.error("No LLM available")
        return state  # Early return if no LLM is available
    
    # Get the latest human message
    latest_message = None
    for message in reversed(state["messages"]):
        if message.get("sender") == "human":
            latest_message = message.get("message")
            break
    
    if not latest_message:
        logger.warning("No human message found")
        response = "I'm sorry, I couldn't understand your message."
        state["messages"].append({
            "sender": "assistant",
            "message": response
        })
        return state

    context = _get_context_from_history(state['messages'])
    

    # Determine which knowledge to use for generating the response
    current_action = state.get("current_action")
    
    if current_action == ActionType.RAG and state.get("rag_results"):
        # Get the RAG results
        context = state["rag_results"]
        
        prompt = f"""
        Answer the user's question based on the following context:
        
        Context:
        {context}
        
        User question: {latest_message}
        
        If the context doesn't contain relevant information to answer the question, 
        please state that you don't have enough information to provide a complete answer,
        but try to be helpful with what you know.
        """
        
        try:
            response = llm.invoke(prompt)
            # Handle different response types
            if hasattr(response, 'content'):
                response = response.content
            else:
                response = str(response)
        except Exception as e:
            logger.error(f"Error generating RAG response: {e}")
            response = "I'm sorry, I encountered an error while processing your query."
    
    elif current_action in [ActionType.TIME_TOOL]:
        tool_results = state.get("tool_results", [])
        latest_result = tool_results[-1].get("result", "I couldn't get the information you requested.")

        prompt = f"""
        Your role: ###{state.get("custom_prompt")}###

        You are an assistant designed for question-answering tasks. 
        - Use the provided pieces of retrieved context to answer questions as accurately as possible. 
        - When the context does not directly provide an answer, or when the question is unrelated to the context, 
        - use your general knowledge to respond appropriately. 
        - Avoid referencing the retrieved context when it is irrelevant to the question.
        
        <context>
        ###Previous Chat Context: %s###
        {context}
        </context>

        <tool-result>
        {latest_result}
        </tool-result>

        Answer the following question:
        {latest_message}
        """

        try:
            response = llm.invoke(prompt)
            if hasattr(response, 'content'):
                response = response.content
            else:
                response = str(response)
        except Exception as e:
            logger.error(f"Error generating direct response: {e}")
            response = "I'm sorry, I encountered an error while processing your message."

    else:
        
        
        prompt = f"""
        You are a helpful AI assistant. Continue the conversation in a helpful and friendly manner.
        
        Previous conversation:
        {context}
        
        Human: {latest_message}
        Assistant:
        """
        
        try:
            response = llm.invoke(prompt)
            # Handle different response types
            if hasattr(response, 'content'):
                response = response.content
            else:
                response = str(response)
        except Exception as e:
            logger.error(f"Error generating direct response: {e}")
            response = "I'm sorry, I encountered an error while processing your message."
    
    # Add the response to messages
    state["messages"].append({
        "sender": "assistant",
        "message": response
    })
    
    logger.info("Response generated successfully")
    return state

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
        lambda state: state["current_action"],
        {
            ActionType.RAG: "perform_rag_retrieval",
            ActionType.TIME_TOOL: "execute_time_tool",
            ActionType.DIRECT: "generate_response"
        }
    )
    
    # Add remaining edges
    workflow.add_edge("perform_rag_retrieval", "generate_response")
    workflow.add_edge("execute_time_tool", "generate_response")
    workflow.add_edge("generate_response", END)
    
    # Set the entry point
    workflow.set_entry_point("query_router")

    # TODO: plot the current graph and save it to the filesystem
    
    return workflow.compile() 