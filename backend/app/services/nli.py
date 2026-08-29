import math

from sentence_transformers import CrossEncoder


class NLIProvider:

    def __init__(self):
        self.model = CrossEncoder(
            "cross-encoder/nli-deberta-v3-base"
        )

    def predict(
        self,
        premise: str,
        hypothesis: str,
    ) -> dict:

        logits = self.model.predict(
            [(premise, hypothesis)]
        )[0]

        # type: ignore is needed because CrossEncoder type stubs don't expose config
        labels = self.model.model.config.id2label  # type: ignore

        probabilities = self._softmax(logits)

        scores = {
            labels[i]: probabilities[i]
            for i in range(len(probabilities))
        }

        best_label = max(
            scores,
            key=scores.__getitem__,
        )

        return {
            "label": best_label,
            "scores": scores,
        }

    @staticmethod
    def _softmax(
        values,
    ) -> list[float]:

        max_value = max(values)

        exponentials = [
            math.exp(value - max_value)
            for value in values
        ]

        total = sum(exponentials)

        return [
            value / total
            for value in exponentials
        ]


nli_provider = NLIProvider()