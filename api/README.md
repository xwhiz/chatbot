# Agentic Chatbot with LangGraph

This chatbot implements an agentic flow using LangGraph to intelligently route user queries to the appropriate handling mechanism:

- **RAG (Retrieval Augmented Generation)**: For information-seeking queries that require knowledge from the document database
- **Tool Execution**: For queries that can be answered by executing specific functions (time, date, calculations, etc.)
- **Direct Conversation**: For general conversational queries

## Architecture

The chatbot uses a LangGraph-based architecture with the following components:

1. **Query Router**: Intelligently classifies incoming queries
2. **RAG System**: Retrieves relevant information from the vector database
3. **Tool System**: Executes specific functions based on query intent
4. **Response Generator**: Creates coherent responses using the LLM

## Features

- **Intelligent Routing**: Automatically determines how to handle each query
- **Tool Registry**: Extensible system for adding new tools/functions
- **Contextual Conversation**: Maintains conversation history for context
- **Document Access Control**: Restricts document access based on user permissions
- **Custom Instructions**: Supports custom prompts per user
- **Streaming Responses**: Supports streaming responses for better UX

## Setup and Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with the following variables:
```
MONGODB_URI=mongodb://localhost:27017
VECTOR_DOC_DB_PATH=./qdrant_data
COLLECTION_NAME=documents
JWT_SECRET=your_secret_key
```

3. Start the API server:
```bash
./start.sh
```

## Agent Flow

The LangGraph agent follows this decision tree:

```
User Query → Query Router → RAG → Response Generator
                         → Time Tool → Response Generator  
                         → Calculator → Response Generator
                         → Calendar → Response Generator
                         → Direct → Response Generator
```

## Adding New Tools

To add a new tool to the agent:

1. Add a new tool function to `api/tools/__init__.py` using the `@register_tool` decorator:

```python
@register_tool
@tool
def my_new_tool(param1: str):
    """Description of what the tool does."""
    # Tool implementation
    return f"Result for {param1}"
```

2. Update the query router in `agent_flow.py` to recognize queries for this tool

## API Endpoints

- `POST /add-message`: Add a message to a chat
- `GET /generate-response/{chat_id}`: Generate a response using the agent
- `GET /health`: Health check endpoint
- Plus existing endpoints for authentication, chat management, document management, etc.

## Dependencies

- **FastAPI**: Web framework
- **LangGraph**: Agentic orchestration
- **LangChain**: LLM tooling
- **Qdrant**: Vector database
- **MongoDB**: Document database
- **Ollama**: Local LLM serving

## Environment Variables

| Variable | Description |
|----------|-------------|
| MONGODB_URI | MongoDB connection string |
| VECTOR_DOC_DB_PATH | Path to Qdrant database |
| COLLECTION_NAME | Vector collection name |
| JWT_SECRET | Secret for JWT authentication |

## Contributing

1. Follow the existing code style
2. Add tests for new features
3. Update documentation when adding features
4. Use descriptive commit messages
