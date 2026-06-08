from groq import Groq

from retrieval.search import SearchResult

_SYSTEM_PROMPT = """You are a research assistant with deep expertise in academic literature.
Your role is to answer questions based strictly on the provided research paper excerpts.

Guidelines:
- Only use information from the provided context
- Cite specific papers and page numbers when referencing information
- If the context does not contain enough information to answer, say so clearly
- Be precise and academic in tone"""


def _build_context(results: list[SearchResult]) -> str:
    parts = [
        f"[Source: {r.filename}, Page {r.page_number}]\n{r.text}"
        for r in results
    ]
    return "\n\n---\n\n".join(parts)


def ask(
    question: str,
    search_results: list[SearchResult],
    client: Groq,
    model: str = "llama-3.3-70b-versatile",
) -> tuple[str, list[SearchResult]]:
    context = _build_context(search_results)
    user_message = f"Context from research papers:\n\n{context}\n\nQuestion: {question}"

    response = client.chat.completions.create(
        model=model,
        max_tokens=1024,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )

    return response.choices[0].message.content, search_results
