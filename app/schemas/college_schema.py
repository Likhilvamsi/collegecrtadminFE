from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# -------------------------------------------------
# BASE
# -------------------------------------------------
class CollegeBase(BaseModel):
    name: str = Field(..., max_length=200)
    code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None

    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None

    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = "India"

    established_year: Optional[int] = None


# -------------------------------------------------
# CREATE
# -------------------------------------------------
class CollegeCreate(CollegeBase):
    pass


# -------------------------------------------------
# UPDATE
# -------------------------------------------------
class CollegeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None

    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None

    established_year: Optional[int] = None
    is_active: Optional[bool] = None


# -------------------------------------------------
# RESPONSE
# -------------------------------------------------
class CollegeResponse(CollegeBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
