from dataclasses import dataclass, field


@dataclass(eq=False)
class TextChunk:
    page_content: str
    metadata: dict = field(default_factory=dict)


class CharacterTextSplitter:
    def __init__(self, separator: str = "\n\n", chunk_size: int = 1000, chunk_overlap: int = 200):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be greater than or equal to 0")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")

        self.separator = separator
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def create_documents(self, texts: list[str]) -> list[TextChunk]:
        documents = []
        for text in texts:
            for chunk in self.split_text(text or ""):
                documents.append(TextChunk(page_content=chunk))
        return documents

    def split_text(self, text: str) -> list[str]:
        text = str(text)
        if not text.strip():
            return []

        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = min(start + self.chunk_size, text_length)

            if self.separator and end < text_length:
                separator_index = text.rfind(self.separator, start, end)
                if separator_index > start:
                    end = separator_index

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            if end >= text_length:
                break

            next_start = max(end - self.chunk_overlap, start + 1)
            start = next_start

        return chunks
