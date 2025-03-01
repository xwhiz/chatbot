"""
Simple CLI test script for the weather tool functionality.
This is useful for testing tool extraction and execution without running the full API.
"""

import asyncio
import sys
from tools import get_weather, get_tool_by_name
import re

# Define the weather patterns from agent_flow.py
WEATHER_PATTERNS = [
    r'weather (in|for|at) (?P<location>\w+)',
    r'what\'s the weather (like )?(in|at) (?P<location>\w+)',
    r'how\'s the weather (in|at) (?P<location>\w+)',
    r'(current|today\'s) weather (in|at) (?P<location>\w+)',
    r'weather forecast',
    r'weather report',
    r'what\'s the weather (like )?today',
    r'how\'s the weather today',
    r'what is the temperature'
]

def extract_location(query):
    """Extract location from a weather query using regex patterns."""
    query = query.lower()
    location = "local"  # Default
    
    # Try patterns with named groups first
    for pattern in WEATHER_PATTERNS:
        match = re.search(pattern, query)
        if match and hasattr(match, 'groupdict') and 'location' in match.groupdict():
            extracted_location = match.group('location')
            if extracted_location:
                location = extracted_location
                return location
    
    # Try simpler patterns as fallback
    location_patterns = [
        r'weather (in|for|at) (\w+)',
        r'what\'s the weather (like )?(in|at|for) (\w+)',
        r'how\'s the weather (in|at|for) (\w+)'
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, query)
        if match and len(match.groups()) >= 2:
            location = match.group(len(match.groups()))
            return location
    
    return location

def test_weather_tool():
    """Test the weather tool with a variety of queries."""
    test_queries = [
        "What's the weather in London?",
        "Weather in New York",
        "How's the weather today?",
        "Tell me the weather forecast for Tokyo",
        "Weather report for Sydney",
        "Current weather in local",
        "What is the temperature?",
        "How hot is it outside?",
        "Will it rain today?",
        "Weather conditions in Paris"
    ]
    
    print("====== Weather Tool Testing ======\n")
    
    for query in test_queries:
        print(f"Query: {query}")
        location = extract_location(query)
        print(f"Extracted location: {location}")
        
        try:
            result = get_weather(location)
            print(f"Result: {result}")
        except Exception as e:
            print(f"Error: {e}")
        
        print("-" * 50)

def interactive_test():
    """Run an interactive test allowing user to input weather queries."""
    print("====== Interactive Weather Tool Test ======")
    print("Type 'exit' or 'quit' to end the test")
    
    while True:
        query = input("\nEnter a weather query: ")
        
        if query.lower() in ['exit', 'quit']:
            break
        
        location = extract_location(query)
        print(f"Extracted location: {location}")
        
        try:
            result = get_weather(location)
            print(f"Result: {result}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    # Run the predefined tests
    test_weather_tool()
    
    # Offer interactive testing if desired
    choice = input("\nWould you like to try interactive testing? (y/n): ")
    if choice.lower() == 'y':
        interactive_test()
    
    print("\nWeather tool testing complete!") 