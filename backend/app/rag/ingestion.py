from typing import List
import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader, UnstructuredMarkdownLoader
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.config import settings
import chromadb

# Initialize Embeddings (Safe to do globally as it's just an API client config)
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=settings.OPENAI_API_KEY
)

def get_vector_store():
    """
    Lazy load vector store to prevent import-time connection errors.
    """
    chroma_client = chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)
    return Chroma(
        client=chroma_client,
        collection_name="rag_collection",
        embedding_function=embeddings,
    )

async def ingest_document(file_path: str, doc_id: int):
    """
    Load, Split, Embed, and Index a document.
    """
    # 1. Load Document
    if file_path.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    elif file_path.endswith(".docx"):
        loader = Docx2txtLoader(file_path)
    elif file_path.endswith(".md"):
        loader = UnstructuredMarkdownLoader(file_path)
    else:
        # Default to TextLoader
        loader = TextLoader(file_path)

    docs = loader.load()

    # 2. Add Metadata
    for doc in docs:
        doc.metadata["source_doc_id"] = doc_id
        doc.metadata["source"] = os.path.basename(file_path)

    # 3. Split Text
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_documents(docs)

    # 4. Filter empty chunks
    chunks = [c for c in chunks if c.page_content.strip()]
    
    if not chunks:
        return # Nothing to index

    # 5. Index to ChromaDB
    vector_store = get_vector_store()
    vector_store.add_documents(documents=chunks)

def delete_document_from_vector_store(doc_id: int):
    """
    Delete all chunks associated with a document ID.
    Since we didn't use custom IDs during ingestion (letting Chroma generate them),
    we must delete by metadata filter.
    """
    try:
        # Delete by metadata "source_doc_id"
        vector_store = get_vector_store()
        vector_store.delete(where={"source_doc_id": doc_id})
    except Exception as e:
        from app.core.logging import logger
        logger.error("chroma_delete_failed", doc_id=doc_id, error=str(e))
