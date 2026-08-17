from pathlib import Path

from app.schemas.document import DocumentContent
from app.schemas.storage import StoredFile
from app.services.pdf_parser import PDFParser


class ParserService:
    def __init__(self):
        self.pdf_parser = PDFParser()

    def parse(
        self,
        stored_file: StoredFile,
    ) -> DocumentContent:

        suffix = stored_file.extension

        if suffix == ".pdf":
            return self.pdf_parser.parse(
                pdf_path=str(stored_file.path),
                filename=stored_file.filename,
            )

        raise ValueError(f"Unsupported file type: {suffix}")
