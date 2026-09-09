from sqlalchemy.ext.asyncio import AsyncSession

from app.prompts.rag import (
    SYSTEM_PROMPT,
    build_rag_prompt,
)
from app.schemas.rag import RAGResult
from app.services.answer_repairer import AnswerRepairer
from app.services.answer_verifier import AnswerVerifier
from app.services.context_builder import ContextBuilder
from app.services.context_formatter import ContextFormatter
from app.services.evidence_gate import EvidenceGate
from app.services.llm import default_llm
from app.services.reranked_retrieval import RerankedRetriever
from app.services.source_registry import SourceRegistry
from app.schemas.citation import CitationVerificationResult
from app.services.answer_relevance import (
    answer_relevance_evaluator,
)


class RAGService:

    def __init__(self):
        self.retriever = RerankedRetriever()
        self.evidence_gate = EvidenceGate()
        self.answer_repairer = AnswerRepairer()
        self.context_builder = ContextBuilder()
        self.context_formatter = ContextFormatter()
        self.llm = default_llm
        self.answer_verifier = AnswerVerifier()

    async def answer(
        self,
        session: AsyncSession,
        query: str,
        document_id: int | None = None,
    ):

        chunks = await self.retriever.retrieve(
            session=session,
            query=query,
            candidate_k=10,
            top_k=5,
            document_id=document_id,
        )

        if not self.evidence_gate.is_answerable(chunks):
            return RAGResult(
                answer=(
                    "I don't have enough information in the "
                    "knowledge base to answer this question."
                ),
                verification=CitationVerificationResult(
                    verifications=[]
                ),
                repaired=False,
                answerable=False,
                retrieval_chunk_ids=[
                    chunk.chunk_id
                    for chunk in chunks
                ],
            )

        context = self.context_builder.build(
            query=query,
            chunks=chunks,
        )

        formatted_context = self.context_formatter.format(
            context
        )

        user_prompt = build_rag_prompt(
            query=query,
            context=formatted_context,
        )

        answer = await self.llm.generate(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        registry = SourceRegistry(chunks)

        initial_answer = answer

        initial_verification = await self.answer_verifier.verify(
            answer=answer,
            registry=registry,
        )

        verification = initial_verification
        repaired = False

        if not verification.all_supported:

            failed_claims = [
                item.claim
                for item in verification.failed
            ]

            answer = await self.answer_repairer.repair(
                answer=answer,
                context=formatted_context,
                failed_claims=failed_claims,
            )

            repaired = True

            verification = await self.answer_verifier.verify(
                answer=answer,
                registry=registry,
            )

        relevance = await answer_relevance_evaluator.evaluate(
            query=query,
            answer=answer,
        )

        return RAGResult(
            answer=answer,
            verification=verification,
            repaired=repaired,
            initial_answer=initial_answer,
            initial_verification=initial_verification,
            answerable=True,
            retrieval_chunk_ids=[
                chunk.chunk_id
                for chunk in chunks
            ],
            relevance=relevance,
        )