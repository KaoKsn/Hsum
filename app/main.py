from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
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
    payments,
)


# Application startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables when the application starts.
    initialize_database()

    # Verify that the database is accessible.
    if not check_database():
        raise RuntimeError("Database connection failed!")

    yield

    # Add shutdown cleanup here if the application needs it later.


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
    payments.router,
    prefix="/payments",
    tags=["Payment Endpoints"],
)

app.include_router(
    managers.router,
    prefix="/managers",
    tags=["Manager Endpoints"],
)


# HTTP Exception Handlers
@app.exception_handler(HTTP_404_NOT_FOUND)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=HTTP_404_NOT_FOUND,
        content={
            "message": "Resource not found",
            "path": str(request.url),
        },
    )


@app.exception_handler(HTTP_400_BAD_REQUEST)
async def bad_request_handler(request: Request, exc):
    return JSONResponse(
        status_code=HTTP_400_BAD_REQUEST,
        content={
            "message": "Bad request",
            "path": str(request.url),
        },
    )


@app.exception_handler(HTTP_401_UNAUTHORIZED)
async def unauthenticated_handler(request: Request, exc):
    return JSONResponse(
        status_code=HTTP_401_UNAUTHORIZED,
        content={
            "message": "Authentication required",
            "path": str(request.url),
        },
    )


@app.exception_handler(HTTP_403_FORBIDDEN)
async def forbidden_handler(request: Request, exc):
    return JSONResponse(
        status_code=HTTP_403_FORBIDDEN,
        content={
            "message": "You are not authorized to access this resource",
            "path": str(request.url),
        },
    )


@app.exception_handler(HTTP_500_INTERNAL_SERVER_ERROR)
async def internal_server_error(request: Request, exc):
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": "Internal server error",
            "path": str(request.url),
        },
    )
