from pydantic import BaseModel

class Claim(BaseModel):
    claim_id: int
    text: str
    source_ids: list[str]
