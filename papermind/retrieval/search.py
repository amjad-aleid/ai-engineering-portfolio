from dataclasses import dataclass

import chromadb
from sentence_transformers import SentenceTransformer

_MODEL_NAME = "all-MiniLM-L6-v2"


@dataclass
class SearchResult:
    chunk_id: str
    text: str
    score: float
    paper_id: str
    page_number: int
    paragraph_number: int
    filename: str


class Searcher:
    def __init__(self, persist_dir: str = "./chroma_db"):
        self.model = SentenceTransformer(_MODEL_NAME)
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name="papers",
            metadata={"hnsw:space": "cosine"},
        )

    def search(
        self,
        query: str,
        paper_ids: list[str] | None = None,
        top_k: int = 5,
    ) -> list[SearchResult]:
        query_embedding = self.model.encode(query).tolist()
        where = {"paper_id": {"$in": paper_ids}} if paper_ids else None

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        search_results = []
        for i, chunk_id in enumerate(results["ids"][0]):
            meta = results["metadatas"][0][i]
            distance = results["distances"][0][i]
            search_results.append(
                SearchResult(
                    chunk_id=chunk_id,
                    text=results["documents"][0][i],
                    score=round(1 - distance, 4),
                    paper_id=meta.get("paper_id", ""),
                    page_number=meta.get("page_number", 0),
                    paragraph_number=meta.get("paragraph_number", 0),
                    filename=meta.get("filename", ""),
                )
            )

        return search_results
