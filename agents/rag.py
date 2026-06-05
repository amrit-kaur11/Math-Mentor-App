import os
from glob import glob
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma


DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "db")
KB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "kb")

_RETRIEVER = None


def get_rag_retriever():
    """
    Initializes the local RAG retriever.

    The retriever is cached so the app does not rebuild embeddings on every
    question. If the KB folder is empty or dependencies fail, the app continues
    without RAG instead of breaking the UI.
    """
    global _RETRIEVER

    if _RETRIEVER is not None:
        return _RETRIEVER

    try:
        os.makedirs(DB_DIR, exist_ok=True)
        os.makedirs(KB_DIR, exist_ok=True)

        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        vectorstore = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)

        kb_files = glob(os.path.join(KB_DIR, "*.md"))

        if vectorstore._collection.count() == 0 and kb_files:
            docs = []
            for file_path in kb_files:
                loader = TextLoader(file_path, encoding="utf-8")
                docs.extend(loader.load())

            text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            splits = text_splitter.split_documents(docs)

            if splits:
                vectorstore.add_documents(splits)

        _RETRIEVER = vectorstore.as_retriever(search_kwargs={"k": 3})
        return _RETRIEVER

    except Exception as exc:
        print(f"RAG initialization skipped: {exc}")
        _RETRIEVER = None
        return None


def retrieve_context(query: str) -> str:
    """
    Retrieve top relevant KB snippets. Returns an empty string safely if RAG is
    unavailable.
    """
    retriever = get_rag_retriever()
    if not retriever:
        return ""

    try:
        docs = retriever.invoke(query)
    except Exception as exc:
        print(f"RAG retrieval skipped: {exc}")
        return ""

    if not docs:
        return ""

    return "\n\n---\n\n".join(
        [
            f"Source: {doc.metadata.get('source', 'Unknown')}\n{doc.page_content}"
            for doc in docs
        ]
    )
