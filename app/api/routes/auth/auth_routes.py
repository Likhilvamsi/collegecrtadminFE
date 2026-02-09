from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.auth_schema import LoginRequest, LoginResponse
from app.services.auth_service import AuthService

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)

auth_service = AuthService()


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK
)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login API

    Returns:
    - access_token
    - token_type
    - role
    """
    return await auth_service.login(
        db=db,
        email=payload.email,
        password=payload.password,
        role=payload.role
    )
