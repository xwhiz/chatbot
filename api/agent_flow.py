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
        return ActionType.DIRECT
    
    # Convert message to lowercase for pattern matching
    message_lower = latest_message.lower()
    
    # Try quick pattern matching first to avoid LLM call for obvious cases
    
    # Check time-related patterns
    for pattern in PATTERNS["time_patterns"]:
        if re.search(pattern, message_lower):
            logger.info("Pattern matched: time tool")
            state["current_action"] = ActionType.TIME_TOOL
            return ActionType.TIME_TOOL
            
    for pattern in PATTERNS["date_patterns"]:
        if re.search(pattern, message_lower):
            logger.info("Pattern matched: time tool (date)")
            state["current_action"] = ActionType.TIME_TOOL
            return ActionType.TIME_TOOL
    
    for pattern in PATTERNS["day_patterns"]:
        if re.search(pattern, message_lower):
            logger.info("Pattern matched: time tool (day)")
            state["current_action"] = ActionType.TIME_TOOL
            return ActionType.TIME_TOOL
    
    # Check weather patterns
    for pattern in PATTERNS["weather_patterns"]:
        if re.search(pattern, message_lower):
            logger.info("Pattern matched: weather tool")
            state["current_action"] = ActionType.WEATHER_TOOL
            return ActionType.WEATHER_TOOL
    
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
            return ActionType.DIRECT
    
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
        query_type = llm.invoke(classification_prompt).strip().lower()
        
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
            # Format the retrieved information with sources
            retrieved_content = ""
            for i, doc in enumerate(docs, 1):
                source = doc.metadata.get('source', 'Unknown source')
                retrieved_content += f"SOURCE {i}: {source}\n"
                retrieved_content += f"CONTENT: {doc.page_content}\n\n"
            
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
    
    # Check for time patterns
    time_requested = any(re.search(pattern, lower_message) for pattern in PATTERNS["time_patterns"])
    date_requested = any(re.search(pattern, lower_message) for pattern in PATTERNS["date_patterns"])
    day_requested = any(re.search(pattern, lower_message) for pattern in PATTERNS["day_patterns"])
    
    # Use tools from registry instead of directly defining them
    if time_requested or not (date_requested or day_requested):
        time_tool = get_tool_by_name("get_current_time")
        if time_tool:
            result = time_tool()
            tool_results.append({"tool": "get_current_time", "result": result})
    
    if date_requested:
        date_tool = get_tool_by_name("get_current_date")
        if date_tool:
            result = date_tool()
            tool_results.append({"tool": "get_current_date", "result": result})
    
    if day_requested:
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

def execute_weather_tool(state: ChatState):
    """
    Execute weather-related tools based on the query.
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
        return "generate_response"
    
    lower_message = latest_message.lower()
    tool_results = []
    
    # Try to extract location from the query
    location = "local"  # Default to local weather
    
    for pattern in PATTERNS["weather_patterns"]:
        match = re.search(pattern, lower_message)
        if match and hasattr(match, 'groupdict') and 'location' in match.groupdict():
            extracted_location = match.group('location')
            if extracted_location:
                location = extracted_location
                break
    
    # Extract location using simple pattern if not found with named group
    if location == "local":
        location_patterns = [
            r'weather (in|for|at) (\w+)',
            r'what\'s the weather (like )?(in|at|for) (\w+)',
            r'how\'s the weather (in|at|for) (\w+)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, lower_message)
            if match and len(match.groups()) >= 2:
                location = match.group(len(match.groups()))
                break
    
    # Call the weather tool
    weather_tool = get_tool_by_name("get_weather")
    if weather_tool:
        try:
            result = weather_tool(location)
            tool_results.append({"tool": "get_weather", "location": location, "result": result})
            logger.info(f"Got weather for {location}")
        except Exception as e:
            logger.error(f"Error getting weather: {e}")
            tool_results.append({"tool": "get_weather", "error": f"Could not get weather for {location}: {str(e)}"})
    else:
        logger.error("Weather tool not found")
        tool_results.append({"tool": "get_weather", "error": "Weather tool not available"})
    
    state["tool_results"] = tool_results
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
    
    # Get conversation history for context
    message_history = []
    for message in state["messages"][-6:-1]:  # Get up to 5 previous messages, excluding the current one
        if message.get("sender") == "human":
            message_history.append(f"Human: {message.get('message')}")
        else:
            message_history.append(f"Assistant: {message.get('message')}")
    
    conversation_context = "\n".join(message_history)
    if conversation_context:
        conversation_context = f"Previous conversation:\n{conversation_context}\n\n"
    
    # Construct the prompt based on the current action
    if current_action == ActionType.RAG and state.get("rag_results"):
        # Use retrieved context in prompt
        prompt = f"""
        You are a helpful assistant. Answer based on the following retrieved documents and previous conversation.
        
        {conversation_context}
        RETRIEVED INFORMATION:
        {state["rag_results"]}
        
        USER QUERY:
        {latest_message}
        
        Provide a comprehensive and accurate response based on the retrieved information.
        Include citations to the sources when appropriate.
        If the retrieved information doesn't fully answer the query, acknowledge that and provide
        the best answer you can with what's available.
        """
    elif state.get("tool_results"):
        # Use tool results in prompt
        tool_outputs = "\n".join([f"{tr.get('tool', 'Unknown tool')}: {tr.get('result', 'No result')}" for tr in state["tool_results"]])
        prompt = f"""
        You are a helpful assistant. Based on the tool execution results and previous conversation:
        
        {conversation_context}
        TOOL RESULTS:
        {tool_outputs}
        
        USER QUERY:
        {latest_message}
        
        Provide a natural and helpful response that incorporates the tool results.
        """
    else:
        # Direct conversation
        prompt = f"""
        You are a helpful assistant. Respond to the following query based on previous conversation:
        
        {conversation_context}
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
    
    # Set the entry point
    workflow.set_entry_point("query_router")
    
    return workflow.compile() 