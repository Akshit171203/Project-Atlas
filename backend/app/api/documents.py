from pathlib import Path

from fastapi import APIRouter, File, UploadFile

from app.services.chunking import ChunkingService
from app.services.pdf_parser import PDFParser

router = APIRouter(prefix="/documents", tags=["Documents"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

parser = PDFParser()
chunking_service = ChunkingService()


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    file_path = UPLOAD_DIR / (file.filename or "unknown_file.pdf")

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    document = parser.parse(
        pdf_path=str(file_path),
        filename=file.filename,
    )

    chunks = chunking_service.chunk_document(document)
   
    for chunk in chunks:
        print(f"{chunk.id} -> {len(chunk.text)} chars")

    return {
        "filename": document.filename,
        "pages": document.total_pages,
        "total_chunks": len(chunks),
        "first_chunk": chunks[0].text,
        "last_chunk": chunks[-1].text,
    }