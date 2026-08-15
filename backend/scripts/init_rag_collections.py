"""Initialize RAG collections for context intelligence.

This script creates the new RAG collections needed for the intelligent chat system:
- conversations: For indexing conversation messages
- business_knowledge: For Deviant AI business domain knowledge
- user_activities: For user activity patterns

Run this script after deploying the context intelligence feature.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.core.config import settings
from app.services.rag_vector_store import get_vector_store


async def init_rag_collections():
    """Initialize RAG collections for context intelligence."""
    print("Initializing RAG collections for context intelligence...")

    # Get vector store
    vector_store = get_vector_store(persist_dir=settings.CHROMADB_PATH)

    # Collection configurations
    collections = [
        {
            "name": "conversations",
            "description": "Indexed conversation messages for context retrieval",
            "metadata": {
                "embedding_model": settings.RAG_EMBEDDING_MODEL,
                "dimensions": 384,  # For all-MiniLM-L6-v2
                "purpose": "context_intelligence"
            }
        },
        {
            "name": "business_knowledge",
            "description": "Deviant AI business domain knowledge",
            "metadata": {
                "embedding_model": settings.RAG_EMBEDDING_MODEL,
                "dimensions": 384,
                "purpose": "business_context"
            }
        },
        {
            "name": "user_activities",
            "description": "Aggregated user activity patterns",
            "metadata": {
                "embedding_model": settings.RAG_EMBEDDING_MODEL,
                "dimensions": 384,
                "purpose": "user_profiling"
            }
        }
    ]

    # Create each collection
    for collection_config in collections:
        try:
            print(f"\nCreating collection: {collection_config['name']}")
            print(f"Description: {collection_config['description']}")

            # Check if collection exists
            existing_collections = await vector_store.list_collections()
            if collection_config["name"] in existing_collections:
                print(f"✓ Collection '{collection_config['name']}' already exists")
                continue

            # Create collection
            await vector_store.create_collection(
                name=collection_config["name"],
                metadata=collection_config["metadata"]
            )

            print(f"✓ Successfully created collection: {collection_config['name']}")

        except Exception as e:
            print(f"✗ Error creating collection {collection_config['name']}: {e}")
            continue

    print("\n" + "="*60)
    print("RAG Collections Initialization Complete")
    print("="*60)

    # List all collections
    print("\nAvailable collections:")
    try:
        all_collections = await vector_store.list_collections()
        for col in all_collections:
            print(f"  - {col}")
    except Exception as e:
        print(f"Error listing collections: {e}")

    print("\nNext steps:")
    print("1. Run the migration: alembic upgrade head")
    print("2. Seed business knowledge documents")
    print("3. Backfill existing conversations (optional)")


def main():
    """Main entry point."""
    print("="*60)
    print("RAG Collections Initialization Script")
    print("="*60)
    print(f"Vector Store: {settings.RAG_VECTOR_STORE}")
    print(f"Embedding Model: {settings.RAG_EMBEDDING_MODEL}")
    print(f"ChromaDB Path: {settings.CHROMADB_PATH}")
    print("="*60)

    # Run async initialization
    asyncio.run(init_rag_collections())


if __name__ == "__main__":
    main()
