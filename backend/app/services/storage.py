from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

class StorageService:
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)

    async def save(self, file: UploadFile) -> Path:
        filename = file.filename or "unknown.pdf"
        unique_filename = f"{uuid4().hex}_{filename}"
        file_path = self.upload_dir / unique_filename

        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        return file_path

