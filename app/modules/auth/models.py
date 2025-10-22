from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    """Token response model"""

    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    """Login request model"""

    username_or_email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)


class RegisterRequest(BaseModel):
    """Registration request model"""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=6)


class ChangePasswordRequest(BaseModel):
    """Change password request model"""

    old_password: str
    new_password: str = Field(..., min_length=6)
