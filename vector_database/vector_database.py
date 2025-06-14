from utils.read_env import GoogleKey
from langchain_qdrant import QdrantVectorStore, RetrievalMode
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

class VectorDatabase:
    def __init__(self, path_storage: str="../vector_storage", num_keys: int=1):
        self.google_key = GoogleKey(pattern="GOOGLE_API_KEY", num_keys=num_keys)
        self.client = QdrantClient(path="../vector_storage")
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=self.google_key.get_key()
        )
        self.vector_store = None

    def create_collection(self, collection_name: str):
        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=3072, distance=Distance.COSINE)
        )
        self.vector_store = QdrantVectorStore(
            client=self.client,
            collection_name="demo_collection",
            embedding=self.embeddings,
        )

    def use_collection(self, collection_name: str):
        self.vector_store = QdrantVectorStore.from_existing_collection(
            client=self.client,
            collection_name="demo_collection",
            embedding=self.embeddings,
        )


