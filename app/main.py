from contextlib import asynccontextmanager
from datetime import datetime
import sys

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from starlette.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from app.database import check_database, initialize_database
from app.routes import (
    appointments,
    doctors,
    managers,
    patients,
    receptionists,
    auth,
    medical_records,
)


# Application startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables when the application starts.
    initialize_database()

    # Verify that the database is accessible.
    if not check_database():
        raise RuntimeError("Database connection failed!")

    try:
        yield
    except KeyboardInterrupt:
        print("SIGTERM caught, Bye..")
        return
    # Add shutdown cleanup here if the application needs it later.
    print("Bye..")


app = FastAPI(
    title="HSum FastAPI Backend",
    version="v0.1.0",
    description=(
        "HSum provides API endpoints for doctors, patients, "
        "receptionists, appointments, payments, and managers. "
        "It also provides utility endpoints such as health checks."
    ),
    summary="HSum FastAPI Backend",
    lifespan=lifespan,
)


# Utility Endpoints
@app.get("/", status_code=HTTP_200_OK)
async def index():
    return {
        "message": "Welcome! HSum Backend",
        "time": datetime.now().astimezone().isoformat(),
    }


@app.get("/health", status_code=HTTP_200_OK)
async def health():
    database_status = check_database()

    if not database_status:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "message": "Database connection failed",
            },
        )

    return {
        "status": "healthy",
        "code": HTTP_200_OK,
        "database": "connected",
        "time": datetime.now().astimezone().isoformat(),
    }


# API Routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])

app.include_router(
    doctors.router,
    prefix="/doctors",
    tags=["Doctor Endpoints"],
)

app.include_router(
    patients.router,
    prefix="/patients",
    tags=["Patient Endpoints"],
)

app.include_router(
    receptionists.router,
    prefix="/receptionists",
    tags=["Receptionist Endpoints"],
)

app.include_router(
    appointments.router,
    prefix="/appointments",
    tags=["Appointment Endpoints"],
)

app.include_router(
    managers.router,
    prefix="/managers",
    tags=["Manager Endpoints"],
)

app.include_router(
    medical_records.router,
    prefix="/medical-records",
    tags=["Medical Records"],
)


# HTTP Exception Handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    messages = {
        400: "Bad request",
        401: "Authentication required",
        403: "You are not authorized to access this resource",
        404: "Resource not found",
    }

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": messages.get(exc.status_code, "Request failed"),
            "detail": exc.detail,
            "path": str(request.url),
        },
    )


@app.exception_handler(Exception)
async def unexpected_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "message": "Internal server error",
            "path": str(request.url),
        },
    )
