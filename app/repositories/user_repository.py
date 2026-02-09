from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import User, Role


class UserRepository:
    """
    User repository with strict role-based login support
    """

    # -------------------------------------------------
    # BASIC FETCH
    # -------------------------------------------------
    async def get_by_id(self, db: AsyncSession, user_id: int):
        stmt = (
            select(User)
            .options(selectinload(User.role))
            .where(User.id == user_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, db: AsyncSession, email: str):
        stmt = (
            select(User)
            .options(selectinload(User.role))
            .where(User.email == email)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    # -------------------------------------------------
    # STRICT ROLE-BASED LOGIN (CORE)
    # -------------------------------------------------
    async def get_user_for_login(
        self,
        db: AsyncSession,
        identifier: str,
        role_name: str
    ):
        """
        Fetch user by identifier + role.
        Identifier = email / phone (future-proof)
        """

        stmt = (
            select(User)
            .join(Role, User.role_id == Role.id)
            .options(selectinload(User.role))
            .where(
                Role.name == role_name,
                or_(
                    User.email == identifier,
                    User.phone == identifier
                )
            )
        )

        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    # -------------------------------------------------
    # ROLE FETCH (UTILITY)
    # -------------------------------------------------
    async def get_role_by_name(
        self,
        db: AsyncSession,
        role_name: str
    ):
        stmt = select(Role).where(Role.name == role_name)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
