from fastapi import APIRouter

from app.scenarios.loader import list_scenarios

router = APIRouter()


@router.get("/api/scenarios")
def get_scenarios() -> list[dict]:
    return [
        {
            "id": s.id,
            "title": s.title,
            "target_language": s.target_language,
            "difficulty": s.difficulty,
        }
        for s in list_scenarios()
    ]
