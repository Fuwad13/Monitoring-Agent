import time
from contextlib import asynccontextmanager
from datetime import timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.targets import router as targets_router
from app.core.config import settings
from app.core.log import get_logger
from app.core.db import database

logger = get_logger(__name__, settings.LOG_FILE_PATH)


@asynccontextmanager
async def life_span(app: FastAPI):
    logger.info("Server is starting......")
    # Initialize database connection
    await database.connect()
    yield
    logger.info("Server is shutting down......")
    # Close database connection
    await database.disconnect()


version = "v1"

app = FastAPI(
    title="Monitoring Agent API",
    description="REST API for Monitoring Agent",
    version=version,
    lifespan=life_span,
)

startup_time = time.time()


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return RedirectResponse(url="/docs", status_code=307)


@app.get("/healthz")
async def health_check():
    current_time = time.time()
    uptime = current_time - startup_time
    db_health = await database.health_check()

    return {
        "status": "running",
        "version": version,
        "uptime": str(timedelta(seconds=uptime)),
        "database": db_health,
    }


app.include_router(auth_router)
app.include_router(targets_router)
