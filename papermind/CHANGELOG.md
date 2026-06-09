# Changelog

All notable changes to PaperMind are listed here, most recent first.

---

## [0.5.0] - 2026-06-08
### Added
- Paragraph-level citation tracking — answers now cite file, page number, and paragraph number
- Paragraph detection in the ingestion pipeline using blank-line splitting
- Chunking now operates per paragraph instead of across raw page text

---

## [0.4.0] - 2026-06-08
### Added
- System architecture document (`ARCHITECTURE.md`) covering ingestion and query pipeline flows, component map, two-stage retrieval rationale, data flow table, and directory structure

---

## [0.3.0] - 2026-06-07
### Added
- Cross-encoder reranking (`ms-marco-MiniLM-L6-v2`) — second-pass scoring of retrieved chunks for improved answer relevance
- Evaluation harness (`eval/evaluate.py`) — auto-generates test Q&A pairs from ingested papers and scores retrieval recall and answer faithfulness
- Expanded README with project purpose, full setup instructions, and eval usage example

---

## [0.2.0] - 2026-06-07
### Changed
- Replaced Anthropic/Claude (paid) with Groq/Llama 3.3 70B (free tier) as the LLM provider
- Updated API key environment variable from `ANTHROPIC_API_KEY` to `GROQ_API_KEY`

---

## [0.1.0] - 2026-06-07
### Added
- Initial project scaffold
- Ingestion pipeline: PDF parsing (`pdfplumber`), sliding-window chunking, sentence-transformer embeddings, ChromaDB vector storage
- RAG query pipeline: semantic search, prompt construction, LLM generation with cited sources
- FastAPI backend with upload, list, delete, and query endpoints
- Streamlit chat UI with file upload sidebar and citation expanders
- CLI ingestion script (`ingest.py`)
