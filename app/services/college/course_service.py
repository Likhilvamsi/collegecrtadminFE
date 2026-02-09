from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.models import (
    CollegeAdmin,
    Student,
    Course,
    StudentCourse,
    CollegeCourse
)
from app.schemas.enrollment_schema import CourseAssignRequest


class CollegeCourseService:
    """
    College Admin → Course assignment & listing service
    """

    # -------------------------------------------------
    # ASSIGN COURSE TO STUDENTS (BY BRANCH + ACADEMIC YEAR)
    # -------------------------------------------------
    async def assign_course_to_students(
        self,
        db: AsyncSession,
        college_admin_user: dict,
        payload: CourseAssignRequest
    ):
        # 1️⃣ Resolve college for admin
        college_admin = (
            await db.execute(
                select(CollegeAdmin)
                .where(CollegeAdmin.user_id == college_admin_user["id"])
            )
        ).scalar_one_or_none()

        if not college_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="College admin not mapped to any college"
            )

        college_id = college_admin.college_id

        # 2️⃣ Validate course is available for this college
        college_course = (
            await db.execute(
                select(CollegeCourse)
                .where(
                    CollegeCourse.course_id == payload.course_id,
                    CollegeCourse.college_id == college_id,
                    CollegeCourse.is_active.is_(True)
                )
            )
        ).scalar_one_or_none()

        if not college_course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not available for this college"
            )

        # 3️⃣ Fetch ALL students by branch + academic year
        students = (
            await db.execute(
                select(Student)
                .where(
                    Student.college_id == college_id,
                    Student.branch_id == payload.branch_id,
                    Student.academic_year_id == payload.academic_year_id
                )
            )
        ).scalars().all()

        if not students:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No students found for given branch and academic year"
            )

        # 4️⃣ Assign course (avoid duplicates)
        assigned_count = 0

        for student in students:
            exists = (
                await db.execute(
                    select(StudentCourse)
                    .where(
                        StudentCourse.student_id == student.id,
                        StudentCourse.course_id == payload.course_id
                    )
                )
            ).scalar_one_or_none()

            if exists:
                continue

            db.add(
                StudentCourse(
                    student_id=student.id,
                    course_id=payload.course_id,
                    enrollment_status="ASSIGNED",
                    progress_percentage=0.0
                )
            )
            assigned_count += 1

        await db.commit()

        return {
            "course_id": payload.course_id,
            "branch_id": payload.branch_id,
            "academic_year_id": payload.academic_year_id,
            "students_assigned": assigned_count
        }

    # -------------------------------------------------
    # LIST COURSES FOR COLLEGE (WITH STATS)
    # -------------------------------------------------
    async def list_college_courses(
        self,
        db: AsyncSession,
        college_admin_user: dict
    ):
        college_admin = (
            await db.execute(
                select(CollegeAdmin)
                .where(CollegeAdmin.user_id == college_admin_user["id"])
            )
        ).scalar_one_or_none()

        if not college_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="College admin not mapped to any college"
            )

        college_id = college_admin.college_id

        result = await db.execute(
            select(Course)
            .join(CollegeCourse)
            .where(
                CollegeCourse.college_id == college_id,
                CollegeCourse.is_active.is_(True),
                Course.is_active.is_(True)
            )
        )

        courses = result.scalars().all()
        response = []

        for course in courses:
            assigned = (
                await db.execute(
                    select(func.count(StudentCourse.id))
                    .where(StudentCourse.course_id == course.id)
                )
            ).scalar() or 0

            completed = (
                await db.execute(
                    select(func.count(StudentCourse.id))
                    .where(
                        StudentCourse.course_id == course.id,
                        StudentCourse.enrollment_status == "COMPLETED"
                    )
                )
            ).scalar() or 0

            response.append({
                "course_id": course.id,
                "course_title": course.title,
                "category": course.category,
                "level": course.level,
                "students_assigned": assigned,
                "students_completed": completed
            })

        return response

    # -------------------------------------------------
    # ADMIN DASHBOARD – COURSES FOR COLLEGE
    # -------------------------------------------------
    async def get_admin_courses_for_college(
        self,
        db: AsyncSession,
        college_admin_user: dict
    ):
        college_admin = (
            await db.execute(
                select(CollegeAdmin)
                .where(CollegeAdmin.user_id == college_admin_user["id"])
            )
        ).scalar_one_or_none()

        if not college_admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="College admin record not found"
            )

        college_id = college_admin.college_id

        result = await db.execute(
            select(Course)
            .join(CollegeCourse)
            .where(
                CollegeCourse.college_id == college_id,
                CollegeCourse.is_active.is_(True),
                Course.is_active.is_(True),
                Course.is_published.is_(True)
            )
            .order_by(Course.created_at.desc())
        )

        courses = result.scalars().all()

        return {
            "college_id": college_id,
            "total_courses": len(courses),
            "courses": [
                {
                    "course_id": c.id,
                    "title": c.title,
                    "category": c.category,
                    "level": c.level,
                    "description": c.description,
                    "thumbnail_url": c.thumbnail_url,
                    "duration_hours": c.duration_hours,
                    "expected_completion_days": c.expected_completion_days,
                    "created_at": c.created_at,
                }
                for c in courses
            ]
        }
