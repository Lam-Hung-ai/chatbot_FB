import os
from utils.read_env import GoogleKey
from vector_database.vector_database import VectorDatabase
from langchain_google_genai import ChatGoogleGenerativeAI

vector_db = VectorDatabase(storage="./vector_storage", num_keys=2, collection_name="chat_FB")
vector_db.create_or_attach_collection()
google_key = GoogleKey(pattern="GOOGLE_API_KEY", num_keys=2)
query = "Khi nào trẻ có thể bắt đầu lẫy, bò, và đi?"
strings = vector_db.similarity_search(query)
print(len(strings))
i = 1
for string in strings:
    print(f"String {i}:", end=" ")
    print(string.page_content)
    i +=1


# llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=key)
# message = llm.invoke("Bao giờ trẻ em biết đi")

