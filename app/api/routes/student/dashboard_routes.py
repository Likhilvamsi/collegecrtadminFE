from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.utils.decorators import require_permission
from app.services.student.dashboard_service import StudentDashboardService

router = APIRouter(
    prefix="/api/student",
    tags=["Student"]
)

service = StudentDashboardService()


@router.get(
    "/dashboard",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("view", "student_dashboard"))]
)
async def student_dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Student Dashboard API

    ACCESS:
    - Role: STUDENT
    - Permission: view:student_dashboard
    """

    user = request.state.user

    # Defense-in-depth role check
    if user.role.name != "STUDENT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access only"
        )

    dashboard_data = await service.get_dashboard_data(
        db=db,
        student_user=user
    )

    return dashboard_data
