from app.schemas.chunk import Chunk
from app.schemas.document import DocumentContent


class ChunkingService:

    def chunk(
        self,
        document: DocumentContent,
        chunk_size: int = 500,
        overlap: int = 50,
    ) -> list[Chunk]:

        chunks = []

        for page in document.pages:

            text = page.text

            start = 0
            chunk_index = 0

            while start < len(text):

                end = min(start + chunk_size, len(text))
                
                if end < len(text):
                    while end > start and not text[end].isspace():
                        end -= 1

                    chunk_text = text[start:end].strip()
                else:
                    chunk_text = text[start:].strip()
                if not chunk_text:
                    break

                chunks.append(
                    Chunk(
                        page_number=page.page_number,
                        chunk_index=chunk_index,
                        text=chunk_text,
                    )
                )

                start += chunk_size - overlap
                chunk_index += 1

        return chunks