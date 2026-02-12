# rag/chunker.py

def chunk_documents(docs, chunk_size=300):
    """
    Simple chunker (docs are already small).
    """
    chunks = []

    for doc in docs:
        chunks.append({
            "id": doc["id"],
            "text": doc["content"]
        })

    return chunks
