# rag/vector_store.py

import faiss
import numpy as np


def build_faiss_index(embeddings):
    """
    Build FAISS index from embeddings.
    """
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    return index
