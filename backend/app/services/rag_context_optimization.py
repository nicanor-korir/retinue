"""
Context optimization service for RAG (Phase 3).

Purpose: Optimize retrieved context for LLM consumption:
1. Smart summarization - Compress long content
2. Token budget management - Stay within limits
3. Relevance prioritization - Show most relevant first
4. Deduplication - Remove redundant information
5. Formatting optimization - Better LLM parsing
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ContentPriority(str, Enum):
    """Priority levels for content."""
    CRITICAL = "critical"      # Must include (>0.9 relevance)
    HIGH = "high"              # Should include (0.7-0.9 relevance)
    MEDIUM = "medium"          # Can include (0.5-0.7 relevance)
    LOW = "low"                # Optional (<0.5 relevance)


@dataclass
class OptimizedContent:
    """Optimized content for LLM."""
    original_text: str
    optimized_text: str
    summary: Optional[str]
    token_estimate: int
    compression_ratio: float
    removed_count: int
    priority: ContentPriority


class ContentSummarizer:
    """Summarizes long content while preserving key information."""

    def __init__(self):
        """Initialize the summarizer."""
        self.key_indicators = {
            "technical": [
                "function", "method", "class", "api", "endpoint",
                "algorithm", "implementation", "pattern", "approach"
            ],
            "decision": [
                "decided", "decision", "chosen", "rationale", "reason",
                "because", "instead", "recommend", "should"
            ],
            "problem": [
                "error", "bug", "issue", "problem", "crash",
                "fail", "fails", "failing", "fix", "solution"
            ],
            "best_practice": [
                "best", "practice", "pattern", "standard",
                "convention", "should", "must", "recommended"
            ],
        }

    def extract_key_sentences(
        self,
        text: str,
        target_sentences: int = 3,
    ) -> List[str]:
        """
        Extract key sentences from text.

        Args:
            text: Input text
            target_sentences: Number of key sentences to extract

        Returns:
            List of key sentences
        """
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) <= target_sentences:
            return sentences

        # Score sentences
        scored = []
        for i, sentence in enumerate(sentences):
            score = self._score_sentence(sentence)
            # Boost early sentences (they're often important)
            if i < len(sentences) * 0.3:
                score *= 1.2
            scored.append((sentence, score))

        # Get top sentences in order
        top = sorted(scored, key=lambda x: x[1], reverse=True)[:target_sentences]
        top = sorted(top, key=lambda x: sentences.index(x[0]))

        return [s[0] for s in top]

    def _score_sentence(self, sentence: str) -> float:
        """Score a sentence for importance."""
        score = 0.0
        lower_sentence = sentence.lower()

        # Check for key indicators
        for category, indicators in self.key_indicators.items():
            matches = sum(1 for ind in indicators if ind in lower_sentence)
            score += matches * 0.3

        # Reward length (but not too long)
        word_count = len(sentence.split())
        if 5 <= word_count <= 25:
            score += 0.5
        elif word_count < 5:
            score -= 0.3

        # Check for proper nouns (capitalized words)
        caps_words = len([w for w in sentence.split() if w[0].isupper()])
        score += min(caps_words * 0.1, 0.5)

        return score

    def summarize(
        self,
        text: str,
        target_length: int = 150,
    ) -> str:
        """
        Summarize text to approximately target length.

        Args:
            text: Text to summarize
            target_length: Target character length

        Returns:
            Summarized text
        """
        if len(text) <= target_length:
            return text

        # Extract key sentences
        target_sentences = max(2, target_length // 50)
        key_sentences = self.extract_key_sentences(text, target_sentences)

        summary = " ".join(key_sentences)

        # Ensure we're near target
        if len(summary) > target_length * 1.5:
            # Try with fewer sentences
            key_sentences = self.extract_key_sentences(
                text,
                max(1, target_sentences - 1)
            )
            summary = " ".join(key_sentences)

        return summary


class ContextOptimizer:
    """
    Optimizes retrieved context for LLM consumption.

    Features:
    - Smart summarization
    - Token budget management
    - Relevance prioritization
    - Deduplication
    - Formatting optimization
    """

    def __init__(self):
        """Initialize the context optimizer."""
        self.summarizer = ContentSummarizer()
        self.enabled = True

    async def optimize_context(
        self,
        results: Dict[str, Any],
        max_tokens: int = 4000,
        preserve_structure: bool = True,
    ) -> Dict[str, Any]:
        """
        Optimize retrieved context for LLM.

        Args:
            results: Retrieved results from RAG
            max_tokens: Maximum tokens for context
            preserve_structure: Keep section structure

        Returns:
            Optimized context
        """
        try:
            if not self.enabled or not results:
                return results

            optimized = {
                "_optimization": {
                    "original_tokens": self._estimate_tokens(str(results)),
                    "max_tokens": max_tokens,
                    "compression_ratio": 0.0,
                    "sections_optimized": 0,
                }
            }

            # Estimate tokens available per section
            section_count = len([k for k in results.keys() if k != "_enhancement"])
            tokens_per_section = max_tokens // section_count if section_count > 0 else max_tokens

            # Process each collection
            for collection_name, items in results.items():
                if collection_name.startswith("_"):
                    optimized[collection_name] = items
                    continue

                if not items or not items.get("documents"):
                    optimized[collection_name] = items
                    continue

                # Optimize this collection
                optimized[collection_name] = await self._optimize_collection(
                    collection_name,
                    items,
                    tokens_per_section,
                )
                optimized["_optimization"]["sections_optimized"] += 1

            # Calculate overall compression
            optimized_tokens = self._estimate_tokens(str(optimized))
            original_tokens = optimized["_optimization"]["original_tokens"]
            optimized["_optimization"]["optimized_tokens"] = optimized_tokens
            if original_tokens > 0:
                optimized["_optimization"]["compression_ratio"] = (
                    1 - optimized_tokens / original_tokens
                )

            logger.debug(f"Optimized context: {optimized['_optimization']['compression_ratio']:.1%} reduction")
            return optimized

        except Exception as e:
            logger.error(f"Error optimizing context: {e}")
            return results

    async def _optimize_collection(
        self,
        collection_name: str,
        items: Dict[str, Any],
        max_tokens: int,
    ) -> Dict[str, Any]:
        """Optimize a single collection."""
        try:
            documents = items.get("documents", [])
            metadatas = items.get("metadatas", [])
            scores = items.get("scores", [])

            if not documents:
                return items

            # Group by relevance
            grouped = self._group_by_relevance(
                documents, metadatas, scores
            )

            optimized_docs = []
            optimized_meta = []
            optimized_scores = []
            current_tokens = 0

            # Add documents by priority
            for priority, docs_data in grouped:
                for doc, meta, score in docs_data:
                    doc_tokens = self._estimate_tokens(doc)

                    # Check if we can add this
                    if current_tokens + doc_tokens > max_tokens:
                        # Try to summarize instead
                        if priority in [ContentPriority.HIGH, ContentPriority.CRITICAL]:
                            summary = self.summarizer.summarize(
                                doc,
                                target_length=max_tokens - current_tokens
                            )
                            doc_tokens = self._estimate_tokens(summary)
                            if current_tokens + doc_tokens <= max_tokens:
                                optimized_docs.append(summary)
                                optimized_meta.append({**meta, "_summarized": True})
                                optimized_scores.append(score)
                                current_tokens += doc_tokens
                        # Skip if can't fit
                        continue

                    optimized_docs.append(doc)
                    optimized_meta.append({**meta, "_summarized": False})
                    optimized_scores.append(score)
                    current_tokens += doc_tokens

            return {
                "documents": optimized_docs,
                "metadatas": optimized_meta,
                "scores": optimized_scores,
                "ids": items.get("ids", [])[:len(optimized_docs)],
            }

        except Exception as e:
            logger.error(f"Error optimizing collection {collection_name}: {e}")
            return items

    def _group_by_relevance(
        self,
        documents: List[str],
        metadatas: List[Dict],
        scores: List[float],
    ) -> List[Tuple[ContentPriority, List[Tuple[str, Dict, float]]]]:
        """Group documents by relevance priority."""
        grouped = {
            ContentPriority.CRITICAL: [],
            ContentPriority.HIGH: [],
            ContentPriority.MEDIUM: [],
            ContentPriority.LOW: [],
        }

        for doc, meta, score in zip(documents, metadatas, scores):
            if score >= 0.9:
                priority = ContentPriority.CRITICAL
            elif score >= 0.7:
                priority = ContentPriority.HIGH
            elif score >= 0.5:
                priority = ContentPriority.MEDIUM
            else:
                priority = ContentPriority.LOW

            grouped[priority].append((doc, meta, score))

        # Return in priority order
        return [
            (ContentPriority.CRITICAL, grouped[ContentPriority.CRITICAL]),
            (ContentPriority.HIGH, grouped[ContentPriority.HIGH]),
            (ContentPriority.MEDIUM, grouped[ContentPriority.MEDIUM]),
            (ContentPriority.LOW, grouped[ContentPriority.LOW]),
        ]

    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count (rough approximation).

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        # Rough estimate: 1 token ≈ 4 characters
        # This is conservative for actual LLM usage
        return max(1, len(text) // 4)

    def _remove_duplicates(
        self,
        documents: List[str],
        metadatas: List[Dict],
    ) -> Tuple[List[str], List[Dict]]:
        """Remove duplicate documents."""
        seen = set()
        unique_docs = []
        unique_meta = []

        for doc, meta in zip(documents, metadatas):
            # Normalize for comparison
            doc_key = doc.strip().lower()[:100]

            if doc_key not in seen:
                seen.add(doc_key)
                unique_docs.append(doc)
                unique_meta.append(meta)

        return unique_docs, unique_meta

    def get_optimization_stats(
        self,
        original_tokens: int,
        optimized_tokens: int,
    ) -> Dict[str, Any]:
        """Get optimization statistics."""
        if original_tokens == 0:
            return {"compression_ratio": 0.0}

        return {
            "original_tokens": original_tokens,
            "optimized_tokens": optimized_tokens,
            "tokens_saved": original_tokens - optimized_tokens,
            "compression_ratio": 1 - optimized_tokens / original_tokens,
        }


# Global instance
_context_optimizer: Optional[ContextOptimizer] = None


def get_context_optimizer() -> ContextOptimizer:
    """Get or create the context optimizer singleton."""
    global _context_optimizer
    if _context_optimizer is None:
        _context_optimizer = ContextOptimizer()
    return _context_optimizer
