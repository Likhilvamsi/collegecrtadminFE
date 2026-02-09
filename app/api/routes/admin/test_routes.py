from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.utils.decorators import require_permission

router = APIRouter(
    prefix="/api/admin/tests",
    tags=["Admin - Tests"]
)

# -------------------------------------------------
# PLACEHOLDER ENDPOINT
# -------------------------------------------------
@router.get(
    "",
    dependencies=[Depends(require_permission("view", "tests"))]
)
async def list_tests(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Placeholder endpoint – implement later
    """
    return {
        "message": "Admin tests module initialized"
    }
