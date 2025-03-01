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

# Define actions
class ActionType:
    RAG = "rag"
    TIME_TOOL = "time_tool"
    WEATHER_TOOL = "weather_tool"
    DIRECT = "direct"

# Define patterns for quick matching
PATTERNS = {
    "time_patterns": [
        r'\b(what|current|tell me|show me).*time\b',
        r'\btime.*now\b',
        r'\bwhat time is it\b'
    ],
    "date_patterns": [
        r'\b(what|current|tell me|show me).*date\b',
        r'\bdate.*today\b',
        r'\bwhat (is the|\'s the) date\b',
        r'\btoday\'s date\b'
    ],
    "day_patterns": [
        r'\b(what|which) day\b',
        r'\bday of (the )?(week|month)\b',
        r'\bwhat day is (it|today)\b'
    ],
    "weather_patterns": [
        r'weather (in|for|at) (?P<location>\w+)',
        r'what\'s the weather (like )?(in|at) (?P<location>\w+)',
        r'how\'s the weather (in|at) (?P<location>\w+)',
        r'(current|today\'s) weather (in|at) (?P<location>\w+)',
        r'weather forecast',
        r'weather report',
        r'what\'s the weather (like )?today',
        r'how\'s the weather today',
        r'what is the temperature'
    ],
    "calculator_patterns": [
        r'\bcalculate\b',
        r'\bcompute\b',
        r'\bsolve\b',
        r'\bmath\b',
        r'\d+\s*[\+\-\*\/\(\)]\s*\d+',  # Basic math expressions like "2 + 2"
    ],
    "rag_indicators": [
        r'\binfo(rmation)? (on|about)\b',
        r'\btell me about\b',
        r'\bwhat is\b',
        r'\bwho is\b',
        r'\bexplain\b',
        r'\bdescribe\b',
        r'\bdo you know\b',
        r'\bwhere\b',
        r'\bwhen\b'
    ]
}

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
        state["current_action"] = ActionType.DIRECT
        return state
    
    # Convert message to lowercase for pattern matching
    message_lower = latest_message.lower()
    
    # Try quick pattern matching first to avoid LLM call for obvious cases
    
    # Check time-related patterns
    for pattern in PATTERNS["time_patterns"]:
        if re.search(pattern, message_lower):
            logger.info("Pattern matched: time tool")
            state["current_action"] = ActionType.TIME_TOOL
            return state
            
    for pattern in PATTERNS["date_patterns"]:
        if re.search(pattern, message_lower):
            logger.info("Pattern matched: time tool (date)")
            state["current_action"] = ActionType.TIME_TOOL
            return state
    
    for pattern in PATTERNS["day_patterns"]:
        if re.search(pattern, message_lower):
            logger.info("Pattern matched: time tool (day)")
            state["current_action"] = ActionType.TIME_TOOL
            return state
    
    # Check weather patterns
    for pattern in PATTERNS["weather_patterns"]:
        if re.search(pattern, message_lower):
            logger.info("Pattern matched: weather tool")
            state["current_action"] = ActionType.WEATHER_TOOL
            return state
    
    # Check calculator patterns
    for pattern in PATTERNS["calculator_patterns"]:
        if re.search(pattern, message_lower):
            logger.info("Pattern matched: calculator - falling back to LLM for confirmation")
            # For calculator, we'll still use LLM to confirm as it's more complex
    
    # Check common RAG indicators (but verify with LLM as these can be ambiguous)
    rag_indicators_found = False
    for pattern in PATTERNS["rag_indicators"]:
        if re.search(pattern, message_lower):
            rag_indicators_found = True
            break
    
    # Simple greeting patterns should go to direct conversation
    greeting_patterns = [
        r'^(hello|hi|hey|greetings|howdy|hola)(\s|$)',
        r'^(good|nice) (morning|afternoon|evening|day)(\s|$)',
        r'^how are (you|things)(\s|$)'
    ]
    
    for pattern in greeting_patterns:
        if re.search(pattern, message_lower):
            logger.info("Pattern matched: direct greeting")
            state["current_action"] = ActionType.DIRECT
            return state
    
    # For ambiguous cases, use the LLM to classify
    llm = state["llm"]
    
    # Get tool descriptions for the prompt
    tool_descriptions = "\n".join([
        f"- {tool['name']}: {tool['description']}" 
        for tool in get_tool_descriptions()
    ])
    
    # Provide hints to the LLM based on pattern matching
    hints = ""
    if rag_indicators_found:
        hints = "Hint: This query contains indicators that it might be seeking information from a knowledge base."
    
    classification_prompt = f"""
    Determine how to process this user query. Choose exactly ONE option that best fits:
    
    Query: {latest_message}
    
    Available tools:
    {tool_descriptions}
    
    {hints}
    
    Options:
    - "{ActionType.RAG}": If the query is requesting information that should be retrieved from a knowledge base or documents
    - "{ActionType.TIME_TOOL}": If the query is asking about current time, date, or day of week
    - "{ActionType.WEATHER_TOOL}": If the query is asking about weather conditions
    - "{ActionType.DIRECT}": If the query is general conversation that doesn't need tools or retrieval
    
    Output format: Return ONLY the classification string, nothing else.
    """
    
    try:
        # Use a low temperature for deterministic output
        response = llm.invoke(classification_prompt)
        
        # Handle different response types (AIMessage or string)
        if hasattr(response, 'content'):
            # This is likely an AIMessage object, extract the content
            query_type = response.content
        else:
            # This is likely a string
            query_type = str(response)
            
        # Clean up and standardize the response
        query_type = query_type.strip().lower()
        
        # Clean up the result in case the LLM outputs extra text
        if ActionType.RAG in query_type:
            query_type = ActionType.RAG
        elif ActionType.TIME_TOOL in query_type:
            query_type = ActionType.TIME_TOOL
        elif ActionType.WEATHER_TOOL in query_type:
            query_type = ActionType.WEATHER_TOOL
        else:
            query_type = ActionType.DIRECT
            
        logger.info(f"Query classified as: {query_type}")
    except Exception as e:
        logger.error(f"Error classifying query: {e}")
        query_type = ActionType.DIRECT  # Default to direct if classification fails
    
    # Set the action in state
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
    
    message_lower = latest_message.lower()
    
    try:
        # Determine which time tool to use
        if any(re.search(pattern, message_lower) for pattern in PATTERNS["time_patterns"]):
            time_tool = get_tool_by_name("get_current_time")
            result = time_tool()
        elif any(re.search(pattern, message_lower) for pattern in PATTERNS["date_patterns"]):
            date_tool = get_tool_by_name("get_current_date")
            result = date_tool()
        elif any(re.search(pattern, message_lower) for pattern in PATTERNS["day_patterns"]):
            day_tool = get_tool_by_name("get_day_of_week")
            result = day_tool()
        else:
            # Default to time if pattern is unclear
            time_tool = get_tool_by_name("get_current_time")
            result = time_tool()
        
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

def execute_weather_tool(state: ChatState):
    """
    Execute the weather tool based on the query.
    """
    logger.info("Executing weather tool")
    
    # Get the latest human message
    latest_message = None
    for message in reversed(state["messages"]):
        if message.get("sender") == "human":
            latest_message = message.get("message")
            break
    
    if not latest_message:
        logger.warning("No human message found for weather tool")
        tool_result = "I couldn't understand your weather query."
        state["tool_results"].append({
            "tool": "weather",
            "result": tool_result
        })
        return state
    
    message_lower = latest_message.lower()
    location = "local"  # Default to local
    
    # Try to extract location from query
    for pattern in PATTERNS["weather_patterns"]:
        match = re.search(pattern, message_lower)
        if match and 'location' in match.groupdict():
            location = match.group('location')
            break
    
    try:
        # Get the weather tool and execute it
        weather_tool = get_tool_by_name("get_weather")
        result = weather_tool(location=location)
        
        state["tool_results"].append({
            "tool": "weather",
            "result": result
        })
        
        logger.info(f"Weather tool result for {location}: {result}")
    except Exception as e:
        logger.error(f"Error executing weather tool: {e}")
        state["tool_results"].append({
            "tool": "weather",
            "result": f"I encountered an error trying to get the weather information for {location}."
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
    else:
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
        
        elif current_action in [ActionType.TIME_TOOL, ActionType.WEATHER_TOOL]:
            # Use the latest tool result
            tool_results = state.get("tool_results", [])
            if tool_results:
                latest_result = tool_results[-1].get("result", "I couldn't get the information you requested.")
                response = latest_result
            else:
                response = "I couldn't process your request. Please try again."
        
        else:
            # Direct conversation - use the chat history for context
            context = ""
            # Get up to 5 previous exchanges for context
            message_pairs = []
            human_msg = None
            
            for message in state["messages"]:
                if message.get("sender") == "human":
                    human_msg = message.get("message")
                elif message.get("sender") == "ai" and human_msg:
                    message_pairs.append((human_msg, message.get("message")))
                    human_msg = None
            
            # Get most recent 5 pairs
            context_pairs = message_pairs[-5:] if len(message_pairs) > 5 else message_pairs
            
            for human, ai in context_pairs:
                context += f"Human: {human}\nAssistant: {ai}\n\n"
            
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
    workflow.add_node("execute_weather_tool", execute_weather_tool)
    workflow.add_node("generate_response", generate_response)
    
    # Add conditional edges from router
    workflow.add_conditional_edges(
        "query_router",
        lambda state: state["current_action"],
        {
            ActionType.RAG: "perform_rag_retrieval",
            ActionType.TIME_TOOL: "execute_time_tool",
            ActionType.WEATHER_TOOL: "execute_weather_tool",
            ActionType.DIRECT: "generate_response"
        }
    )
    
    # Add remaining edges
    workflow.add_edge("perform_rag_retrieval", "generate_response")
    workflow.add_edge("execute_time_tool", "generate_response")
    workflow.add_edge("execute_weather_tool", "generate_response")
    workflow.add_edge("generate_response", END)
    
    # Set the entry point
    workflow.set_entry_point("query_router")
    
    return workflow.compile() 