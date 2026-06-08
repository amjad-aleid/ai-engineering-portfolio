"""
Evaluation harness for PaperMind.

Generates test questions from an ingested paper, then measures:
  - Retrieval recall: did the right chunks come back?
  - Answer faithfulness: is the generated answer grounded in the source?

Usage:
    python eval/evaluate.py <paper_id>
"""
import json
import os
import sys

from dotenv import load_dotenv
from groq import Groq

from retrieval.reranker import Reranker
from retrieval.search import Searcher

load_dotenv()

_N_QUESTIONS = 5


def generate_questions(paper_id: str, client: Groq, searcher: Searcher) -> list[dict]:
    """Pull sample chunks from a paper and ask the LLM to generate Q&A pairs."""
    results = searcher.search("summary methods results findings", paper_ids=[paper_id], top_k=8)
    context = "\n\n".join(r.text for r in results)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=1024,
        messages=[
            {
                "role": "system",
                "content": "You generate evaluation Q&A pairs from academic text. Respond with a JSON array only.",
            },
            {
                "role": "user",
                "content": (
                    f"Generate {_N_QUESTIONS} question-answer pairs from the text below. "
                    "Each pair should have a specific, answerable question and a short answer (1-2 sentences) "
                    "that can only be answered using this text.\n\n"
                    f"Text:\n{context}\n\n"
                    'Respond as a JSON array: [{"question": "...", "answer": "..."}, ...]'
                ),
            },
        ],
    )

    return json.loads(response.choices[0].message.content)


def check_faithfulness(question: str, answer: str, context: str, client: Groq) -> float:
    """Ask the LLM to rate how faithful the answer is to the retrieved context (0.0–1.0)."""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=50,
        messages=[
            {
                "role": "system",
                "content": "You are an evaluator. Respond with a single number between 0.0 and 1.0 only.",
            },
            {
                "role": "user",
                "content": (
                    f"Question: {question}\n"
                    f"Answer: {answer}\n"
                    f"Context: {context}\n\n"
                    "Rate how well the answer is supported by the context. "
                    "1.0 = fully supported, 0.0 = not supported at all."
                ),
            },
        ],
    )
    try:
        return float(response.choices[0].message.content.strip())
    except ValueError:
        return 0.0


def evaluate(paper_id: str) -> None:
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    searcher = Searcher()
    reranker = Reranker()

    print(f"\nGenerating {_N_QUESTIONS} test questions for paper: {paper_id}")
    qa_pairs = generate_questions(paper_id, client, searcher)
    print(f"Generated {len(qa_pairs)} questions\n")

    retrieval_hits = 0
    faithfulness_scores = []

    for i, pair in enumerate(qa_pairs, 1):
        question = pair["question"]
        expected_answer = pair["answer"]

        # Retrieve then rerank
        raw_results = searcher.search(question, paper_ids=[paper_id], top_k=10)
        reranked = reranker.rerank(question, raw_results, top_k=3)

        # Retrieval recall: did any top-3 chunk contain keywords from the expected answer?
        answer_keywords = set(expected_answer.lower().split())
        hit = any(
            len(answer_keywords & set(r.text.lower().split())) >= 3
            for r in reranked
        )
        if hit:
            retrieval_hits += 1

        # Answer faithfulness
        context = "\n\n".join(r.text for r in reranked)
        faithfulness = check_faithfulness(question, expected_answer, context, client)
        faithfulness_scores.append(faithfulness)

        print(f"Q{i}: {question}")
        print(f"     Retrieval hit: {'yes' if hit else 'no'} | Faithfulness: {faithfulness:.2f}\n")

    recall = retrieval_hits / len(qa_pairs)
    avg_faithfulness = sum(faithfulness_scores) / len(faithfulness_scores)

    print("=" * 50)
    print(f"Retrieval recall:      {recall:.0%} ({retrieval_hits}/{len(qa_pairs)} questions)")
    print(f"Avg faithfulness:      {avg_faithfulness:.2f} / 1.00")
    print("=" * 50)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python eval/evaluate.py <paper_id>")
        sys.exit(1)
    evaluate(sys.argv[1])
