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

    async def get(
        self,
        session: AsyncSession,
        document_id: int,
    ) -> Document | None:
        raise NotImplementedError()

    async def delete(
        self,
        session: AsyncSession,
        document_id: int,
    ) -> None:
        raise NotImplementedError()