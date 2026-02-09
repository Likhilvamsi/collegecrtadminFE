from fastapi import (
    APIRouter, Request, Depends,
    HTTPException, status, Query,
    UploadFile, File
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.college.student_service import CollegeStudentService
from app.schemas.student_schema import StudentCreate

router = APIRouter(
    prefix="/api/college",
    tags=["College - Students"]
)

service = CollegeStudentService()


# =====================================================
# 🔐 COMMON ROLE CHECK
# =====================================================
def ensure_college_admin(user: dict):
    if user.get("role") != "COLLEGE_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="College admin access only"
        )


# =====================================================
# 1️⃣ LIST STUDENTS
# =====================================================
@router.get("/students")
async def list_students(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user = request.state.user
    ensure_college_admin(user)

    return await service.list_students(
        db=db,
        college_admin_user=user
    )


# =====================================================
# 2️⃣ FILTER STUDENTS
# =====================================================
@router.get("/students/filter")
async def filter_students(
    request: Request,
    department_id: int | None = Query(None, description="Branch / Department ID"),
    academic_year_id: int | None = Query(None, description="Academic Year ID"),
    min_completion: float | None = Query(None, ge=0, le=100),
    max_completion: float | None = Query(None, ge=0, le=100),
    db: AsyncSession = Depends(get_db)
):
    user = request.state.user
    ensure_college_admin(user)

    return await service.filter_students(
        db=db,
        college_admin_user=user,
        department_id=department_id,
        academic_year_id=academic_year_id,
        min_completion=min_completion,
        max_completion=max_completion
    )


# =====================================================
# 3️⃣ SEARCH STUDENTS
# =====================================================
@router.get("/students/search")
async def search_students(
    request: Request,
    q: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db)
):
    user = request.state.user
    ensure_college_admin(user)

    return await service.search_students(
        db=db,
        college_admin_user=user,
        query=q
    )


# =====================================================
# ➕ ADD SINGLE STUDENT
# =====================================================
@router.post("", status_code=status.HTTP_201_CREATED)
async def add_single_student(
    payload: StudentCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user = request.state.user
    ensure_college_admin(user)

    return await service.add_single_student(
        db=db,
        college_admin_user=user,
        data=payload
    )


# =====================================================
# 📥 BULK UPLOAD STUDENTS
# =====================================================
@router.post("/bulk-upload", status_code=status.HTTP_201_CREATED)
async def bulk_upload_students(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    user = request.state.user
    ensure_college_admin(user)

    return await service.bulk_upload_students(
        db=db,
        college_admin_user=user,
        file=file
    )
