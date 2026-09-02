from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app import settings
from app.languages import list_languages
from app.llm_catalog import as_dicts as catalog_as_dicts
from app.pipeline.llm import (
    LLMError,
    _base_url,
    get_pull_state,
    list_installed_models,
    start_pull,
)

router = APIRouter()


class UpdateModelsRequest(BaseModel):
    stt_model: str | None = None
    llm_model: str | None = None
    tts_voices: dict[str, str] | None = None


def _current_state() -> dict:
    current = settings.as_dict()
    installed = list_installed_models()

    return {
        "stt": {
            "engine": "faster-whisper",
            "model": current["stt_model"],
            "options": list(settings.STT_MODEL_SIZES),
        },
        "llm": {
            "engine": "Ollama",
            "model": current["llm_model"],
            "base_url": _base_url(),
            "installed": installed,
            # Ollama answered but doesn't have the configured model pulled —
            # worth flagging, since turns will fail until it's pulled.
            "reachable": bool(installed),
            "model_installed": current["llm_model"] in installed,
            "catalog": catalog_as_dicts(),
            "pull": get_pull_state(),
        },
        "tts": {
            "engine": "Piper",
            "voices": [
                {
                    "code": language.code,
                    "label": language.native_label,
                    "voice": current["tts_voices"].get(language.code, language.voice),
                    "options": list(language.voices),
                }
                for language in list_languages()
            ],
        },
    }


@router.get("/api/models")
def get_models() -> dict:
    return _current_state()


@router.put("/api/models")
def update_models(request: UpdateModelsRequest) -> dict:
    try:
        settings.update(
            stt_model=request.stt_model,
            llm_model=request.llm_model,
            tts_voices=request.tts_voices,
        )
    except settings.InvalidSetting as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _current_state()


class PullModelRequest(BaseModel):
    model: str


@router.post("/api/models/llm/pull")
def pull_model(request: PullModelRequest) -> dict:
    name = request.model.strip()
    if not name:
        raise HTTPException(status_code=400, detail="model name cannot be empty")
    try:
        return start_pull(name)
    except LLMError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/api/models/llm/pull")
def pull_status() -> dict:
    return get_pull_state()
