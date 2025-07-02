from utils.read_env import GoogleKey
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from vector_database.vector_database import VectorDatabase

if __name__ == "__main__":
    google_key = GoogleKey(num_keys=2)
    loader = DirectoryLoader(path="./raw_data", glob="*.txt", loader_cls=TextLoader)
    documents = loader.load()
    text_spliter = RecursiveCharacterTextSplitter(separators=["\n\n", "\n"], chunk_size=600, chunk_overlap=75)
    chunks = text_spliter.split_documents(documents)
    vector_db = VectorDatabase(storage="./vector_storage", num_keys=2, collection_name="chatbot_FB")
    vector_db.create_or_attach_collection(recreate=True)
    vector_db.add_documents(chunks)
    print("Luu du lieu thanh cong")

