__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import os
import traceback
import asyncio
from pathlib import Path
from typing import List, Any

# --- Langchain Core ---
from langchain_core.tools import tool
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.output_parsers import StrOutputParser

# --- Langchain Community Components ---
from langchain_community.document_loaders import (
    PyMuPDFLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
    CSVLoader,
)
from langchain_huggingface import HuggingFaceEmbeddings  # Updated import for embeddings
from langchain_chroma import Chroma  # Updated import for Chroma vector store

# --- Langchain Text Splitters ---
from langchain.text_splitter import RecursiveCharacterTextSplitter

# --- Project Imports ---
try:
    from app import WORKSPACE_DIR, color_text
except ImportError:
    WORKSPACE_DIR = Path("./raiden_workspace_srv")
    WORKSPACE_DIR.mkdir(exist_ok=True)
    def color_text(text, color="WHITE"): print(f"[{color}] {text}"); return text

# --- Configuration ---
VECTORSTORE_DIR = WORKSPACE_DIR / "vectorstore"
VECTORSTORE_DIR.mkdir(exist_ok=True)
EMBEDDING_MODEL = "models/text-embedding-004"  # Updated to Google's latest embedding model
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

# --- Global Variables ---
embedding_function = None
vector_store = None

def initialize_rag_components():
    """Initialize RAG components with Google's text-embedding-004"""
    global embedding_function, vector_store
    try:
        if embedding_function is None:
            try:
                from langchain_google_genai import GoogleGenerativeAIEmbeddings
                print(color_text(f"Initializing Google embeddings model: {EMBEDDING_MODEL}", "CYAN"))
                embedding_function = GoogleGenerativeAIEmbeddings(
                    model=EMBEDDING_MODEL,
                    google_api_key=os.environ.get("GOOGLE_API_KEY")
                )
                print(color_text("Google embeddings initialized.", "GREEN"))
            except Exception as e:
                print(color_text(f"Warning: Failed to initialize Google embeddings: {e}", "YELLOW"))
                embedding_function = None

        if vector_store is None:
            print(color_text(f"Initializing vector store at: {VECTORSTORE_DIR}", "CYAN"))
            vector_store = Chroma(
                persist_directory=str(VECTORSTORE_DIR.resolve()),
                embedding_function=embedding_function,
                collection_name="raiden_collection"  # Ensure a collection name is provided
            )
            print(color_text("Vector store initialized.", "GREEN"))
    except Exception as e:
        print(color_text(f"Error initializing RAG components: {e}", "RED"))
        traceback.print_exc()

def _is_cuda_available():
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False

initialize_rag_components()

def _get_document_loader(file_path: Path):
    extension = file_path.suffix.lower()
    str_file_path = str(file_path.resolve())
    if extension == ".pdf":
        return PyMuPDFLoader(str_file_path)
    elif extension == ".docx":
        return Docx2txtLoader(str_file_path)
    elif extension == ".txt":
        return TextLoader(str_file_path, encoding="utf-8")
    elif extension == ".md":
        return UnstructuredMarkdownLoader(str_file_path, mode="elements")
    elif extension == ".csv":
        return CSVLoader(str_file_path, encoding="utf-8")
    else:
        print(color_text(f"Unsupported file type: {extension}", "YELLOW"))
        return None

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    length_function=len,
    add_start_index=True,
)

@tool
async def index_document(file_path: str) -> str:
    """
    Indexes a document into the vector store for semantic search.
    
    Args:
        file_path (str): The path to the document to be indexed.
    
    Returns:
        str: A message indicating the success or failure of the indexing process.
    """
    global vector_store, embedding_function
    print(color_text(f"--- RAG: Indexing Document: {file_path} ---", "CYAN"))

    if vector_store is None or embedding_function is None:
        return "Error: RAG components not initialized. Cannot index document."

    try:
        from app import _resolve_safe_path
        safe_doc_path = _resolve_safe_path(file_path)

        if not safe_doc_path.is_file():
            return f"Error: Document not found at workspace path: '{file_path}'"

        loader = _get_document_loader(safe_doc_path)
        if loader is None:
            return f"Error: Unsupported file type for document: '{file_path}'"

        docs = await asyncio.to_thread(loader.load)
        if not docs:
            return f"Error: Could not load any content from document: '{file_path}'"

        for doc in docs:
            doc.metadata["source_rel_path"] = file_path

        chunks = await asyncio.to_thread(text_splitter.split_documents, docs)
        if not chunks:
            return f"Error: Failed to split document '{file_path}' into chunks."

        ids = [f"{file_path}_{i}" for i in range(len(chunks))]
        await asyncio.to_thread(vector_store.add_documents, documents=chunks, ids=ids)

        return f"Successfully indexed document '{file_path}'. It can now be queried."
    except Exception as e:
        print(color_text(f"Error indexing document '{file_path}': {e}", "RED"))
        traceback.print_exc()
        return f"Error indexing document '{file_path}': {e}"

RAG_PROMPT_TEMPLATE = """You are Raiden, an AI assistant. Answer the following question based *only* on the provided context. If the context doesn't contain the answer, state clearly that you cannot answer based on the provided documents. Be concise and helpful.

Context:
{context}

Question:
{question}

Answer:"""

rag_prompt = ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)

@tool
async def query_documents(query: str) -> str:
    """
    Queries the vector store to retrieve relevant documents based on the input query.
    
    Args:
        query (str): The search query.
    
    Returns:
        str: The results of the query, including relevant document excerpts.
    """
    global vector_store
    print(color_text(f"--- RAG: Querying Documents: '{query}' ---", "CYAN"))

    if vector_store is None:
        return "Error: Vector store not initialized. Cannot query documents."

    try:
        retriever = vector_store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={'k': 5, 'score_threshold': 0.5}
        )

        def format_docs(docs: List[Document]) -> str:
            return "\n\n".join(f"Source: {doc.metadata.get('source_rel_path', 'Unknown')}\nContent: {doc.page_content}" for doc in docs)

        # Fetch documents first
        docs = await asyncio.to_thread(retriever.get_relevant_documents, query)
        if not docs:
            return "No relevant documents found for your query."

        formatted_context = format_docs(docs)
        
        response = f"Here are the relevant document excerpts for your query:\n\n{formatted_context}"
        return response
        
    except Exception as e:
        print(color_text(f"Error querying documents for '{query}': {e}", "RED"))
        traceback.print_exc()
        return f"Error processing query '{query}': {e}"
