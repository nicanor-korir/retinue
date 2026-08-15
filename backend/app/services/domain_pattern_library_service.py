"""
Domain Pattern Library Service

Manages domain-specific pattern libraries and provides organized access to patterns.
Enables creation, management, and querying of domain-specific pattern repositories.
"""

import logging
from typing import List, Dict, Any, Optional, Set
from uuid import UUID
from datetime import datetime, timedelta
from collections import defaultdict

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class DomainPatternLibrary:
    """Represents a domain-specific pattern library"""

    def __init__(
        self,
        domain_name: str,
        domain_id: str,
        description: str,
        patterns: List[Dict[str, Any]],
        keywords: List[str],
        technology_focus: List[str],
        complexity_levels: List[str],
        created_at: datetime,
        updated_at: datetime,
        usage_count: int = 0,
        success_rate: float = 0.0
    ):
        self.domain_name = domain_name
        self.domain_id = domain_id
        self.description = description
        self.patterns = patterns
        self.keywords = keywords
        self.technology_focus = technology_focus
        self.complexity_levels = complexity_levels
        self.created_at = created_at
        self.updated_at = updated_at
        self.usage_count = usage_count
        self.success_rate = success_rate

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "domain_name": self.domain_name,
            "domain_id": self.domain_id,
            "description": self.description,
            "pattern_count": len(self.patterns),
            "patterns": self.patterns,
            "keywords": self.keywords,
            "technology_focus": self.technology_focus,
            "complexity_levels": list(set(self.complexity_levels)),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "usage_count": self.usage_count,
            "success_rate": self.success_rate
        }


class DomainPatternLibraryService:
    """Service for managing domain-specific pattern libraries"""

    # Predefined domains
    DOMAINS = {
        "ecommerce": {
            "name": "E-Commerce",
            "description": "Patterns for e-commerce applications",
            "keywords": ["shopping", "cart", "checkout", "payment", "inventory"],
            "technologies": ["React", "Node.js", "PostgreSQL", "Stripe"]
        },
        "saas": {
            "name": "SaaS",
            "description": "Patterns for Software-as-a-Service applications",
            "keywords": ["subscription", "billing", "multi-tenant", "onboarding"],
            "technologies": ["FastAPI", "React", "PostgreSQL", "Redis"]
        },
        "social": {
            "name": "Social Media",
            "description": "Patterns for social platforms",
            "keywords": ["feed", "messaging", "notifications", "followers", "timeline"],
            "technologies": ["Node.js", "React", "MongoDB", "WebSocket"]
        },
        "enterprise": {
            "name": "Enterprise",
            "description": "Patterns for large-scale enterprise applications",
            "keywords": ["integration", "workflows", "reporting", "compliance"],
            "technologies": ["Java", "Spring", "Oracle", "Kafka"]
        },
        "iot": {
            "name": "IoT",
            "description": "Patterns for Internet of Things applications",
            "keywords": ["sensors", "realtime", "edge", "data-collection"],
            "technologies": ["Python", "MQTT", "InfluxDB", "Grafana"]
        },
        "ai": {
            "name": "AI/ML",
            "description": "Patterns for AI and Machine Learning applications",
            "keywords": ["model", "training", "inference", "pipeline", "dataset"],
            "technologies": ["Python", "TensorFlow", "PyTorch", "FastAPI"]
        }
    }

    def __init__(self):
        """Initialize the domain pattern library service"""
        self.libraries = {}
        self.cache = {}
        self.cache_ttl = 600  # 10 minutes
        self.last_cache_update = {}

    async def initialize_default_libraries(self, session: AsyncSession) -> Dict[str, DomainPatternLibrary]:
        """Initialize default domain libraries"""
        try:
            initialized = {}

            for domain_key, domain_info in self.DOMAINS.items():
                library = DomainPatternLibrary(
                    domain_name=domain_info["name"],
                    domain_id=domain_key,
                    description=domain_info["description"],
                    patterns=[],  # Will be populated from database
                    keywords=domain_info["keywords"],
                    technology_focus=domain_info["technologies"],
                    complexity_levels=["Easy", "Medium", "Hard"],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )

                # Load patterns for this domain
                patterns = await self._load_domain_patterns(session, domain_key)
                library.patterns = patterns

                self.libraries[domain_key] = library
                initialized[domain_key] = library

            logger.info(f"Initialized {len(initialized)} domain pattern libraries")
            return initialized

        except Exception as e:
            logger.error(f"Error initializing domain libraries: {e}")
            return {}

    async def _load_domain_patterns(
        self,
        session: AsyncSession,
        domain_key: str
    ) -> List[Dict[str, Any]]:
        """Load patterns for a specific domain from the database"""
        try:
            from app.db.models import Task, Project, TaskStatus

            domain_keywords = self.DOMAINS[domain_key]["keywords"]

            # Query for tasks matching domain keywords
            query = select(Task).where(
                and_(
                    Task.status == TaskStatus.COMPLETED,
                    Task.success_score >= 0.7,
                    Task.created_at >= datetime.utcnow() - timedelta(days=180)
                )
            )

            result = await session.execute(query)
            tasks = result.scalars().all()

            # Filter tasks by domain relevance
            domain_patterns = []
            seen_patterns = set()

            for task in tasks:
                task_text = f"{task.title} {task.description}".lower()

                # Check if task matches domain keywords
                keyword_matches = sum(1 for kw in domain_keywords if kw.lower() in task_text)

                if keyword_matches >= 1 and task.pattern_category:
                    pattern_key = f"{task.pattern_category}_{task.project_id}"

                    if pattern_key not in seen_patterns:
                        domain_patterns.append({
                            "pattern_name": task.pattern_category,
                            "description": task.description or "",
                            "success_score": task.success_score or 0,
                            "technologies": task.technologies or [],
                            "effort_minutes": task.estimated_effort_minutes or 0,
                            "task_id": str(task.task_id),
                            "project_id": str(task.project_id)
                        })
                        seen_patterns.add(pattern_key)

            return domain_patterns[:20]  # Limit to 20 patterns per domain

        except Exception as e:
            logger.error(f"Error loading domain patterns: {e}")
            return []

    async def get_library_by_domain(
        self,
        session: AsyncSession,
        domain_key: str
    ) -> Optional[DomainPatternLibrary]:
        """Get a domain pattern library by domain key"""
        try:
            # Initialize if not already done
            if not self.libraries:
                await self.initialize_default_libraries(session)

            return self.libraries.get(domain_key)

        except Exception as e:
            logger.error(f"Error getting library by domain: {e}")
            return None

    async def get_all_libraries(self, session: AsyncSession) -> Dict[str, DomainPatternLibrary]:
        """Get all domain pattern libraries"""
        try:
            if not self.libraries:
                await self.initialize_default_libraries(session)
            return self.libraries

        except Exception as e:
            logger.error(f"Error getting all libraries: {e}")
            return {}

    async def search_patterns_in_domain(
        self,
        session: AsyncSession,
        domain_key: str,
        query: str
    ) -> List[Dict[str, Any]]:
        """Search for patterns within a specific domain"""
        try:
            library = await self.get_library_by_domain(session, domain_key)
            if not library:
                return []

            query_lower = query.lower()
            results = []

            for pattern in library.patterns:
                # Score based on keyword matching
                pattern_text = f"{pattern['pattern_name']} {pattern['description']}".lower()

                if query_lower in pattern_text:
                    # Calculate relevance score
                    relevance = self._calculate_relevance_score(query_lower, pattern_text)

                    results.append({
                        **pattern,
                        "relevance_score": relevance
                    })

            # Sort by relevance
            results.sort(key=lambda r: r["relevance_score"], reverse=True)

            return results[:10]

        except Exception as e:
            logger.error(f"Error searching patterns: {e}")
            return []

    def _calculate_relevance_score(self, query: str, text: str) -> float:
        """Calculate relevance score for pattern search"""
        query_words = set(query.split())
        text_words = set(text.split())

        if not query_words or not text_words:
            return 0.0

        overlap = len(query_words & text_words)
        union = len(query_words | text_words)

        return overlap / union if union > 0 else 0.0

    async def get_patterns_by_complexity(
        self,
        session: AsyncSession,
        domain_key: str,
        complexity_level: str
    ) -> List[Dict[str, Any]]:
        """Get patterns in a domain filtered by complexity level"""
        try:
            library = await self.get_library_by_domain(session, domain_key)
            if not library:
                return []

            # For now, use success score as proxy for difficulty
            # Higher success = easier
            if complexity_level == "Easy":
                return [p for p in library.patterns if p.get("success_score", 0) >= 0.8]
            elif complexity_level == "Medium":
                return [p for p in library.patterns if 0.6 <= p.get("success_score", 0) < 0.8]
            else:  # Hard
                return [p for p in library.patterns if p.get("success_score", 0) < 0.6]

        except Exception as e:
            logger.error(f"Error getting patterns by complexity: {e}")
            return []

    async def get_patterns_by_technology(
        self,
        session: AsyncSession,
        domain_key: str,
        technology: str
    ) -> List[Dict[str, Any]]:
        """Get patterns in a domain using specific technology"""
        try:
            library = await self.get_library_by_domain(session, domain_key)
            if not library:
                return []

            tech_lower = technology.lower()
            results = []

            for pattern in library.patterns:
                techs = [t.lower() for t in pattern.get("technologies", [])]
                if any(tech_lower in t for t in techs):
                    results.append(pattern)

            return results

        except Exception as e:
            logger.error(f"Error getting patterns by technology: {e}")
            return []

    async def get_library_statistics(
        self,
        session: AsyncSession,
        domain_key: str
    ) -> Dict[str, Any]:
        """Get statistics for a domain library"""
        try:
            library = await self.get_library_by_domain(session, domain_key)
            if not library:
                return {}

            if not library.patterns:
                return {
                    "domain": domain_key,
                    "domain_name": library.domain_name,
                    "pattern_count": 0,
                    "average_success_rate": 0,
                    "technologies": library.technology_focus
                }

            avg_success = sum(p.get("success_score", 0) for p in library.patterns) / len(library.patterns)
            all_techs = set()
            for pattern in library.patterns:
                all_techs.update(pattern.get("technologies", []))

            # Group patterns by complexity
            easy = sum(1 for p in library.patterns if p.get("success_score", 0) >= 0.8)
            medium = sum(1 for p in library.patterns if 0.6 <= p.get("success_score", 0) < 0.8)
            hard = sum(1 for p in library.patterns if p.get("success_score", 0) < 0.6)

            return {
                "domain": domain_key,
                "domain_name": library.domain_name,
                "description": library.description,
                "pattern_count": len(library.patterns),
                "average_success_rate": avg_success,
                "difficulty_distribution": {
                    "easy": easy,
                    "medium": medium,
                    "hard": hard
                },
                "technologies_used": list(all_techs),
                "keywords": library.keywords,
                "updated_at": library.updated_at.isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting library statistics: {e}")
            return {}

    async def get_all_library_statistics(
        self,
        session: AsyncSession
    ) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all domain libraries"""
        try:
            if not self.libraries:
                await self.initialize_default_libraries(session)

            stats = {}
            for domain_key in self.libraries.keys():
                stats[domain_key] = await self.get_library_statistics(session, domain_key)

            return stats

        except Exception as e:
            logger.error(f"Error getting all library statistics: {e}")
            return {}

    async def recommend_domains_for_project(
        self,
        session: AsyncSession,
        project_name: str,
        project_description: str
    ) -> List[Dict[str, Any]]:
        """Recommend domain libraries for a project"""
        try:
            if not self.libraries:
                await self.initialize_default_libraries(session)

            project_text = f"{project_name} {project_description}".lower()
            recommendations = []

            for domain_key, library in self.libraries.items():
                # Score based on keyword match
                keywords_lower = [k.lower() for k in library.keywords]
                keyword_matches = sum(1 for kw in keywords_lower if kw in project_text)

                if keyword_matches > 0:
                    relevance_score = keyword_matches / len(keywords_lower)

                    recommendations.append({
                        "domain": domain_key,
                        "domain_name": library.domain_name,
                        "description": library.description,
                        "relevance_score": relevance_score,
                        "keywords": library.keywords,
                        "pattern_count": len(library.patterns)
                    })

            # Sort by relevance
            recommendations.sort(key=lambda r: r["relevance_score"], reverse=True)

            return recommendations

        except Exception as e:
            logger.error(f"Error recommending domains: {e}")
            return []


# Singleton instance
_domain_pattern_library_service: Optional[DomainPatternLibraryService] = None


def get_domain_pattern_library_service() -> DomainPatternLibraryService:
    """Get or create the domain pattern library service singleton"""
    global _domain_pattern_library_service
    if _domain_pattern_library_service is None:
        _domain_pattern_library_service = DomainPatternLibraryService()
    return _domain_pattern_library_service
