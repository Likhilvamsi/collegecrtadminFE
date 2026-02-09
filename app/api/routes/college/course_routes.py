from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.college.course_service import CollegeCourseService
from app.schemas.enrollment_schema import (
    CourseAssignRequest,
    CollegeCourseSummaryResponse
)

router = APIRouter(
    prefix="/api/college/courses",
    tags=["College - Courses"]
)

service = CollegeCourseService()


# -------------------------------------------------
# ASSIGN COURSE TO STUDENTS
# -------------------------------------------------
@router.post(
    "/assign",
    status_code=status.HTTP_201_CREATED
)
async def assign_course(
    payload: CourseAssignRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user = request.state.user

    if user.get("role") != "COLLEGE_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="College admin access only"
        )

    return await service.assign_course_to_students(
        db=db,
        college_admin_user=user,
        payload=payload
    )

# -------------------------------------------------
# LIST COURSES (COLLEGE SCOPE)
# -------------------------------------------------
@router.get(
    "",
    response_model=list[CollegeCourseSummaryResponse]
)
async def list_college_courses(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user = request.state.user

    if user.get("role") != "COLLEGE_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="College admin access only"
        )

    return await service.list_college_courses(
        db=db,
        college_admin_user=user
    )

# -------------------------------------------------
# LIST AVAILABLE COURSES FOR COLLEGE
# -------------------------------------------------
@router.get("/courses")
async def list_admin_courses_for_college(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user = request.state.user

    if user.get("role") != "COLLEGE_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="College admin access only"
        )

    return await service.get_admin_courses_for_college(
        db=db,
        college_admin_user=user
    )
