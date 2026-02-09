from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# -------------------------------------------------
# COURSE ASSIGNMENT (College → Students)
# -------------------------------------------------
class CourseAssignRequest(BaseModel):
    course_id: int
    branch_id: int
    academic_year_id: int


# -------------------------------------------------
# COURSE ENROLLMENT RESPONSE (College/Admin View)
# -------------------------------------------------
class CourseEnrollmentResponse(BaseModel):
    id: int
    student_id: int
    course_id: int

    enrollment_status: str
    progress_percentage: float

    start_date: Optional[datetime]
    completion_date: Optional[datetime]
    last_accessed_at: Optional[datetime]

    class Config:
        from_attributes = True


# -------------------------------------------------
# STUDENT COURSE RESPONSE (Student View)
# -------------------------------------------------
class StudentCourseResponse(BaseModel):
    id: int
    course_id: int

    enrollment_status: str
    progress_percentage: float

    start_date: Optional[datetime]
    completion_date: Optional[datetime]

    class Config:
        from_attributes = True


# -------------------------------------------------
# STUDENT COURSE PROGRESS UPDATE (Student → API)
# -------------------------------------------------
class StudentCourseProgressUpdate(BaseModel):
    progress_percentage: float = Field(..., ge=0, le=100)


class CollegeCourseSummaryResponse(BaseModel):
    course_id: int
    course_title: str
    category: str | None
    level: str
    students_assigned: int
    students_completed: int

    class Config:
        from_attributes = True
