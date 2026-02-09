from fastapi import Request, HTTPException, status
from typing import Callable


def require_permission(action: str, resource: str) -> Callable:
    """
    Dependency to enforce permission-based access.

    JWT payload example:
    {
        "sub": 1,
        "role": "COLLEGE_ADMIN",
        "permissions": ["view:college_dashboard"]
    }
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

        # ✅ ADMIN BYPASS
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
