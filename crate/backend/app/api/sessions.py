"""Listening session API routes."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.services.listening_sessions import generate_session
from app.dependencies import get_user_id

router = APIRouter(prefix="/sessions", tags=["sessions"])


class SessionRequest(BaseModel):
    prompt: str
    group_id: str | None = None
    max_records: int = 10


@router.post("/generate")
def create_session(req: SessionRequest, uid: str = Depends(get_user_id)):
    return generate_session(
        user_id=uid,
        prompt_text=req.prompt,
        group_id=req.group_id,
        max_records=req.max_records,
    )
