from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.models import (
    Student,
    StudentCourse,
    Course,
    Test,
    TestAttempt,
    StudentScore
)


class StudentDashboardService:
    """
    Student Dashboard Aggregation Service
    """

    async def get_dashboard_data(
        self,
        db: AsyncSession,
        student_user
    ):
        # -------------------------------------------------
        # 1️⃣ Resolve Student profile
        # -------------------------------------------------
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

        # -------------------------------------------------
        # 2️⃣ Student Info
        # -------------------------------------------------
        student_info = {
            "student_id": student.id,
            "student_name": student.user.full_name,
            "college": student.college.name,
            "branch": student.branch.branch_name,
            "academic_year": student.academic_year.year_name,
            "roll_number": student.roll_number,
            "student_unique_id": student.student_unique_id
        }

        # -------------------------------------------------
        # 3️⃣ Course Summary
        # -------------------------------------------------
        total_assigned = (
            await db.execute(
                select(func.count(StudentCourse.id))
                .where(StudentCourse.student_id == student.id)
            )
        ).scalar()

        completed_courses = (
            await db.execute(
                select(func.count(StudentCourse.id))
                .where(
                    StudentCourse.student_id == student.id,
                    StudentCourse.enrollment_status == "COMPLETED"
                )
            )
        ).scalar()

        course_summary = {
            "total_courses_assigned": total_assigned or 0,
            "total_courses_completed": completed_courses or 0
        }

        # -------------------------------------------------
        # 4️⃣ Assigned Courses Details
        # -------------------------------------------------
        assigned_courses = []

        enrollments = (
            await db.execute(
                select(StudentCourse)
                .where(StudentCourse.student_id == student.id)
            )
        ).scalars().all()

        for enrollment in enrollments:
            course = (
                await db.execute(
                    select(Course)
                    .where(Course.id == enrollment.course_id)
                )
            ).scalar_one()

            assigned_courses.append({
                "course_id": course.id,
                "course_title": course.title,
                "category": course.category,
                "level": course.level,
                "enrollment_status": enrollment.enrollment_status,
                "progress_percentage": enrollment.progress_percentage,
                "course_score": enrollment.course_score
            })

        # -------------------------------------------------
        # 5️⃣ Tests Summary
        # -------------------------------------------------
        tests_attempted = (
            await db.execute(
                select(func.count(TestAttempt.id))
                .where(TestAttempt.student_id == student.id)
            )
        ).scalar()

        tests_passed = (
            await db.execute(
                select(func.count(TestAttempt.id))
                .where(
                    TestAttempt.student_id == student.id,
                    TestAttempt.is_passed == True
                )
            )
        ).scalar()

        tests_summary = {
            "tests_attempted": tests_attempted or 0,
            "tests_passed": tests_passed or 0
        }

        # -------------------------------------------------
        # 6️⃣ Performance Summary
        # -------------------------------------------------
        score = (
            await db.execute(
                select(StudentScore)
                .where(StudentScore.student_id == student.id)
            )
        ).scalar_one_or_none()

        performance_summary = {
            "total_crt_score": score.total_crt_score if score else 0.0,
            "average_test_score": score.average_test_score if score else 0.0,
            "overall_percentage": score.overall_percentage if score else 0.0
        }

        # -------------------------------------------------
        # FINAL DASHBOARD RESPONSE
        # -------------------------------------------------
        return {
            "student_info": student_info,
            "course_summary": course_summary,
            "assigned_courses": assigned_courses,
            "tests_summary": tests_summary,
            "performance_summary": performance_summary
        }
