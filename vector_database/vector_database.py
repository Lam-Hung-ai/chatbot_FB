from typing import List, Optional, Sequence
from uuid import uuid4
from pathlib import Path
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

from utils.read_env import GoogleKey


class VectorDatabase:
    """
    Vector DB wrapper cho Qdrant + LangChain.

    Parameters
    ----------
    collection_name : str
        Tên collection trong Qdrant.
    storage : str
        ':memory:'  → in‑memory, hoặc đường dẫn thư mục để lưu on‑disk.
    retrieval_mode : RetrievalMode
        DENSE | SPARSE | HYBRID.
    vector_size : int
        Kích thước embedding dense (phải khớp model).
    google_key_pattern / num_keys
        Cách lấy GOOGLE_API_KEY nếu dùng Google Generative AI Embeddings.
    """

    def __init__(
        self,
        collection_name: str,
        storage: str = ":memory:",
        retrieval_mode: RetrievalMode = RetrievalMode.DENSE,
        vector_size: int = 1024,
        google_key_pattern: str = "GOOGLE_API_KEY",
        num_keys: int = 1,
    ) -> None:
        # 1. Embeddings -------------------------------------------------------
        self._google_key = GoogleKey(pattern=google_key_pattern, num_keys=num_keys)
        # self._dense_embeddings = GoogleGenerativeAIEmbeddings(
        #     model="models/text-embedding-004",
        #     google_api_key=self._google_key.get_key(),
        # )

        cache_path = str(Path(__file__).resolve().parents[1] / "cache")
        self._dense_embeddings = HuggingFaceEmbeddings(
            cache_folder=cache_path,
            model_name="AITeamVN/Vietnamese_Embedding",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': False}
        )

        # Sparse embedding (chỉ cần nếu SPARSE/HYBRID)
        self._sparse_embeddings = (
            FastEmbedSparse(model_name="Qdrant/bm25")
            if retrieval_mode in {RetrievalMode.SPARSE, RetrievalMode.HYBRID}
            else None
        )

        # 2. Qdrant client (local mode) ---------------------------------------
        self._client = QdrantClient(path=storage)

        # 3. Store các tham số -------------------------------------------------
        self.collection_name = collection_name
        self.retrieval_mode = retrieval_mode
        self.vector_size = vector_size

        # 4. VectorStore (khởi tạo sau) ---------------------------------------
        self._vector_store: Optional[QdrantVectorStore] = None

    # --------------------------------------------------------------------- #
    #  PUBLIC API                                                           #
    # --------------------------------------------------------------------- #
    def create_or_attach_collection(self, recreate: bool = False) -> None:
        """
        Tạo collection mới (hoặc gắn vào collection cũ).
        Nếu `recreate=True` và collection đã tồn tại → xóa rồi tạo lại.
        """
        if recreate and self._client.collection_exists(self.collection_name):
            self._client.delete_collection(self.collection_name)

        # Xác định cấu hình vectors & sparse vectors tuỳ retrieval_mode
        vectors_cfg = {"dense": VectorParams(size=self.vector_size, distance=Distance.COSINE)}
        sparse_cfg = None
        if self.retrieval_mode in {RetrievalMode.SPARSE, RetrievalMode.HYBRID}:
            sparse_cfg = {
                "sparse": SparseVectorParams(
                    index=models.SparseIndexParams(on_disk=False)
                )
            }

        # Tạo collection nếu chưa có
        if not self._client.collection_exists(self.collection_name):
            self._client.create_collection(
                collection_name=self.collection_name,
                vectors_config=vectors_cfg if sparse_cfg is None else vectors_cfg,
                sparse_vectors_config=sparse_cfg,
            )

        # Khởi tạo QdrantVectorStore
        self._vector_store = QdrantVectorStore(
            client=self._client,
            collection_name=self.collection_name,
            embedding=self._dense_embeddings
            if self.retrieval_mode != RetrievalMode.SPARSE
            else None,
            sparse_embedding=self._sparse_embeddings
            if self.retrieval_mode != RetrievalMode.DENSE
            else None,
            retrieval_mode=self.retrieval_mode,
            vector_name="dense" if self.retrieval_mode != RetrievalMode.SPARSE else None,
            sparse_vector_name="sparse"
            if self.retrieval_mode != RetrievalMode.DENSE
            else None,
        )

    def add_documents(self, docs: Sequence[Document], ids: Optional[Sequence[str]] = None) -> None:
        """Thêm tài liệu vào collection."""
        self._require_store()
        if ids is None:
            ids = [str(uuid4()) for _ in range(len(docs))]
        self._vector_store.add_documents(documents=list(docs), ids=list(ids))

    def similarity_search(
        self, query: str, k: int = 4, **kwargs
    ) -> List[Document]:
        """Tra cứu tương tự (top‑k docs)."""
        self._require_store()
        return self._vector_store.similarity_search(query=query, k=k, **kwargs)

    def similarity_search_with_score(
        self, query: str, k: int = 4, **kwargs
    ) -> List[tuple[Document, float]]:
        """Tra cứu tương tự + điểm số."""
        self._require_store()
        return self._vector_store.similarity_search_with_score(query=query, k=k, **kwargs)

    def delete(self, ids: Sequence[str]) -> None:
        """Xoá vector/tài liệu theo id."""
        self._require_store()
        self._vector_store.delete(ids=list(ids))

    def as_retriever(self, **search_kwargs):
        """Trả về retriever để dùng trong RAG chains."""
        self._require_store()
        return self._vector_store.as_retriever(**search_kwargs)

    # --------------------------------------------------------------------- #
    #  PRIVATE UTILS                                                        #
    # --------------------------------------------------------------------- #
    def _require_store(self) -> None:
        if self._vector_store is None:
            raise RuntimeError("Collection chưa được khởi tạo – gọi create_or_attach_collection() trước.")

