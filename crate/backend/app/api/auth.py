"""Auth API routes: register, login."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.services.auth import register_user, authenticate_user, create_token
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    name: str
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    token: str
    user_id: str
    name: str
    email: str


class UserResponse(BaseModel):
    user_id: str
    name: str
    email: str


@router.post("/register", response_model=AuthResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    try:
        user = await register_user(db, email=req.email, name=req.name, password=req.password)
    except Exception:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Also create Neo4j user node
    from app.graph.connection import get_neo4j_driver
    driver = get_neo4j_driver()
    with driver.session() as session:
        session.run(
            "MERGE (u:User {id: $id}) SET u.name = $name",
            id=str(user.id), name=user.name,
        )

    token = create_token(str(user.id), user.name)
    return AuthResponse(token=token, user_id=str(user.id), name=user.name, email=user.email)


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, email=req.email, password=req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_token(str(user.id), user.name)
    return AuthResponse(token=token, user_id=str(user.id), name=user.name, email=user.email)


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return UserResponse(user_id=str(user.id), name=user.name, email=user.email)
