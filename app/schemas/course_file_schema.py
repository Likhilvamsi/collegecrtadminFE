from pydantic import BaseModel
from datetime import datetime


class CourseFileResponse(BaseModel):
    id: int
    course_id: int
    file_name: str
    file_url: str
    created_at: datetime

    class Config:
        from_attributes = True
