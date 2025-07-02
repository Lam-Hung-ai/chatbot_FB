from typing import List, Optional, Sequence, Any
import torch
from uuid import uuid4
from langchain_core.documents import Document
from langchain_qdrant import (
    FastEmbedSparse,
    QdrantVectorStore,
    RetrievalMode,
)
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import (
    Distance,
    SparseVectorParams,
    VectorParams,
)

class VectorDatabase:
    """
    Vector DB wrapper cho Qdrant + LangChain.

    Hỗ trợ sync và async cho indexing và search.
    """

    def __init__(
        self,
        collection_name: str,
        storage: str = "./vector_storage",
        cache_path: str = "./cache",
        retrieval_mode: RetrievalMode = RetrievalMode.DENSE,
        vector_size: int = 1024,
    ) -> None:
        # 1. Embeddings
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self._dense_embeddings = HuggingFaceEmbeddings(
            cache_folder=cache_path,
            model_name="AITeamVN/Vietnamese_Embedding",
            model_kwargs={'device': device},
            encode_kwargs={'normalize_embeddings': False}
        )

        self._sparse_embeddings = (
            FastEmbedSparse(model_name="Qdrant/bm25")
            if retrieval_mode in {RetrievalMode.SPARSE, RetrievalMode.HYBRID}
            else None
        )

        # 2. Qdrant client
        self._client = QdrantClient(path=storage)

        # 3. Store params
        self.collection_name = collection_name
        self.retrieval_mode = retrieval_mode
        self.vector_size = vector_size

        # 4. VectorStore (init later)
        self._vector_store: Optional[QdrantVectorStore] = None

    def create_or_attach_collection(self, recreate: bool = False) -> None:
        if recreate and self._client.collection_exists(self.collection_name):
            self._client.delete_collection(self.collection_name)

        vectors_cfg = {"dense": VectorParams(size=self.vector_size, distance=Distance.COSINE)}
        sparse_cfg = None
        if self.retrieval_mode in {RetrievalMode.SPARSE, RetrievalMode.HYBRID}:
            sparse_cfg = {"sparse": SparseVectorParams(index=models.SparseIndexParams(on_disk=False))}

        if not self._client.collection_exists(self.collection_name):
            self._client.create_collection(
                collection_name=self.collection_name,
                vectors_config=vectors_cfg if sparse_cfg is None else vectors_cfg,
                sparse_vectors_config=sparse_cfg,
            )

        self._vector_store = QdrantVectorStore(
            client=self._client,
            collection_name=self.collection_name,
            embedding=self._dense_embeddings if self.retrieval_mode != RetrievalMode.SPARSE else None,
            sparse_embedding=self._sparse_embeddings if self.retrieval_mode != RetrievalMode.DENSE else None,
            retrieval_mode=self.retrieval_mode,
            vector_name="dense" if self.retrieval_mode != RetrievalMode.SPARSE else None,
            sparse_vector_name="sparse" if self.retrieval_mode != RetrievalMode.DENSE else None,
        )

    def _require_store(self) -> None:
        if self._vector_store is None:
            raise RuntimeError("Collection chưa được khởi tạo – gọi create_or_attach_collection() trước.")

    # -- Sync methods ----------------------------------------------------------------
    def add_documents(self, docs: Sequence[Document], ids: Optional[Sequence[str]] = None) -> None:
        self._require_store()
        if ids is None:
            ids = [str(uuid4()) for _ in range(len(docs))]
        self._vector_store.add_documents(documents=list(docs), ids=list(ids))

    def similarity_search(self, query: str, k: int = 4, **kwargs: Any) -> List[Document]:
        self._require_store()
        return self._vector_store.similarity_search(query=query, k=k, **kwargs)

    def similarity_search_with_score(self, query: str, k: int = 4, **kwargs: Any) -> List[tuple[Document, float]]:
        self._require_store()
        return self._vector_store.similarity_search_with_score(query=query, k=k, **kwargs)

    def delete(self, ids: Sequence[str]) -> None:
        self._require_store()
        self._vector_store.delete(ids=list(ids))

    def as_retriever(self, **search_kwargs: Any):
        self._require_store()
        return self._vector_store.as_retriever(**search_kwargs)

    # -- Async methods ----------------------------------------------------------------
    async def aadd_documents(self, docs: Sequence[Document], ids: Optional[Sequence[str]] = None) -> List[str]:
        """Async add documents"""
        self._require_store()
        if ids is None:
            ids = [str(uuid4()) for _ in range(len(docs))]
        return await self._vector_store.aadd_documents(documents=list(docs), ids=list(ids))

    async def asimilarity_search(self, query: str, k: int = 4, **kwargs: Any) -> List[Document]:
        """Async similarity search"""
        self._require_store()
        return await self._vector_store.asimilarity_search(query=query, k=k, **kwargs)

    async def asimilarity_search_with_score(self, query: str, k: int = 4, **kwargs: Any) -> List[tuple[Document, float]]:
        """Async search with score"""
        self._require_store()
        return await self._vector_store.asimilarity_search_with_score(query=query, k=k, **kwargs)

    async def adelete(self, ids: Sequence[str]) -> Any:
        """Async delete documents"""
        self._require_store()
        return await self._vector_store.adelete(ids=list(ids))

    def a_as_retriever(self, **search_kwargs: Any):
        """Async-compatible retriever (same as sync as_retriever)"""
        self._require_store()
        return self._vector_store.as_retriever(**search_kwargs)
