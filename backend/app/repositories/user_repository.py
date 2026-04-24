from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, Role, UserRole


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.user_roles).selectinload(UserRole.role))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.user_roles).selectinload(UserRole.role))
            .where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def create(self, name: str, email: str, password_hash: str) -> User:
        user = User(name=name, email=email, password_hash=password_hash)
        self.db.add(user)
        await self.db.flush()
        return user

    async def assign_role(self, user_id: int, role_name: str) -> None:
        role = await self._get_role_by_name(role_name)
        if role:
            self.db.add(UserRole(user_id=user_id, role_id=role.id))
            await self.db.flush()

    async def _get_role_by_name(self, name: str) -> Role | None:
        result = await self.db.execute(select(Role).where(Role.name == name))
        return result.scalar_one_or_none()

    async def get_role_by_name(self, name: str) -> Role | None:
        return await self._get_role_by_name(name)

    async def create_role(self, name: str) -> Role:
        role = Role(name=name)
        self.db.add(role)
        await self.db.flush()
        return role

    async def update_last_login(self, user: User) -> None:
        from datetime import datetime, timezone
        user.last_login_at = datetime.now(timezone.utc)
        await self.db.flush()
