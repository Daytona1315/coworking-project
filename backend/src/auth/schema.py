import uuid
from pydantic import BaseModel


class BaseUser(BaseModel):
    email: str
    username: str

    class Config:
        from_attributes = True


class UserCreate(BaseUser):
    password: str


class User(BaseUser):
    id: uuid.UUID

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class Token(BaseModel):
    access_token: str
    token_type: str = 'bearer'
