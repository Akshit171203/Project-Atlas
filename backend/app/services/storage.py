from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.schemas.storage import StoredFile

class StorageService:
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)

    async def save(self, file: UploadFile) -> StoredFile:
        filename = file.filename or "unknown.pdf"
        unique_filename = f"{uuid4().hex}_{filename}"
        file_path = self.upload_dir / unique_filename

        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        extension = file_path.suffix.lower()

        return StoredFile(
            filename=filename,
            path=file_path,
            extension=extension,
        )

