# rag/index_builder.py

import os
import faiss
import numpy as np
import pickle

from rag.embedder import embed_text

KB_FOLDER = "rag/knowledge_base"
INDEX_PATH = "rag/faiss_index.index"
DOCS_PATH = "rag/documents.pkl"


def load_markdown_files():
    documents = []

    for filename in os.listdir(KB_FOLDER):
        if filename.endswith(".md"):
            with open(os.path.join(KB_FOLDER, filename), "r", encoding="utf-8") as f:
                content = f.read()
                documents.append(content)

    return documents


def build_index():
    print("Building FAISS index...")

    documents = load_markdown_files()

    embeddings = []

    for doc in documents:
        vector = embed_text(doc)
        embeddings.append(vector[0])

    embeddings = np.array(embeddings).astype("float32")

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    faiss.write_index(index, INDEX_PATH)

    with open(DOCS_PATH, "wb") as f:
        pickle.dump(documents, f)

    print("Index built successfully.")


def load_index():
    if not os.path.exists(INDEX_PATH):
        build_index()

    return faiss.read_index(INDEX_PATH)


def load_documents():
    if not os.path.exists(DOCS_PATH):
        build_index()

    with open(DOCS_PATH, "rb") as f:
        return pickle.load(f)
