"""Collaborative annotations API."""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.annotation import Annotation
from app.models.user import User
from app.dependencies import get_current_user

router = APIRouter(prefix="/annotations", tags=["annotations"])


class CreateAnnotationRequest(BaseModel):
    node_label: str  # Artist, Album, Label, etc.
    node_name: str
    text: str


class AnnotationResponse(BaseModel):
    id: str
    user_id: str
    user_name: str
    node_label: str
    node_name: str
    text: str
    created_at: str


@router.post("/", response_model=AnnotationResponse)
async def create_annotation(
    req: CreateAnnotationRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    annotation = Annotation(
        user_id=user.id,
        node_label=req.node_label,
        node_name=req.node_name,
        text=req.text,
    )
    db.add(annotation)
    await db.commit()
    await db.refresh(annotation)

    return AnnotationResponse(
        id=str(annotation.id),
        user_id=str(user.id),
        user_name=user.name,
        node_label=annotation.node_label,
        node_name=annotation.node_name,
        text=annotation.text,
        created_at=annotation.created_at.isoformat(),
    )


@router.get("/node/{node_label}/{node_name}", response_model=list[AnnotationResponse])
async def get_annotations(
    node_label: str,
    node_name: str,
    db: AsyncSession = Depends(get_db),
):
    """Get all annotations for a specific graph node."""
    result = await db.execute(
        select(Annotation, User)
        .join(User, Annotation.user_id == User.id)
        .where(Annotation.node_label == node_label, Annotation.node_name == node_name)
        .order_by(Annotation.created_at.desc())
    )
    return [
        AnnotationResponse(
            id=str(a.id),
            user_id=str(a.user_id),
            user_name=u.name,
            node_label=a.node_label,
            node_name=a.node_name,
            text=a.text,
            created_at=a.created_at.isoformat(),
        )
        for a, u in result.all()
    ]
