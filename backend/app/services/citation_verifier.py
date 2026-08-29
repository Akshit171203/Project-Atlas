from app.schemas.citation import CitationVerification
from app.services.nli import nli_provider
from app.services.source_registry import SourceRegistry
from app.services.source_sentence_splitter import split_sentences


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

        sentences = split_sentences(
            source.text
        )

        if not sentences:
            return CitationVerification(
                claim=claim,
                source_id=source_id,
                label="no_source_text",
                score=0.0,
                supported=False,
                reason="Source contains no usable sentences.",
            )

        best_label = "neutral"
        best_score = 0.0

        for sentence in sentences:

            result = self.nli.predict(
                premise=sentence,
                hypothesis=claim,
            )

            entailment_score = result["scores"][
                "entailment"
            ]

            if entailment_score > best_score:

                best_score = entailment_score
                best_label = result["label"]

        supported = (
            best_label == "entailment"
            and best_score >= self.entailment_threshold
        )

        return CitationVerification(
            claim=claim,
            source_id=source_id,
            label=best_label,
            score=best_score,
            supported=supported,
            reason=(
                "Claim is supported by the source."
                if supported
                else "Claim is not supported by the source."
            ),
        )