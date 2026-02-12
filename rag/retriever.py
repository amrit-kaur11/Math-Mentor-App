from rag.embedder import embed_text
from rag.index_builder import load_index, load_documents


def retrieve(query: str, top_k: int = 3):

    index = load_index()
    documents = load_documents()

    query_vector = embed_text(query)

    distances, indices = index.search(query_vector, top_k)

    retrieved = []

    for idx in indices[0]:
        retrieved.append(documents[idx])

    return retrieved
