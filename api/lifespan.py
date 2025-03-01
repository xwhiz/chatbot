from motor.motor_asyncio import AsyncIOMotorClient
from decouple import config
from fastapi import FastAPI
from qdrant_client.http.models import Distance, VectorParams
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from contextlib import asynccontextmanager
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application initialization")
    
    # Connect to MongoDB
    CONNECTION_STRING = config("MONGODB_URI")
    app.mongodb_client = AsyncIOMotorClient(CONNECTION_STRING)
    app.database = app.mongodb_client.get_database("chatbot")

    ping_response = await app.mongodb_client.admin.command("ping")

    if int(ping_response["ok"]) != 1:
        logger.error("Could not connect to database")
        raise Exception("Could not connect to database")
    else:
        logger.info("Connected to database")

    # Initialize Qdrant vector database
    vectordb_path = config("VECTOR_DOC_DB_PATH")
    collection_name = config("COLLECTION_NAME")

    logger.info("Creating Qdrant client")
    client = QdrantClient(path=vectordb_path)

    if client.collection_exists(collection_name):
        logger.info(f"Collection {collection_name} already exists. Using the existing one.")
    else:
        logger.info(f"Creating collection: {collection_name}")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
        )

    app.client = client
    logger.info("Qdrant client created")

    # Initialize embeddings model
    logger.info("Creating embeddings model")
    embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")
    logger.info("Embeddings model created")

    # Initialize vector store
    logger.info("Creating vector store")
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings,
    )
    app.vector_store = vector_store
    logger.info("Vector store created")

    # Initialize LLM
    logger.info("Creating LLM")
    # Use a larger context window for the LLM to accommodate agent prompts
    llm = ChatOllama(model="llama3.1", num_ctx=12288, temperature=0.1)
    app.llm = llm
    logger.info("LLM created")
    
    # Set application version
    app.version = "1.0.0-langgraph"
    logger.info(f"Application version: {app.version}")

    logger.info("Application initialization complete")
    yield

    # Cleanup on shutdown
    app.mongodb_client.close()
    app.client.close()

    logger.info("Disconnected from database")
    logger.info("Disconnected from Qdrant client")
