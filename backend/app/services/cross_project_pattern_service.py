"""
Cross-Project Pattern Service

Handles pattern sharing and reuse across multiple projects.
Enables knowledge transfer and pattern discovery across the organization.
"""

import json
import logging
from typing import List, Dict, Any, Optional, Set
from uuid import UUID
from datetime import datetime, timedelta
from collections import defaultdict

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class PatternOccurrence:
    """Represents a single occurrence of a pattern in a task"""

    def __init__(
        self,
        task_id: UUID,
        project_id: UUID,
        pattern_name: str,
        success_score: float,
        context: str,
        technologies: List[str],
        timestamp: datetime
    ):
        self.task_id = task_id
        self.project_id = project_id
        self.pattern_name = pattern_name
        self.success_score = success_score
        self.context = context
        self.technologies = technologies
        self.timestamp = timestamp


class CrossProjectPattern:
    """Represents a pattern that appears across multiple projects"""

    def __init__(
        self,
        pattern_id: str,
        pattern_name: str,
        category: str,
        description: str,
        occurrences: List[PatternOccurrence],
        success_rate: float,
        technology_stack: List[str],
        project_ids: Set[str],
        difficulty_level: str,
        estimated_effort_minutes: int,
        best_practices: List[str],
        anti_patterns: List[str],
        last_used: datetime,
        usage_count: int,
        effectiveness_score: float
    ):
        self.pattern_id = pattern_id
        self.pattern_name = pattern_name
        self.category = category
        self.description = description
        self.occurrences = occurrences
        self.success_rate = success_rate
        self.technology_stack = technology_stack
        self.project_ids = project_ids
        self.difficulty_level = difficulty_level
        self.estimated_effort_minutes = estimated_effort_minutes
        self.best_practices = best_practices
        self.anti_patterns = anti_patterns
        self.last_used = last_used
        self.usage_count = usage_count
        self.effectiveness_score = effectiveness_score

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "pattern_id": self.pattern_id,
            "pattern_name": self.pattern_name,
            "category": self.category,
            "description": self.description,
            "success_rate": self.success_rate,
            "technology_stack": self.technology_stack,
            "project_ids": list(self.project_ids),
            "project_count": len(self.project_ids),
            "difficulty_level": self.difficulty_level,
            "estimated_effort_minutes": self.estimated_effort_minutes,
            "best_practices": self.best_practices,
            "anti_patterns": self.anti_patterns,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "usage_count": self.usage_count,
            "effectiveness_score": self.effectiveness_score,
            "occurrence_count": len(self.occurrences)
        }


class CrossProjectPatternService:
    """Service for managing patterns across multiple projects"""

    def __init__(self):
        """Initialize the cross-project pattern service"""
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        self.last_cache_update = {}

    async def find_patterns_across_projects(
        self,
        session: AsyncSession,
        min_occurrences: int = 2,
        min_success_rate: float = 0.7,
        days_back: int = 90
    ) -> List[CrossProjectPattern]:
        """
        Find patterns that occur across multiple projects.

        Args:
            session: Database session
            min_occurrences: Minimum number of occurrences to consider a pattern
            min_success_rate: Minimum success rate threshold
            days_back: Only consider patterns from last N days

        Returns:
            List of patterns found across projects
        """
        cache_key = f"cross_patterns_{min_occurrences}_{min_success_rate}"

        # Check cache
        if cache_key in self.cache:
            if datetime.now() - self.last_cache_update.get(cache_key, datetime.min) < timedelta(seconds=self.cache_ttl):
                return self.cache[cache_key]

        try:
            # Import models here to avoid circular imports
            from app.db.models import Task, Project, TaskStatus

            cutoff_date = datetime.utcnow() - timedelta(days=days_back)

            # Get all successfully completed tasks in that period
            result = await session.execute(
                select(Task).where(
                    and_(
                        Task.status == TaskStatus.COMPLETED,
                        Task.success_score >= min_success_rate,
                        Task.created_at >= cutoff_date,
                        Task.pattern_category.isnot(None)
                    )
                )
            )

            completed_tasks = result.scalars().all()

            # Group by pattern category
            patterns_by_category = defaultdict(list)
            for task in completed_tasks:
                if task.pattern_category:
                    patterns_by_category[task.pattern_category].append(task)

            # Create cross-project patterns
            cross_patterns = []
            for category, tasks in patterns_by_category.items():
                if len(tasks) >= min_occurrences:
                    # Get unique projects
                    project_ids = set(str(t.project_id) for t in tasks)

                    # Only include if in multiple projects
                    if len(project_ids) >= 2:
                        pattern = await self._create_cross_project_pattern(
                            session=session,
                            category=category,
                            tasks=tasks,
                            project_ids=project_ids
                        )
                        cross_patterns.append(pattern)

            # Sort by effectiveness
            cross_patterns.sort(
                key=lambda p: p.effectiveness_score,
                reverse=True
            )

            # Cache results
            self.cache[cache_key] = cross_patterns
            self.last_cache_update[cache_key] = datetime.now()

            logger.info(f"Found {len(cross_patterns)} cross-project patterns")
            return cross_patterns

        except Exception as e:
            logger.error(f"Error finding cross-project patterns: {e}")
            return []

    async def _create_cross_project_pattern(
        self,
        session: AsyncSession,
        category: str,
        tasks: List[Any],
        project_ids: Set[str]
    ) -> CrossProjectPattern:
        """
        Create a cross-project pattern from multiple task occurrences.

        Args:
            session: Database session
            category: Pattern category
            tasks: List of tasks using this pattern
            project_ids: Set of project IDs

        Returns:
            CrossProjectPattern instance
        """
        # Calculate metrics
        success_scores = [t.success_score or 0 for t in tasks]
        success_rate = sum(success_scores) / len(success_scores) if success_scores else 0

        avg_effort = sum(t.estimated_effort_minutes or 0 for t in tasks) / len(tasks) if tasks else 0

        # Collect technologies
        all_techs = set()
        for task in tasks:
            if task.technologies:
                all_techs.update(task.technologies)

        # Collect best practices and anti-patterns
        best_practices = []
        anti_patterns = []
        for task in tasks:
            if task.lessons_learned:
                if "best" in task.lessons_learned.lower() or "effective" in task.lessons_learned.lower():
                    best_practices.append(task.lessons_learned[:100])
                if "avoid" in task.lessons_learned.lower() or "issue" in task.lessons_learned.lower():
                    anti_patterns.append(task.lessons_learned[:100])

        # Remove duplicates
        best_practices = list(set(best_practices))[:5]
        anti_patterns = list(set(anti_patterns))[:5]

        # Determine difficulty level
        avg_success_rate = sum(t.success_score or 0 for t in tasks) / len(tasks) if tasks else 0
        if avg_success_rate >= 0.85:
            difficulty = "Easy"
        elif avg_success_rate >= 0.7:
            difficulty = "Medium"
        else:
            difficulty = "Hard"

        # Calculate effectiveness (considering reuse count and success rate)
        effectiveness = (success_rate * 0.7) + (len(project_ids) / 10 * 0.3)

        # Create pattern occurrences
        occurrences = [
            PatternOccurrence(
                task_id=t.task_id,
                project_id=t.project_id,
                pattern_name=category,
                success_score=t.success_score or 0,
                context=t.description or "",
                technologies=t.technologies or [],
                timestamp=t.created_at or datetime.utcnow()
            )
            for t in tasks[:10]  # Limit to 10 most recent
        ]

        pattern = CrossProjectPattern(
            pattern_id=f"pattern_{category}_{int(datetime.now().timestamp())}",
            pattern_name=f"{category.replace('_', ' ').title()} Pattern",
            category=category,
            description=f"Pattern discovered across {len(project_ids)} projects from {len(tasks)} successful uses",
            occurrences=occurrences,
            success_rate=success_rate,
            technology_stack=list(all_techs),
            project_ids=project_ids,
            difficulty_level=difficulty,
            estimated_effort_minutes=int(avg_effort),
            best_practices=best_practices,
            anti_patterns=anti_patterns,
            last_used=max(t.created_at or datetime.min for t in tasks),
            usage_count=len(tasks),
            effectiveness_score=effectiveness
        )

        return pattern

    async def get_patterns_by_category(
        self,
        session: AsyncSession,
        category: str
    ) -> List[CrossProjectPattern]:
        """Get all patterns in a specific category"""
        try:
            all_patterns = await self.find_patterns_across_projects(session)
            return [p for p in all_patterns if p.category == category]
        except Exception as e:
            logger.error(f"Error getting patterns by category: {e}")
            return []

    async def get_patterns_for_project(
        self,
        session: AsyncSession,
        project_id: UUID
    ) -> List[CrossProjectPattern]:
        """Get patterns used by other projects similar to this one"""
        try:
            from app.db.models import Project

            # Get project info
            project = await session.get(Project, project_id)
            if not project:
                return []

            # Get all cross-project patterns
            all_patterns = await self.find_patterns_across_projects(session)

            # Filter to patterns not yet used by this project
            project_patterns = [
                p for p in all_patterns
                if str(project_id) not in p.project_ids
            ]

            # Score by relevance (tech stack match, success rate)
            scored_patterns = []
            for pattern in project_patterns:
                score = self._calculate_pattern_relevance(project, pattern)
                scored_patterns.append((pattern, score))

            # Sort by relevance score
            scored_patterns.sort(key=lambda x: x[1], reverse=True)

            return [p for p, _ in scored_patterns[:10]]

        except Exception as e:
            logger.error(f"Error getting patterns for project: {e}")
            return []

    def _calculate_pattern_relevance(
        self,
        project: Any,
        pattern: CrossProjectPattern
    ) -> float:
        """
        Calculate relevance score of a pattern for a project.

        Considers:
        - Technology stack match
        - Success rate
        - Project complexity match
        - Difficulty level match
        """
        score = 0.0

        # Tech stack match (0.4 weight)
        if project.tech_stack:
            project_techs = set()
            if isinstance(project.tech_stack, dict):
                for v in project.tech_stack.values():
                    if isinstance(v, list):
                        project_techs.update(v)
                    else:
                        project_techs.add(str(v))

            pattern_techs = set(pattern.technology_stack)
            if project_techs and pattern_techs:
                overlap = len(project_techs & pattern_techs)
                tech_match = overlap / len(project_techs | pattern_techs)
                score += tech_match * 0.4
        else:
            score += 0.2  # Partial credit if no tech stack specified

        # Success rate (0.3 weight)
        score += pattern.success_rate * 0.3

        # Effectiveness (0.3 weight)
        score += pattern.effectiveness_score * 0.3

        return score

    async def recommend_patterns_for_task(
        self,
        session: AsyncSession,
        task_title: str,
        task_description: str,
        project_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        Recommend patterns for a new task based on its description.

        Args:
            session: Database session
            task_title: Task title
            task_description: Task description
            project_id: Project ID

        Returns:
            List of recommended patterns with relevance scores
        """
        try:
            # Get patterns for this project
            available_patterns = await self.get_patterns_for_project(session, project_id)

            if not available_patterns:
                return []

            # Simple keyword matching for pattern relevance
            task_text = f"{task_title} {task_description}".lower()

            recommendations = []
            for pattern in available_patterns:
                # Score based on pattern description match
                pattern_text = f"{pattern.pattern_name} {pattern.description}".lower()

                # Simple word overlap scoring
                task_words = set(task_text.split())
                pattern_words = set(pattern_text.split())

                if task_words and pattern_words:
                    overlap = len(task_words & pattern_words)
                    relevance = overlap / len(task_words | pattern_words)
                else:
                    relevance = 0

                # Combine with pattern effectiveness
                final_score = (relevance * 0.5) + (pattern.effectiveness_score * 0.5)

                if final_score > 0:
                    recommendations.append({
                        "pattern": pattern.to_dict(),
                        "relevance_score": final_score,
                        "confidence": pattern.success_rate,
                        "recommendation_reason": f"Proven pattern with {pattern.usage_count} uses across {len(pattern.project_ids)} projects"
                    })

            # Sort by score
            recommendations.sort(key=lambda r: r["relevance_score"], reverse=True)

            return recommendations[:5]  # Return top 5

        except Exception as e:
            logger.error(f"Error recommending patterns: {e}")
            return []

    async def get_pattern_by_id(
        self,
        session: AsyncSession,
        pattern_id: str
    ) -> Optional[CrossProjectPattern]:
        """Get a specific pattern by ID"""
        try:
            all_patterns = await self.find_patterns_across_projects(session)
            for pattern in all_patterns:
                if pattern.pattern_id == pattern_id:
                    return pattern
            return None
        except Exception as e:
            logger.error(f"Error getting pattern by ID: {e}")
            return None

    async def get_pattern_statistics(
        self,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Get statistics about all cross-project patterns"""
        try:
            patterns = await self.find_patterns_across_projects(session)

            if not patterns:
                return {
                    "total_patterns": 0,
                    "total_categories": 0,
                    "average_success_rate": 0,
                    "average_usage_count": 0,
                    "top_patterns": []
                }

            categories = set(p.category for p in patterns)
            avg_success = sum(p.success_rate for p in patterns) / len(patterns)
            avg_usage = sum(p.usage_count for p in patterns) / len(patterns)

            top_patterns = sorted(patterns, key=lambda p: p.effectiveness_score, reverse=True)[:5]

            return {
                "total_patterns": len(patterns),
                "total_categories": len(categories),
                "categories": list(categories),
                "average_success_rate": avg_success,
                "average_usage_count": avg_usage,
                "top_patterns": [p.to_dict() for p in top_patterns],
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting pattern statistics: {e}")
            return {}


# Singleton instance
_cross_project_pattern_service: Optional[CrossProjectPatternService] = None


def get_cross_project_pattern_service() -> CrossProjectPatternService:
    """Get or create the cross-project pattern service singleton"""
    global _cross_project_pattern_service
    if _cross_project_pattern_service is None:
        _cross_project_pattern_service = CrossProjectPatternService()
    return _cross_project_pattern_service
