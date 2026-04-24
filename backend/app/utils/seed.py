"""Seed inicial: cria roles padrão e usuário admin se não existirem."""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.repositories.user_repository import UserRepository
from app.core.security import hash_password

ROLES = ["admin", "reviewer", "user"]

ADMIN_NAME = "Admin"
ADMIN_EMAIL = "admin@tipster.local"
ADMIN_PASSWORD = "admin1234"  # Trocar via variável de ambiente em produção


async def run_seed(db: AsyncSession) -> None:
    repo = UserRepository(db)

    for role_name in ROLES:
        existing = await repo.get_role_by_name(role_name)
        if not existing:
            await repo.create_role(role_name)
            print(f"[seed] Role criada: {role_name}")

    admin = await repo.get_by_email(ADMIN_EMAIL)
    if not admin:
        admin = await repo.create(
            name=ADMIN_NAME,
            email=ADMIN_EMAIL,
            password_hash=hash_password(ADMIN_PASSWORD),
        )
        await repo.assign_role(admin.id, "admin")
        print(f"[seed] Usuário admin criado: {ADMIN_EMAIL}")

    await db.commit()
    print("[seed] Concluído.")


async def main():
    async with AsyncSessionLocal() as db:
        await run_seed(db)


if __name__ == "__main__":
    asyncio.run(main())
