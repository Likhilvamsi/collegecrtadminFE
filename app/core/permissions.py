from fastapi import Request, HTTPException, status
from typing import Callable


def require_permission(action: str, resource: str) -> Callable:
    """
    Dependency to enforce role & permission based access.
    Uses request.state.user (set by auth middleware).
    """

    async def permission_checker(request: Request):
        user = getattr(request.state, "user", None)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )

        role = user.get("role")
        permissions = user.get("permissions", [])

        # ✅ Super Admin / Admin full access
        if role == "ADMIN":
            return True

        required_permission = f"{action}:{resource}"

        if required_permission not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action"
            )

        return True

    return permission_checker
