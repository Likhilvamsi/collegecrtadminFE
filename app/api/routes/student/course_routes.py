from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.utils.decorators import require_permission
from app.services.student.course_service import StudentCourseService
from app.schemas.enrollment_schema import (
    StudentCourseProgressUpdate,
    StudentCourseResponse
)

router = APIRouter(
    prefix="/api/student/courses",
    tags=["Student - Courses"]
)

service = StudentCourseService()


# -------------------------------------------------
# LIST ASSIGNED COURSES
# -------------------------------------------------
@router.get(
    "",
    response_model=list[StudentCourseResponse],
    dependencies=[Depends(require_permission("view", "student_courses"))]
)
async def list_my_courses(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    List courses assigned to the logged-in student
    """

    user = request.state.user

    if user.role.name != "STUDENT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access only"
        )

    return await service.list_student_courses(
        db=db,
        student_user=user
    )


# -------------------------------------------------
# UPDATE COURSE PROGRESS
# -------------------------------------------------
@router.patch(
    "/{course_id}/progress",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("update", "student_courses"))]
)
async def update_course_progress(
    course_id: int,
    payload: StudentCourseProgressUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Update progress for a course (percentage, last accessed)
    """

    user = request.state.user

    if user.role.name != "STUDENT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access only"
        )

    return await service.update_course_progress(
        db=db,
        student_user=user,
        course_id=course_id,
        payload=payload
    )
