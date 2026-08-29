from app.schemas.citation import CitationVerification
from app.services.nli import nli_provider
from app.services.source_registry import SourceRegistry


class CitationVerifier:

    def __init__(
        self,
        entailment_threshold: float = 0.75,
    ):
        self.nli = nli_provider
        self.entailment_threshold = entailment_threshold

    def verify(
        self,
        claim: str,
        source_id: str,
        registry: SourceRegistry,
    ) -> CitationVerification:

        source = registry.get(source_id)

        if source is None:
            return CitationVerification(
                claim=claim,
                source_id=source_id,
                label="missing_source",
                score=0.0,
                supported=False,
                reason="Source does not exist.",
            )

        result = self.nli.predict(
            premise=source.text,
            hypothesis=claim,
        )

        scores = result["scores"]
        entailment_score = scores["entailment"]

        supported = (
            result["label"] == "entailment"
            and entailment_score >= self.entailment_threshold
        )

        return CitationVerification(
            claim=claim,
            source_id=source_id,
            label=result["label"],
            score=entailment_score,
            supported=supported,
            reason=(
                "Claim is supported by the source."
                if supported
                else "Claim is not supported by the source."
            ),
        )