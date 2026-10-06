import hashlib
from dataclasses import dataclass

CHUNK_VERSION = "characters-v1-900-120"


@dataclass(frozen=True)
class Chunk:
    ordinal: int
    start: int
    end: int
    text: str


def content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def split_content(content: str, size: int = 900, overlap: int = 120) -> list[Chunk]:
    if not 0 <= overlap < size:
        raise ValueError("Chunk overlap must be smaller than size")
    chunks = []
    start = 0
    while start < len(content):
        end = min(start + size, len(content))
        if content[start:end].strip():
            chunks.append(Chunk(len(chunks), start, end, content[start:end]))
        if end == len(content):
            break
        start = end - overlap
    return chunks
