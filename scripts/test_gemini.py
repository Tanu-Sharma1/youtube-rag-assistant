import os
import time

t = time.time()
from dotenv import load_dotenv
load_dotenv()
print("env loaded:", round(time.time() - t, 1), "sec")

from langchain_google_genai import ChatGoogleGenerativeAI
print("import done:", round(time.time() - t, 1), "sec")

model = os.getenv("GEMINI_MODEL")
print("model:", model)
print("key found:", bool(os.getenv("GOOGLE_API_KEY")))

# timeout=30 aur max_retries=1: atkne ki jagah jaldi error dega
llm = ChatGoogleGenerativeAI(model=model, temperature=0, timeout=30, max_retries=1)
print("calling Gemini...")
print("answer:", llm.invoke("Say hello in one word").content)
print("total:", round(time.time() - t, 1), "sec")
