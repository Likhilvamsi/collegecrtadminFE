from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repository import UserRepository
from app.core.security import verify_password
from app.core.jwt import create_access_token


class AuthService:
    """
    Authentication service
    - Strict role-based login
    - JWT standard compliant
    """

    def __init__(self):
        self.user_repo = UserRepository()

    async def login(
        self,
        db: AsyncSession,
        email: str,
        password: str,
        role: str
    ) -> dict:
        # -------------------------------------------------
        # 1️⃣ Fetch user (email + role validation)
        # -------------------------------------------------
        user = await self.user_repo.get_user_for_login(
            db=db,
            identifier=email,
            role_name=role
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials for selected role"
            )

        # -------------------------------------------------
        # 2️⃣ User account checks
        # -------------------------------------------------
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )

        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is not verified"
            )

        # -------------------------------------------------
        # 3️⃣ Verify password
        # -------------------------------------------------
        if not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        # -------------------------------------------------
        # 4️⃣ Trust role from database
        # -------------------------------------------------
        role_name = user.role.name

        # -------------------------------------------------
        # 5️⃣ Assign permissions by role
        # -------------------------------------------------
        permissions: list[str]

        if role_name == "ADMIN":
            permissions = ["admin:*"]

        elif role_name == "COLLEGE_ADMIN":
            permissions = [
                "view:college_dashboard",
                "view:students",
                "view:courses"
            ]

        elif role_name == "TEACHER":
            permissions = [
                "view:courses",
                "create:tests"
            ]

        elif role_name == "STUDENT":
            permissions = [
                "view:student_dashboard"
            ]

        else:
            permissions = []

        # -------------------------------------------------
        # 6️⃣ Create JWT access token
        # -------------------------------------------------
        access_token = create_access_token(
            {
                "sub": str(user.id),        # JWT subject (standard)
                "role": role_name,
                "permissions": permissions
            }
        )

        # -------------------------------------------------
        # 7️⃣ Response
        # -------------------------------------------------
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "role": role_name
        }
