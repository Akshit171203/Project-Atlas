from app.schemas.citation import CitationVerificationResult
from app.services.citation import extract_citations
from app.services.citation_verifier import CitationVerifier
from app.services.claim_extractor import extract_claims
from app.services.source_registry import SourceRegistry


class AnswerVerifier:

    def __init__(self):
        self.citation_verifier = CitationVerifier()

    def verify(
        self,
        answer: str,
        registry: SourceRegistry,
    ) -> CitationVerificationResult:

        claims = extract_claims(answer)

        verifications = []

        for claim, source_ids in claims:

            for source_id in source_ids:

                verification = self.citation_verifier.verify(
                    claim=claim,
                    source_id=source_id,
                    registry=registry,
                )

                verifications.append(
                    verification
                )

        return CitationVerificationResult(
            verifications=verifications
        )