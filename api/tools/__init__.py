"""
Tools registry for the chatbot agent.

This module provides a central registry for all tools that can be used by the agent.
"""

from langchain_core.tools import tool
from datetime import datetime
import logging
from typing import Dict, Callable, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Tool registry
TOOL_REGISTRY: Dict[str, Callable] = {}

def register_tool(tool_func: Callable) -> Callable:
    """Register a tool function in the registry."""
    TOOL_REGISTRY[tool_func.__name__] = tool_func
    return tool_func

# Time and date tools
@register_tool
@tool
def get_current_time():
    """Get the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@register_tool
@tool
def get_current_date():
    """Get the current date."""
    return datetime.now().strftime("%Y-%m-%d")

@register_tool
@tool
def get_day_of_week():
    """Get the current day of the week."""
    return datetime.now().strftime("%A")

# Calendar tools - placeholders for future implementation
@register_tool
@tool
def list_upcoming_events(days: int = 7):
    """List upcoming events in the calendar for the next n days."""
    # Placeholder implementation
    return f"Would show events for the next {days} days (functionality not implemented yet)"

# Calculator tool
@register_tool
@tool
def calculate(expression: str):
    """Evaluate a mathematical expression."""
    try:
        # Use eval with restricted globals for safety
        result = eval(expression, {"__builtins__": {}}, {"abs": abs, "round": round, "min": min, "max": max})
        return f"Result: {result}"
    except Exception as e:
        return f"Error calculating '{expression}': {str(e)}"

def get_all_tools() -> List[Callable]:
    """Get all registered tools."""
    return list(TOOL_REGISTRY.values())

def get_tool_by_name(name: str) -> Callable:
    """Get a tool by name."""
    return TOOL_REGISTRY.get(name)

def get_tool_descriptions() -> List[Dict[str, Any]]:
    """Get descriptions of all tools for LLM consumption."""
    return [
        {
            "name": name,
            "description": func.__doc__ or "No description available.",
            "function": func
        }
        for name, func in TOOL_REGISTRY.items()
    ] 