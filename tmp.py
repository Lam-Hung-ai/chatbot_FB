from langchain_google_genai import GoogleGenerativeAIEmbeddings
from utils.read_env import GoogleKey
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_google_genai import ChatGoogleGenerativeAI

google_key = GoogleKey(num_keys=2)
embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=google_key.get_key()
        )
loader = DirectoryLoader(path="./raw_data", glob="*.txt", loader_cls=TextLoader)
documents = loader.load()
text_spliter = RecursiveCharacterTextSplitter(chunk_size=750, chunk_overlap=100)
chunks = text_spliter.split_documents(documents)


