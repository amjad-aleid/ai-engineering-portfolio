# PaperMind

## What is this?

Researchers and students often need to extract specific information from large volumes of academic papers — a task that is slow and tedious when done manually. PaperMind solves this by letting you upload any collection of research PDFs and ask plain-English questions about them. Instead of reading every paper, you get direct answers with citations pointing back to the exact page and document the information came from.

Under the hood, this is a **Retrieval-Augmented Generation (RAG)** system. RAG bridges the gap between a language model's general knowledge and a specific document collection: it retrieves the most relevant passages from your papers first, then feeds only those passages to the AI to generate a grounded, cited answer. This prevents the model from hallucinating and keeps every response traceable to a real source.

## Architecture

```
PDF → parse → chunk → embed → ChromaDB
                                  ↓
User question → embed → search → rerank → Groq (Llama 3.3 70B) → answer + citations
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

### Cross-encoder reranker (`ms-marco-MiniLM-L6-v2`)
A second-pass ranking model that scores each (question, chunk) pair together, catching relevance that cosine similarity alone misses. Runs locally after the initial vector search, improving answer quality without extra API calls.

### Evaluation harness (`eval/evaluate.py`)
Uses the LLM to generate test Q&A pairs from an ingested paper, then measures two things: retrieval recall (did the right chunks come back?) and answer faithfulness (is the generated answer grounded in the source?). Produces a scored report per paper.

## Setup

**Requirements:** Python 3.10+

```bash
# 1. Clone and enter the project
git clone https://github.com/amjad-aleid/ai-engineering-portfolio.git
cd ai-engineering-portfolio/papermind

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate       # Mac/Linux
.venv\Scripts\activate          # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your Groq API key (free at console.groq.com)
cp .env.example .env
# Open .env and set: GROQ_API_KEY=your_key_here
```

> **Note:** PDFs must have a text layer (not scanned images). Papers from [arxiv.org](https://arxiv.org) always work.

## Make commands

All common tasks are available as `make` commands defined in `Makefile` at the root of this project. Run them from the `papermind/` directory.

| Command | Description |
|---|---|
| `make install` | Create `.venv` and install all dependencies |
| `make dev-all` | Kill any running processes, then start API + frontend in development mode (recommended) |
| `make prod-all` | Kill any running processes, then start API + frontend in production mode |
| `make dev` | Kill any running processes, then start the API only in development mode |
| `make prod` | Kill any running processes, then start the API only in production mode |
| `make frontend` | Kill any running processes, then start the Streamlit frontend only |
| `make kill` | Stop all running API and frontend processes |
| `make ingest ARGS="paper.pdf"` | Ingest one or more PDFs into the vector index |
| `make eval ARGS="paper_id"` | Run the evaluation harness on an ingested paper |

All run commands automatically kill any existing processes before starting fresh — no need to manually stop anything first. `Ctrl+C` on `make dev-all` or `make prod-all` stops both the API and frontend cleanly.

To run in production mode, prefix with `APP_ENV=production`:
```bash
make ingest ARGS="paper.pdf" APP_ENV=production
make eval ARGS="my_paper" APP_ENV=production
```

## Running the app

Start everything with one command:
```bash
make dev-all
```
This starts the backend API at http://localhost:8000 and the frontend UI at http://localhost:8501. Visit http://localhost:8000/docs for an interactive API explorer.

## Ingesting papers via CLI

Ingest PDFs directly from the terminal without using the UI:

```bash
make ingest ARGS="path/to/paper.pdf"
make ingest ARGS="papers/*.pdf"    # ingest multiple at once
```

The paper ID (used to filter queries) is the filename without the `.pdf` extension.

## Running the evaluation harness

Once a paper is ingested, run the evaluation harness to measure retrieval and answer quality:

```bash
make eval ARGS="<paper_id>"
```

This will:
1. Auto-generate 5 test questions from the paper
2. Retrieve and rerank chunks for each question
3. Score **retrieval recall** — did the right content come back?
4. Score **answer faithfulness** — is the answer grounded in the source?
5. Print a summary report

Example output:
```
Q1: What dataset was used in the experiments?
     Retrieval hit: yes | Faithfulness: 0.95

Q2: What baseline methods were compared?
     Retrieval hit: yes | Faithfulness: 0.88

==================================================
Retrieval recall:      100% (5/5 questions)
Avg faithfulness:      0.91 / 1.00
==================================================
```
