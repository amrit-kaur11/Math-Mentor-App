import numpy as np
from sentence_transformers import SentenceTransformer

# Load model once (global)
model = SentenceTransformer("all-MiniLM-L6-v2")


def embed_text(text: str):
    """
    Returns embedding vector as numpy float32 array shaped (1, dim)
    """
    embedding = model.encode([text])
    return np.array(embedding).astype("float32")
