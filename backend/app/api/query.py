from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.repositories.document_repository import DocumentRepository
from app.schemas.rag import QueryRequest, RAGResult
from app.services.rag import RAGService

router = APIRouter(
    prefix="/query",
    tags=["Query"],
)

rag_service = RAGService()
document_repository = DocumentRepository()


@router.post("")
async def query(
    request: QueryRequest,
    session: AsyncSession = Depends(get_db),
) -> RAGResult:

    document = await document_repository.get(
        session=session,
        document_id=request.document_id,
    )

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    return await rag_service.answer(
        session=session,
        query=request.query,
        document_id=request.document_id,
    )
