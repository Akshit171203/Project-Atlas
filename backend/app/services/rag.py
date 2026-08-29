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
from app.services.llm import gemini_provider
from app.services.reranked_retrieval import RerankedRetriever
from app.services.source_registry import SourceRegistry
from app.schemas.citation import CitationVerificationResult


class RAGService:

    def __init__(self):
        self.retriever = RerankedRetriever()
        self.evidence_gate = EvidenceGate()
        self.answer_repairer = AnswerRepairer()
        self.context_builder = ContextBuilder()
        self.context_formatter = ContextFormatter()
        self.llm = gemini_provider
        self.answer_verifier = AnswerVerifier()

    async def answer(
        self,
        session: AsyncSession,
        query: str,
    ):

        chunks = await self.retriever.retrieve(
            session=session,
            query=query,
            candidate_k=10,
            top_k=5,
        )

        if not self.evidence_gate.is_answerable(chunks):
            return RAGResult(
                answer="I don't have enough information in the knowledge base to answer this question.",
                verification=CitationVerificationResult(verifications=[]),
                repaired=False,
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

        verification = self.answer_verifier.verify(
            answer=answer,
            registry=registry,
        )

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

            verification = self.answer_verifier.verify(
                answer=answer,
                registry=registry,
            )

        return RAGResult(
            answer=answer,
            verification=verification,
            repaired=repaired,
        )