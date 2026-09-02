from fastapi import APIRouter

from app.api.scenarios import router as scenarios_router
from app.api.session_start import router as session_start_router
from app.api.turn import router as turn_router

api_router = APIRouter()
api_router.include_router(scenarios_router)
api_router.include_router(session_start_router)
api_router.include_router(turn_router)
