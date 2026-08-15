"""
Knowledge Processing Pipeline

Processes, enriches, categorizes, and validates extracted knowledge.
Implements the processing pipeline from INTELLIGENT_KNOWLEDGE_BASE.md including:
- Content normalization and structuring
- Enrichment with context and metadata
- Relationship mapping
- Auto-tagging and categorization
- Quality validation
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime
from uuid import UUID
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from anthropic import AsyncAnthropic

from app.db.knowledge_models import (
    ExtractionCandidate,
    KnowledgeEntry,
    KnowledgeRelationship,
    KnowledgeCategory,
    KnowledgeVersion,
    KnowledgeEntryType,
    ValidationStatus,
    KnowledgeStatus,
    RelationshipType
)
from app.services.rag_embedding_service import get_embedding_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class KnowledgeProcessingService:
    """
    Service for processing and enriching extracted knowledge.
    """

    def __init__(self):
        """Initialize the knowledge processing service."""
        self.embedding_service = get_embedding_service()
        self.anthropic_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.processing_model = settings.DEFAULT_LLM_MODEL

    # ===== CANDIDATE CONVERSION =====

    async def convert_candidate_to_entry(
        self,
        db: AsyncSession,
        candidate: ExtractionCandidate
    ) -> Optional[KnowledgeEntry]:
        """
        Convert an approved extraction candidate to a knowledge entry.

        Args:
            db: Database session
            candidate: Approved extraction candidate

        Returns:
            Created KnowledgeEntry or None
        """
        try:
            # Extract data from candidate
            content_data = candidate.extracted_content

            # Normalize and clean content
            normalized = await self._normalize_content(content_data)

            # Generate embeddings
            embeddings = await self._generate_embeddings(normalized)

            # Auto-tag
            tags = await self._auto_tag_content(normalized)

            # Categorize
            category_id = await self._categorize_content(db, normalized, tags)

            # Create knowledge entry
            entry = KnowledgeEntry(
                title=normalized["title"],
                summary=normalized["summary"],
                content=normalized["content"],
                content_format="markdown",
                content_structured=normalized.get("structured", {}),
                entry_type=candidate.extraction_type,
                primary_category_id=category_id,
                tags=tags,
                keywords=self._extract_keywords(normalized["content"]),
                domain=self._determine_domain(tags),
                confidence_score=candidate.confidence_score,
                novelty_score=candidate.novelty_score,
                relevance_score=candidate.relevance_score,
                quality_score=candidate.extraction_quality,
                problem_context=normalized.get("problem_context"),
                applicable_scenarios=normalized.get("applicable_scenarios", []),
                prerequisites=normalized.get("prerequisites", []),
                limitations=normalized.get("limitations", []),
                related_technologies=normalized.get("related_technologies", []),
                validation_status=ValidationStatus.UNVALIDATED,
                source_type="conversation" if candidate.conversation_id else "project",
                source_conversation_id=candidate.conversation_id,
                source_project_id=candidate.project_id,
                source_task_id=candidate.task_id,
                source_message_ids=content_data.get("message_ids", []),
                created_by_type="system",
                created_by_id="extraction_engine",
                status=KnowledgeStatus.ACTIVE,
                version=1,
                title_embedding=embeddings["title"],
                summary_embedding=embeddings["summary"],
                content_embedding=embeddings["content"],
                problem_embedding=embeddings.get("problem")
            )

            db.add(entry)
            await db.commit()
            await db.refresh(entry)

            # Create version record
            await self._create_version_record(db, entry, "created", "Initial extraction")

            # Auto-discover relationships
            await self._discover_relationships(db, entry)

            logger.info(f"Converted candidate {candidate.candidate_id} to entry {entry.entry_id}")

            return entry

        except Exception as e:
            logger.error(f"Error converting candidate to entry: {e}", exc_info=True)
            await db.rollback()
            return None

    # ===== CONTENT NORMALIZATION =====

    async def _normalize_content(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize and clean extracted content.

        Args:
            content_data: Raw extracted content

        Returns:
            Normalized content dict
        """
        normalized = {
            "title": self._clean_title(content_data.get("title", "")),
            "summary": self._clean_text(content_data.get("summary", "")),
            "content": self._clean_and_decontextualize(content_data.get("content", "")),
            "problem_context": self._clean_text(content_data.get("problem_context", "")),
            "applicable_scenarios": content_data.get("applicable_scenarios", []),
            "prerequisites": content_data.get("prerequisites", []),
            "limitations": content_data.get("limitations", []),
            "related_technologies": content_data.get("related_technologies", [])
        }

        return normalized

    def _clean_title(self, title: str) -> str:
        """Clean and normalize title."""
        # Remove conversational artifacts
        title = re.sub(r'\b(um|uh|well|so|like)\b', '', title, flags=re.IGNORECASE)
        # Remove extra whitespace
        title = re.sub(r'\s+', ' ', title).strip()
        # Capitalize first letter
        if title:
            title = title[0].upper() + title[1:]
        # Limit length
        return title[:500]

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""

        # Remove conversational artifacts
        text = re.sub(r'\b(um|uh|well|so|basically|actually)\b', '', text, flags=re.IGNORECASE)
        # Fix obvious typos (simple cases)
        text = re.sub(r'(\w)\1{2,}', r'\1\1', text)  # Remove triple+ repeated chars
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def _clean_and_decontextualize(self, content: str) -> str:
        """
        Clean content and make it standalone by resolving references.

        Args:
            content: Raw content with potential context dependencies

        Returns:
            Decontextualized content
        """
        if not content:
            return ""

        # Clean basic artifacts
        content = self._clean_text(content)

        # Resolve common pronouns and references (simple heuristics)
        # This would ideally use more sophisticated NLP
        content = re.sub(r'\bthis approach\b', 'the described approach', content, flags=re.IGNORECASE)
        content = re.sub(r'\bthat method\b', 'the mentioned method', content, flags=re.IGNORECASE)

        return content

    # ===== EMBEDDING GENERATION =====

    async def _generate_embeddings(self, normalized: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate embeddings for different content fields.

        Args:
            normalized: Normalized content

        Returns:
            Dict of embeddings
        """
        embeddings = {}

        # Title embedding
        if normalized["title"]:
            embeddings["title"] = await self.embedding_service.embed_text(normalized["title"])

        # Summary embedding
        if normalized["summary"]:
            embeddings["summary"] = await self.embedding_service.embed_text(normalized["summary"])

        # Full content embedding
        if normalized["content"]:
            embeddings["content"] = await self.embedding_service.embed_text(normalized["content"])

        # Problem context embedding (for problem-solution matching)
        if normalized.get("problem_context"):
            embeddings["problem"] = await self.embedding_service.embed_text(normalized["problem_context"])

        return embeddings

    # ===== AUTO-TAGGING =====

    async def _auto_tag_content(self, normalized: Dict[str, Any]) -> List[str]:
        """
        Automatically generate tags for content.

        Args:
            normalized: Normalized content

        Returns:
            List of tags
        """
        try:
            # Combine content for analysis
            combined_text = f"{normalized['title']} {normalized['summary']} {normalized['content']}"

            # Use LLM to extract tags
            tagging_prompt = f"""
Analyze this knowledge content and generate relevant tags.

CONTENT:
Title: {normalized['title']}
Summary: {normalized['summary']}
Full Content: {normalized['content'][:1000]}...

Generate 5-10 relevant tags that:
1. Capture key concepts and topics
2. Include technical terms and technologies
3. Describe the knowledge type/category
4. Are searchable and specific

Return only the tags as a comma-separated list, lowercase, no special characters.
Example: authentication, jwt, api, security, best-practice
"""

            response = await self.anthropic_client.messages.create(
                model=self.processing_model,
                max_tokens=200,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": tagging_prompt}
                ]
            )

            tags_text = response.content[0].text.strip()
            tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]

            # Add domain-specific tags
            tags.extend(self._extract_technical_tags(combined_text))

            # Deduplicate and normalize
            tags = list(set(tag.lower().replace(" ", "-") for tag in tags))

            return tags[:15]  # Limit to 15 tags

        except Exception as e:
            logger.error(f"Error auto-tagging content: {e}")
            # Fallback to keyword extraction
            return self._extract_keywords(normalized["content"])[:10]

    def _extract_technical_tags(self, text: str) -> List[str]:
        """Extract technical terms as tags."""
        # Common technical patterns
        technical_patterns = [
            r'\b(api|rest|graphql|grpc)\b',
            r'\b(react|vue|angular|svelte)\b',
            r'\b(python|javascript|typescript|java|go|rust)\b',
            r'\b(postgresql|mysql|mongodb|redis)\b',
            r'\b(docker|kubernetes|aws|gcp|azure)\b',
            r'\b(authentication|authorization|jwt|oauth)\b',
            r'\b(microservice|monolith|serverless)\b',
        ]

        tags = []
        text_lower = text.lower()

        for pattern in technical_patterns:
            matches = re.findall(pattern, text_lower)
            tags.extend(matches)

        return list(set(tags))

    def _extract_keywords(self, content: str) -> List[str]:
        """Extract keywords using TF-IDF-like approach."""
        if not content:
            return []

        # Simple keyword extraction (in production, use proper NLP)
        words = re.findall(r'\b[a-z]{4,}\b', content.lower())

        # Count frequencies
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1

        # Filter common words (stop words)
        stop_words = {
            'this', 'that', 'with', 'from', 'have', 'will', 'would',
            'should', 'could', 'been', 'were', 'they', 'their', 'there'
        }

        keywords = [
            word for word, freq in sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            if word not in stop_words and freq > 1
        ]

        return keywords[:20]

    # ===== CATEGORIZATION =====

    async def _categorize_content(
        self,
        db: AsyncSession,
        normalized: Dict[str, Any],
        tags: List[str]
    ) -> Optional[UUID]:
        """
        Determine primary category for content.

        Args:
            db: Database session
            normalized: Normalized content
            tags: Generated tags

        Returns:
            Category UUID or None
        """
        try:
            # Get all categories
            query = select(KnowledgeCategory)
            result = await db.execute(query)
            categories = result.scalars().all()

            if not categories:
                return None

            # Simple matching based on tags and content
            category_scores = {}

            for category in categories:
                score = 0

                # Match category name with tags
                category_keywords = category.name.lower().split()
                for tag in tags:
                    if any(keyword in tag for keyword in category_keywords):
                        score += 2

                # Match category description with content
                if category.description:
                    desc_keywords = category.description.lower().split()
                    content_lower = normalized["content"].lower()
                    for keyword in desc_keywords[:10]:  # Top keywords
                        if keyword in content_lower:
                            score += 1

                category_scores[category.category_id] = score

            # Return category with highest score
            if category_scores:
                best_category_id = max(category_scores.items(), key=lambda x: x[1])[0]
                if category_scores[best_category_id] > 0:
                    return best_category_id

            return None

        except Exception as e:
            logger.error(f"Error categorizing content: {e}")
            return None

    def _determine_domain(self, tags: List[str]) -> str:
        """Determine domain from tags."""
        # Domain classification based on tags
        domain_keywords = {
            "technical": ["api", "code", "database", "architecture", "security", "performance"],
            "business": ["strategy", "planning", "requirements", "stakeholder", "budget"],
            "process": ["workflow", "procedure", "guideline", "standard", "policy"],
            "user": ["preference", "feedback", "communication", "experience"]
        }

        domain_scores = {domain: 0 for domain in domain_keywords.keys()}

        for tag in tags:
            for domain, keywords in domain_keywords.items():
                if any(keyword in tag for keyword in keywords):
                    domain_scores[domain] += 1

        # Return domain with highest score
        best_domain = max(domain_scores.items(), key=lambda x: x[1])
        return best_domain[0] if best_domain[1] > 0 else "general"

    # ===== RELATIONSHIP DISCOVERY =====

    async def _discover_relationships(
        self,
        db: AsyncSession,
        entry: KnowledgeEntry
    ) -> None:
        """
        Automatically discover relationships with existing knowledge.

        Args:
            db: Database session
            entry: New knowledge entry
        """
        try:
            # Find similar entries using embedding similarity
            similar_entries = await self._find_similar_entries(db, entry, top_k=10)

            for similar_entry, similarity_score in similar_entries:
                if similarity_score > 0.85:
                    # Very high similarity - might be related or alternative
                    rel_type = RelationshipType.SIMILAR_TO
                elif similarity_score > 0.7:
                    # Related content
                    rel_type = RelationshipType.RELATED_TO
                else:
                    continue  # Too low similarity

                # Create relationship
                relationship = KnowledgeRelationship(
                    source_entry_id=entry.entry_id,
                    target_entry_id=similar_entry.entry_id,
                    relationship_type=rel_type,
                    strength=similarity_score,
                    bidirectional=True,
                    auto_generated=True
                )

                db.add(relationship)

            await db.commit()

            logger.info(f"Discovered {len(similar_entries)} relationships for entry {entry.entry_id}")

        except Exception as e:
            logger.error(f"Error discovering relationships: {e}")

    async def _find_similar_entries(
        self,
        db: AsyncSession,
        entry: KnowledgeEntry,
        top_k: int = 10
    ) -> List[Tuple[KnowledgeEntry, float]]:
        """
        Find similar knowledge entries using vector similarity.

        Args:
            db: Database session
            entry: Reference entry
            top_k: Number of similar entries to return

        Returns:
            List of (entry, similarity_score) tuples
        """
        try:
            if not entry.content_embedding:
                return []

            # Use pgvector for similarity search
            # This is a simplified version - in production, use proper vector index
            query = select(KnowledgeEntry).where(
                and_(
                    KnowledgeEntry.entry_id != entry.entry_id,
                    KnowledgeEntry.status == KnowledgeStatus.ACTIVE,
                    KnowledgeEntry.content_embedding.isnot(None)
                )
            ).limit(100)  # Get candidates

            result = await db.execute(query)
            candidates = result.scalars().all()

            # Calculate similarities (cosine similarity)
            similar_entries = []
            for candidate in candidates:
                if candidate.content_embedding:
                    similarity = self._cosine_similarity(
                        entry.content_embedding,
                        candidate.content_embedding
                    )
                    if similarity > 0.6:  # Threshold
                        similar_entries.append((candidate, similarity))

            # Sort by similarity
            similar_entries.sort(key=lambda x: x[1], reverse=True)

            return similar_entries[:top_k]

        except Exception as e:
            logger.error(f"Error finding similar entries: {e}")
            return []

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import numpy as np

        # Convert to numpy arrays
        a = np.array(vec1)
        b = np.array(vec2)

        # Calculate cosine similarity
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    # ===== VERSION MANAGEMENT =====

    async def _create_version_record(
        self,
        db: AsyncSession,
        entry: KnowledgeEntry,
        change_type: str,
        change_summary: str
    ) -> None:
        """Create version record for knowledge entry."""
        try:
            version = KnowledgeVersion(
                entry_id=entry.entry_id,
                version_number=entry.version,
                title=entry.title,
                summary=entry.summary,
                content=entry.content,
                change_type=change_type,
                change_summary=change_summary,
                changed_by_type=entry.created_by_type,
                changed_by_id=entry.created_by_id
            )

            db.add(version)
            await db.commit()

        except Exception as e:
            logger.error(f"Error creating version record: {e}")

    # ===== QUALITY VALIDATION =====

    async def validate_entry_quality(
        self,
        db: AsyncSession,
        entry: KnowledgeEntry
    ) -> Dict[str, Any]:
        """
        Validate quality of knowledge entry and suggest improvements.

        Args:
            db: Database session
            entry: Knowledge entry to validate

        Returns:
            Validation results with suggestions
        """
        validation_results = {
            "is_valid": True,
            "quality_score": 0.0,
            "issues": [],
            "suggestions": []
        }

        # Check completeness
        if not entry.title or len(entry.title) < 10:
            validation_results["issues"].append("Title too short")
            validation_results["is_valid"] = False

        if not entry.summary or len(entry.summary) < 20:
            validation_results["issues"].append("Summary too brief")

        if not entry.content or len(entry.content) < 50:
            validation_results["issues"].append("Content too minimal")
            validation_results["is_valid"] = False

        if not entry.tags or len(entry.tags) < 2:
            validation_results["suggestions"].append("Add more tags for better searchability")

        # Check clarity (using simple heuristics)
        if entry.content:
            # Check for code blocks, examples
            has_examples = bool(re.search(r'```|example|for instance', entry.content, re.IGNORECASE))
            if not has_examples and entry.entry_type == KnowledgeEntryType.SOLUTION:
                validation_results["suggestions"].append("Consider adding code examples or concrete instances")

        # Calculate overall quality score
        quality_factors = []

        # Completeness (0-1)
        completeness = min(1.0, (
            (1 if entry.title and len(entry.title) >= 10 else 0) +
            (1 if entry.summary and len(entry.summary) >= 50 else 0.5) +
            (1 if entry.content and len(entry.content) >= 100 else 0.5) +
            (1 if entry.tags and len(entry.tags) >= 3 else 0.5)
        ) / 4)
        quality_factors.append(completeness)

        # Metadata richness (0-1)
        metadata_richness = min(1.0, (
            (1 if entry.problem_context else 0) +
            (1 if entry.applicable_scenarios else 0) +
            (1 if entry.prerequisites else 0) +
            (1 if entry.tags and len(entry.tags) >= 5 else 0.5)
        ) / 4)
        quality_factors.append(metadata_richness)

        # Confidence scores
        quality_factors.append(entry.confidence_score)
        quality_factors.append(entry.relevance_score)

        # Overall quality
        validation_results["quality_score"] = sum(quality_factors) / len(quality_factors)

        return validation_results

    # ===== ENRICHMENT =====

    async def enrich_entry(
        self,
        db: AsyncSession,
        entry: KnowledgeEntry
    ) -> None:
        """
        Enrich knowledge entry with additional context and metadata.

        Args:
            db: Database session
            entry: Knowledge entry to enrich
        """
        try:
            # Add prerequisite knowledge links
            await self._link_prerequisites(db, entry)

            # Add related best practices
            await self._link_best_practices(db, entry)

            # Update quality score based on usage
            await self._update_quality_score(db, entry)

            await db.commit()

        except Exception as e:
            logger.error(f"Error enriching entry {entry.entry_id}: {e}")

    async def _link_prerequisites(self, db: AsyncSession, entry: KnowledgeEntry) -> None:
        """Link prerequisite knowledge entries."""
        # Find entries that should be understood first
        # This is a simplified version
        if entry.prerequisites:
            for prereq_text in entry.prerequisites:
                # Search for matching knowledge
                # In production, use proper semantic search
                pass

    async def _link_best_practices(self, db: AsyncSession, entry: KnowledgeEntry) -> None:
        """Link related best practices."""
        # Find best practice entries in same domain
        query = select(KnowledgeEntry).where(
            and_(
                KnowledgeEntry.entry_type == KnowledgeEntryType.BEST_PRACTICE,
                KnowledgeEntry.domain == entry.domain,
                KnowledgeEntry.status == KnowledgeStatus.ACTIVE
            )
        ).limit(5)

        result = await db.execute(query)
        best_practices = result.scalars().all()

        for bp in best_practices:
            # Create relationship if not exists
            relationship = KnowledgeRelationship(
                source_entry_id=entry.entry_id,
                target_entry_id=bp.entry_id,
                relationship_type=RelationshipType.RELATED_TO,
                strength=0.6,
                auto_generated=True
            )
            db.add(relationship)

    async def _update_quality_score(self, db: AsyncSession, entry: KnowledgeEntry) -> None:
        """Update quality score based on usage metrics."""
        # Calculate dynamic quality score
        base_quality = (entry.confidence_score + entry.relevance_score) / 2

        # Adjust based on usage
        if entry.use_count > 0:
            helpfulness_ratio = entry.helpfulness_up / (entry.helpfulness_up + entry.helpfulness_down + 1)
            usage_factor = min(1.2, 1.0 + (entry.use_count / 100))  # Cap at 1.2x
            adjusted_quality = base_quality * helpfulness_ratio * usage_factor
        else:
            adjusted_quality = base_quality

        entry.quality_score = min(1.0, adjusted_quality)


# Singleton instance
_knowledge_processing_service: Optional[KnowledgeProcessingService] = None


def get_knowledge_processing_service() -> KnowledgeProcessingService:
    """Get or create singleton knowledge processing service."""
    global _knowledge_processing_service
    if _knowledge_processing_service is None:
        _knowledge_processing_service = KnowledgeProcessingService()
    return _knowledge_processing_service
