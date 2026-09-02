from fastapi import APIRouter

from app.difficulty import list_difficulties

router = APIRouter()


@router.get("/api/difficulties")
def get_difficulties() -> list[dict]:
    return [
        {"code": level.code, "label": level.label, "hint": level.hint}
        for level in list_difficulties()
    ]
