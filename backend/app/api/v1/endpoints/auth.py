from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.auth import LoginRequest, RegisterRequest, RefreshRequest, TokenResponse, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService(db).login(data)


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService(db).register(data)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService(db).refresh(data.refresh_token)


@router.get("/me", response_model=UserResponse)
async def me(current_user=Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        is_active=current_user.is_active,
        roles=[r.name for r in current_user.roles],
    )
