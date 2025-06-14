import os
from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI

key = os.getenv('GG_API_KEY')
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=key)
message = llm.invoke("Deepwork là gì")
print(message.content)
