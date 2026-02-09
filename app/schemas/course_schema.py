from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


# -------------------------------------------------
# ENUMS
# -------------------------------------------------
class CourseLevel(str, Enum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"


# -------------------------------------------------
# BASE
# -------------------------------------------------
class CourseBase(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    course_code: str = Field(..., max_length=50)

    category: Optional[str] = None
    level: CourseLevel = CourseLevel.BEGINNER

    duration_hours: Optional[int] = None
    expected_completion_days: Optional[int] = None

    thumbnail_url: Optional[str] = None


# -------------------------------------------------
# CREATE
# -------------------------------------------------
class CourseCreate(CourseBase):
    teacher_id: Optional[int] = None
    # Admin can create course without assigning teacher initially


# -------------------------------------------------
# UPDATE
# -------------------------------------------------
class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    level: Optional[CourseLevel] = None

    duration_hours: Optional[int] = None
    expected_completion_days: Optional[int] = None
    thumbnail_url: Optional[str] = None


# -------------------------------------------------
# RESPONSE
# -------------------------------------------------
class CourseResponse(CourseBase):
    id: int
    teacher_id: Optional[int]

    is_active: bool
    is_published: bool
    created_at: datetime

    class Config:
        from_attributes = True
