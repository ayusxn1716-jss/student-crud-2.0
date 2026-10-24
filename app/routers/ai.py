import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status

from .. import ai_service
from ..database import get_db
from ..schemas import AskRequest, AskResponse

router = APIRouter(prefix="/ai", tags=["AI (optional bonus)"])


@router.post("/ask", response_model=AskResponse,
             summary="Ask a natural-language question about the students")
def ask(payload: AskRequest, db: sqlite3.Connection = Depends(get_db)):
    try:
        return ai_service.answer_question(db, payload.question)
    except ai_service.OllamaUnavailable as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc))
