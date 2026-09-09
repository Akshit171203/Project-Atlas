from app.schemas.citation import (
    CitationVerification,
    CitationVerificationResult,
)
from app.services.citation import extract_citations
from app.services.citation_verifier import CitationVerifier
from app.services.claim_extractor import extract_claims
from app.services.source_registry import SourceRegistry


class AnswerVerifier:

    def __init__(self):
        self.citation_verifier = CitationVerifier()

    async def verify(
        self,
        answer: str,
        registry: SourceRegistry,
    ) -> CitationVerificationResult:

        claims = await extract_claims(answer)

        verifications = [
            self._verify_against_all_sources(
                claim=claim.text,
                registry=registry,
            )
            for claim in claims
        ]

        return CitationVerificationResult(
            verifications=verifications
        )

    def _verify_against_all_sources(
        self,
        claim: str,
        registry: SourceRegistry,
    ) -> CitationVerification:
        # Check every retrieved source, not just whichever one the LLM
        # happened to cite. The generating model routinely synthesizes
        # across multiple retrieved chunks but attributes everything to
        # one citation marker (measured example: a claim about Redis was
        # cited [S1], but only entailed by S2 — see
        # EVIDENCE_GATE_CALIBRATION.md). Checking every source finds the
        # claim's real support, so a lazy citation habit in the LLM no
        # longer reads as a hallucinated claim.

        sources = registry.all()

        if not sources:
            return CitationVerification(
                claim=claim,
                source_id="",
                label="no_sources",
                score=0.0,
                supported=False,
                reason="No sources were retrieved to check against.",
            )

        best: CitationVerification | None = None

        for source_id in sources:

            result = self.citation_verifier.verify(
                claim=claim,
                source_id=source_id,
                registry=registry,
            )

            if best is None or result.score > best.score:
                best = result

        assert best is not None
        return best