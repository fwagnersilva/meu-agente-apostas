from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = UserRepository(db)

    async def login(self, data: LoginRequest) -> TokenResponse:
        user = await self.repo.get_by_email(data.email)
        if not user or not verify_password(data.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário inativo")

        await self.repo.update_last_login(user)
        roles = [r.name for r in user.roles]
        return TokenResponse(
            access_token=create_access_token(user.id, roles),
            refresh_token=create_refresh_token(user.id),
        )

    async def register(self, data: RegisterRequest) -> UserResponse:
        existing = await self.repo.get_by_email(data.email)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email já cadastrado")

        user = await self.repo.create(
            name=data.name,
            email=data.email,
            password_hash=hash_password(data.password),
        )
        await self.repo.assign_role(user.id, "user")

        # Recarrega com roles
        user = await self.repo.get_by_id(user.id)
        return UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            is_active=user.is_active,
            roles=[r.name for r in user.roles],
        )

    async def refresh(self, refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido")

        user_id = int(payload["sub"])
        user = await self.repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário inativo")

        roles = [r.name for r in user.roles]
        return TokenResponse(
            access_token=create_access_token(user.id, roles),
            refresh_token=create_refresh_token(user.id),
        )
