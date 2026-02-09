from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.models import (
    College,
    CollegeAdmin,
    AcademicYear,
    CollegeBranch,
    Student,
    Course,
    StudentCourse,
    StudentScore,
    Ranking,
    User,
)


class DashboardService:
    """
    Handles BOTH:
    - ADMIN dashboard
    - COLLEGE ADMIN dashboard
    """

    # =====================================================
    # ADMIN DASHBOARD
    # =====================================================
    async def get_admin_dashboard(self, db: AsyncSession):

        total_colleges = await db.scalar(
            select(func.count(College.id))
        ) or 0

        total_students = await db.scalar(
            select(func.count(Student.id))
        ) or 0

        avg_completion = await db.scalar(
            select(func.avg(StudentCourse.progress_percentage))
        ) or 0.0

        avg_score = await db.scalar(
            select(func.avg(StudentCourse.course_score))
        ) or 0.0

        overview = {
            "total_colleges": total_colleges,
            "total_students": total_students,
            "avg_completion": round(avg_completion, 2),
            "avg_score": round(avg_score, 2),
        }

        # ---------------- RANKINGS ----------------
        ranking_stmt = (
            select(
                College.name.label("college"),
                func.avg(StudentCourse.progress_percentage).label("completion"),
                func.avg(StudentCourse.course_score).label("points"),
            )
            .join(Student, Student.college_id == College.id)
            .join(StudentCourse, StudentCourse.student_id == Student.id)
            .group_by(College.id)
            .order_by(func.avg(StudentCourse.course_score).desc())
        )

        ranking_rows = await db.execute(ranking_stmt)

        rankings = []
        for idx, row in enumerate(ranking_rows.all(), start=1):
            rankings.append({
                "rank": idx,
                "college": row.college,
                "completion": round(row.completion or 0, 2),
                "points": round(row.points or 0, 2),
            })

        # ---------------- COURSE ADOPTION ----------------
        course_stmt = (
            select(
                Course.title.label("course"),
                func.count(func.distinct(College.id)).label("college_count"),
            )
            .join(StudentCourse, StudentCourse.course_id == Course.id)
            .join(Student, Student.id == StudentCourse.student_id)
            .join(College, College.id == Student.college_id)
            .group_by(Course.id)
        )

        course_rows = await db.execute(course_stmt)

        course_adoption = []
        for row in course_rows.all():
            percent = (
                (row.college_count / total_colleges) * 100
                if total_colleges else 0
            )

            course_adoption.append({
                "course": row.course,
                "adoption_percent": round(percent),
                "adopted_by": f"{row.college_count} of {total_colleges} colleges",
            })

        return {
            "overview": overview,
            "rankings": rankings,
            "course_adoption": course_adoption,
        }

    # =====================================================
    # COLLEGE ADMIN DASHBOARD
    # =====================================================
    async def get_college_dashboard(self, db: AsyncSession, user: dict):

        if user.get("role") != "COLLEGE_ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="College admin access only",
            )

        user_id = user.get("id")

        college_admin = await db.scalar(
            select(CollegeAdmin).where(CollegeAdmin.user_id == user_id)
        )

        if not college_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="College admin not mapped to any college",
            )

        college_id = college_admin.college_id

        college = await db.scalar(
            select(College).where(College.id == college_id)
        )

        if not college:
            raise HTTPException(status_code=404, detail="College not found")

        return {
            "college_info": {
                "college_id": college.id,
                "college_name": college.name,
                "city": college.city,
            }
        }
