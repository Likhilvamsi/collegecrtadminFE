from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from jose import JWTError

from app.core.jwt import decode_access_token

PUBLIC_PATHS = (
    "/api/auth",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/health",
)


class AuthMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        path = request.url.path
        method = request.method

        # ------------------------------------------------
        # ✅ ALLOW OPTIONS (CORS PREFLIGHT)
        # ------------------------------------------------
        if method == "OPTIONS":
            return await call_next(request)

        # ------------------------------------------------
        # ✅ ALLOW PUBLIC ROUTES
        # ------------------------------------------------
        if any(path.startswith(p) for p in PUBLIC_PATHS):
            return await call_next(request)

        # ------------------------------------------------
        # AUTH HEADER
        # ------------------------------------------------
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authentication required"},
            )

        token = auth_header.split(" ", 1)[1]

        # ------------------------------------------------
        # DECODE TOKEN (SAFE)
        # ------------------------------------------------
        try:
            payload = decode_access_token(token)
        except JWTError:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid or expired token"},
            )

        if not payload or "sub" not in payload:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid token payload"},
            )

        # ------------------------------------------------
        # ATTACH USER CONTEXT ✅
        # ------------------------------------------------
        request.state.user = {
            "id": int(payload.get("sub")),
            "role": payload.get("role", "USER"),
            "permissions": payload.get("permissions", []),
        }

        return await call_next(request)
