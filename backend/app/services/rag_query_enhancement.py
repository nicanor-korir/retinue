"""
Query enhancement service for Phase 3 RAG optimization.

Purpose: Improve RAG query effectiveness through:
1. Query Classification - Identify query type and domain
2. Query Expansion - Add related terms and context
3. Intent Extraction - Understand user intent
4. Query Normalization - Standardize query format
"""

import logging
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class QueryType(str, Enum):
    """Classification of query types."""
    TECHNICAL = "technical"
    ARCHITECTURAL = "architectural"
    IMPLEMENTATION = "implementation"
    DEBUGGING = "debugging"
    PERFORMANCE = "performance"
    SECURITY = "security"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    PLANNING = "planning"
    DECISION = "decision"
    REVIEW = "review"
    OTHER = "other"


class QueryDomain(str, Enum):
    """Domain classification of queries."""
    BACKEND = "backend"
    FRONTEND = "frontend"
    DEVOPS = "devops"
    DATABASE = "database"
    API = "api"
    AUTH = "auth"
    UI_UX = "ui_ux"
    ARCHITECTURE = "architecture"
    PROCESS = "process"
    GENERAL = "general"


@dataclass
class EnhancedQuery:
    """Result of query enhancement."""
    original_query: str
    normalized_query: str
    query_type: QueryType
    query_domain: QueryDomain
    intent: str
    keywords: List[str]
    expanded_terms: List[str]
    confidence: float


class QueryEnhancementService:
    """
    Service for enhancing RAG queries to improve retrieval effectiveness.

    Features:
    - Query type classification
    - Domain detection
    - Intent extraction
    - Query expansion with synonyms
    - Keyword extraction
    - Query normalization
    """

    def __init__(self):
        """Initialize the query enhancement service."""
        self.enabled = True
        self._setup_keyword_mappings()

    def _setup_keyword_mappings(self):
        """Setup keyword mappings for expansion and classification."""
        # Technical keywords by type
        self.technical_keywords = {
            "api": ["endpoint", "route", "request", "response", "method", "protocol", "rest", "http"],
            "database": ["query", "schema", "migration", "index", "cache", "transaction", "sql"],
            "auth": ["authentication", "authorization", "login", "token", "jwt", "password", "permission"],
            "performance": ["optimization", "speed", "latency", "cache", "memory", "cpu", "load"],
            "security": ["vulnerability", "exploit", "encryption", "ssl", "tls", "attack", "defense"],
            "testing": ["test", "unit", "integration", "e2e", "coverage", "mock", "stub"],
        }

        # Domain keywords
        self.domain_keywords = {
            "backend": ["server", "api", "database", "service", "microservice", "queue", "worker"],
            "frontend": ["ui", "component", "react", "vue", "angular", "css", "html", "button"],
            "devops": ["deployment", "container", "docker", "kubernetes", "ci/cd", "pipeline"],
            "database": ["sql", "nosql", "query", "schema", "migration", "orm"],
            "auth": ["login", "password", "token", "permission", "role", "access"],
            "ui_ux": ["design", "layout", "interaction", "accessibility", "responsive"],
        }

        # Query type indicators
        self.query_type_indicators = {
            "debugging": ["bug", "error", "issue", "problem", "crash", "fail", "debug"],
            "performance": ["slow", "optimize", "latency", "throughput", "cache", "memory"],
            "security": ["secure", "vulnerability", "encrypt", "attack", "defense", "token"],
            "testing": ["test", "coverage", "mock", "stub", "fixture", "assertion"],
            "decision": ["should", "best", "recommend", "approach", "pattern", "practice"],
            "review": ["review", "approve", "check", "validate", "verify", "audit"],
        }

        # Synonym mappings for expansion
        self.synonym_mappings = {
            "api": ["endpoint", "service", "route", "interface"],
            "database": ["db", "storage", "persistence", "datastore"],
            "authentication": ["auth", "login", "identity"],
            "optimization": ["performance", "efficiency", "speed"],
            "bug": ["error", "issue", "defect", "problem"],
            "security": ["protection", "defense", "safety"],
            "code": ["implementation", "source", "script"],
            "documentation": ["docs", "guide", "readme"],
        }

    async def enhance_query(
        self,
        query: str,
        agent_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> EnhancedQuery:
        """
        Enhance a query for better RAG retrieval.

        Args:
            query: Original user query
            agent_id: Optional agent ID for context
            project_id: Optional project ID for context

        Returns:
            Enhanced query with metadata
        """
        try:
            # Normalize query
            normalized = self._normalize_query(query)

            # Extract keywords
            keywords = self._extract_keywords(normalized)

            # Classify query type
            query_type = self._classify_query_type(normalized, keywords)

            # Detect domain
            query_domain = self._detect_domain(normalized, keywords, agent_id)

            # Extract intent
            intent = self._extract_intent(normalized, query_type)

            # Expand query with synonyms
            expanded_terms = self._expand_query(normalized, keywords)

            # Calculate confidence
            confidence = self._calculate_confidence(keywords, query_type, query_domain)

            enhanced = EnhancedQuery(
                original_query=query,
                normalized_query=normalized,
                query_type=query_type,
                query_domain=query_domain,
                intent=intent,
                keywords=keywords,
                expanded_terms=expanded_terms,
                confidence=confidence,
            )

            logger.debug(
                f"Enhanced query: type={query_type.value}, domain={query_domain.value}, "
                f"confidence={confidence:.2f}"
            )

            return enhanced

        except Exception as e:
            logger.error(f"Error enhancing query: {e}")
            # Return basic enhanced query on error
            return EnhancedQuery(
                original_query=query,
                normalized_query=self._normalize_query(query),
                query_type=QueryType.OTHER,
                query_domain=QueryDomain.GENERAL,
                intent="general_question",
                keywords=self._extract_keywords(query),
                expanded_terms=[],
                confidence=0.5,
            )

    def _normalize_query(self, query: str) -> str:
        """
        Normalize query for consistent processing.

        Args:
            query: Raw query string

        Returns:
            Normalized query
        """
        # Convert to lowercase
        normalized = query.lower().strip()

        # Remove extra whitespace
        normalized = " ".join(normalized.split())

        # Remove punctuation except spaces
        normalized = re.sub(r"[^\w\s\-]", " ", normalized)

        # Remove duplicate spaces
        normalized = " ".join(normalized.split())

        return normalized

    def _extract_keywords(self, query: str) -> List[str]:
        """
        Extract important keywords from query.

        Args:
            query: Normalized query

        Returns:
            List of keywords
        """
        # Split into words
        words = query.split()

        # Filter stop words
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "is", "are", "was", "were", "be", "been", "how", "what",
            "when", "where", "why", "which", "who", "by", "from", "as", "if"
        }

        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        return keywords

    def _classify_query_type(self, query: str, keywords: List[str]) -> QueryType:
        """
        Classify the type of query.

        Args:
            query: Normalized query
            keywords: Extracted keywords

        Returns:
            Query type
        """
        # Check for specific indicators
        for query_type, indicators in self.query_type_indicators.items():
            if any(ind in query for ind in indicators):
                return QueryType(query_type)

        # Check if question about implementation
        if any(word in query for word in ["how", "implement", "build", "create", "write"]):
            return QueryType.IMPLEMENTATION

        # Check if architectural question
        if any(word in query for word in ["architecture", "design", "pattern", "structure"]):
            return QueryType.ARCHITECTURAL

        # Default
        return QueryType.TECHNICAL

    def _detect_domain(
        self,
        query: str,
        keywords: List[str],
        agent_id: Optional[str] = None,
    ) -> QueryDomain:
        """
        Detect the domain of the query.

        Args:
            query: Normalized query
            keywords: Extracted keywords
            agent_id: Optional agent ID for context

        Returns:
            Query domain
        """
        # Score each domain based on keyword matches
        domain_scores = {domain: 0 for domain in QueryDomain}

        for domain_name, domain_kws in self.domain_keywords.items():
            for keyword in keywords:
                if keyword in domain_kws or any(keyword.startswith(kw) for kw in domain_kws):
                    domain_scores[domain_name] += 1

        # Use agent ID as hint
        if agent_id:
            if "frontend" in agent_id.lower():
                domain_scores["frontend"] += 2
            elif "backend" in agent_id.lower():
                domain_scores["backend"] += 2
            elif "designer" in agent_id.lower():
                domain_scores["ui_ux"] += 2

        # Find best matching domain
        best_domain = max(domain_scores, key=domain_scores.get)
        return QueryDomain(best_domain)

    def _extract_intent(self, query: str, query_type: QueryType) -> str:
        """
        Extract the intent of the query.

        Args:
            query: Normalized query
            query_type: Classified query type

        Returns:
            Intent description
        """
        intents = {
            QueryType.DEBUGGING: "troubleshoot_issue",
            QueryType.PERFORMANCE: "optimize_system",
            QueryType.SECURITY: "improve_security",
            QueryType.TESTING: "improve_testing",
            QueryType.DECISION: "make_decision",
            QueryType.REVIEW: "review_code",
            QueryType.DOCUMENTATION: "understand_feature",
            QueryType.IMPLEMENTATION: "implement_feature",
            QueryType.ARCHITECTURAL: "design_system",
            QueryType.TECHNICAL: "solve_technical_problem",
            QueryType.PLANNING: "plan_work",
        }

        return intents.get(query_type, "general_inquiry")

    def _expand_query(self, query: str, keywords: List[str]) -> List[str]:
        """
        Expand query with related terms.

        Args:
            query: Normalized query
            keywords: Extracted keywords

        Returns:
            List of expanded terms
        """
        expanded = []

        # Add synonyms for each keyword
        for keyword in keywords:
            # Check if keyword has synonyms
            if keyword in self.synonym_mappings:
                expanded.extend(self.synonym_mappings[keyword])
            else:
                # Check if keyword contains substring with synonyms
                for mapped_word, synonyms in self.synonym_mappings.items():
                    if mapped_word in keyword or keyword in mapped_word:
                        expanded.extend(synonyms)
                        break

        # Remove duplicates and original keywords
        expanded = list(set(expanded) - set(keywords))

        # Limit to 10 most relevant
        return expanded[:10]

    def _calculate_confidence(
        self,
        keywords: List[str],
        query_type: QueryType,
        query_domain: QueryDomain,
    ) -> float:
        """
        Calculate confidence in the enhancement.

        Args:
            keywords: Extracted keywords
            query_type: Classified type
            query_domain: Detected domain

        Returns:
            Confidence score (0-1)
        """
        confidence = 0.5

        # More keywords = higher confidence
        if len(keywords) >= 3:
            confidence += 0.2
        elif len(keywords) >= 1:
            confidence += 0.1

        # Specific type = higher confidence
        if query_type != QueryType.OTHER:
            confidence += 0.15

        # Specific domain = higher confidence
        if query_domain != QueryDomain.GENERAL:
            confidence += 0.15

        # Cap at 1.0
        return min(confidence, 1.0)

    async def build_enhanced_search_query(
        self,
        enhanced: EnhancedQuery,
    ) -> str:
        """
        Build optimized search query from enhancement.

        Args:
            enhanced: Enhanced query data

        Returns:
            Optimized query string for RAG search
        """
        # Combine original, normalized, and expanded terms
        parts = [
            enhanced.normalized_query,
        ]

        # Add important keywords
        if enhanced.keywords:
            parts.append(" ".join(enhanced.keywords[:5]))

        # Add expanded terms for high confidence
        if enhanced.confidence > 0.7 and enhanced.expanded_terms:
            parts.append(" ".join(enhanced.expanded_terms[:3]))

        # Combine with weights
        search_query = " ".join(parts)

        logger.debug(f"Built search query: {search_query[:100]}...")

        return search_query


# Global instance
_query_enhancement_service: Optional[QueryEnhancementService] = None


def get_query_enhancement_service() -> QueryEnhancementService:
    """Get or create the query enhancement service singleton."""
    global _query_enhancement_service
    if _query_enhancement_service is None:
        _query_enhancement_service = QueryEnhancementService()
    return _query_enhancement_service
