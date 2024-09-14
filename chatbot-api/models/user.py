from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


class User(BaseModel):
    name: str = Field(...)
    email: EmailStr = Field(...)
    password: str = Field(...)
    role: str = Field(...)
    created_at: datetime = Field(default_factory=datetime.now)
