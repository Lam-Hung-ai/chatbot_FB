from utils.read_env import GoogleKey
from langchain_qdrant import QdrantVectorStore, RetrievalMode
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

client = QdrantClient(path="/home/lamhung/PycharmProjects/chatbot_FB/vector_storage")
google_key = GoogleKey(pattern="GOOGLE_API_KEY", num_keys=2)
print(google_key.get_key())
client.create_collection(
    collection_name="demo_collection",
    vectors_config=VectorParams(size=768, distance=Distance.COSINE),
)
embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=google_key.get_key()
)
vector_store = QdrantVectorStore(
    client=client,
    collection_name="demo_collection",
    embedding=embeddings,
)
# Lưu hàng loạt văn bản
vector_store.add_texts([
    "Tài liệu về AI",
    "Hướng dẫn sử dụng LangChain"
], metadatas=[{"source":"doc1"}, {"source":"doc2"}])

# Tìm kiếm 5 văn bản tương tự với truy vấn
results = vector_store.similarity_search("Hướng dẫn AI cơ bản", k=5)
print(results)