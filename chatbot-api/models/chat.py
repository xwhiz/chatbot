from pydantic import BaseModel, Field


class Chat(BaseModel):
    title: str = Field(default_factory=str)
    user_email: str = Field(...)
    messages: list[dict] = Field(default_factory=list)
