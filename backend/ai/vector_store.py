import chromadb
from chromadb.config import Settings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from voyageai import Client as VoyageClient
from typing import List, Dict, Any
import os

from config import RAGConfig


class VoyageEmbeddings:
    """Wrapper für Voyage AI Embeddings kompatibel mit LangChain"""

    def __init__(self, api_key: str, model: str = "voyage-finance-2"):
        self.client = VoyageClient(api_key=api_key)
        self.model = model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents"""
        result = self.client.embed(texts, model=self.model, input_type="document")
        return result.embeddings

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query"""
        result = self.client.embed([text], model=self.model, input_type="query")
        return result.embeddings[0]


class VectorStore:
    """Vector Store Manager für Financial Documents"""

    def __init__(self):
        self.config = RAGConfig()
        self.embeddings = VoyageEmbeddings(
            api_key=self.config.VOYAGE_API_KEY, model=self.config.EMBEDDING_MODEL
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.CHUNK_SIZE,
            chunk_overlap=self.config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ".", " ", ""],
        )
        self._initialize_chroma()

    def _initialize_chroma(self):
        """Initialize ChromaDB with persistence"""
        os.makedirs(self.config.CHROMA_PERSIST_DIR, exist_ok=True)

        self.vectorstore = Chroma(
            collection_name=self.config.COLLECTION_NAME,
            embedding_function=self.embeddings,
            persist_directory=self.config.CHROMA_PERSIST_DIR,
        )

    def add_documents(self, documents: List[Any]) -> int:
        """
        Add documents to vector store

        Args:
            documents: List of LangChain Documents OR dicts with 'text' and 'metadata' keys

        Returns:
            Number of chunks added
        """
        # Convert to LangChain Document format if needed
        docs = []
        for doc in documents:
            if isinstance(doc, Document):
                # Already a Document, use as-is
                docs.append(doc)
            elif isinstance(doc, dict):
                # Dict format, convert to Document
                docs.append(
                    Document(page_content=doc["text"], metadata=doc.get("metadata", {}))
                )
            else:
                raise TypeError(f"Expected Document or dict, got {type(doc)}")

        # Split documents into chunks
        chunks = self.text_splitter.split_documents(docs)

        # Add to vector store
        self.vectorstore.add_documents(chunks)

        return len(chunks)

    def similarity_search(self, query: str, k: int = None) -> List[Document]:
        """
        Search for similar documents

        Args:
            query: Search query
            k: Number of results (default from config)

        Returns:
            List of relevant documents
        """
        if k is None:
            k = self.config.TOP_K_RESULTS

        return self.vectorstore.similarity_search(query, k=k)

    def similarity_search_with_score(self, query: str, k: int = None) -> List[tuple]:
        """
        Search with relevance scores

        Returns:
            List of (document, score) tuples
        """
        if k is None:
            k = self.config.TOP_K_RESULTS

        return self.vectorstore.similarity_search_with_score(query, k=k)

    def delete_collection(self):
        """Delete entire collection (use with caution!)"""
        self.vectorstore.delete_collection()

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection"""
        collection = self.vectorstore._collection
        return {
            "name": collection.name,
            "count": collection.count(),
        }


# Helper function for easy initialization
def get_vector_store() -> VectorStore:
    """Factory function to get vector store instance"""
    return VectorStore()
