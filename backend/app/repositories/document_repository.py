from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document


class DocumentRepository:

    async def save(
        self,
        session: AsyncSession,
        filename: str,
        total_pages: int,
    ) -> Document:

        document = Document(
            filename=filename,
            total_pages=total_pages,
        )

        session.add(document)

        # Flush gives us document.id without committing
        await session.flush()

        return document

    async def list_all(
        self,
        session: AsyncSession,
    ) -> list[Document]:

        result = await session.execute(
            select(Document).order_by(Document.id)
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