from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
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
    user: User = Depends(get_current_user),
) -> list[DocumentRecord]:

    documents = await document_repository.list_for_user(
        session=session,
        user_id=user.id,
    )

    return [
        DocumentRecord.model_validate(document)
        for document in documents
    ]


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: int,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:

    document = await document_repository.get_for_user(
        session=session,
        document_id=document_id,
        user_id=user.id,
    )

    # 404 rather than 403 for a document owned by someone else: replying
    # "forbidden" confirms that document_id exists, which lets an attacker
    # enumerate the whole corpus. To a non-owner it simply isn't there.
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
    user: User = Depends(get_current_user),
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
            user_id=user.id,
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
