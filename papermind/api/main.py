import logging
import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
from pydantic import BaseModel

from config import get_settings
from generation.rag import ask
from ingestion.chunker import chunk_pages
from ingestion.embedder import Embedder
from ingestion.parser import parse_pdf
from retrieval.reranker import Reranker
from retrieval.search import Searcher

settings = get_settings()

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="PaperMind API", debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

embedder = Embedder(persist_dir=settings.chroma_db_path)
searcher = Searcher(persist_dir=settings.chroma_db_path)
reranker = Reranker()
groq_client = Groq(api_key=settings.groq_api_key)

logger.info(f"PaperMind API starting in {settings.app_env} mode")


class QueryRequest(BaseModel):
    question: str
    paper_ids: list[str] | None = None
    top_k: int = settings.retrieval_top_k


class Citation(BaseModel):
    filename: str
    page_number: int
    paragraph_number: int
    excerpt: str
    score: float


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]


@app.get("/health")
def health():
    return {"status": "ok", "env": settings.app_env}


@app.post("/papers/upload")
async def upload_paper(file: UploadFile = File(...)):
    if not (file.filename or "").endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        pages = parse_pdf(tmp_path)
        if not pages:
            raise HTTPException(400, "Could not extract text from this PDF")

        chunks = chunk_pages(pages)
        embedder.embed_chunks(chunks)

        paper_id = Path(file.filename).stem
        logger.info(f"Ingested paper: {paper_id} ({len(pages)} pages, {len(chunks)} chunks)")

        return {"paper_id": paper_id, "pages": len(pages), "chunks": len(chunks)}
    finally:
        os.unlink(tmp_path)


@app.get("/papers")
def list_papers():
    return {"papers": embedder.get_paper_ids()}


@app.delete("/papers/{paper_id}")
def delete_paper(paper_id: str):
    embedder.delete_paper(paper_id)
    logger.info(f"Deleted paper: {paper_id}")
    return {"deleted": paper_id}


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    logger.debug(f"Query: {request.question}")

    results = searcher.search(request.question, request.paper_ids, request.top_k)
    if not results:
        raise HTTPException(404, "No relevant content found")

    results = reranker.rerank(request.question, results, top_k=settings.rerank_top_k)
    answer, used = ask(request.question, results, groq_client, model=settings.groq_model)

    citations = [
        Citation(
            filename=r.filename,
            page_number=r.page_number,
            paragraph_number=r.paragraph_number,
            excerpt=r.text[:200] + "..." if len(r.text) > 200 else r.text,
            score=r.score,
        )
        for r in used
    ]

    return QueryResponse(answer=answer, citations=citations)
