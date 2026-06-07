import chromadb
from sentence_transformers import SentenceTransformer

from ingestion.chunker import Chunk

_MODEL_NAME = "all-MiniLM-L6-v2"


class Embedder:
    def __init__(self, persist_dir: str = "./chroma_db"):
        self.model = SentenceTransformer(_MODEL_NAME)
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name="papers",
            metadata={"hnsw:space": "cosine"},
        )

    def embed_chunks(self, chunks: list[Chunk]) -> None:
        if not chunks:
            return
        texts = [c.text for c in chunks]
        embeddings = self.model.encode(texts, show_progress_bar=True).tolist()
        self.collection.upsert(
            ids=[c.chunk_id for c in chunks],
            documents=texts,
            embeddings=embeddings,
            metadatas=[c.metadata for c in chunks],
        )

    def get_paper_ids(self) -> list[str]:
        results = self.collection.get(include=["metadatas"])
        metadatas = results.get("metadatas") or []
        ids = {m.get("paper_id", "") for m in metadatas}
        return sorted(ids - {""})

    def delete_paper(self, paper_id: str) -> None:
        results = self.collection.get(where={"paper_id": paper_id})
        if results["ids"]:
            self.collection.delete(ids=results["ids"])
