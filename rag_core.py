# rag_core.py
import os
import chromadb
from sentence_transformers import SentenceTransformer
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

CHROMA_DIR = "chroma_store"

model = SentenceTransformer("all-MiniLM-L6-v2")

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Load vector DB collection
chroma = chromadb.PersistentClient(path=CHROMA_DIR)
collection = chroma.get_collection("docs")

def retrieve(query, top_k=3):
    query_emb = model.encode([query]).tolist()[0]

    results = collection.query(
        query_embeddings=[query_emb],
        n_results=top_k
    )

    docs = results["documents"][0]
    return docs

def generate_answer(query, context_chunks):
    context_text = "\n\n".join(context_chunks)

    prompt = f"""
You are a precise assistant. 
Use ONLY the context below to answer.

Context:
{context_text}

Question: {query}

Answer clearly:
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content

def rag_answer(query):
    chunks = retrieve(query)
    answer = generate_answer(query, chunks)
    return answer
