from motor.motor_asyncio import AsyncIOMotorClient
from decouple import config
from fastapi import FastAPI
from qdrant_client.http.models import Distance, VectorParams
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from contextlib import asynccontextmanager
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama


@asynccontextmanager
async def lifespan(app: FastAPI):
    CONNECTION_STRING = config("MONGODB_URI")

    app.mongodb_client = AsyncIOMotorClient(CONNECTION_STRING)
    app.database = app.mongodb_client.get_database("chatbot")

    ping_response = await app.mongodb_client.admin.command("ping")

    if int(ping_response["ok"]) != 1:
        raise Exception("Could not connect to database")
    else:
        print("Connected to database")

    # Startup event
    vectordb_path = config("VECTOR_DOC_DB_PATH")
    collection_name = config("COLLECTION_NAME")

    print("Creating Qdrant client")
    client = QdrantClient(path=vectordb_path)

    if client.collection_exists(collection_name):
        print(f"Collection {collection_name} already exists. Using the existing one.")
    else:
        print(f"Creating collection: {collection_name}")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=1024,
                distance=Distance.COSINE,
                on_disk=True,
            ),
        )

    app.client = client
    print("Qdrant client created")

    print("Creating embeddings")
    embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")
    print("Embeddings created")

    print("Creating vector store")
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings,
    )
    app.vector_store = vector_store
    print("Vector store created")

    # print("Creating retriever")
    # retriever = vector_store.as_retriever(
    #     search_type="similarity", search_kwargs={"k": 10, "score_threshold": 0.2}
    # )
    # print("Retriever created")

    print("Creating Llama")
    llm = ChatOllama(model="llama3.1", num_ctx=8192)
    app.llm = llm
    print("LLm created")

    yield

    app.mongodb_client.close()
    app.client.close()

    print("Disconnected from database")
    print("Disconnected from Qdrant client")
