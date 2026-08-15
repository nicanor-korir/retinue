"""
Knowledge Repository Service

Implements hybrid search (full-text + vector + exact match) for knowledge retrieval.
Provides context-aware search with user preferences, recency, and quality scoring.
Based on INTELLIGENT_KNOWLEDGE_BASE.md specifications.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.orm import selectinload

from app.db.knowledge_models import (
    KnowledgeEntry,
    KnowledgeRelationship,
    KnowledgeCategory,
    KnowledgeUsageLog,
    UserKnowledgeProfile,
    KnowledgeStatus,
    ValidationStatus,
    UsageType
)
from app.services.rag_embedding_service import get_embedding_service
from app.services.rag_cache_service import get_cache_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class KnowledgeRepositoryService:
    """
    Service for storing and retrieving knowledge with hybrid search.
    """

    def __init__(self):
        """Initialize the knowledge repository service."""
        self.embedding_service = get_embedding_service()
        self.cache_service = get_cache_service()
        self.default_top_k = 10
        self.similarity_threshold = 0.6

    # ===== HYBRID SEARCH =====

    async def hybrid_search(
        self,
        db: AsyncSession,
        query: str,
        user_id: Optional[UUID] = None,
        agent_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 10,
        include_relations: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining full-text, vector, and exact matching.

        Args:
            db: Database session
            query: Search query
            user_id: User ID for personalization (optional)
            agent_id: Agent ID for context (optional)
            filters: Additional filters (entry_type, domain, tags, etc.)
            top_k: Number of results
            include_relations: Include related entries

        Returns:
            List of search results with scores and metadata
        """
        try:
            # Check cache
            cache_key = f"knowledge_search:{hash(query)}:{user_id}:{top_k}"
            cached = self.cache_service.get(cache_key)
            if cached:
                logger.info(f"Cache hit for knowledge search: {query[:50]}")
                return cached

            # Analyze query
            query_type = self._analyze_query(query)

            # Execute multi-strategy search
            fts_results = await self._full_text_search(db, query, filters, top_k * 2)
            vector_results = await self._vector_search(db, query, filters, top_k * 2)
            exact_results = await self._exact_match_search(db, query, filters, top_k)

            # Fuse results using Reciprocal Rank Fusion (RRF)
            fused_results = self._reciprocal_rank_fusion(
                fts_results=fts_results,
                vector_results=vector_results,
                exact_results=exact_results,
                weights={
                    "fts": 0.3 if query_type == "question" else 0.4,
                    "vector": 0.5 if query_type == "question" else 0.4,
                    "exact": 0.2
                }
            )

            # Re-rank with context
            if user_id:
                user_profile = await self._get_user_profile(db, user_id)
                fused_results = await self._rerank_with_user_context(
                    db, fused_results, user_profile
                )

            # Apply quality and recency boosts
            fused_results = self._apply_ranking_boosts(fused_results)

            # Limit results
            final_results = fused_results[:top_k]

            # Expand with related entries if requested
            if include_relations:
                final_results = await self._expand_with_relations(db, final_results, top_k // 2)

            # Format results
            formatted_results = await self._format_search_results(db, final_results)

            # Cache results
            self.cache_service.set(cache_key, formatted_results, ttl=300)  # 5 min cache

            logger.info(f"Hybrid search for '{query}' returned {len(formatted_results)} results")

            return formatted_results

        except Exception as e:
            logger.error(f"Error in hybrid search: {e}", exc_info=True)
            return []

    def _analyze_query(self, query: str) -> str:
        """Analyze query type (keyword, question, phrase)."""
        query_lower = query.lower().strip()

        # Question detection
        question_words = ["how", "what", "why", "when", "where", "who", "which", "can", "should"]
        if any(query_lower.startswith(word) for word in question_words) or query.endswith("?"):
            return "question"

        # Phrase detection (quoted or multi-word)
        if '"' in query or len(query.split()) > 3:
            return "phrase"

        # Default to keyword
        return "keyword"

    # ===== FULL-TEXT SEARCH =====

    async def _full_text_search(
        self,
        db: AsyncSession,
        query: str,
        filters: Optional[Dict[str, Any]],
        limit: int
    ) -> List[Tuple[KnowledgeEntry, float]]:
        """
        PostgreSQL full-text search.

        Args:
            db: Database session
            query: Search query
            filters: Filters to apply
            limit: Max results

        Returns:
            List of (entry, score) tuples
        """
        try:
            # Build FTS query
            # Use PostgreSQL's to_tsvector and to_tsquery
            base_query = select(
                KnowledgeEntry,
                func.ts_rank(
                    func.to_tsvector('english',
                        func.coalesce(KnowledgeEntry.title, '') + ' ' +
                        func.coalesce(KnowledgeEntry.summary, '') + ' ' +
                        func.coalesce(KnowledgeEntry.content, '')
                    ),
                    func.to_tsquery('english', self._prepare_fts_query(query))
                ).label('rank')
            ).where(
                and_(
                    KnowledgeEntry.status == KnowledgeStatus.ACTIVE,
                    func.to_tsvector('english',
                        func.coalesce(KnowledgeEntry.title, '') + ' ' +
                        func.coalesce(KnowledgeEntry.summary, '') + ' ' +
                        func.coalesce(KnowledgeEntry.content, '')
                    ).op('@@')(
                        func.to_tsquery('english', self._prepare_fts_query(query))
                    )
                )
            )

            # Apply filters
            if filters:
                base_query = self._apply_filters(base_query, filters)

            # Order by rank and limit
            base_query = base_query.order_by(text('rank DESC')).limit(limit)

            result = await db.execute(base_query)
            rows = result.all()

            return [(row[0], float(row[1])) for row in rows]

        except Exception as e:
            logger.error(f"Error in full-text search: {e}")
            return []

    def _prepare_fts_query(self, query: str) -> str:
        """Prepare query for PostgreSQL full-text search."""
        # Convert query to tsquery format
        # Handle special characters and add & between words
        words = query.strip().split()
        return " & ".join(word for word in words if word)

    # ===== VECTOR SEARCH =====

    async def _vector_search(
        self,
        db: AsyncSession,
        query: str,
        filters: Optional[Dict[str, Any]],
        limit: int
    ) -> List[Tuple[KnowledgeEntry, float]]:
        """
        Vector similarity search using embeddings.

        Args:
            db: Database session
            query: Search query
            filters: Filters to apply
            limit: Max results

        Returns:
            List of (entry, similarity_score) tuples
        """
        try:
            # Generate query embedding
            query_embedding = await self.embedding_service.embed_text(query)

            if not query_embedding:
                return []

            # Use pgvector for cosine similarity
            # This requires the pgvector extension and proper indexes
            base_query = select(KnowledgeEntry).where(
                and_(
                    KnowledgeEntry.status == KnowledgeStatus.ACTIVE,
                    KnowledgeEntry.content_embedding.isnot(None)
                )
            )

            # Apply filters
            if filters:
                base_query = self._apply_filters(base_query, filters)

            # Get candidates
            result = await db.execute(base_query.limit(500))  # Get more candidates for scoring
            candidates = result.scalars().all()

            # Calculate similarities (in production, use vector index directly)
            similarities = []
            for entry in candidates:
                if entry.content_embedding:
                    similarity = self._cosine_similarity(query_embedding, entry.content_embedding)
                    if similarity >= self.similarity_threshold:
                        similarities.append((entry, similarity))

            # Sort by similarity
            similarities.sort(key=lambda x: x[1], reverse=True)

            return similarities[:limit]

        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return []

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity."""
        import numpy as np
        a = np.array(vec1)
        b = np.array(vec2)
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot_product / (norm_a * norm_b))

    # ===== EXACT MATCH SEARCH =====

    async def _exact_match_search(
        self,
        db: AsyncSession,
        query: str,
        filters: Optional[Dict[str, Any]],
        limit: int
    ) -> List[Tuple[KnowledgeEntry, float]]:
        """
        Exact phrase or tag matching.

        Args:
            db: Database session
            query: Search query
            filters: Filters to apply
            limit: Max results

        Returns:
            List of (entry, score=1.0) tuples
        """
        try:
            query_lower = query.lower().strip()

            base_query = select(KnowledgeEntry).where(
                and_(
                    KnowledgeEntry.status == KnowledgeStatus.ACTIVE,
                    or_(
                        KnowledgeEntry.title.ilike(f"%{query_lower}%"),
                        KnowledgeEntry.tags.contains([query_lower]),  # Tag exact match
                        KnowledgeEntry.keywords.contains([query_lower])  # Keyword match
                    )
                )
            )

            # Apply filters
            if filters:
                base_query = self._apply_filters(base_query, filters)

            result = await db.execute(base_query.limit(limit))
            entries = result.scalars().all()

            return [(entry, 1.0) for entry in entries]

        except Exception as e:
            logger.error(f"Error in exact match search: {e}")
            return []

    # ===== FILTERS =====

    def _apply_filters(self, query, filters: Dict[str, Any]):
        """Apply additional filters to query."""
        if not filters:
            return query

        conditions = []

        if "entry_type" in filters:
            conditions.append(KnowledgeEntry.entry_type == filters["entry_type"])

        if "domain" in filters:
            conditions.append(KnowledgeEntry.domain == filters["domain"])

        if "tags" in filters:
            # Match any of the provided tags
            for tag in filters["tags"]:
                conditions.append(KnowledgeEntry.tags.contains([tag]))

        if "validation_status" in filters:
            conditions.append(KnowledgeEntry.validation_status == filters["validation_status"])

        if "min_quality" in filters:
            conditions.append(KnowledgeEntry.quality_score >= filters["min_quality"])

        if "category_id" in filters:
            conditions.append(KnowledgeEntry.primary_category_id == filters["category_id"])

        if "created_after" in filters:
            conditions.append(KnowledgeEntry.created_at >= filters["created_after"])

        if conditions:
            query = query.where(and_(*conditions))

        return query

    # ===== RESULT FUSION =====

    def _reciprocal_rank_fusion(
        self,
        fts_results: List[Tuple[KnowledgeEntry, float]],
        vector_results: List[Tuple[KnowledgeEntry, float]],
        exact_results: List[Tuple[KnowledgeEntry, float]],
        weights: Dict[str, float] = None
    ) -> List[Tuple[KnowledgeEntry, float]]:
        """
        Fuse multiple result sets using Reciprocal Rank Fusion.

        Args:
            fts_results: Full-text search results
            vector_results: Vector search results
            exact_results: Exact match results
            weights: Weights for each strategy

        Returns:
            Fused and ranked results
        """
        if weights is None:
            weights = {"fts": 0.4, "vector": 0.4, "exact": 0.2}

        # Collect all unique entries with RRF scores
        rrf_scores = {}
        k = 60  # RRF constant

        def add_rrf_score(results: List[Tuple[KnowledgeEntry, float]], weight: float):
            for rank, (entry, score) in enumerate(results, start=1):
                entry_id = entry.entry_id
                rrf_score = weight / (k + rank)

                if entry_id in rrf_scores:
                    rrf_scores[entry_id]["score"] += rrf_score
                else:
                    rrf_scores[entry_id] = {
                        "entry": entry,
                        "score": rrf_score,
                        "original_scores": {}
                    }

                # Track original scores
                rrf_scores[entry_id]["original_scores"][weight] = score

        # Add scores from each strategy
        add_rrf_score(fts_results, weights["fts"])
        add_rrf_score(vector_results, weights["vector"])
        add_rrf_score(exact_results, weights["exact"])

        # Convert to list and sort
        fused = [(data["entry"], data["score"]) for data in rrf_scores.values()]
        fused.sort(key=lambda x: x[1], reverse=True)

        return fused

    # ===== RE-RANKING =====

    async def _rerank_with_user_context(
        self,
        db: AsyncSession,
        results: List[Tuple[KnowledgeEntry, float]],
        user_profile: Optional[Any]
    ) -> List[Tuple[KnowledgeEntry, float]]:
        """Re-rank results based on user context."""
        if not user_profile:
            return results

        reranked = []

        for entry, score in results:
            adjusted_score = score

            # Boost based on user's expertise areas
            if user_profile.expertise_areas and entry.domain:
                domain_expertise = user_profile.expertise_areas.get(entry.domain, {})
                if domain_expertise:
                    expertise_level = domain_expertise.get("level", "intermediate")
                    if expertise_level == "expert" or expertise_level == "advanced":
                        adjusted_score *= 1.2  # Boost advanced content for experts

            # Boost based on past helpful entries
            if entry.entry_id in user_profile.meta_data.get("helpful_entries", []):
                adjusted_score *= 1.3

            # Boost based on preferred technical depth match
            # (Would need more sophisticated matching in production)

            reranked.append((entry, adjusted_score))

        reranked.sort(key=lambda x: x[1], reverse=True)
        return reranked

    def _apply_ranking_boosts(
        self,
        results: List[Tuple[KnowledgeEntry, float]]
    ) -> List[Tuple[KnowledgeEntry, float]]:
        """Apply quality and recency boosts to results."""
        boosted = []

        for entry, score in results:
            adjusted_score = score

            # Quality boost
            quality_boost = 1.0 + (entry.quality_score * 0.5)  # Up to 1.5x for quality=1.0
            adjusted_score *= quality_boost

            # Recency boost (favor recent entries slightly)
            if entry.created_at:
                days_old = (datetime.utcnow() - entry.created_at).days
                if days_old < 7:
                    recency_boost = 1.2
                elif days_old < 30:
                    recency_boost = 1.1
                elif days_old > 365:
                    recency_boost = 0.9
                else:
                    recency_boost = 1.0

                adjusted_score *= recency_boost

            # Validation boost
            validation_boosts = {
                ValidationStatus.ORGANIZATIONAL_STANDARD: 1.3,
                ValidationStatus.HUMAN_VALIDATED: 1.2,
                ValidationStatus.AGENT_VALIDATED: 1.1,
                ValidationStatus.UNVALIDATED: 1.0
            }
            adjusted_score *= validation_boosts.get(entry.validation_status, 1.0)

            # Usage success boost
            if entry.use_count > 0:
                helpfulness_ratio = entry.helpfulness_up / (entry.helpfulness_up + entry.helpfulness_down + 1)
                usage_boost = 1.0 + (helpfulness_ratio * 0.3)  # Up to 1.3x
                adjusted_score *= usage_boost

            boosted.append((entry, adjusted_score))

        boosted.sort(key=lambda x: x[1], reverse=True)
        return boosted

    # ===== RELATION EXPANSION =====

    async def _expand_with_relations(
        self,
        db: AsyncSession,
        results: List[Tuple[KnowledgeEntry, float]],
        max_related: int
    ) -> List[Tuple[KnowledgeEntry, float]]:
        """Expand results with related entries."""
        expanded = list(results)
        entry_ids_included = {entry.entry_id for entry, _ in results}

        for entry, score in results[:max_related]:  # Only expand top results
            # Get related entries
            related_query = select(KnowledgeEntry).join(
                KnowledgeRelationship,
                KnowledgeRelationship.target_entry_id == KnowledgeEntry.entry_id
            ).where(
                and_(
                    KnowledgeRelationship.source_entry_id == entry.entry_id,
                    KnowledgeRelationship.strength >= 0.7,
                    KnowledgeEntry.status == KnowledgeStatus.ACTIVE
                )
            ).limit(3)

            result = await db.execute(related_query)
            related_entries = result.scalars().all()

            for related in related_entries:
                if related.entry_id not in entry_ids_included:
                    # Add with reduced score
                    expanded.append((related, score * 0.6))
                    entry_ids_included.add(related.entry_id)

        expanded.sort(key=lambda x: x[1], reverse=True)
        return expanded

    # ===== FORMATTING =====

    async def _format_search_results(
        self,
        db: AsyncSession,
        results: List[Tuple[KnowledgeEntry, float]]
    ) -> List[Dict[str, Any]]:
        """Format search results for API response."""
        formatted = []

        for entry, score in results:
            formatted.append({
                "entry_id": str(entry.entry_id),
                "title": entry.title,
                "summary": entry.summary,
                "content_excerpt": entry.content[:300] + "..." if len(entry.content) > 300 else entry.content,
                "entry_type": entry.entry_type.value,
                "domain": entry.domain,
                "tags": entry.tags,
                "validation_status": entry.validation_status.value,
                "quality_score": round(entry.quality_score, 3),
                "relevance_score": round(score, 3),
                "use_count": entry.use_count,
                "helpfulness_ratio": round(
                    entry.helpfulness_up / (entry.helpfulness_up + entry.helpfulness_down + 1),
                    3
                ),
                "created_at": entry.created_at.isoformat() if entry.created_at else None,
                "last_accessed_at": entry.last_accessed_at.isoformat() if entry.last_accessed_at else None
            })

        return formatted

    # ===== USAGE LOGGING =====

    async def log_knowledge_usage(
        self,
        db: AsyncSession,
        entry_id: UUID,
        agent_id: str,
        usage_type: UsageType,
        context: Optional[Dict[str, Any]] = None,
        was_helpful: Optional[bool] = None
    ) -> None:
        """Log knowledge usage for analytics."""
        try:
            usage_log = KnowledgeUsageLog(
                entry_id=entry_id,
                used_by_agent_id=agent_id,
                usage_type=usage_type,
                conversation_context=context or {},
                was_helpful=was_helpful
            )

            db.add(usage_log)

            # Update entry metrics
            entry = await db.get(KnowledgeEntry, entry_id)
            if entry:
                entry.use_count += 1
                entry.last_accessed_at = datetime.utcnow()

            await db.commit()

        except Exception as e:
            logger.error(f"Error logging knowledge usage: {e}")

    # ===== HELPERS =====

    async def _get_user_profile(
        self,
        db: AsyncSession,
        user_id: UUID
    ) -> Optional[UserKnowledgeProfile]:
        """Get user knowledge profile."""
        try:
            result = await db.execute(
                select(UserKnowledgeProfile).where(
                    UserKnowledgeProfile.user_id == user_id
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return None


# Singleton instance
_knowledge_repository_service: Optional[KnowledgeRepositoryService] = None


def get_knowledge_repository_service() -> KnowledgeRepositoryService:
    """Get or create singleton knowledge repository service."""
    global _knowledge_repository_service
    if _knowledge_repository_service is None:
        _knowledge_repository_service = KnowledgeRepositoryService()
    return _knowledge_repository_service
