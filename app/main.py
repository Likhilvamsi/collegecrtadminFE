from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.middleware.auth_middleware import AuthMiddleware
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.error_handler import register_exception_handlers

# -----------------------------
# ROUTERS
# -----------------------------
from app.api.routes.auth.auth_routes import router as auth_router

from app.api.routes.admin.dashboard_routes import router as admin_dashboard_router
from app.api.routes.admin.college_routes import router as admin_college_router
from app.api.routes.admin.course_routes import router as admin_course_router
from app.api.routes.admin.test_routes import router as admin_test_router
from app.api.routes.admin.course_file_routes import router as admin_course_file_router

from app.api.routes.college.dashboard_routes import router as college_dashboard_router
from app.api.routes.college.student_routes import router as college_student_router
from app.api.routes.college.course_routes import router as college_course_router

from app.api.routes.student.dashboard_routes import router as student_dashboard_router
from app.api.routes.student.course_routes import router as student_course_router

from dotenv import load_dotenv
load_dotenv()

def create_app() -> FastAPI:
    app = FastAPI(
        title="CRT Backend API",
        description="Complete Role-based Training Platform Backend",
        version="1.0.0"
    )

    # -----------------------------
    # CORS
    # -----------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # -----------------------------
    # MIDDLEWARE
    # -----------------------------
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(AuthMiddleware)

    # -----------------------------
    # EXCEPTION HANDLERS
    # -----------------------------
    register_exception_handlers(app)

    # -----------------------------
    # ROUTERS
    # -----------------------------
    app.include_router(auth_router)

    app.include_router(admin_dashboard_router)
    app.include_router(admin_college_router)
    app.include_router(admin_course_router)
    app.include_router(admin_test_router)
    app.include_router(admin_course_file_router)

    app.include_router(college_dashboard_router)
    app.include_router(college_student_router)
    app.include_router(college_course_router)

    app.include_router(student_dashboard_router)
    app.include_router(student_course_router)

    return app


app = create_app()


# -----------------------------
# Swagger Security (Bearer)
# -----------------------------
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="CRT Backend API",
        version="1.0.0",
        description="Complete Role-based Training Platform Backend",
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }

    for path in openapi_schema["paths"].values():
        for method in path.values():
            method.setdefault("security", [{"BearerAuth": []}])

    app.openapi_schema = openapi_schema
    return app.openapi_schema


# ✅ VERY IMPORTANT
app.openapi = custom_openapi


# -----------------------------
# HEALTH CHECK
# -----------------------------
@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "OK",
        "service": "CRT Backend",
        "version": "1.0.0"
    }
