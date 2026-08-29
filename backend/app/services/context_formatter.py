from app.schemas.context import RetrievedContext


class ContextFormatter:

    def format(
        self,
        context: RetrievedContext,
    ) -> str:

        sections = []

        for source in context.sources:

            section = (
                f"[{source.source_id}]\n"
                f"Document: {source.filename}\n"
                f"Page: {source.page_number}\n"
                f"Chunk: {source.chunk_id}\n\n"
                f"{source.text}"
            )

            sections.append(section)

        return "\n\n---\n\n".join(sections)