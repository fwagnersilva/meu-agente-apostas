from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import decode_token
from app.repositories.user_repository import UserRepository

bearer = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
):
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

    user_id = int(payload["sub"])
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário inativo")
    return user


def require_roles(*roles: str):
    async def checker(current_user=Depends(get_current_user)):
        user_roles = {r.name for r in current_user.roles}
        if not user_roles.intersection(roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão negada")
        return current_user
    return checker


require_admin = require_roles("admin")
require_reviewer = require_roles("admin", "reviewer")
