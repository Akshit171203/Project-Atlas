from pydantic import BaseModel

class CitationVerification(BaseModel):
    claim: str
    source_id: str
    label: str
    score: float
    supported: bool
    reason: str

class CitationVerificationResult(BaseModel):
    verifications: list[CitationVerification]

    @property
    def all_supported(self) -> bool:
        return all(
            verification.supported
            for verification in self.verifications
        )

    @property
    def failed(self) -> list[CitationVerification]:
        return [
            verification
            for verification in self.verifications
            if not verification.supported
        ]
