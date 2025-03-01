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

# Time and date tools
@tool
@register_tool
def get_current_time():
    """Get the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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

# Weather tool - uses dummy data for demonstration
@tool
@register_tool
def get_weather(location: str = "local"):
    """Get the current weather for a specified location. Defaults to local weather if no location provided."""
    # This is a dummy implementation for demonstration purposes
    # In a real implementation, you would connect to a weather API
    
    # Map of sample weather conditions for demonstration
    weather_conditions = {
        "local": {
            "temperature": random.randint(65, 85),
            "condition": random.choice(["Sunny", "Partly Cloudy", "Cloudy", "Rainy", "Thunderstorms"]),
            "humidity": random.randint(30, 80),
            "wind_speed": random.randint(0, 20),
        },
        "new york": {
            "temperature": random.randint(50, 85),
            "condition": random.choice(["Sunny", "Partly Cloudy", "Cloudy", "Rainy", "Foggy"]),
            "humidity": random.randint(30, 70),
            "wind_speed": random.randint(5, 25),
        },
        "london": {
            "temperature": random.randint(45, 70),
            "condition": random.choice(["Cloudy", "Rainy", "Foggy", "Drizzle", "Partly Cloudy"]),
            "humidity": random.randint(50, 90),
            "wind_speed": random.randint(5, 20),
        },
        "tokyo": {
            "temperature": random.randint(55, 80),
            "condition": random.choice(["Sunny", "Partly Cloudy", "Rainy", "Humid", "Clear"]),
            "humidity": random.randint(40, 85),
            "wind_speed": random.randint(2, 18),
        },
        "sydney": {
            "temperature": random.randint(65, 85),
            "condition": random.choice(["Sunny", "Clear", "Partly Cloudy", "Breezy", "Warm"]),
            "humidity": random.randint(30, 70),
            "wind_speed": random.randint(5, 25),
        }
    }
    
    # Default to local if location not found in our sample data
    location = location.lower()
    weather = weather_conditions.get(location, weather_conditions["local"])
    
    return f"Weather for {location.title()}: {weather['temperature']}°F, {weather['condition']}, " \
           f"Humidity: {weather['humidity']}%, Wind: {weather['wind_speed']} mph"

# Calendar tools - placeholders for future implementation
@tool
@register_tool
def list_upcoming_events(days: int = 7):
    """List upcoming events in the calendar for the next n days."""
    # Placeholder implementation
    return f"Would show events for the next {days} days (functionality not implemented yet)"

# Calculator tool
@tool
@register_tool
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