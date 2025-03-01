"""
Tools registry for the chatbot agent.

This module provides a central registry for all tools that can be used by the agent.
"""

from langchain_core.tools import tool
from datetime import datetime
import logging
import random
from typing import Dict, Callable, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Tool registry
TOOL_REGISTRY: Dict[str, Callable] = {}

def register_tool(tool_func: Callable) -> Callable:
    """Register a tool function in the registry."""
    # Check if the tool_func is a StructuredTool or similar with a 'name' attribute
    if hasattr(tool_func, 'name'):
        TOOL_REGISTRY[tool_func.name] = tool_func
    else:
        # Fall back to __name__ for regular functions
        TOOL_REGISTRY[tool_func.__name__] = tool_func
    return tool_func

@tool
@register_tool
def get_current_time():
    """Get the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@tool
@register_tool
def get_day_date_time() -> str:
    """Get the current day, date, and time."""
    return datetime.now().strftime("%A, %B %d, %Y %I:%M %p")


@tool
@register_tool
def get_current_date():
    """Get the current date."""
    return datetime.now().strftime("%Y-%m-%d")

@tool
@register_tool
def get_day_of_week():
    """Get the current day of the week."""
    return datetime.now().strftime("%A")

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