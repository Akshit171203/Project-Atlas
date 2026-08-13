from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.services.ingestion import IngestionService

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

ingestion_service = IngestionService()


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
):

    document, chunks = await ingestion_service.ingest(
        session=session,
        file=file,
    )

    return {
        "document_id": document.id,
        "filename": document.filename,
        "pages": document.total_pages,
        "chunks": len(chunks),
    }