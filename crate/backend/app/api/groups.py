"""Group management API routes."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.group import Group, GroupMembership
from app.models.user import User
from app.dependencies import get_current_user
from app.graph.connection import get_neo4j_driver

router = APIRouter(prefix="/groups", tags=["groups"])


class CreateGroupRequest(BaseModel):
    name: str


class JoinGroupRequest(BaseModel):
    invite_code: str


class GroupResponse(BaseModel):
    id: str
    name: str
    invite_code: str
    role: str
    member_count: int


class GroupMemberResponse(BaseModel):
    user_id: str
    name: str
    role: str


@router.post("/", response_model=GroupResponse)
async def create_group(
    req: CreateGroupRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    group = Group(name=req.name, created_by=user.id)
    db.add(group)
    await db.flush()

    membership = GroupMembership(user_id=user.id, group_id=group.id, role="admin")
    db.add(membership)
    await db.commit()

    # Create group node in Neo4j and link user
    driver = get_neo4j_driver()
    with driver.session() as session:
        session.run(
            """
            MERGE (g:Group {id: $group_id})
            SET g.name = $name
            WITH g
            MATCH (u:User {id: $user_id})
            MERGE (u)-[:MEMBER_OF_GROUP {role: 'admin', joined_at: datetime()}]->(g)
            """,
            group_id=str(group.id), name=group.name, user_id=str(user.id),
        )

    return GroupResponse(
        id=str(group.id), name=group.name, invite_code=group.invite_code,
        role="admin", member_count=1,
    )


@router.post("/join", response_model=GroupResponse)
async def join_group(
    req: JoinGroupRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Group).where(Group.invite_code == req.invite_code))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Invalid invite code")

    # Check if already a member
    existing = await db.execute(
        select(GroupMembership).where(
            GroupMembership.user_id == user.id,
            GroupMembership.group_id == group.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already a member")

    membership = GroupMembership(user_id=user.id, group_id=group.id, role="member")
    db.add(membership)
    await db.commit()

    # Link in Neo4j
    driver = get_neo4j_driver()
    with driver.session() as session:
        session.run(
            """
            MATCH (u:User {id: $user_id}), (g:Group {id: $group_id})
            MERGE (u)-[:MEMBER_OF_GROUP {role: 'member', joined_at: datetime()}]->(g)
            """,
            user_id=str(user.id), group_id=str(group.id),
        )

    # Count members
    count_result = await db.execute(
        select(GroupMembership).where(GroupMembership.group_id == group.id)
    )
    member_count = len(count_result.all())

    return GroupResponse(
        id=str(group.id), name=group.name, invite_code=group.invite_code,
        role="member", member_count=member_count,
    )


@router.get("/", response_model=list[GroupResponse])
async def list_groups(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Group, GroupMembership.role)
        .join(GroupMembership, GroupMembership.group_id == Group.id)
        .where(GroupMembership.user_id == user.id)
    )
    groups = []
    for group, role in result.all():
        count_result = await db.execute(
            select(GroupMembership).where(GroupMembership.group_id == group.id)
        )
        groups.append(GroupResponse(
            id=str(group.id), name=group.name, invite_code=group.invite_code,
            role=role, member_count=len(count_result.all()),
        ))
    return groups


@router.get("/{group_id}/members", response_model=list[GroupMemberResponse])
async def list_members(
    group_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User, GroupMembership.role)
        .join(GroupMembership, GroupMembership.user_id == User.id)
        .where(GroupMembership.group_id == uuid.UUID(group_id))
    )
    return [
        GroupMemberResponse(user_id=str(u.id), name=u.name, role=role)
        for u, role in result.all()
    ]
