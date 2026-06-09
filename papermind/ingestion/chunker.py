from dataclasses import dataclass

from ingestion.parser import ParsedPage


@dataclass
class Chunk:
    paper_id: str
    chunk_id: str
    text: str
    page_number: int
    paragraph_number: int
    metadata: dict


def chunk_pages(
    pages: list[ParsedPage], chunk_size: int = 512, overlap: int = 50
) -> list[Chunk]:
    chunks = []

    for page in pages:
        # Fall back to treating the whole page as one paragraph if none were detected
        paragraphs = page.paragraphs if page.paragraphs else [page.text]

        for para_idx, paragraph in enumerate(paragraphs, start=1):
            words = paragraph.split()
            if not words:
                continue

            start = 0
            chunk_index = 0

            while start < len(words):
                end = min(start + chunk_size, len(words))
                chunk_text = " ".join(words[start:end])
                chunk_id = f"{page.paper_id}_p{page.page_number}_para{para_idx}_c{chunk_index}"

                chunks.append(
                    Chunk(
                        paper_id=page.paper_id,
                        chunk_id=chunk_id,
                        text=chunk_text,
                        page_number=page.page_number,
                        paragraph_number=para_idx,
                        metadata={
                            **page.metadata,
                            "paper_id": page.paper_id,
                            "page_number": page.page_number,
                            "paragraph_number": para_idx,
                            "chunk_index": chunk_index,
                        },
                    )
                )

                if end == len(words):
                    break
                start = end - overlap
                chunk_index += 1

    return chunks
