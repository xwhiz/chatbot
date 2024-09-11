from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from decouple import config


app = FastAPI()

CONNECTION_STRING = config()
