# PaperMind

A RAG-powered research paper assistant. Upload academic PDFs, ask questions, get answers grounded in what the papers actually say — with citations.

## Architecture

```
PDF → parse → chunk → embed → ChromaDB
                                  ↓
         User question → embed → search → Groq (Llama 3.3 70B) → answer + citations
```

## Tooling decisions

### Groq (LLM inference)
Groq runs open-source models (Llama 3.3 70B) on custom hardware called an LPU, purpose-built for fast inference. Chosen over other providers because it offers a generous free tier with no credit card required, no data training on prompts, and the fastest response times of any hosted option — making the chat UI feel snappy.

### Llama 3.3 70B
Meta's open-weight model, one of the strongest available for Q&A and summarization tasks. Comparable to paid models for this use case, and freely accessible via Groq.

### sentence-transformers (`all-MiniLM-L6-v2`)
Converts text into vectors (embeddings) for semantic search. Runs entirely locally — no API call, no cost, no latency overhead per chunk. `all-MiniLM-L6-v2` is a well-established model that balances speed and quality for retrieval tasks.

### ChromaDB
A vector database that stores embeddings and retrieves the most semantically similar chunks for a given query. Chosen because it runs locally with zero configuration — no server to spin up, no cloud account. Data stays on your machine.

### pdfplumber
Extracts text from PDFs page by page, including positional metadata. More reliable than alternatives like PyPDF2 for complex layouts, and exposes page numbers which we use for citations.

### FastAPI
Python's standard framework for building APIs. Chosen for its automatic request/response validation via Pydantic, built-in interactive docs at `/docs`, and async support — all with minimal boilerplate.

### Streamlit
Turns Python scripts into interactive web UIs with almost no frontend code. The right tool for AI demos and portfolio projects where the goal is showing the capability, not building a production frontend.

## Running locally

```bash
# 1. Set up environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # add your GROQ_API_KEY

# 2. Ingest papers
python ingest.py path/to/paper.pdf

# 3. Start the backend
uvicorn api.main:app --reload

# 4. Start the frontend (separate terminal)
streamlit run frontend/app.py
```

Open http://localhost:8501 in your browser.
