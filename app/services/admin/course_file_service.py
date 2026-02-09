from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import Course, CourseFile
from app.core.s3 import upload_file_to_s3


class AdminCourseFileService:

    async def upload_course_file(
        self,
        db: AsyncSession,
        course_id: int,
        file: UploadFile,
        file_title: str | None,
        file_description: str | None,
        duration_seconds: int | None,
    ):
        # --------------------------------------------------
        # 1️⃣ Validate Course
        # --------------------------------------------------
        result = await db.execute(
            select(Course).where(Course.id == course_id)
        )
        course = result.scalar_one_or_none()

        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        # --------------------------------------------------
        # 2️⃣ Upload file to S3 (INLINE VIEW ENABLED)
        # --------------------------------------------------
        s3_result = await upload_file_to_s3(
            file=file,
            folder=f"Courses/{course_id}"
        )

        # --------------------------------------------------
        # 3️⃣ Detect file type
        # --------------------------------------------------
        if file.content_type == "application/pdf":
            file_type = "PDF"
        elif file.content_type and file.content_type.startswith("video/"):
            file_type = "VIDEO"
        else:
            file_type = "DOCUMENT"

        # --------------------------------------------------
        # 4️⃣ Save DB record
        # --------------------------------------------------
        course_file = CourseFile(
            course_id=course_id,
            file_name=file.filename,
            file_title=file_title or file.filename,
            file_description=file_description,
            duration_seconds=duration_seconds,
            file_type=file_type,
            file_size=s3_result["file_size"],
            mime_type=s3_result["content_type"],
            file_url=s3_result["file_url"],
            is_published=True,
            download_allowed=True,
        )

        db.add(course_file)
        await db.commit()
        await db.refresh(course_file)

        return course_file

    # --------------------------------------------------
    # LIST FILES
    # --------------------------------------------------
    async def list_course_files(
        self,
        db: AsyncSession,
        course_id: int
    ):
        result = await db.execute(
            select(CourseFile)
            .where(CourseFile.course_id == course_id)
            .order_by(CourseFile.created_at.desc())
        )
        return result.scalars().all()

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
