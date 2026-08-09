import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    chunk_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    doc_id: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    start_char: int = 0
    end_char: int = 0


class TextChunker:
    """Intelligent text chunker supporting overlapping sliding windows and boundary awareness."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be strictly less than chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str, doc_id: str, metadata: Optional[Dict[str, Any]] = None) -> List[DocumentChunk]:
        if not text.strip():
            return []

        meta = metadata or {}
        chunks: List[DocumentChunk] = []
        
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + self.chunk_size
            if end > text_length:
                end = text_length
            else:
                # Try to adjust boundary to nearest whitespace or newline
                boundary = text.rfind("\n", start + self.chunk_size // 2, end)
                if boundary == -1:
                    boundary = text.rfind(" ", start + self.chunk_size // 2, end)
                if boundary != -1 and boundary > start:
                    end = boundary

            chunk_str = text[start:end].strip()
            if chunk_str:
                chunks.append(
                    DocumentChunk(
                        doc_id=doc_id,
                        content=chunk_str,
                        metadata=meta,
                        start_char=start,
                        end_char=end
                    )
                )

            if end == text_length:
                break

            # Slide start index accounting for overlap
            start = end - self.chunk_overlap
            if start < 0:
                start = 0

        return chunks
