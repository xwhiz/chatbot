from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


class User(BaseModel):
    name: str = Field(...)
    email: EmailStr = Field(...)
    password: str = Field(...)
    role: str = Field(...)
    # i need a field called accessible_docs which have the default value of ['all']
    accessible_docs: list = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
