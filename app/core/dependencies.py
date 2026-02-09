from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.jwt import decode_access_token
from app.repositories.user_repository import UserRepository

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    auth = request.headers.get("Authorization")

    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Access token missing")

    token = auth.split(" ")[1]
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await UserRepository().get_by_id(db, payload["user_id"])

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User inactive")

    return user
