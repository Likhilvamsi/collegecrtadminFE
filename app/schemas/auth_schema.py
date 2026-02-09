from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal
from enum import Enum

# =========================================================
# LOGIN REQUEST
# =========================================================

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    COLLEGE_ADMIN = "COLLEGE_ADMIN"
    TEACHER = "TEACHER"
    STUDENT = "STUDENT"

class LoginRequest(BaseModel):
    email: str
    password: str
    role: UserRole



# =========================================================
# LOGIN RESPONSE
# =========================================================
class LoginResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    role: Literal[
        "ADMIN",
        "COLLEGE_ADMIN",
        "TEACHER",
        "STUDENT"
    ]


# =========================================================
# REGISTER REQUEST (OPTIONAL – FUTURE USE)
# =========================================================
class RegisterRequest(BaseModel):
    """
    Optional schema (for future self-registration if needed).
    Admin-controlled creation is recommended.
    """

    full_name: str
    email: EmailStr
    password: str
    role: Literal["STUDENT", "TEACHER"]


# =========================================================
# TOKEN PAYLOAD (INTERNAL USE)
# =========================================================
class TokenPayload(BaseModel):
    user_id: int
    role: str
    exp: int
