from fastapi import APIRouter

from app.languages import list_languages

router = APIRouter()


@router.get("/api/languages")
def get_languages() -> list[dict]:
    return [
        {
            "code": language.code,
            "label": language.label,
            "native_label": language.native_label,
        }
        for language in list_languages()
    ]
