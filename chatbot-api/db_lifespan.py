from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from decouple import config
from fastapi import FastAPI
from urllib.parse import quote


async def db_lifespan(app: FastAPI):
    CONNECTION_STRING = config("MONGODB_URI")

    app.mongodb_client = AsyncIOMotorClient(CONNECTION_STRING)
    app.database = app.mongodb_client.get_database("chatbot")

    ping_response = await app.mongodb_client.admin.command("ping")

    if int(ping_response["ok"]) != 1:
        raise Exception("Could not connect to database")
    else:
        print("Connected to database")

    yield

    app.mongodb_client.close()
