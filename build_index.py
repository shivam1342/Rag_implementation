# build_index.py
import os
import chromadb
from sentence_transformers import SentenceTransformer

DATA_DIR = "data"
CHROMA_DIR = "chroma_store"

def load_documents():
    docs = []
    for file in os.listdir(DATA_DIR):
        path = os.path.join(DATA_DIR, file)
        if path.endswith(".txt"):
            with open(path, "r", encoding="utf-8") as f:
                docs.append(f.read())
    return docs

def chunk_text(text, size=300):
    chunks = []
    for i in range(0, len(text), size):
        chunks.append(text[i:i+size])
    return chunks

def main():
    os.makedirs(CHROMA_DIR, exist_ok=True)

    # 1. Load tiny corpus
    documents = load_documents()

    # 2. Chunk
    all_chunks = []
    for doc in documents:
        all_chunks.extend(chunk_text(doc))

    # 3. Create DB
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_or_create_collection(
        name="docs", 
        metadata={"hnsw:space": "cosine"}
    )

    # 4. Embedding model
    model = SentenceTransformer("all-MiniLM-L6-v2")

    embeddings = model.encode(all_chunks).tolist()

    # 5. Insert into DB
    ids = [f"chunk_{i}" for i in range(len(all_chunks))]

    collection.add(
        embeddings=embeddings,
        documents=all_chunks,
        ids=ids
    )

    print("Index built successfully.")

if __name__ == "__main__":
    main()
