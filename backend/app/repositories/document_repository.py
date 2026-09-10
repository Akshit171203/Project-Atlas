import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document


class DocumentRepository:

    async def save(
        self,
        session: AsyncSession,
        filename: str,
        total_pages: int,
        user_id: uuid.UUID,
    ) -> Document:

        document = Document(
            filename=filename,
            total_pages=total_pages,
            user_id=user_id,
        )

        session.add(document)

        # Flush gives us document.id without committing
        await session.flush()

        return document

    async def list_for_user(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
    ) -> list[Document]:

        result = await session.execute(
            select(Document)
            .where(Document.user_id == user_id)
            .order_by(Document.id)
        )

        return list(result.scalars().all())

    async def get(
        self,
        session: AsyncSession,
        document_id: int,
    ) -> Document | None:

        result = await session.execute(
            select(Document).where(Document.id == document_id)
        )

        return result.scalar_one_or_none()

    async def get_for_user(
        self,
        session: AsyncSession,
        document_id: int,
        user_id: uuid.UUID,
    ) -> Document | None:
        """Fetch a document only if `user_id` owns it.

        Ownership is enforced in the WHERE clause rather than by fetching
        the row and comparing afterwards, so there is no code path where a
        document belonging to someone else has been loaded and might be
        acted on by mistake.
        """

        result = await session.execute(
            select(Document).where(
                Document.id == document_id,
                Document.user_id == user_id,
            )
        )

        return result.scalar_one_or_none()

    async def delete(
        self,
        session: AsyncSession,
        document_id: int,
    ) -> None:

        document = await self.get(
            session=session,
            document_id=document_id,
        )

        if document is None:
            return

        await session.delete(document)
        await session.commit()
