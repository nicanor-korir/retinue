"""
Project Similarity Detection Service - Phase 2 Component 4

Finds similar projects and provides recommendations based on learnings:
- Detects similar past projects using embeddings
- Retrieves learnings from similar projects
- Provides actionable recommendations
- Tracks knowledge reuse and ROI
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import Project, ProjectStatus
from app.services.rag_cache_service import get_cache_service
from app.services.rag_vector_store import get_vector_store
from app.services.rag_embedding_service import get_embedding_service
from app.services.project_learnings_service import get_project_learnings_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class SimilarProject:
    """Represents a similar project with learnings."""

    def __init__(
        self,
        project_id: UUID,
        name: str,
        similarity_score: float,
        learnings: List[Dict[str, Any]],
        metrics: Dict[str, Any],
    ):
        """Initialize a similar project."""
        self.project_id = project_id
        self.name = name
        self.similarity_score = similarity_score  # 0-1
        self.learnings = learnings
        self.metrics = metrics

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "project_id": str(self.project_id),
            "name": self.name,
            "similarity_score": round(self.similarity_score, 2),
            "learnings": self.learnings,
            "metrics": self.metrics,
        }


class ProjectRecommendation:
    """Represents a recommendation based on similar projects."""

    def __init__(
        self,
        title: str,
        description: str,
        category: str,  # "best_practice", "caution", "opportunity"
        confidence: float,  # 0-1
        source_projects: List[str],  # Project IDs
        evidence: List[str],
    ):
        """Initialize a recommendation."""
        self.title = title
        self.description = description
        self.category = category
        self.confidence = confidence
        self.source_projects = source_projects
        self.evidence = evidence
        self.created_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "confidence": round(self.confidence, 2),
            "source_projects": self.source_projects,
            "evidence": self.evidence,
            "created_at": self.created_at.isoformat(),
        }


class ProjectSimilarityService:
    """Service for finding similar projects and providing recommendations."""

    def __init__(self):
        """Initialize the project similarity service."""
        self.cache_service = get_cache_service()
        self.vector_store = get_vector_store(persist_dir=settings.CHROMADB_PATH)
        self.embedding_service = get_embedding_service()
        self.learnings_service = get_project_learnings_service()
        self.cache_ttl = 600  # 10 minutes
        self.similarity_threshold = 0.6

    async def find_similar_projects(
        self,
        session: AsyncSession,
        project_id: UUID,
        name: str,
        description: str,
        top_k: int = 5,
        min_similarity: float = 0.6,
    ) -> List[SimilarProject]:
        """
        Find similar completed projects.

        Uses vector similarity to find projects with similar characteristics,
        then retrieves learnings from those projects.

        Args:
            session: Database session
            project_id: Current project ID (for context, not to exclude)
            name: Current project name
            description: Current project description
            top_k: Number of similar projects to retrieve
            min_similarity: Minimum similarity score threshold (0-1)

        Returns:
            List of similar projects with learnings
        """
        try:
            search_query = f"{name} {description}"

            # Check cache first
            cache_key = f"similar_projects:{project_id}"
            cached = self.cache_service.get(cache_key)
            if cached:
                logger.info(f"Cache hit for similar projects: {project_id}")
                return cached

            # Generate embedding
            query_embedding = await self.embedding_service.embed_text(search_query)

            # Query vector store for similar projects
            collection = self.vector_store.collections.get("projects")
            if not collection:
                logger.warning("Projects collection not found in vector store")
                return []

            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k * 2,  # Get more to filter by threshold
                where={
                    "$and": [
                        {"entity_type": {"$eq": "project"}},
                        {"status": {"$eq": "completed"}},
                    ]
                },
            )

            similar_projects: List[SimilarProject] = []

            if results and results.get("ids") and len(results["ids"]) > 0:
                for i, doc_id in enumerate(results["ids"][0]):
                    try:
                        metadata = results["metadatas"][0][i]
                        similarity_score = 1 - (results["distances"][0][i] / 2)

                        # Filter by similarity threshold
                        if similarity_score < min_similarity:
                            continue

                        # Get project learnings
                        similar_project_id = UUID(metadata.get("entity_id"))
                        learnings = await self.learnings_service.extract_learnings_from_project(
                            session=session,
                            project_id=similar_project_id,
                        )

                        # Get project metrics
                        metrics = await self.learnings_service.calculate_project_metrics(
                            session=session,
                            project_id=similar_project_id,
                        )

                        # Create similar project object
                        similar_project = SimilarProject(
                            project_id=similar_project_id,
                            name=metadata.get("name", ""),
                            similarity_score=similarity_score,
                            learnings=[l.to_dict() for l in learnings],
                            metrics=metrics,
                        )
                        similar_projects.append(similar_project)

                        if len(similar_projects) >= top_k:
                            break

                    except Exception as e:
                        logger.warning(f"Error processing similar project {doc_id}: {e}")
                        continue

            # Sort by similarity score
            similar_projects.sort(key=lambda x: x.similarity_score, reverse=True)

            # Cache the result
            self.cache_service.set(cache_key, similar_projects, ttl=self.cache_ttl)

            logger.info(f"Found {len(similar_projects)} similar projects for {project_id}")
            return similar_projects

        except Exception as e:
            logger.error(f"Error finding similar projects for {project_id}: {e}")
            return []

    async def generate_recommendations(
        self,
        session: AsyncSession,
        project_id: UUID,
        name: str,
        description: str,
        top_k: int = 5,
    ) -> Tuple[List[ProjectRecommendation], float]:
        """
        Generate recommendations based on similar projects.

        Analyzes learnings from similar projects and creates actionable
        recommendations for the current project.

        Args:
            session: Database session
            project_id: Current project ID
            name: Current project name
            description: Current project description
            top_k: Number of similar projects to consider

        Returns:
            Tuple of (recommendations, average_similarity_score)
        """
        try:
            # Find similar projects
            similar_projects = await self.find_similar_projects(
                session=session,
                project_id=project_id,
                name=name,
                description=description,
                top_k=top_k,
            )

            if not similar_projects:
                logger.info(f"No similar projects found for {project_id}")
                return [], 0.0

            recommendations: List[ProjectRecommendation] = []
            avg_similarity = sum(p.similarity_score for p in similar_projects) / len(
                similar_projects
            )

            # Collect learnings from all similar projects
            best_practices = []
            cautions = []
            opportunities = []

            for similar_project in similar_projects:
                for learning in similar_project.learnings:
                    learning_type = learning.get("learning_type", "")
                    title = learning.get("title", "")
                    description = learning.get("description", "")
                    relevance = learning.get("relevance_score", 0)

                    # Categorize learnings
                    if learning_type == "best_practice":
                        best_practices.append(
                            {
                                "title": title,
                                "description": description,
                                "relevance": relevance,
                                "source": str(similar_project.project_id),
                            }
                        )
                    elif learning_type == "improvement":
                        cautions.append(
                            {
                                "title": title,
                                "description": description,
                                "relevance": relevance,
                                "source": str(similar_project.project_id),
                            }
                        )

            # Generate best practice recommendations
            for bp in best_practices[:3]:  # Top 3 best practices
                rec = ProjectRecommendation(
                    title=f"Adopt: {bp['title']}",
                    description=f"{bp['description']} - Based on {len(similar_projects)} similar projects",
                    category="best_practice",
                    confidence=min(bp['relevance'] * avg_similarity, 1.0),
                    source_projects=[bp['source']],
                    evidence=[
                        f"Found in similar project: {bp['source']}",
                        f"Relevance score: {bp['relevance']:.0%}",
                    ],
                )
                recommendations.append(rec)

            # Generate caution recommendations
            for caution in cautions[:2]:  # Top 2 cautions
                rec = ProjectRecommendation(
                    title=f"Watch Out: {caution['title']}",
                    description=f"Previous projects encountered: {caution['description']}",
                    category="caution",
                    confidence=min(caution['relevance'] * avg_similarity, 1.0),
                    source_projects=[caution['source']],
                    evidence=[
                        f"Identified in similar project: {caution['source']}",
                        f"Risk level: {caution['relevance']:.0%}",
                    ],
                )
                recommendations.append(rec)

            # Generate opportunity recommendations
            high_success_projects = [
                p for p in similar_projects if p.metrics.get("success_score", 0) > 0.85
            ]
            if high_success_projects:
                avg_success = sum(
                    p.metrics.get("success_score", 0) for p in high_success_projects
                ) / len(high_success_projects)
                rec = ProjectRecommendation(
                    title="High Success Potential",
                    description=f"Similar projects achieved {avg_success:.0%} success rate - "
                    f"Follow their approach for optimal results",
                    category="opportunity",
                    confidence=avg_success,
                    source_projects=[str(p.project_id) for p in high_success_projects],
                    evidence=[
                        f"Based on {len(high_success_projects)} high-success projects",
                        f"Average success score: {avg_success:.0%}",
                    ],
                )
                recommendations.append(rec)

            # Sort by confidence
            recommendations.sort(key=lambda x: x.confidence, reverse=True)

            logger.info(
                f"Generated {len(recommendations)} recommendations for project {project_id}"
            )
            return recommendations, avg_similarity

        except Exception as e:
            logger.error(f"Error generating recommendations for {project_id}: {e}")
            return [], 0.0

    async def get_knowledge_reuse_insights(
        self,
        session: AsyncSession,
        project_id: UUID,
    ) -> Dict[str, Any]:
        """
        Get insights on knowledge reuse and ROI from similar projects.

        Args:
            session: Database session
            project_id: Project ID

        Returns:
            Dictionary with knowledge reuse metrics
        """
        try:
            # Fetch current project
            result = await session.execute(
                select(Project).where(Project.project_id == project_id)
            )
            project = result.scalar_one_or_none()

            if not project:
                return {"error": "Project not found"}

            # Find similar projects
            similar_projects = await self.find_similar_projects(
                session=session,
                project_id=project_id,
                name=project.name,
                description=project.description or "",
                top_k=5,
            )

            if not similar_projects:
                return {
                    "project_id": str(project_id),
                    "similar_projects_count": 0,
                    "knowledge_reuse_potential": "low",
                    "estimated_savings": None,
                }

            # Calculate metrics
            avg_similarity = sum(p.similarity_score for p in similar_projects) / len(
                similar_projects
            )
            avg_success_rate = sum(
                p.metrics.get("success_score", 0) for p in similar_projects
            ) / len(similar_projects)
            total_learnings = sum(len(p.learnings) for p in similar_projects)

            # Estimate time savings (assumption: 10% per learning adopted)
            current_estimated_hours = project.agent_days_elapsed * 8 if project.agent_days_elapsed else 0
            potential_savings_hours = current_estimated_hours * (total_learnings * 0.05)

            knowledge_reuse_potential = "high" if avg_similarity > 0.8 else (
                "medium" if avg_similarity > 0.6 else "low"
            )

            return {
                "project_id": str(project_id),
                "similar_projects_count": len(similar_projects),
                "average_similarity": round(avg_similarity, 2),
                "average_success_rate": round(avg_success_rate, 2),
                "total_applicable_learnings": total_learnings,
                "knowledge_reuse_potential": knowledge_reuse_potential,
                "estimated_time_savings_hours": round(potential_savings_hours, 1),
                "estimated_cost_savings_percent": round(
                    (potential_savings_hours / current_estimated_hours * 100)
                    if current_estimated_hours > 0 else 0,
                    1,
                ),
            }

        except Exception as e:
            logger.error(f"Error calculating knowledge reuse insights for {project_id}: {e}")
            return {"error": str(e), "project_id": str(project_id)}


# Singleton instance
_project_similarity_service: Optional["ProjectSimilarityService"] = None


def get_project_similarity_service() -> ProjectSimilarityService:
    """Get or create the ProjectSimilarityService singleton."""
    global _project_similarity_service
    if _project_similarity_service is None:
        _project_similarity_service = ProjectSimilarityService()
    return _project_similarity_service
