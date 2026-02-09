from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.utils.decorators import require_permission
from app.services.admin.college_service import AdminCollegeService
from app.schemas.college_schema import (
    CollegeCreate,
    CollegeUpdate,
    CollegeResponse
)

router = APIRouter(
    prefix="/api/admin/colleges",
    tags=["Admin - Colleges"]
)

service = AdminCollegeService()

# -------------------------------------------------
# CREATE COLLEGE
# -------------------------------------------------
@router.post(
    "",
    response_model=CollegeResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("create", "colleges"))]
)
async def create_college(
    payload: CollegeCreate,
    db: AsyncSession = Depends(get_db)
):
    return await service.create_college(db, payload)


# -------------------------------------------------
# LIST COLLEGES
# -------------------------------------------------
@router.get(
    "",
    response_model=list[CollegeResponse],
    dependencies=[Depends(require_permission("view", "colleges"))]
)
async def list_colleges(
    db: AsyncSession = Depends(get_db)
):
    return await service.list_colleges(db)


# -------------------------------------------------
# GET COLLEGE BY ID
# -------------------------------------------------
@router.get(
    "/{college_id}",
    response_model=CollegeResponse,
    dependencies=[Depends(require_permission("view", "colleges"))]
)
async def get_college(
    college_id: int,
    db: AsyncSession = Depends(get_db)
):
    college = await service.get_college(db, college_id)
    if not college:
        raise HTTPException(status_code=404, detail="College not found")
    return college


# -------------------------------------------------
# UPDATE COLLEGE
# -------------------------------------------------
@router.put(
    "/{college_id}",
    response_model=CollegeResponse,
    dependencies=[Depends(require_permission("edit", "colleges"))]
)
async def update_college(
    college_id: int,
    payload: CollegeUpdate,
    db: AsyncSession = Depends(get_db)
):
    college = await service.update_college(db, college_id, payload)
    if not college:
        raise HTTPException(status_code=404, detail="College not found")
    return college


# -------------------------------------------------
# DELETE COLLEGE
# -------------------------------------------------
@router.delete(
    "/{college_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("delete", "colleges"))]
)
async def delete_college(
    college_id: int,
    db: AsyncSession = Depends(get_db)
):
    deleted = await service.delete_college(db, college_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="College not found")
