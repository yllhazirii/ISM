import sentry_sdk
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
import asyncio
import pandas as pd

from app.api.main import api_router
from app.core.config import settings
from app.api.services.EmailParser import EmailParser
from app.api.services.DataSyncer import DataSyncer
from app.api.services.GraphClient import GraphClient
from app.api.services.DatabaseClient import DatabaseClient
from app.api.services.FileEditor import FileEditor


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"



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
    # graphClient = GraphClient()
    # dbClient = DatabaseClient()
    # fileEditor = FileEditor(graphClient)
    #
    # dataSyncer = DataSyncer(fileEditor, dbClient)
    # emailParser = EmailParser(graphClient)
    # structured = emailParser.get_emails(top=5, distribution_list="Inventory")
    # for record in structured:
    #     print(record)
    # dataSyncer.check_and_sync()


# Schedule the job every 5 minutes
scheduler.add_job(inventory_job, 'interval', seconds=60)


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
