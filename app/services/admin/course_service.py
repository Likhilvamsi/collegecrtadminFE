from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.models import Course
from app.schemas.course_schema import CourseCreate, CourseUpdate


class AdminCourseService:
    """
    Admin service for managing courses (ASYNC SAFE)
    """

    # -------------------------------------------------
    # CREATE COURSE
    # -------------------------------------------------
    async def create_course(
        self,
        db: AsyncSession,
        payload: CourseCreate
    ) -> Course:

        # Optional: prevent duplicate course code
        existing = await db.scalar(
            select(Course).where(Course.course_code == payload.course_code)
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Course with this course_code already exists"
            )

        course = Course(
            teacher_id=payload.teacher_id,
            title=payload.title,
            description=payload.description,
            course_code=payload.course_code,
            category=payload.category,
            level=payload.level,
            duration_hours=payload.duration_hours,
            expected_completion_days=payload.expected_completion_days,
            thumbnail_url=payload.thumbnail_url,

            # ✅ CONTROLLED INTERNALLY
            is_active=True,
            is_published=False
        )

        db.add(course)
        await db.commit()
        await db.refresh(course)
        return course

    # -------------------------------------------------
    # LIST COURSES
    # -------------------------------------------------
    async def list_courses(self, db: AsyncSession):
        result = await db.execute(
            select(Course)
            .where(Course.is_active == True)
            .order_by(Course.created_at.desc())
        )
        return result.scalars().all()

    # -------------------------------------------------
    # GET COURSE
    # -------------------------------------------------
    async def get_course(self, db: AsyncSession, course_id: int):
        return await db.scalar(
            select(Course).where(Course.id == course_id)
        )

    # -------------------------------------------------
    # UPDATE COURSE
    # -------------------------------------------------
    async def update_course(
        self,
        db: AsyncSession,
        course_id: int,
        payload: CourseUpdate
    ):
        course = await self.get_course(db, course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(course, field, value)

        await db.commit()
        await db.refresh(course)
        return course

    # -------------------------------------------------
    # DELETE COURSE (SOFT DELETE)
    # -------------------------------------------------
    async def delete_course(self, db: AsyncSession, course_id: int):
        course = await self.get_course(db, course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        course.is_active = False
        await db.commit()
