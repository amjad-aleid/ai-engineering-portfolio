from sentence_transformers import CrossEncoder

from retrieval.search import SearchResult

_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L6-v2"


class Reranker:
    def __init__(self):
        self.model = CrossEncoder(_MODEL_NAME)

    def rerank(self, query: str, results: list[SearchResult], top_k: int = 3) -> list[SearchResult]:
        """Score each (query, chunk) pair and return top_k by relevance."""
        if not results:
            return results

        pairs = [(query, r.text) for r in results]
        scores = self.model.predict(pairs).tolist()

        reranked = sorted(zip(results, scores), key=lambda x: x[1], reverse=True)
        return [r for r, _ in reranked[:top_k]]
