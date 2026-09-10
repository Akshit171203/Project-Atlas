import uuid

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.user import User, UserRole


class UserRepository:

    async def get_by_email(
        self,
        session: AsyncSession,
        email: str,
    ) -> User | None:
        result = await session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
    ) -> User | None:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def count(self, session: AsyncSession) -> int:
        result = await session.execute(
            select(func.count()).select_from(User)
        )
        return result.scalar_one()

    async def list_all(self, session: AsyncSession) -> list[User]:
        result = await session.execute(
            select(User).order_by(User.created_at)
        )
        return list(result.scalars().all())

    async def create(
        self,
        session: AsyncSession,
        name: str,
        email: str,
        password_hash: str,
        role: UserRole,
        verified: bool,
    ) -> User:
        user = User(
            name=name,
            email=email,
            password_hash=password_hash,
            role=role,
            verified=verified,
        )
        session.add(user)
        await session.flush()
        return user

    async def mark_verified(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
    ) -> None:
        await session.execute(
            update(User).where(User.id == user_id).values(verified=True)
        )

    async def adopt_ownerless_documents(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
    ) -> int:
        """Hand every unowned document to `user_id`.

        Documents ingested before auth existed have `user_id IS NULL`. The
        first registered account (seeded ADMIN) adopts them, so the existing
        corpus - including the documents the eval suite depends on - stays
        reachable through the API instead of being stranded.
        """
        result = await session.execute(
            update(Document)
            .where(Document.user_id.is_(None))
            .values(user_id=user_id)
        )
        return result.rowcount or 0
