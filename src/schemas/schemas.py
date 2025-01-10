from pydantic import BaseModel, EmailStr
from typing import Optional

# Pydantic model for user registration
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

# Pydantic model for user login
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Pydantic model for JWT token response
class Token(BaseModel):
    access_token: str
    token_type: str
