from pydantic import BaseModel, Field


class Scenario(BaseModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    target_language: str = Field(min_length=1)
    persona_prompt: str = Field(min_length=1)
    goal: str = Field(min_length=1)
    difficulty: str = Field(min_length=1)
