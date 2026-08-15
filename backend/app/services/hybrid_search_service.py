"""
Hybrid Search Service

Combines vector similarity search with keyword-based search for improved retrieval.
Provides hybrid search capabilities leveraging both semantic and keyword matching.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from collections import defaultdict

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class HybridSearchResult:
    """Represents a hybrid search result"""

    def __init__(
        self,
        entity_id: str,
        entity_type: str,
        entity_name: str,
        entity_description: str,
        vector_score: float,
        keyword_score: float,
        combined_score: float,
        metadata: Dict[str, Any]
    ):
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.entity_name = entity_name
        self.entity_description = entity_description
        self.vector_score = vector_score
        self.keyword_score = keyword_score
        self.combined_score = combined_score
        self.metadata = metadata

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "entity_name": self.entity_name,
            "entity_description": self.entity_description,
            "vector_score": round(self.vector_score, 3),
            "keyword_score": round(self.keyword_score, 3),
            "combined_score": round(self.combined_score, 3),
            "metadata": self.metadata
        }


class HybridSearchService:
    """Service for hybrid search combining vector and keyword matching"""

    def __init__(self, vector_weight: float = 0.6, keyword_weight: float = 0.4):
        """
        Initialize hybrid search service.

        Args:
            vector_weight: Weight for vector similarity scores (0-1)
            keyword_weight: Weight for keyword matching scores (0-1)
        """
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        self.last_cache_update = {}

    async def hybrid_search(
        self,
        session: AsyncSession,
        query: str,
        entity_types: Optional[List[str]] = None,
        top_k: int = 10,
        min_combined_score: float = 0.3
    ) -> List[HybridSearchResult]:
        """
        Perform hybrid search across entities.

        Args:
            session: Database session
            query: Search query
            entity_types: Optional list of entity types to search (task, project, decision)
            top_k: Number of results to return
            min_combined_score: Minimum combined score threshold

        Returns:
            List of hybrid search results sorted by combined score
        """
        cache_key = f"hybrid_{query}_{entity_types}_{top_k}"

        # Check cache
        if cache_key in self.cache:
            if datetime.now() - self.last_cache_update.get(cache_key, datetime.min) < timedelta(seconds=self.cache_ttl):
                return self.cache[cache_key]

        try:
            results = []

            # Get vector scores (semantic search)
            vector_results = await self._get_vector_scores(
                session=session,
                query=query,
                entity_types=entity_types,
                top_k=top_k
            )

            # Get keyword scores (keyword search)
            keyword_results = await self._get_keyword_scores(
                session=session,
                query=query,
                entity_types=entity_types,
                top_k=top_k
            )

            # Combine results
            combined = self._combine_search_results(
                vector_results=vector_results,
                keyword_results=keyword_results,
                top_k=top_k
            )

            # Filter by minimum score and convert to result objects
            for item in combined:
                if item["combined_score"] >= min_combined_score:
                    result = HybridSearchResult(
                        entity_id=item["entity_id"],
                        entity_type=item["entity_type"],
                        entity_name=item["entity_name"],
                        entity_description=item["entity_description"],
                        vector_score=item["vector_score"],
                        keyword_score=item["keyword_score"],
                        combined_score=item["combined_score"],
                        metadata=item["metadata"]
                    )
                    results.append(result)

            # Cache results
            self.cache[cache_key] = results
            self.last_cache_update[cache_key] = datetime.now()

            logger.info(f"Hybrid search for '{query}' returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            return []

    async def _get_vector_scores(
        self,
        session: AsyncSession,
        query: str,
        entity_types: Optional[List[str]] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get vector similarity scores for query.

        In a real implementation, this would use ChromaDB or similar.
        For now, we'll use a simplified approach with embeddings.
        """
        try:
            from app.db.models import Task, Project, Decision, TaskStatus

            results = []

            # If entity_types not specified, search all
            if not entity_types:
                entity_types = ["task", "project", "decision"]

            # Search Tasks
            if "task" in entity_types:
                task_results = await session.execute(
                    select(Task).where(
                        and_(
                            Task.status == TaskStatus.COMPLETED,
                            Task.created_at >= datetime.utcnow() - timedelta(days=180)
                        )
                    ).limit(top_k * 2)
                )

                for task in task_results.scalars().all():
                    # Calculate simple semantic score based on text similarity
                    score = self._calculate_semantic_similarity(query, task.title, task.description)
                    if score > 0:
                        results.append({
                            "entity_id": str(task.task_id),
                            "entity_type": "task",
                            "entity_name": task.title,
                            "entity_description": task.description or "",
                            "vector_score": score,
                            "metadata": {
                                "project_id": str(task.project_id),
                                "status": str(task.status),
                                "success_score": task.success_score
                            }
                        })

            # Search Projects
            if "project" in entity_types:
                project_results = await session.execute(
                    select(Project).where(
                        Project.created_at >= datetime.utcnow() - timedelta(days=180)
                    ).limit(top_k * 2)
                )

                for project in project_results.scalars().all():
                    score = self._calculate_semantic_similarity(query, project.name, project.description)
                    if score > 0:
                        results.append({
                            "entity_id": str(project.project_id),
                            "entity_type": "project",
                            "entity_name": project.name,
                            "entity_description": project.description or "",
                            "vector_score": score,
                            "metadata": {
                                "status": str(project.status) if hasattr(project, 'status') else "unknown",
                                "quality_score": getattr(project, 'quality_score', 0)
                            }
                        })

            # Sort by vector score
            results.sort(key=lambda r: r["vector_score"], reverse=True)

            return results[:top_k]

        except Exception as e:
            logger.error(f"Error getting vector scores: {e}")
            return []

    async def _get_keyword_scores(
        self,
        session: AsyncSession,
        query: str,
        entity_types: Optional[List[str]] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Get keyword matching scores for query"""
        try:
            from app.db.models import Task, Project, Decision, TaskStatus

            results = []
            query_terms = set(query.lower().split())

            if not entity_types:
                entity_types = ["task", "project", "decision"]

            # Search Tasks by keywords
            if "task" in entity_types:
                task_results = await session.execute(
                    select(Task).where(
                        Task.status == TaskStatus.COMPLETED
                    ).limit(top_k * 2)
                )

                for task in task_results.scalars().all():
                    text = f"{task.title} {task.description}".lower()
                    score = self._calculate_keyword_score(query_terms, text)

                    if score > 0:
                        results.append({
                            "entity_id": str(task.task_id),
                            "entity_type": "task",
                            "entity_name": task.title,
                            "entity_description": task.description or "",
                            "keyword_score": score,
                            "metadata": {
                                "project_id": str(task.project_id),
                                "status": str(task.status),
                                "success_score": task.success_score
                            }
                        })

            # Search Projects by keywords
            if "project" in entity_types:
                project_results = await session.execute(
                    select(Project).limit(top_k * 2)
                )

                for project in project_results.scalars().all():
                    text = f"{project.name} {project.description}".lower()
                    score = self._calculate_keyword_score(query_terms, text)

                    if score > 0:
                        results.append({
                            "entity_id": str(project.project_id),
                            "entity_type": "project",
                            "entity_name": project.name,
                            "entity_description": project.description or "",
                            "keyword_score": score,
                            "metadata": {
                                "status": str(project.status) if hasattr(project, 'status') else "unknown",
                                "quality_score": getattr(project, 'quality_score', 0)
                            }
                        })

            # Sort by keyword score
            results.sort(key=lambda r: r["keyword_score"], reverse=True)

            return results[:top_k]

        except Exception as e:
            logger.error(f"Error getting keyword scores: {e}")
            return []

    def _calculate_semantic_similarity(
        self,
        query: str,
        title: str,
        description: str
    ) -> float:
        """
        Calculate semantic similarity between query and entity.

        Simple implementation using word overlap.
        In production, would use actual embeddings.
        """
        query_words = set(query.lower().split())
        entity_text = f"{title} {description}".lower()
        entity_words = set(entity_text.split())

        if not query_words or not entity_words:
            return 0.0

        overlap = len(query_words & entity_words)
        union = len(query_words | entity_words)

        return overlap / union if union > 0 else 0.0

    def _calculate_keyword_score(self, query_terms: set, text: str) -> float:
        """Calculate keyword matching score"""
        text_words = set(text.split())
        matches = len(query_terms & text_words)

        if not query_terms:
            return 0.0

        return matches / len(query_terms)

    def _combine_search_results(
        self,
        vector_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Combine vector and keyword search results"""
        # Create lookup dictionaries
        vector_lookup = {
            (r["entity_id"], r["entity_type"]): r["vector_score"]
            for r in vector_results
        }

        keyword_lookup = {
            (r["entity_id"], r["entity_type"]): r["keyword_score"]
            for r in keyword_results
        }

        # Combine all unique entities
        combined = {}
        for item in vector_results + keyword_results:
            key = (item["entity_id"], item["entity_type"])

            if key not in combined:
                vector_score = vector_lookup.get(key, 0.0)
                keyword_score = keyword_lookup.get(key, 0.0)

                combined_score = (
                    vector_score * self.vector_weight +
                    keyword_score * self.keyword_weight
                )

                combined[key] = {
                    "entity_id": item["entity_id"],
                    "entity_type": item["entity_type"],
                    "entity_name": item["entity_name"],
                    "entity_description": item["entity_description"],
                    "vector_score": vector_score,
                    "keyword_score": keyword_score,
                    "combined_score": combined_score,
                    "metadata": item.get("metadata", {})
                }

        # Sort by combined score
        results = sorted(
            combined.values(),
            key=lambda r: r["combined_score"],
            reverse=True
        )

        return results[:top_k]

    async def advanced_search(
        self,
        session: AsyncSession,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 20
    ) -> List[HybridSearchResult]:
        """
        Advanced search with filters.

        Filters can include:
        - entity_type: List of types to search
        - min_success_score: Minimum success score
        - date_range: (start_date, end_date)
        - technologies: List of technologies
        """
        results = await self.hybrid_search(
            session=session,
            query=query,
            entity_types=filters.get("entity_type") if filters else None,
            top_k=top_k
        )

        # Apply filters
        if filters:
            filtered = []
            for result in results:
                if self._matches_filters(result, filters):
                    filtered.append(result)
            return filtered

        return results

    def _matches_filters(self, result: HybridSearchResult, filters: Dict[str, Any]) -> bool:
        """Check if result matches filter criteria"""
        # Entity type filter
        if "entity_type" in filters:
            allowed_types = filters["entity_type"]
            if isinstance(allowed_types, list) and result.entity_type not in allowed_types:
                return False

        # Success score filter
        if "min_success_score" in filters:
            min_score = filters["min_success_score"]
            entity_score = result.metadata.get("success_score", 0)
            if entity_score < min_score:
                return False

        # Combined score threshold
        if "min_combined_score" in filters:
            if result.combined_score < filters["min_combined_score"]:
                return False

        return True


# Singleton instance
_hybrid_search_service: Optional[HybridSearchService] = None


def get_hybrid_search_service(
    vector_weight: float = 0.6,
    keyword_weight: float = 0.4
) -> HybridSearchService:
    """Get or create the hybrid search service singleton"""
    global _hybrid_search_service
    if _hybrid_search_service is None:
        _hybrid_search_service = HybridSearchService(vector_weight, keyword_weight)
    return _hybrid_search_service
