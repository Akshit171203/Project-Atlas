from pathlib import Path
from pydantic import BaseModel

class StoredFile(BaseModel):
    filename: str
    path: Path
    extension: str
