from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from io import BytesIO

import pandas as pd
from fastapi import UploadFile


from app.core.security import hash_password
from app.models.models import (
    User,
    Student,
    CollegeAdmin,
    Role,
    CollegeBranch,
    AcademicYear,
    StudentCourse,
    StudentScore,
)
from app.schemas.student_schema import StudentCreate


class CollegeStudentService:
    """
    College Admin → Student onboarding & listing service
    """

    # =================================================
    # INTERNAL: Resolve college_id from admin user
    # =================================================
    async def _get_college_id(self, db: AsyncSession, admin_user: dict) -> int:
        college_admin = await db.scalar(
            select(CollegeAdmin)
            .where(CollegeAdmin.user_id == admin_user["id"])
        )

        if not college_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="College admin not mapped to any college"
            )

        return college_admin.college_id

    # =================================================
    # CREATE STUDENT (PRIMARY METHOD)
    # =================================================
    async def add_single_student(
        self,
        db: AsyncSession,
        college_admin_user: dict,
        data: StudentCreate
    ):
        college_id = await self._get_college_id(db, college_admin_user)

        # 1️⃣ Fetch STUDENT role
        role_id = await db.scalar(
            select(Role.id).where(Role.name == "STUDENT")
        )

        if not role_id:
            raise HTTPException(
                status_code=500,
                detail="STUDENT role not configured"
            )

        try:
            # 2️⃣ Create USER
            user = User(
                role_id=role_id,
                full_name=data.name,
                email=data.email,
                phone=data.phone,
                password_hash=hash_password(data.roll_number),
                is_active=True,
                is_verified=True,
            )
            db.add(user)
            await db.flush()  # get user.id

            # 3️⃣ Create STUDENT
            student = Student(
                user_id=user.id,
                college_id=college_id,
                branch_id=data.branch_id,
                academic_year_id=data.academic_year_id,
                roll_number=data.roll_number,
                student_unique_id=f"STU-{college_id}-{data.roll_number}",
                enrollment_status="ACTIVE",
            )
            db.add(student)
            await db.flush()

            # 4️⃣ Create STUDENT SCORE
            db.add(StudentScore(student_id=student.id))

            await db.commit()

            return {
                "student_id": student.id,
                "name": user.full_name,
                "email": user.email,
                "roll_no": student.roll_number,
                "status": student.enrollment_status,
            }

        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duplicate email / roll number / student ID"
            )

    # =================================================
    # CREATE STUDENT (ALIAS – keeps old code working)
    # =================================================
    async def create_student(
        self,
        db: AsyncSession,
        college_admin_user: dict,
        payload: StudentCreate
    ):
        return await self.add_single_student(
            db=db,
            college_admin_user=college_admin_user,
            data=payload
        )

    # =================================================
    # LIST STUDENTS (COLLEGE SCOPE)
    # =================================================
    async def list_students(
        self,
        db: AsyncSession,
        college_admin_user: dict
    ):
        college_id = await self._get_college_id(db, college_admin_user)

        result = await db.execute(
            select(
                Student.id,
                User.full_name,
                User.email,
                Student.roll_number,
                CollegeBranch.branch_name,
                AcademicYear.year_name,
                Student.enrollment_status,
            )
            .join(User, User.id == Student.user_id)
            .join(CollegeBranch, CollegeBranch.id == Student.branch_id)
            .join(AcademicYear, AcademicYear.id == Student.academic_year_id)
            .where(Student.college_id == college_id)
            .order_by(User.full_name)
        )

        return [
            {
                "student_id": r.id,
                "name": r.full_name,
                "email": r.email,
                "roll_no": r.roll_number,
                "branch": r.branch_name,
                "academic_year": r.year_name,
                "status": r.enrollment_status,
            }
            for r in result.all()
        ]

    # =================================================
    # FILTER STUDENTS
    # =================================================
    async def filter_students(
        self,
        db: AsyncSession,
        college_admin_user: dict,
        department_id: int | None,
        academic_year_id: int | None,
        min_completion: float | None,
        max_completion: float | None,
    ):
        college_id = await self._get_college_id(db, college_admin_user)

        stmt = (
            select(
                Student.id,
                User.full_name,
                User.email,
                Student.roll_number,
                CollegeBranch.branch_name,
                AcademicYear.year_name,
                func.coalesce(func.avg(StudentCourse.progress_percentage), 0)
                    .label("completion"),
            )
            .join(User, User.id == Student.user_id)
            .join(CollegeBranch, CollegeBranch.id == Student.branch_id)
            .join(AcademicYear, AcademicYear.id == Student.academic_year_id)
            .outerjoin(StudentCourse, StudentCourse.student_id == Student.id)
            .where(Student.college_id == college_id)
            .group_by(Student.id)
        )

        if department_id:
            stmt = stmt.where(Student.branch_id == department_id)

        if academic_year_id:
            stmt = stmt.where(Student.academic_year_id == academic_year_id)

        if min_completion is not None:
            stmt = stmt.having(func.avg(StudentCourse.progress_percentage) >= min_completion)

        if max_completion is not None:
            stmt = stmt.having(func.avg(StudentCourse.progress_percentage) <= max_completion)

        result = await db.execute(stmt)

        return [
            {
                "student_id": r.id,
                "name": r.full_name,
                "email": r.email,
                "roll_no": r.roll_number,
                "branch": r.branch_name,
                "academic_year": r.year_name,
                "course_completion_percentage": round(r.completion, 2),
            }
            for r in result.all()
        ]

    # =================================================
    # SEARCH STUDENTS
    # =================================================
    async def search_students(
        self,
        db: AsyncSession,
        college_admin_user: dict,
        query: str
    ):
        college_id = await self._get_college_id(db, college_admin_user)

        result = await db.execute(
            select(
                Student.id,
                User.full_name,
                User.email,
                Student.roll_number,
                CollegeBranch.branch_name,
                AcademicYear.year_name,
            )
            .join(User, User.id == Student.user_id)
            .join(CollegeBranch, CollegeBranch.id == Student.branch_id)
            .join(AcademicYear, AcademicYear.id == Student.academic_year_id)
            .where(
                Student.college_id == college_id,
                or_(
                    User.full_name.ilike(f"%{query}%"),
                    User.email.ilike(f"%{query}%"),
                    Student.roll_number.ilike(f"%{query}%"),
                    CollegeBranch.branch_name.ilike(f"%{query}%"),
                )
            )
        )

        return [
            {
                "student_id": r.id,
                "name": r.full_name,
                "email": r.email,
                "roll_no": r.roll_number,
                "branch": r.branch_name,
                "academic_year": r.year_name,
            }
            for r in result.all()
        ]

    # =================================================
    # BULK STUDENT UPLOAD (EXCEL / CSV)
    # =================================================
    async def bulk_upload_students(
        self,
        db: AsyncSession,
        college_admin_user: dict,
        file: UploadFile
    ):
        college_id = await self._get_college_id(db, college_admin_user)

        if not file.filename.endswith((".xlsx", ".csv")):
            raise HTTPException(
                status_code=400,
                detail="Only Excel (.xlsx) or CSV files are supported"
            )

        try:
            contents = await file.read()
            file_stream = BytesIO(contents)

            if file.filename.endswith(".xlsx"):
                df = pd.read_excel(file_stream, engine="openpyxl")
            elif file.filename.endswith(".csv"):
                df = pd.read_csv(file_stream)
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Unsupported file type"
                )
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file format: {str(e)}"
            )


        required_columns = {
            "name",
            "email",
            "roll_number",
            "phone",
            "academic_year_id",
            "branch_id",
            "password",
        }

        if not required_columns.issubset(df.columns):
            raise HTTPException(
                status_code=400,
                detail=f"Missing columns. Required: {required_columns}"
            )

        role_id = await db.scalar(
            select(Role.id).where(Role.name == "STUDENT")
        )

        success_count = 0
        failed_rows = []

        for index, row in df.iterrows():
            try:
                # Create USER
                user = User(
                    role_id=role_id,
                    full_name=row["name"],
                    email=row["email"],
                    phone=str(row["phone"]),
                    password_hash=hash_password(str(row["password"])),
                    is_active=True,
                    is_verified=True,
                )
                db.add(user)
                await db.flush()

                # Create STUDENT
                student = Student(
                    user_id=user.id,
                    college_id=college_id,
                    branch_id=int(row["branch_id"]),
                    academic_year_id=int(row["academic_year_id"]),
                    roll_number=row["roll_number"],
                    student_unique_id=f"STU-{college_id}-{row['roll_number']}",
                    enrollment_status="ACTIVE",
                )
                db.add(student)
                await db.flush()

                # Create STUDENT SCORE
                db.add(StudentScore(student_id=student.id))

                success_count += 1

            except IntegrityError:
                await db.rollback()
                failed_rows.append({
                    "row": index + 2,
                    "email": row["email"],
                    "reason": "Duplicate email / roll number"
                })

            except Exception as e:
                await db.rollback()
                failed_rows.append({
                    "row": index + 2,
                    "email": row["email"],
                    "reason": str(e)
                })

        await db.commit()

        return {
            "message": "Bulk upload completed",
            "total_records": len(df),
            "successfully_created": success_count,
            "failed_records": failed_rows,
        }
