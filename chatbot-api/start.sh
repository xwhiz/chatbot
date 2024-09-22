#!/bin/bash

# Start Ollama in the background
ollama serve &

# Wait for Ollama to start up
sleep 10

# Pull the llama3.1 model
ollama pull llama3.1

# Start the FastAPI application
uvicorn main:app --host 0.0.0.0 --port 8000
