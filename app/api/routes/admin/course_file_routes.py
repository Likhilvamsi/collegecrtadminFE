from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Request,
    status,
)
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.services.admin.course_file_service import AdminCourseFileService
from app.schemas.course_file_schema import CourseFileResponse
from app.models.models import CourseFile
from fastapi.responses import StreamingResponse
import httpx
router = APIRouter(
    prefix="/api/admin/courses",
    tags=["Admin - Course Files"]
)

service = AdminCourseFileService()

# -------------------------------------------------
# UPLOAD FILE (PDF / VIDEO / DOC)
# -------------------------------------------------
@router.post(
    "/{course_id}/files",
    response_model=CourseFileResponse,
    status_code=status.HTTP_201_CREATED
)
async def upload_course_file(
    course_id: int,
    request: Request,
    file: UploadFile = File(...),
    file_title: str | None = None,
    file_description: str | None = None,
    duration_seconds: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    if request.state.user["role"] != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access only"
        )

    return await service.upload_course_file(
        db=db,
        course_id=course_id,
        file=file,
        file_title=file_title,
        file_description=file_description,
        duration_seconds=duration_seconds,
    )


# -------------------------------------------------
# LIST ALL FILES FOR A COURSE
# -------------------------------------------------
@router.get(
    "/{course_id}/files",
    response_model=list[CourseFileResponse]
)
async def list_course_files(
    course_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    if request.state.user["role"] != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access only"
        )

    return await service.list_course_files(db, course_id)


# -------------------------------------------------
# LIST ONLY PDFs FOR A COURSE
# -------------------------------------------------
@router.get("/{course_id}/pdfs")
async def list_course_pdfs(
    course_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    if request.state.user["role"] != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access only"
        )

    result = await db.execute(
        select(CourseFile)
        .where(
            CourseFile.course_id == course_id,
            CourseFile.file_type == "PDF",
            CourseFile.is_published.is_(True),
        )
        .order_by(CourseFile.created_at.desc())
    )

    pdfs = result.scalars().all()

    return {
        "course_id": course_id,
        "total_pdfs": len(pdfs),
        "files": [
            {
                "id": pdf.id,
                "file_name": pdf.file_name,
                "file_title": pdf.file_title,
                "description": pdf.file_description,
                "file_url": pdf.file_url,
                "uploaded_at": pdf.created_at,
            }
            for pdf in pdfs
        ],
    }


# -------------------------------------------------
# VIEW A SINGLE PDF (REDIRECT TO S3)
# -------------------------------------------------


@router.get("/course-files/{file_id}/stream")
async def stream_pdf(
    file_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    if request.state.user["role"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access only")

    pdf = await db.scalar(
        select(CourseFile).where(
            CourseFile.id == file_id,
            CourseFile.file_type == "PDF"
        )
    )

    if not pdf:
        raise HTTPException(status_code=404, detail="PDF not found")

    async with httpx.AsyncClient() as client:
        r = await client.get(pdf.file_url)

    return StreamingResponse(
        r.aiter_bytes(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{pdf.file_name}"'
        }
    )
