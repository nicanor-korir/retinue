"""Vector store implementation for RAG - stores and retrieves embeddings."""

import logging
import os
from typing import Any, Dict, List, Optional
import chromadb

logger = logging.getLogger(__name__)


class VectorStore:
    """Vector store using ChromaDB for Phase 1 (can be extended for Qdrant/Pinecone)."""

    def __init__(self, persist_dir: str = "./data/chromadb"):
        """
        Initialize the vector store.

        Args:
            persist_dir: Directory to persist ChromaDB data
        """
        # Create directory if it doesn't exist
        os.makedirs(persist_dir, exist_ok=True)

        # Initialize ChromaDB with new persistent client (updated for ChromaDB 0.4+)
        try:
            # New way: Use PersistentClient for ChromaDB 0.4+
            self.client = chromadb.PersistentClient(path=persist_dir)
            logger.info("Using ChromaDB PersistentClient (0.4+)")
        except AttributeError:
            # Fallback for older ChromaDB versions
            logger.warning("ChromaDB PersistentClient not available, trying deprecated Client")
            try:
                from chromadb.config import Settings as ChromaSettings
                settings = ChromaSettings(
                    chroma_db_impl="duckdb+parquet",
                    persist_directory=persist_dir,
                    anonymized_telemetry=False,
                    is_persistent=True,
                )
                self.client = chromadb.Client(settings)
            except Exception as e:
                logger.error(f"Failed to initialize ChromaDB: {e}")
                raise

        self.persist_dir = persist_dir

        # Create or get collections for different entity types
        self.collections = {
            "tasks": self.client.get_or_create_collection(
                name="tasks",
                metadata={"hnsw:space": "cosine"}
            ),
            "decisions": self.client.get_or_create_collection(
                name="decisions",
                metadata={"hnsw:space": "cosine"}
            ),
            "messages": self.client.get_or_create_collection(
                name="messages",
                metadata={"hnsw:space": "cosine"}
            ),
            "escalations": self.client.get_or_create_collection(
                name="escalations",
                metadata={"hnsw:space": "cosine"}
            ),
            "projects": self.client.get_or_create_collection(
                name="projects",
                metadata={"hnsw:space": "cosine"}
            ),
            "knowledge_base": self.client.get_or_create_collection(
                name="knowledge_base",
                metadata={"hnsw:space": "cosine"}
            ),
            "business_knowledge": self.client.get_or_create_collection(
                name="business_knowledge",
                metadata={"hnsw:space": "cosine"}
            ),
        }

        logger.info(f"Initialized vector store with persist_dir: {persist_dir}")

    async def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
    ) -> None:
        """
        Add documents to the vector store.

        Args:
            collection_name: Name of the collection (e.g., "tasks", "decisions")
            documents: List of document texts
            embeddings: List of embedding vectors
            metadatas: List of metadata dictionaries
            ids: List of document IDs
        """
        try:
            if collection_name not in self.collections:
                raise ValueError(f"Unknown collection: {collection_name}")

            collection = self.collections[collection_name]

            # ChromaDB add method
            collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids,
            )

            logger.info(
                f"Added {len(documents)} documents to {collection_name} collection"
            )

        except Exception as e:
            logger.error(f"Error adding documents to {collection_name}: {e}")
            raise

    async def search(
        self,
        collection_name: str,
        query_embedding: List[float],
        top_k: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Search for similar documents in the vector store.

        Args:
            collection_name: Name of the collection to search
            query_embedding: Query embedding vector
            top_k: Number of results to return
            where: Optional metadata filter

        Returns:
            Dictionary with IDs, distances, metadatas, and documents
        """
        try:
            if collection_name not in self.collections:
                raise ValueError(f"Unknown collection: {collection_name}")

            collection = self.collections[collection_name]

            # ChromaDB query method
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where,
            )

            logger.debug(f"Retrieved {len(results['ids'][0])} results from {collection_name}")

            return {
                "ids": results["ids"][0] if results["ids"] else [],
                "distances": results["distances"][0] if results["distances"] else [],
                "metadatas": results["metadatas"][0] if results["metadatas"] else [],
                "documents": results["documents"][0] if results["documents"] else [],
            }

        except Exception as e:
            logger.error(f"Error searching {collection_name}: {e}")
            raise

    async def delete(
        self, collection_name: str, ids: List[str]
    ) -> None:
        """
        Delete documents from the vector store.

        Args:
            collection_name: Name of the collection
            ids: List of document IDs to delete
        """
        try:
            if collection_name not in self.collections:
                raise ValueError(f"Unknown collection: {collection_name}")

            collection = self.collections[collection_name]
            collection.delete(ids=ids)

            logger.info(f"Deleted {len(ids)} documents from {collection_name}")

        except Exception as e:
            logger.error(f"Error deleting documents from {collection_name}: {e}")
            raise

    async def update(
        self,
        collection_name: str,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
    ) -> None:
        """
        Update documents in the vector store.

        Args:
            collection_name: Name of the collection
            documents: List of document texts
            embeddings: List of embedding vectors
            metadatas: List of metadata dictionaries
            ids: List of document IDs
        """
        try:
            if collection_name not in self.collections:
                raise ValueError(f"Unknown collection: {collection_name}")

            collection = self.collections[collection_name]

            # ChromaDB upsert method (update or insert)
            collection.upsert(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids,
            )

            logger.info(f"Updated {len(documents)} documents in {collection_name}")

        except Exception as e:
            logger.error(f"Error updating documents in {collection_name}: {e}")
            raise

    async def get_collection_size(self, collection_name: str) -> int:
        """
        Get the number of documents in a collection.

        Args:
            collection_name: Name of the collection

        Returns:
            Number of documents in the collection
        """
        try:
            if collection_name not in self.collections:
                raise ValueError(f"Unknown collection: {collection_name}")

            collection = self.collections[collection_name]
            return collection.count()

        except Exception as e:
            logger.error(f"Error getting collection size for {collection_name}: {e}")
            raise

    async def persist(self) -> None:
        """Persist the vector store to disk."""
        try:
            self.client.persist()
            logger.info("Vector store persisted to disk")
        except Exception as e:
            logger.error(f"Error persisting vector store: {e}")
            raise


# Global instance
_vector_store: Optional[VectorStore] = None


def get_vector_store(persist_dir: str = "./data/chromadb") -> VectorStore:
    """Get or create the global vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore(persist_dir=persist_dir)
    return _vector_store


async def close_vector_store():
    """Close the vector store (cleanup)."""
    global _vector_store
    if _vector_store is not None:
        await _vector_store.persist()
        _vector_store = None
