from pathlib import Path

from app.schemas.document import DocumentContent
from app.services.pdf_parser import PDFParser


class ParserService:
    def __init__(self):
        self.pdf_parser = PDFParser()

    def parse(
        self,
        file_path: Path,
        filename: str,
    ) -> DocumentContent:

        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            return self.pdf_parser.parse(
                pdf_path=str(file_path),
                filename=filename,
            )

        raise ValueError(f"Unsupported file type: {suffix}")
