import base64

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.pipeline.turn import TurnError, run_turn

router = APIRouter()


@router.post("/api/session/{session_id}/turn")
async def submit_turn(session_id: str, audio: UploadFile = File(...)) -> dict:
    audio_bytes = await audio.read()

    try:
        result = run_turn(session_id, audio_bytes)
    except TurnError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    return {
        "user_text": result.user_text,
        "ai_text": result.ai_text,
        "audio_base64": base64.b64encode(result.audio_bytes).decode("ascii"),
    }
