from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.utils.decorators import require_permission
from app.services.admin.course_service import AdminCourseService
from app.schemas.course_schema import (
    CourseCreate,
    CourseUpdate,
    CourseResponse
)

router = APIRouter(
    prefix="/api/admin/courses",
    tags=["Admin - Courses"]
)

service = AdminCourseService()


# -------------------------------------------------
# CREATE COURSE
# -------------------------------------------------
@router.post(
    "",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("create", "courses"))]
)
async def create_course(
    payload: CourseCreate,
    db: AsyncSession = Depends(get_db)
):
    return await service.create_course(db, payload)


# -------------------------------------------------
# LIST COURSES
# -------------------------------------------------
@router.get(
    "",
    response_model=list[CourseResponse],
    dependencies=[Depends(require_permission("view", "courses"))]
)
async def list_courses(
    db: AsyncSession = Depends(get_db)
):
    return await service.list_courses(db)


# -------------------------------------------------
# GET COURSE BY ID
# -------------------------------------------------
@router.get(
    "/{course_id}",
    response_model=CourseResponse,
    dependencies=[Depends(require_permission("view", "courses"))]
)
async def get_course(
    course_id: int,
    db: AsyncSession = Depends(get_db)
):
    course = await service.get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    return course


# -------------------------------------------------
# UPDATE COURSE
# -------------------------------------------------
@router.put(
    "/{course_id}",
    response_model=CourseResponse,
    dependencies=[Depends(require_permission("edit", "courses"))]
)
async def update_course(
    course_id: int,
    payload: CourseUpdate,
    db: AsyncSession = Depends(get_db)
):
    return await service.update_course(db, course_id, payload)


# -------------------------------------------------
# DELETE COURSE
# -------------------------------------------------
@router.delete(
    "/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("delete", "courses"))]
)
async def delete_course(
    course_id: int,
    db: AsyncSession = Depends(get_db)
):
    await service.delete_course(db, course_id)
    return None
