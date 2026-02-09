from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import IntegrityError


def register_exception_handlers(app: FastAPI):
    """
    Register global exception handlers
    """

    # -----------------------------------------
    # HTTP Exceptions (raised via HTTPException)
    # -----------------------------------------
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException
    ):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.detail
            }
        )

    # -----------------------------------------
    # Request validation errors (Pydantic)
    # -----------------------------------------
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError
    ):
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "message": "Validation error",
                "errors": exc.errors()
            }
        )

    # -----------------------------------------
    # Database integrity errors
    # -----------------------------------------
    @app.exception_handler(IntegrityError)
    async def integrity_exception_handler(
        request: Request,
        exc: IntegrityError
    ):
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": "Database constraint violation"
            }
        )

    # -----------------------------------------
    # Unhandled server errors
    # -----------------------------------------
    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request,
        exc: Exception
    ):
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Internal server error"
            }
        )
