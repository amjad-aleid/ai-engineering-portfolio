import os
import tempfile
from pathlib import Path

from groq import Groq
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from generation.rag import ask
from ingestion.chunker import chunk_pages
from ingestion.embedder import Embedder
from ingestion.parser import parse_pdf
from retrieval.reranker import Reranker
from retrieval.search import Searcher

load_dotenv()

app = FastAPI(title="PaperMind API")

embedder = Embedder()
searcher = Searcher()
reranker = Reranker()
claude = Groq(api_key=os.environ["GROQ_API_KEY"])


class QueryRequest(BaseModel):
    question: str
    paper_ids: list[str] | None = None
    top_k: int = 5


class Citation(BaseModel):
    filename: str
    page_number: int
    paragraph_number: int
    excerpt: str
    score: float


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]


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

        return {
            "paper_id": Path(file.filename).stem,
            "pages": len(pages),
            "chunks": len(chunks),
        }
    finally:
        os.unlink(tmp_path)


@app.get("/papers")
def list_papers():
    return {"papers": embedder.get_paper_ids()}


@app.delete("/papers/{paper_id}")
def delete_paper(paper_id: str):
    embedder.delete_paper(paper_id)
    return {"deleted": paper_id}


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    results = searcher.search(request.question, request.paper_ids, request.top_k)
    if not results:
        raise HTTPException(404, "No relevant content found")

    results = reranker.rerank(request.question, results, top_k=3)
    answer, used = ask(request.question, results, claude)

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
