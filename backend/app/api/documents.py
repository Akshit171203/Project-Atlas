from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import DocumentRecord
from app.services.ingestion import IngestionService

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

ingestion_service = IngestionService()
document_repository = DocumentRepository()


@router.get("")
async def list_documents(
    session: AsyncSession = Depends(get_db),
) -> list[DocumentRecord]:

    documents = await document_repository.list_all(session=session)

    return [
        DocumentRecord.model_validate(document)
        for document in documents
    ]


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: int,
    session: AsyncSession = Depends(get_db),
) -> None:

    document = await document_repository.get(
        session=session,
        document_id=document_id,
    )

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    await document_repository.delete(
        session=session,
        document_id=document_id,
    )


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
        document, chunks, embedding_count = await ingestion_service.ingest(
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
        "document_id": document.id,
        "filename": document.filename,
        "pages": document.total_pages,
        "chunks": len(chunks),
        "embeddings": embedding_count,
    }