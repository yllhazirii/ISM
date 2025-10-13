from fastapi import APIRouter

from app.api.routes import items, login, private, users, utils, depot_address, depot_master, gate_out
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)
api_router.include_router(depot_address.router)
api_router.include_router(depot_master.router)
api_router.include_router(gate_out.router)

if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
