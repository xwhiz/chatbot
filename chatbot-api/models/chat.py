from uuid import uuid4
from pydantic import BaseModel, Field


class Chat(BaseModel):
    title: str = Field(default_factory=str)
    chat_id: str = Field(default_factory=uuid4)
    user_email: str = Field(...)
    messages: list[dict] = Field(default_factory=list)
