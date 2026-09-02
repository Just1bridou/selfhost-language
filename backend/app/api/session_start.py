from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.scenarios.loader import get_scenario
from app.state.session_store import create_session

router = APIRouter()


class StartSessionRequest(BaseModel):
    scenario_id: str


class StartSessionResponse(BaseModel):
    session_id: str


@router.post("/api/session/start", response_model=StartSessionResponse)
def start_session(request: StartSessionRequest) -> StartSessionResponse:
    scenario = get_scenario(request.scenario_id)
    if scenario is None:
        raise HTTPException(
            status_code=404, detail=f"unknown scenario id: {request.scenario_id!r}"
        )

    session = create_session(request.scenario_id)
    return StartSessionResponse(session_id=session.id)
