from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.models import College
from app.schemas.college_schema import CollegeCreate, CollegeUpdate


class AdminCollegeService:
    """
    Admin service for managing colleges (ASYNC SAFE, SOFT DELETE)
    """

    # -------------------------------------------------
    # CREATE COLLEGE
    # -------------------------------------------------
    async def create_college(
        self,
        db: AsyncSession,
        payload: CollegeCreate
    ) -> College:

        # Prevent duplicate college code
        existing = await db.scalar(
            select(College).where(College.code == payload.code)
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="College with this code already exists"
            )

        college = College(
            name=payload.name,
            code=payload.code,
            description=payload.description,
            email=payload.email,
            phone=payload.phone,
            website=payload.website,
            city=payload.city,
            state=payload.state,
            country=payload.country,
            established_year=payload.established_year,
            is_active=True  # controlled internally
        )

        db.add(college)
        await db.commit()
        await db.refresh(college)
        return college

    # -------------------------------------------------
    # LIST COLLEGES (ACTIVE ONLY)
    # -------------------------------------------------
    async def list_colleges(self, db: AsyncSession):
        result = await db.execute(
            select(College)
            .where(College.is_active.is_(True))
            .order_by(College.created_at.desc())
        )
        return result.scalars().all()

    # -------------------------------------------------
    # GET COLLEGE BY ID (ADMIN – ACTIVE / INACTIVE)
    # -------------------------------------------------
    async def get_college(
        self,
        db: AsyncSession,
        college_id: int
    ) -> College | None:
        return await db.scalar(
            select(College).where(College.id == college_id)
        )

    # -------------------------------------------------
    # UPDATE COLLEGE
    # -------------------------------------------------
    async def update_college(
        self,
        db: AsyncSession,
        college_id: int,
        payload: CollegeUpdate
    ) -> College:

        college = await self.get_college(db, college_id)
        if not college:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="College not found"
            )

        update_data = payload.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(college, field, value)

        await db.commit()
        await db.refresh(college)
        return college

    # -------------------------------------------------
    # DELETE COLLEGE (SOFT DELETE)
    # -------------------------------------------------
    async def delete_college(
        self,
        db: AsyncSession,
        college_id: int
    ) -> None:

        college = await self.get_college(db, college_id)
        if not college or not college.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="College not found"
            )

        college.is_active = False
        await db.commit()

    async def get_admin_courses_for_college(
        self,
        db: AsyncSession,
        college_admin_user: dict
    ):
        # 1️⃣ Get college_id from college_admin
        result = await db.execute(
            select(CollegeAdmin)
            .where(CollegeAdmin.user_id == college_admin_user["id"])
        )
        college_admin = result.scalar_one_or_none()

        if not college_admin:
            raise HTTPException(
                status_code=404,
                detail="College admin record not found"
            )

        college_id = college_admin.college_id

        # 2️⃣ Fetch ADMIN-provided courses for this college
        result = await db.execute(
            select(Course)
            .where(
                Course.college_id == college_id,
                Course.is_active == True,
                Course.is_published == True
            )
            .order_by(Course.created_at.desc())
        )

        courses = result.scalars().all()

        # 3️⃣ Response shaping
        return {
            "college_id": college_id,
            "total_courses": len(courses),
            "courses": [
                {
                    "course_id": course.id,
                    "title": course.title,
                    "category": course.category,
                    "level": course.level,
                    "description": course.description,
                    "thumbnail_url": course.thumbnail_url,
                    "duration_hours": course.duration_hours,
                    "expected_completion_days": course.expected_completion_days,
                    "created_at": course.created_at,
                }
                for course in courses
            ]
        }
