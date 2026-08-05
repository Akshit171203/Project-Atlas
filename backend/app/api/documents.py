from pathlib import Path

from fastapi import APIRouter, File, UploadFile

from app.services.pdf_parser import PDFParser

router = APIRouter(prefix="/documents", tags=["Documents"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

parser = PDFParser()


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    file_path = UPLOAD_DIR / (file.filename or "unknown_file.pdf")

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    document = parser.parse_pdf(str(file_path))

    return {
        "filename": document.filename,
        "pages": document.total_pages,
        "characters": sum(len(page.text) for page in document.pages),
        "preview": document.pages[0].text[:1000] if document.pages else "",
    }