from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.schemas.rag import QueryRequest, RAGResult
from app.services.rag import RAGService

router = APIRouter(
    prefix="/query",
    tags=["Query"],
)

rag_service = RAGService()


@router.post("")
async def query(
    request: QueryRequest,
    session: AsyncSession = Depends(get_db),
) -> RAGResult:

    return await rag_service.answer(
        session=session,
        query=request.query,
    )
