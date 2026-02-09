from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime


# -------------------------------------------------
# BASE
# -------------------------------------------------
class StudentBase(BaseModel):
    name: str = Field(..., max_length=200)
    email: EmailStr
    roll_number: str = Field(..., max_length=50)

    phone: Optional[str] = None

    academic_year_id: int
    branch_id: int
    college_id: int


# -------------------------------------------------
# CREATE
# -------------------------------------------------
class StudentCreate(StudentBase):
    password: str = Field(..., min_length=6)


# -------------------------------------------------
# UPDATE
# -------------------------------------------------
class StudentUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[str] = None
    academic_year_id: Optional[int] = None
    branch_id: Optional[int] = None
    is_active: Optional[bool] = None


# -------------------------------------------------
# RESPONSE
# -------------------------------------------------
class StudentResponse(StudentBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
