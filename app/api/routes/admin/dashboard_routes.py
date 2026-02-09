from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.admin.dashboard_service import DashboardService

router = APIRouter(
    prefix="/api/admin",
    tags=["Dashboard"]
)

service = DashboardService()


@router.get("/admin/dashboard")
async def admin_dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user = getattr(request.state, "user", None)

    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if user["role"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Admins only")

    return await service.get_admin_dashboard(db)
