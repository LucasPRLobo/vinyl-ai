"""FastAPI dependencies: DB sessions, auth middleware."""

from fastapi import Depends, HTTPException, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.services.auth import decode_token, get_user_by_id


async def get_current_user(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Extract and validate JWT from Authorization header. Returns User. Raises 401 if not authenticated."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    token = authorization.split(" ", 1)[1]
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await get_user_by_id(db, payload["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def get_optional_user(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Like get_current_user but returns None instead of 401 if no token."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        return None
    return await get_user_by_id(db, payload["sub"])


async def get_user_id(
    authorization: str = Header(None),
    user_id: str = Query(None),
    db: AsyncSession = Depends(get_db),
) -> str:
    """Get user ID from auth token if present, otherwise from query param.
    This allows authenticated and unauthenticated access during development."""
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
        payload = decode_token(token)
        if payload and "sub" in payload:
            return payload["sub"]

    if user_id:
        return user_id

    raise HTTPException(status_code=401, detail="Authentication required. Provide a token or user_id param.")
