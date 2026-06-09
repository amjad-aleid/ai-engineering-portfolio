import re
from dataclasses import dataclass, field
from pathlib import Path

import pdfplumber


@dataclass
class ParsedPage:
    paper_id: str
    page_number: int
    text: str
    paragraphs: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


def _extract_paragraphs(text: str) -> list[str]:
    """Split page text into paragraphs on blank lines, filtering noise."""
    raw = re.split(r"\n\s*\n", text)
    return [p.strip() for p in raw if len(p.split()) >= 5]


def parse_pdf(file_path: str | Path) -> list[ParsedPage]:
    path = Path(file_path)
    paper_id = path.stem
    pages = []

    with pdfplumber.open(path) as pdf:
        total = len(pdf.pages)
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            if text.strip():
                pages.append(
                    ParsedPage(
                        paper_id=paper_id,
                        page_number=i,
                        text=text,
                        paragraphs=_extract_paragraphs(text),
                        metadata={
                            "source": str(path),
                            "filename": path.name,
                            "total_pages": total,
                        },
                    )
                )

    return pages
