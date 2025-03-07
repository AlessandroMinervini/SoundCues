from pydantic import BaseModel, Field
from typing import Dict, List


class Question(BaseModel):
    question: str


class AnswerModel(BaseModel):
    results: List[str] = Field(
        ...,
        description="A list of artists, bands, or songs suggested based on the user input.",
    )
    valid_request: bool = Field(
        ...,
        description="A boolean indicating if the input was a valid music recommendation request.",
    )


class Status:
    OK: int = 200
    BAD_REQUEST: int = 400
    NOT_FOUND: int = 404
    INTERNAL_SERVER_ERROR: int = 500


class Response(BaseModel):
    status: int
    status_message: str
    metadata: str | Dict | None = None


class Error(Exception):
    def __init__(
        self, message: str, status_message: str | None = None, detail: str | None = None
    ):
        super().__init__(message)
        self.status_message = status_message
        self.detail = detail
