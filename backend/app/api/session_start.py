from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.difficulty import get_difficulty
from app.languages import get_language
from app.scenarios.loader import get_scenario
from app.state.session_store import create_session

router = APIRouter()


class StartSessionRequest(BaseModel):
    scenario_id: str
    language: str
    difficulty: str


class StartSessionResponse(BaseModel):
    session_id: str
    language: str
    difficulty: str


@router.post("/api/session/start", response_model=StartSessionResponse)
def start_session(request: StartSessionRequest) -> StartSessionResponse:
    scenario = get_scenario(request.scenario_id)
    if scenario is None:
        raise HTTPException(
            status_code=404, detail=f"unknown scenario id: {request.scenario_id!r}"
        )

    language = get_language(request.language)
    if language is None:
        raise HTTPException(
            status_code=400, detail=f"unsupported language: {request.language!r}"
        )

    difficulty = get_difficulty(request.difficulty)
    if difficulty is None:
        raise HTTPException(
            status_code=400, detail=f"unsupported difficulty: {request.difficulty!r}"
        )

    session = create_session(
        request.scenario_id, language=language.code, difficulty=difficulty.code
    )
    return StartSessionResponse(
        session_id=session.id,
        language=session.language,
        difficulty=session.difficulty,
    )
