from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
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
    user: User = Depends(get_current_user),
) -> RAGResult:

    # Ownership is checked before retrieval runs. Without this a logged-in
    # user could pass any document_id and have the pipeline answer from a
    # document belonging to somebody else - the retrieved chunks are quoted
    # back in the answer, so that would leak the source text itself, not
    # just its existence.
    document = await document_repository.get_for_user(
        session=session,
        document_id=request.document_id,
        user_id=user.id,
    )

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    return await rag_service.answer(
        session=session,
        query=request.query,
        document_id=request.document_id,
    )
