from fastapi import HTTPException, status
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

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


class CollegeDashboardService:
    """
    College Admin Dashboard Service (ASYNC SAFE)
    """

    async def get_dashboard_data(self, db: AsyncSession, user: dict):

        # -------------------------------------------------
        # 0️⃣ Role validation
        # -------------------------------------------------
        if user.get("role") != "COLLEGE_ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="College admin access only"
            )

        user_id = user.get("id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )

        # -------------------------------------------------
        # 1️⃣ Resolve college mapping
        # -------------------------------------------------
        college_admin = await db.scalar(
            select(CollegeAdmin).where(CollegeAdmin.user_id == user_id)
        )

        if not college_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="College admin is not assigned to any college"
            )

        college_id = college_admin.college_id

        # -------------------------------------------------
        # 2️⃣ College basic info
        # -------------------------------------------------
        college = await db.scalar(
            select(College).where(College.id == college_id)
        )

        if not college:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="College not found"
            )

        college_info = {
            "college_id": college.id,
            "college_name": college.name,
            "city": college.city,
            "established_year": college.established_year,
            "total_students": await db.scalar(
                select(func.count(Student.id))
                .where(Student.college_id == college_id)
            ) or 0,
            "total_branches": await db.scalar(
                select(func.count(CollegeBranch.id))
                .where(CollegeBranch.college_id == college_id)
            ) or 0,
            "total_courses": await db.scalar(
                select(func.count(Course.id))
            ) or 0,
        }

        # -------------------------------------------------
        # 3️⃣ Academic year summary
        # -------------------------------------------------
        academic_years_data = []

        years = (
            await db.execute(
                select(AcademicYear)
                .where(AcademicYear.college_id == college_id)
            )
        ).scalars().all()

        for year in years:
            academic_years_data.append({
                "academic_year_id": year.id,
                "year_name": year.year_name,
                "students_count": await db.scalar(
                    select(func.count(Student.id))
                    .where(Student.academic_year_id == year.id)
                ) or 0
            })

        # -------------------------------------------------
        # 4️⃣ Branch-wise summary
        # -------------------------------------------------
        branches_data = []

        branches = (
            await db.execute(
                select(CollegeBranch)
                .where(CollegeBranch.college_id == college_id)
            )
        ).scalars().all()

        for branch in branches:

            avg_score = await db.scalar(
                select(func.avg(StudentScore.total_crt_score))
                .join(Student)
                .where(Student.branch_id == branch.id)
            ) or 0.0

            total_enrollments = await db.scalar(
                select(func.count(StudentCourse.id))
                .join(Student)
                .where(Student.branch_id == branch.id)
            ) or 0

            completed_enrollments = await db.scalar(
                select(func.count(StudentCourse.id))
                .join(Student)
                .where(
                    Student.branch_id == branch.id,
                    StudentCourse.enrollment_status == "COMPLETED"
                )
            ) or 0

            avg_completion = (
                (completed_enrollments / total_enrollments) * 100
                if total_enrollments > 0 else 0.0
            )

            branches_data.append({
                "branch_id": branch.id,
                "branch_name": branch.branch_name,
                "branch_code": branch.branch_code,
                "total_students": await db.scalar(
                    select(func.count(Student.id))
                    .where(Student.branch_id == branch.id)
                ) or 0,
                "average_crt_score": round(avg_score, 2),
                "average_course_completion": round(avg_completion, 2)
            })

        # -------------------------------------------------
        # 5️⃣ Course allocation summary
        # -------------------------------------------------
        courses_data = []

        courses = (
            await db.execute(
                select(Course)
            )
        ).scalars().all()

        for course in courses:
            courses_data.append({
                "course_id": course.id,
                "course_title": course.title,
                "category": course.category,
                "level": course.level,
                "students_assigned": await db.scalar(
                    select(func.count(StudentCourse.id))
                    .where(StudentCourse.course_id == course.id)
                ) or 0,
                "students_completed": await db.scalar(
                    select(func.count(StudentCourse.id))
                    .where(
                        StudentCourse.course_id == course.id,
                        StudentCourse.enrollment_status == "COMPLETED"
                    )
                ) or 0,
                "average_course_score": round(
                    await db.scalar(
                        select(func.avg(StudentCourse.course_score))
                        .where(StudentCourse.course_id == course.id)
                    ) or 0.0,
                    2
                )
            })

        # -------------------------------------------------
        # 6️⃣ Top students
        # -------------------------------------------------
        top_students_data = []

        result = await db.execute(
            select(
                Student.id,
                User.full_name,
                CollegeBranch.branch_name,
                AcademicYear.year_name,
                Ranking.score_at_ranking,
                Ranking.rank_position,
            )
            .join(Ranking, Ranking.student_id == Student.id)
            .join(User, User.id == Student.user_id)
            .join(CollegeBranch, CollegeBranch.id == Student.branch_id)
            .join(AcademicYear, AcademicYear.id == Student.academic_year_id)
            .where(
                Ranking.college_id == college_id,
                Ranking.ranking_type == "COLLEGE_OVERALL"
            )
            .order_by(Ranking.rank_position)
            .limit(5)
        )

        for row in result.all():
            top_students_data.append({
                "student_id": row.id,
                "student_name": row.full_name,
                "branch": row.branch_name,
                "academic_year": row.year_name,
                "crt_score": row.score_at_ranking,
                "college_rank": row.rank_position
            })

        # -------------------------------------------------
        # 7️⃣ Students overview (NEW)
        # -------------------------------------------------
        students_overview = []

        result = await db.execute(
            select(
                Student.id,
                User.full_name,
                User.email,
                Student.roll_number,
                CollegeBranch.branch_name,
                AcademicYear.year_name,
                func.count(StudentCourse.id).label("assigned"),
                func.sum(
                    case(
                        (StudentCourse.enrollment_status == "COMPLETED", 1),
                        else_=0
                    )
                ).label("completed")
            )
            .join(User, User.id == Student.user_id)
            .join(CollegeBranch, CollegeBranch.id == Student.branch_id)
            .join(AcademicYear, AcademicYear.id == Student.academic_year_id)
            .outerjoin(StudentCourse, StudentCourse.student_id == Student.id)
            .where(Student.college_id == college_id)
            .group_by(
                Student.id,
                User.full_name,
                User.email,
                Student.roll_number,
                CollegeBranch.branch_name,
                AcademicYear.year_name
            )
        )

        for r in result.all():
            completion = (r.completed / r.assigned * 100) if r.assigned else 0

            students_overview.append({
                "student_id": r.id,
                "name": r.full_name,
                "email": r.email,
                "roll_no": r.roll_number,
                "department": r.branch_name,
                "academic_year": r.year_name,
                "courses_assigned": r.assigned,
                "courses_completed": r.completed,
                "course_completion_percentage": round(completion, 2)
            })

        # -------------------------------------------------
        # 8️⃣ Performance summary
        # -------------------------------------------------
        performance_summary = {
            "average_crt_score": round(
                await db.scalar(
                    select(func.avg(StudentScore.total_crt_score))
                    .join(Student)
                    .where(Student.college_id == college_id)
                ) or 0.0, 2
            ),
            "highest_crt_score": round(
                await db.scalar(
                    select(func.max(StudentScore.total_crt_score))
                    .join(Student)
                    .where(Student.college_id == college_id)
                ) or 0.0, 2
            ),
            "lowest_crt_score": round(
                await db.scalar(
                    select(func.min(StudentScore.total_crt_score))
                    .join(Student)
                    .where(Student.college_id == college_id)
                ) or 0.0, 2
            ),
            "students_above_70_percent": await db.scalar(
                select(func.count(StudentScore.id))
                .where(StudentScore.total_crt_score >= 70)
            ) or 0,
            "students_below_40_percent": await db.scalar(
                select(func.count(StudentScore.id))
                .where(StudentScore.total_crt_score < 40)
            ) or 0,
        }

        # -------------------------------------------------
        # FINAL RESPONSE
        # -------------------------------------------------
        return {
            "college_info": college_info,
            "academic_years": academic_years_data,
            "branches": branches_data,
            "courses_allocated": courses_data,
            "top_students": top_students_data,
            "students_overview": students_overview,
            "performance_summary": performance_summary
        }
