from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from datetime import datetime

from app.models.models import (
    Student,
    StudentCourse,
    Course
)
from app.schemas.enrollment_schema import StudentCourseProgressUpdate


class StudentCourseService:
    """
    Student → Course listing & progress update service
    """

    # -------------------------------------------------
    # LIST STUDENT COURSES
    # -------------------------------------------------
    async def list_student_courses(
        self,
        db: AsyncSession,
        student_user
    ):
        """
        List all courses assigned to the logged-in student
        """

        # Resolve student profile
        student = (
            await db.execute(
                select(Student)
                .where(Student.user_id == student_user.id)
            )
        ).scalar_one_or_none()

        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student profile not found"
            )

        enrollments = (
            await db.execute(
                select(StudentCourse)
                .where(StudentCourse.student_id == student.id)
            )
        ).scalars().all()

        response = []

        for enrollment in enrollments:
            course = (
                await db.execute(
                    select(Course)
                    .where(Course.id == enrollment.course_id)
                )
            ).scalar_one()

            response.append({
                "course_id": course.id,
                "course_title": course.title,
                "category": course.category,
                "level": course.level,
                "enrollment_status": enrollment.enrollment_status,
                "progress_percentage": enrollment.progress_percentage,
                "course_score": enrollment.course_score,
                "last_accessed_at": enrollment.last_accessed_at
            })

        return response

    # -------------------------------------------------
    # UPDATE COURSE PROGRESS
    # -------------------------------------------------
    async def update_course_progress(
        self,
        db: AsyncSession,
        student_user,
        course_id: int,
        payload: StudentCourseProgressUpdate
    ):
        """
        Update progress percentage for a course
        """

        # Resolve student profile
        student = (
            await db.execute(
                select(Student)
                .where(Student.user_id == student_user.id)
            )
        ).scalar_one_or_none()

        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student profile not found"
            )

        enrollment = (
            await db.execute(
                select(StudentCourse)
                .where(
                    StudentCourse.student_id == student.id,
                    StudentCourse.course_id == course_id
                )
            )
        ).scalar_one_or_none()

        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not assigned to this student"
            )

        # Update fields
        if payload.progress_percentage is not None:
            enrollment.progress_percentage = payload.progress_percentage

            # Auto-update status
            if payload.progress_percentage >= 100:
                enrollment.enrollment_status = "COMPLETED"
                enrollment.completion_date = datetime.utcnow()
            elif payload.progress_percentage > 0:
                enrollment.enrollment_status = "IN_PROGRESS"

        enrollment.last_accessed_at = datetime.utcnow()

        await db.commit()
        await db.refresh(enrollment)

        return {
            "course_id": course_id,
            "enrollment_status": enrollment.enrollment_status,
            "progress_percentage": enrollment.progress_percentage,
            "last_accessed_at": enrollment.last_accessed_at
        }
