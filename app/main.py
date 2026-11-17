from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
from datetime import datetime
from starlette.status import (
    HTTP_404_NOT_FOUND,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
)

from app.routes import doctors, patients, receptionists, payments, managers
from app.database import check_database, initialize_database


@asynccontextmanager
async def lifespan(app: FastAPI):

    initialize_database()  # Initialize the database when the server starts.

    if not check_database():
        raise RuntimeError("Database connection failed!")

    yield

    print("HSum Backend Shutting down..")


app = FastAPI(
    title="HSum FastAPI Backend",
    version="v0.1.0",
    description="""HSum FastAPI Backend provides many API endpoints for doctors, patients, receptionists, payments, and managers. It also provides some Utility Endpoints like `health`.
    A GET request to `/` returns a `/health` like message""",
    summary="HSum FastAPI Backend",
    lifespan=lifespan,
)


# Utility Endpoints
@app.get("/")
async def index():
    return JSONResponse(
        content={
            "message": "Welcome! HSum Backend",
            "time": datetime.now().isoformat(),
        },
        status_code=200,
        headers={"Content-Type": "application/json"},
    )


@app.get("/health")
async def health():
    return {"status": "healthy", "code": 200, "time": datetime.now().isoformat()}


# API routers for doctors, patients, receptionists, and managers.
app.include_router(doctors.router, prefix="/doctors", tags=["Doctor Endpoints"])

app.include_router(patients.router, prefix="/patients", tags=["Patient Endpoints"])

app.include_router(
    receptionists.router, prefix="/receptionists", tags=["Receptionist Endpoints"]
)

app.include_router(payments.router, prefix="/payments", tags=["Payment Route"])

app.include_router(managers.router, prefix="/managers", tags=["Manager Endpoints"])


# HTTP Exception Handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=HTTP_404_NOT_FOUND,
        content={"message": "Not found", "path": str(request.url)},
    )


@app.exception_handler(HTTP_400_BAD_REQUEST)
async def bad_request_handler(request: Request, exc):
    return JSONResponse(
        status_code=HTTP_400_BAD_REQUEST,
        content={"message": "Bad request", "path": str(request.url)},
    )


@app.exception_handler(HTTP_401_UNAUTHORIZED)
async def unauthenticated_handler(request: Request, exc):
    return JSONResponse(
        status_code=HTTP_401_UNAUTHORIZED,
        content={"message": "Authentication required", "path": str(request.url)},
    )


@app.exception_handler(HTTP_403_FORBIDDEN)
async def unauthorized_handler(request: Request, exc):
    return JSONResponse(
        status_code=HTTP_403_FORBIDDEN,
        content={
            "message": "You are not authorized to access this resource",
            "path": str(request.url),
        },
    )


@app.exception_handler(500)
async def internal_server_error(request: Request, exc):
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Sever Error.", "path": str(request.url)},
    )
