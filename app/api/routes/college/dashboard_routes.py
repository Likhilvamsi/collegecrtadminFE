from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.utils.decorators import require_permission
from app.services.college.dashboard_service import CollegeDashboardService

router = APIRouter(
    prefix="/api/college",
    tags=["College"]
)

service = CollegeDashboardService()


@router.get(
    "/dashboard",
    dependencies=[Depends(require_permission("view", "college_dashboard"))]
)
async def college_dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    dashboard_data = await service.get_dashboard_data(
        db=db,
        user=request.state.user
    )

    return {
        "message": "Welcome College Admin",
        "college_admin_id": request.state.user["id"],
        "stats": dashboard_data
    }
