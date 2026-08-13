from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document


class DocumentRepository:

    async def create(
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