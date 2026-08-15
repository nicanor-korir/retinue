"""Core RAG service for indexing and retrieving context."""

import logging
import re
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from app.core.config import settings
from app.services.rag_embedding_service import get_embedding_service
from app.services.rag_vector_store import get_vector_store
from app.services.rag_cache_service import get_cache_service
from app.services.rag_query_enhancement import get_query_enhancement_service
from app.services.rag_feedback_loop import get_feedback_loop_service
from app.services.rag_context_optimization import get_context_optimizer

logger = logging.getLogger(__name__)


class RAGService:
    """Main RAG service for indexing and retrieving context from knowledge base."""

    def __init__(self):
        """Initialize the RAG service."""
        self.embedding_service = get_embedding_service()
        self.vector_store = get_vector_store(persist_dir=settings.CHROMADB_PATH)
        self.cache_service = get_cache_service()
        self.query_enhancement_service = get_query_enhancement_service()
        self.feedback_loop_service = get_feedback_loop_service()
        self.context_optimizer = get_context_optimizer()
        self.chunk_size = settings.RAG_CHUNK_SIZE
        self.chunk_overlap = settings.RAG_CHUNK_OVERLAP
        self.top_k = settings.RAG_TOP_K
        self.similarity_threshold = settings.RAG_SIMILARITY_THRESHOLD

    def _chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks.

        Args:
            text: Text to chunk

        Returns:
            List of text chunks
        """
        if not text or len(text) < self.chunk_size:
            return [text]

        chunks = []
        words = text.split()
        current_chunk = []
        current_length = 0

        for word in words:
            word_length = len(word) + 1  # +1 for space

            if current_length + word_length > self.chunk_size and current_chunk:
                # Save current chunk
                chunk = " ".join(current_chunk)
                chunks.append(chunk)

                # Keep last N words for overlap
                overlap_words = max(
                    1, int(self.chunk_overlap / len(current_chunk[0]))
                )
                current_chunk = current_chunk[-overlap_words:] + [word]
                current_length = sum(len(w) for w in current_chunk) + len(
                    current_chunk
                )
            else:
                current_chunk.append(word)
                current_length += word_length

        # Add last chunk
        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    async def index_task(
        self,
        task_id: str,
        title: str,
        description: str,
        output: Optional[str] = None,
        completion_notes: Optional[str] = None,
        agent_id: Optional[str] = None,
        project_id: Optional[str] = None,
        status: str = "completed",
    ) -> None:
        """
        Index a task to the RAG knowledge base.

        Args:
            task_id: Unique task ID
            title: Task title
            description: Task description
            output: Task output/result
            completion_notes: Notes on completion
            agent_id: ID of agent who completed the task
            project_id: ID of parent project
            status: Task status (default: "completed")
        """
        try:
            # Build indexable text
            text_parts = [title, description]
            if output:
                text_parts.append(f"Output: {output}")
            if completion_notes:
                text_parts.append(f"Notes: {completion_notes}")

            full_text = "\n".join(text_parts)

            # Chunk the text
            chunks = self._chunk_text(full_text)

            # Generate embeddings
            embeddings = await self.embedding_service.embed_batch(chunks)

            # Prepare metadata and IDs
            ids = [f"{task_id}_chunk_{i}" for i in range(len(chunks))]
            metadatas = [
                {
                    "entity_type": "task",
                    "entity_id": task_id,
                    "chunk_index": i,
                    "project_id": project_id,
                    "agent_id": agent_id,
                    "status": status,
                    "title": title,
                    "created_at": datetime.utcnow().isoformat(),
                }
                for i in range(len(chunks))
            ]

            # Store in vector database
            await self.vector_store.add_documents(
                collection_name="tasks",
                documents=chunks,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids,
            )

            logger.info(f"Indexed task {task_id} with {len(chunks)} chunks")

        except Exception as e:
            logger.error(f"Error indexing task {task_id}: {e}")
            raise

    async def index_decision(
        self,
        decision_id: str,
        question: str,
        decision: str,
        rationale: str,
        decision_type: str = "general",
        agent_id: Optional[str] = None,
        project_id: Optional[str] = None,
        approved: bool = False,
    ) -> None:
        """
        Index a decision to the RAG knowledge base.

        Args:
            decision_id: Unique decision ID
            question: The decision question
            decision: The decision made
            rationale: Reasoning behind the decision
            decision_type: Type of decision (technical, strategic, etc.)
            agent_id: ID of agent who made the decision
            project_id: ID of related project
            approved: Whether the decision was approved
        """
        try:
            # Build indexable text
            text_parts = [
                f"Decision Question: {question}",
                f"Decision: {decision}",
                f"Rationale: {rationale}",
            ]

            full_text = "\n".join(text_parts)

            # Generate embedding (decisions are usually short, no chunking needed)
            embedding = await self.embedding_service.embed_text(full_text)

            # Prepare metadata and ID
            decision_id_full = f"{decision_id}_main"
            metadata = {
                "entity_type": "decision",
                "entity_id": decision_id,
                "chunk_index": 0,
                "project_id": project_id,
                "agent_id": agent_id,
                "decision_type": decision_type,
                "approved": str(approved),
                "created_at": datetime.utcnow().isoformat(),
            }

            # Store in vector database
            await self.vector_store.add_documents(
                collection_name="decisions",
                documents=[full_text],
                embeddings=[embedding],
                metadatas=[metadata],
                ids=[decision_id_full],
            )

            logger.info(f"Indexed decision {decision_id}")

        except Exception as e:
            logger.error(f"Error indexing decision {decision_id}: {e}")
            raise

    async def index_message(
        self,
        message_id: str,
        content: str,
        from_agent_id: str,
        to_agent_id: Optional[str] = None,
        message_type: str = "info",
        project_id: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> None:
        """
        Index a message to the RAG knowledge base.

        Args:
            message_id: Unique message ID
            content: Message content
            from_agent_id: ID of agent who sent the message
            to_agent_id: ID of agent who received the message
            message_type: Type of message (info, request, etc.)
            project_id: ID of related project
            task_id: ID of related task
        """
        try:
            # Generate embedding
            embedding = await self.embedding_service.embed_text(content)

            # Prepare metadata and ID
            message_id_full = f"{message_id}_main"
            metadata = {
                "entity_type": "message",
                "entity_id": message_id,
                "chunk_index": 0,
                "project_id": project_id,
                "task_id": task_id,
                "from_agent_id": from_agent_id,
                "to_agent_id": to_agent_id,
                "message_type": message_type,
                "created_at": datetime.utcnow().isoformat(),
            }

            # Store in vector database
            await self.vector_store.add_documents(
                collection_name="messages",
                documents=[content],
                embeddings=[embedding],
                metadatas=[metadata],
                ids=[message_id_full],
            )

            logger.info(f"Indexed message {message_id}")

        except Exception as e:
            logger.error(f"Error indexing message {message_id}: {e}")
            raise

    async def retrieve_context(
        self,
        query: str,
        agent_id: Optional[str] = None,
        project_id: Optional[str] = None,
        collections: Optional[List[str]] = None,
        top_k: Optional[int] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Retrieve relevant context from the RAG knowledge base.

        Args:
            query: Query string
            agent_id: Filter by agent ID (optional)
            project_id: Filter by project ID (optional)
            collections: Collections to search (default: all)
            top_k: Number of results per collection (default: settings.RAG_TOP_K)
            use_cache: Whether to use cache (default: True)

        Returns:
            Dictionary with retrieved context organized by collection
        """
        try:
            if top_k is None:
                top_k = self.top_k

            # Default collections for Phase 1
            if collections is None:
                collections = ["tasks", "decisions", "messages"]

            # Try to get from cache first
            if use_cache:
                cached_results = await self.cache_service.get(
                    query=query,
                    agent_id=agent_id,
                    project_id=project_id,
                    collections=collections,
                )
                if cached_results:
                    logger.debug(f"Cache HIT for query: {query[:50]}...")
                    return cached_results

            # Generate query embedding
            query_embedding = await self.embedding_service.embed_text(query)

            results = {}

            for collection_name in collections:
                # Build metadata filter if needed
                # ChromaDB where filters: single condition = {"key": value}
                # Multiple conditions = {"$and": [{"key1": value1}, {"key2": value2}]}
                where_filter = None
                if agent_id or project_id:
                    conditions = []
                    if agent_id:
                        conditions.append({"agent_id": agent_id})
                    if project_id:
                        conditions.append({"project_id": project_id})

                    if len(conditions) == 1:
                        where_filter = conditions[0]
                    elif len(conditions) > 1:
                        where_filter = {"$and": conditions}

                # Search in collection
                collection_results = await self.vector_store.search(
                    collection_name=collection_name,
                    query_embedding=query_embedding,
                    top_k=top_k,
                    where=where_filter,
                )

                # Filter by similarity threshold
                filtered_results = {
                    "ids": [],
                    "documents": [],
                    "metadatas": [],
                    "scores": [],
                }

                for i, distance in enumerate(collection_results["distances"]):
                    # Convert distance to similarity score (1 - distance for cosine)
                    similarity = 1 - distance

                    if similarity >= self.similarity_threshold:
                        filtered_results["ids"].append(collection_results["ids"][i])
                        filtered_results["documents"].append(
                            collection_results["documents"][i]
                        )
                        filtered_results["metadatas"].append(
                            collection_results["metadatas"][i]
                        )
                        filtered_results["scores"].append(similarity)

                results[collection_name] = filtered_results

            # Cache the results for future queries
            if use_cache and results:
                await self.cache_service.set(
                    query=query,
                    results={
                        "collections": collections,
                        "agent_id": agent_id,
                        "project_id": project_id,
                        "data": results,
                    },
                    agent_id=agent_id,
                    project_id=project_id,
                    collections=collections,
                )

            logger.info(
                f"Retrieved context for query (length: {len(query)}) from {len(collections)} collections"
            )

            return results

        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            raise

    async def retrieve_context_enhanced(
        self,
        query: str,
        agent_id: Optional[str] = None,
        project_id: Optional[str] = None,
        collections: Optional[List[str]] = None,
        top_k: Optional[int] = None,
        use_cache: bool = True,
        use_enhancement: bool = True,
    ) -> Dict[str, Any]:
        """
        Retrieve context with query enhancement (Phase 3).

        Enhances the query before retrieval using:
        - Query normalization
        - Classification (type, domain)
        - Intent extraction
        - Query expansion with synonyms

        Args:
            query: Original user query
            agent_id: Filter by agent ID (optional)
            project_id: Filter by project ID (optional)
            collections: Collections to search (optional)
            top_k: Number of results per collection (optional)
            use_cache: Whether to use cache (default: True)
            use_enhancement: Whether to use enhancement (default: True)

        Returns:
            Dictionary with retrieved context and enhancement metadata
        """
        try:
            # Enhance query if enabled
            enhancement_metadata = None
            search_query = query

            if use_enhancement:
                enhanced = await self.query_enhancement_service.enhance_query(
                    query=query,
                    agent_id=agent_id,
                    project_id=project_id,
                )
                enhancement_metadata = {
                    "query_type": enhanced.query_type.value,
                    "query_domain": enhanced.query_domain.value,
                    "intent": enhanced.intent,
                    "confidence": enhanced.confidence,
                    "keywords": enhanced.keywords,
                    "expanded_terms": enhanced.expanded_terms,
                }

                # Build optimized search query
                search_query = await self.query_enhancement_service.build_enhanced_search_query(
                    enhanced
                )

                logger.debug(
                    f"Enhanced query: {search_query[:100]}... "
                    f"(type={enhanced.query_type.value}, domain={enhanced.query_domain.value})"
                )

            # Retrieve using enhanced query
            results = await self.retrieve_context(
                query=search_query,
                agent_id=agent_id,
                project_id=project_id,
                collections=collections,
                top_k=top_k,
                use_cache=use_cache,
            )

            # Add enhancement metadata to results
            if enhancement_metadata:
                results["_enhancement"] = enhancement_metadata

            return results

        except Exception as e:
            logger.error(f"Error in enhanced retrieval: {e}")
            # Fallback to regular retrieval
            return await self.retrieve_context(
                query=query,
                agent_id=agent_id,
                project_id=project_id,
                collections=collections,
                top_k=top_k,
                use_cache=use_cache,
            )

    async def format_context_for_prompt(
        self, retrieval_results: Dict[str, Any], max_tokens: int = 4000
    ) -> str:
        """
        Format retrieval results into a context string for the LLM prompt.

        Args:
            retrieval_results: Results from retrieve_context()
            max_tokens: Maximum tokens for context (approximate)

        Returns:
            Formatted context string
        """
        context_parts = []
        token_count = 0
        max_chars = max_tokens * 4  # Rough estimate: 1 token ≈ 4 characters

        for collection_name, results in retrieval_results.items():
            if not results["documents"]:
                continue

            context_parts.append(f"\n## Relevant {collection_name.upper().replace('_', ' ')}:\n")

            for i, (doc, metadata, score) in enumerate(
                zip(
                    results["documents"],
                    results["metadatas"],
                    results["scores"]
                ),
                1,
            ):
                if token_count >= max_chars:
                    break

                # Format individual result
                result_text = f"[{i}] (Relevance: {score:.2%})\n{doc[:500]}"
                if len(doc) > 500:
                    result_text += "...\n"

                context_parts.append(result_text + "\n")
                token_count += len(result_text)

        full_context = "".join(context_parts)

        if not full_context.strip():
            return "No relevant context found in knowledge base."

        return f"""## RELEVANT CONTEXT FROM PAST WORK:

{full_context}

---

Use the context above to inform your response. Apply patterns and approaches from past work when relevant."""

    async def format_context_optimized(
        self,
        retrieval_results: Dict[str, Any],
        max_tokens: int = 4000,
    ) -> str:
        """
        Format and optimize context for LLM (Phase 3).

        Applies:
        - Smart summarization of long content
        - Token budget optimization
        - Relevance prioritization
        - Automatic deduplication

        Args:
            retrieval_results: Results from retrieve_context()
            max_tokens: Maximum tokens for context

        Returns:
            Optimized context string
        """
        try:
            # Optimize context
            optimized = await self.context_optimizer.optimize_context(
                retrieval_results,
                max_tokens=max_tokens,
            )

            # Format optimized results
            context_parts = []
            token_count = 0
            max_chars = max_tokens * 4

            optimization_info = optimized.get("_optimization", {})
            compression = optimization_info.get("compression_ratio", 0)

            # Add compression info if significant
            if compression > 0.1:
                context_parts.append(
                    f"\n[Context optimized: {compression:.0%} compression ratio]\n"
                )

            for collection_name, results in optimized.items():
                if collection_name.startswith("_") or not results or not results.get("documents"):
                    continue

                context_parts.append(
                    f"\n## {collection_name.upper().replace('_', ' ')}:\n"
                )

                for i, (doc, metadata, score) in enumerate(
                    zip(
                        results.get("documents", []),
                        results.get("metadatas", []),
                        results.get("scores", [])
                    ),
                    1
                ):
                    if token_count >= max_chars:
                        break

                    # Add summarization indicator if applicable
                    summarized = metadata.get("_summarized", False)
                    summary_tag = "[Summarized] " if summarized else ""

                    result_text = f"[{i}] {summary_tag}(Relevance: {score:.2%})\n{doc[:500]}"
                    if len(doc) > 500:
                        result_text += "\n...\n"

                    context_parts.append(result_text + "\n")
                    token_count += len(result_text)

            full_context = "".join(context_parts)

            if not full_context.strip():
                return "No relevant context found in knowledge base."

            return f"""## RELEVANT CONTEXT FROM PAST WORK:
{full_context}
---

Use the context above to inform your response. Apply patterns and approaches from past work when relevant."""

        except Exception as e:
            logger.error(f"Error formatting optimized context: {e}")
            # Fallback to regular formatting
            return await self.format_context_for_prompt(retrieval_results, max_tokens)

    async def get_stats(self) -> Dict[str, int]:
        """
        Get statistics about the RAG knowledge base.

        Returns:
            Dictionary with collection sizes
        """
        try:
            stats = {}
            for collection_name in self.vector_store.collections.keys():
                stats[collection_name] = await self.vector_store.get_collection_size(
                    collection_name
                )
            return stats
        except Exception as e:
            logger.error(f"Error getting RAG stats: {e}")
            return {}


# Global instance
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get or create the global RAG service instance."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
