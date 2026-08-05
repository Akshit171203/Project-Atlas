import fitz
from app.schemas.document import Page, DocumentContent

class PDFParser:
    def parse_pdf(self, pdf_path: str) -> DocumentContent:
        document = fitz.open(pdf_path)

        pages = []

        for page in document:

            pages.append(
                Page(
                    page_number=int(page.number or 0) + 1,
                    text=str(page.get_text()),
                )
            )

        document.close()

        return DocumentContent(
            filename=pdf_path,
            total_pages=len(pages),
            pages=pages,
        )