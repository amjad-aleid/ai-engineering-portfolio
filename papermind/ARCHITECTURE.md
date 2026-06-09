# PaperMind — System Architecture

## Overview

PaperMind is composed of two independent pipelines that share a vector database:

- **Ingestion pipeline** — runs once per document, offline
- **Query pipeline** — runs on every user question, in real time

---

## Component Map

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Streamlit)                  │
│                        localhost:8501                        │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP
┌───────────────────────────▼─────────────────────────────────┐
│                      Backend API (FastAPI)                    │
│                        localhost:8000                        │
│                                                              │
│   POST /papers/upload    GET /papers    POST /query          │
└──────┬──────────────────────────────────────┬───────────────┘
       │                                      │
       ▼                                      ▼
┌─────────────────┐                ┌──────────────────────┐
│Ingestion Pipeline│                │   Query Pipeline      │
│                 │                │                      │
│ 1. Parse PDF    │                │ 1. Embed question    │
│ 2. Chunk text   │                │ 2. Search ChromaDB   │
│ 3. Embed chunks │                │ 3. Rerank results    │
│ 4. Store vectors│                │ 4. Build prompt      │
└────────┬────────┘                │ 5. Call Groq API     │
         │                         └──────────┬───────────┘
         ▼                                    │
┌─────────────────┐                           │
│    ChromaDB     │◄──────────────────────────┘
│  (local, disk)  │
└─────────────────┘
```

---

## Ingestion Pipeline

Triggered when a PDF is uploaded. Runs entirely locally — no external API calls.

```
PDF file
   │
   ▼
[parser.py] ── pdfplumber extracts text page by page
               Output: list of ParsedPage(paper_id, page_number, text)
   │
   ▼
[chunker.py] ── splits each page into 512-word chunks with 50-word overlap
                Overlap ensures context is not lost at chunk boundaries
                Output: list of Chunk(chunk_id, text, page_number, metadata)
   │
   ▼
[embedder.py] ── sentence-transformers converts each chunk to a 384-dim vector
                 Vectors + text + metadata upserted into ChromaDB
                 Output: persisted to ./chroma_db on disk
```

**Why chunking with overlap?**
A 512-word window keeps chunks small enough for precise retrieval. The 50-word overlap means a sentence that falls at a page boundary is still fully represented in at least one chunk.

---

## Query Pipeline

Triggered on every user question. Combines local retrieval with a hosted LLM call.

```
User question (text)
   │
   ▼
[search.py] ── sentence-transformers embeds the question into a 384-dim vector
               ChromaDB finds the top 10 most similar chunk vectors (cosine similarity)
               Output: list of SearchResult(text, score, page_number, filename)
   │
   ▼
[reranker.py] ── cross-encoder scores each (question, chunk) pair together
                 More accurate than cosine similarity: reads both texts jointly
                 Top 3 chunks selected
                 Output: reranked list of SearchResult
   │
   ▼
[rag.py] ── builds a structured prompt:
            - System: role + instructions
            - Context: the 3 retrieved chunks with source labels
            - User: the original question
            Sends to Groq API → Llama 3.3 70B generates answer
            Output: answer text + source citations
   │
   ▼
API response: { answer, citations: [{ filename, page_number, excerpt, score }] }
```

**Why two-stage retrieval (search + rerank)?**
Cosine similarity is fast but compares vectors independently. A cross-encoder reads the question and chunk together, catching subtle relevance that vector search misses. Running it on 10 candidates (not the full index) keeps it fast.

---

## Evaluation Pipeline

Standalone CLI tool for measuring RAG quality on an ingested paper.

```
paper_id
   │
   ▼
Sample 8 chunks from paper → Groq generates 5 test Q&A pairs
   │
   ▼
For each question:
   ├── Search + rerank → top 3 chunks
   ├── Retrieval recall: keyword overlap between expected answer and retrieved chunks
   └── Faithfulness: Groq judges whether the answer is supported by the context (0.0–1.0)
   │
   ▼
Summary report: recall % and average faithfulness score
```

---

## Data Flow Summary

| Stage | Input | Output | Where |
|---|---|---|---|
| Parse | PDF file | Pages with text + metadata | `ingestion/parser.py` |
| Chunk | Pages | Fixed-size text windows | `ingestion/chunker.py` |
| Embed | Text chunks | 384-dim vectors | `ingestion/embedder.py` |
| Store | Vectors + metadata | Persisted index | ChromaDB (`./chroma_db`) |
| Search | Question vector | Top-10 candidate chunks | `retrieval/search.py` |
| Rerank | Question + chunks | Top-3 by relevance | `retrieval/reranker.py` |
| Generate | Chunks + question | Grounded answer | `generation/rag.py` |
| Evaluate | Paper ID | Recall + faithfulness scores | `eval/evaluate.py` |

---

## Directory Structure

```
papermind/
├── ingestion/
│   ├── parser.py       # PDF → pages
│   ├── chunker.py      # pages → chunks
│   └── embedder.py     # chunks → vectors → ChromaDB
├── retrieval/
│   ├── search.py       # question → top-K chunks
│   └── reranker.py     # rerank by cross-encoder
├── generation/
│   └── rag.py          # prompt builder + Groq call
├── api/
│   └── main.py         # FastAPI endpoints
├── frontend/
│   └── app.py          # Streamlit UI
├── eval/
│   └── evaluate.py     # retrieval + faithfulness eval
├── ingest.py           # CLI ingestion script
├── requirements.txt
└── .env.example
```
