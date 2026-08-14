from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
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
) -> dict:

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported.",
        )

    try:
        result = await ingestion_service.ingest(
            session=session,
            file=file,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {e}",
        )

    return {
        "document_id": result.document.id,
        "filename": result.document.filename,
        "pages": result.document.total_pages,
        "chunks": len(result.chunks),
    }