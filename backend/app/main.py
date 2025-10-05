import sentry_sdk
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
import asyncio

from app.api.main import api_router
from app.core.config import settings

def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"

# Initialize Sentry if configured
if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include your API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# -----------------------
# Scheduler setup
# -----------------------
scheduler = BackgroundScheduler()

def inventory_job():
    """
    Put your scheduled job logic here.
    For example, fetch SharePoint files, read emails, or update database.
    """
    print("Running inventory job...")

# Schedule the job every 5 minutes
scheduler.add_job(inventory_job, 'interval', minutes=5)

# Start the scheduler when the app starts
@app.on_event("startup")
async def start_scheduler():
    scheduler.start()
    print("Scheduler started")

# Optional: shutdown scheduler gracefully
@app.on_event("shutdown")
async def shutdown_scheduler():
    scheduler.shutdown()
    print("Scheduler stopped")
