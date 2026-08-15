"""
Knowledge Extraction Engine

Automatically identifies, extracts, categorizes, and indexes valuable knowledge
from conversations, tasks, projects, and decisions. Implements the extraction
taxonomy and triggers specified in INTELLIGENT_KNOWLEDGE_BASE.md.
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from uuid import UUID
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from anthropic import AsyncAnthropic

from app.db.knowledge_models import (
    ExtractionCandidate,
    ExtractionTriggerType,
    ExtractionStatus,
    KnowledgeEntryType,
    KnowledgeEntry,
    Conversation
)
from app.db.models import Message, Task, Project, Decision, Agent
from app.services.rag_embedding_service import get_embedding_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class KnowledgeExtractionService:
    """
    Service for automatically extracting knowledge from conversations and activities.
    """

    def __init__(self):
        """Initialize the knowledge extraction service."""
        self.embedding_service = get_embedding_service()
        self.anthropic_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.extraction_model = settings.DEFAULT_LLM_MODEL

    # ===== MESSAGE-LEVEL EXTRACTION =====

    async def analyze_message(
        self,
        db: AsyncSession,
        message: Message,
        conversation_context: Optional[List[Message]] = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze a single message for knowledge extraction opportunities.

        Args:
            db: Database session
            message: Message to analyze
            conversation_context: Recent messages for context (optional)

        Returns:
            List of extraction candidates as dicts
        """
        try:
            # Skip if message is too short
            if not message.content or len(message.content.strip()) < 20:
                return []

            # Build context
            context_messages = []
            if conversation_context:
                context_messages = [
                    f"{msg.from_agent_id}: {msg.content[:200]}"
                    for msg in conversation_context[-5:]  # Last 5 messages
                ]

            # Prepare prompt for LLM
            analysis_prompt = f"""
Analyze this agent message for extractable knowledge. Identify patterns, decisions,
solutions, preferences, or insights that should be saved for future use.

MESSAGE:
From: {message.from_agent_id}
To: {message.to_agent_id}
Type: {message.message_type}
Content: {message.content}

CONTEXT (recent messages):
{chr(10).join(context_messages) if context_messages else "No prior context"}

INSTRUCTIONS:
Identify if this message contains:
1. **Solutions**: Problem-solving approaches or implementations
2. **Decisions**: Choices made with reasoning
3. **Preferences**: User or agent preferences expressed
4. **Standards**: Guidelines or best practices mentioned
5. **Lessons**: Things learned from success/failure
6. **Patterns**: Recurring approaches or methodologies
7. **Definitions**: Important concepts defined

For each extractable piece of knowledge, provide:
- type: (solution|decision|preference|standard|lesson_learned|pattern|definition)
- title: Clear, searchable title (max 100 chars)
- summary: 2-3 sentence summary
- content: Full detailed content (markdown format)
- confidence: 0.0-1.0 (how sure you are this is valuable)
- novelty: 0.0-1.0 (how unique/new this is)
- relevance: 0.0-1.0 (how broadly applicable)
- tags: List of relevant tags
- applicable_scenarios: When this knowledge applies

Return JSON array of extractions, or empty array [] if nothing extractable.
"""

            # Call LLM for analysis
            response = await self.anthropic_client.messages.create(
                model=self.extraction_model,
                max_tokens=2000,
                temperature=0.3,  # Lower temperature for structured extraction
                messages=[
                    {"role": "user", "content": analysis_prompt}
                ]
            )

            # Parse LLM response
            response_text = response.content[0].text
            extractions = self._parse_extraction_response(response_text)

            logger.info(
                f"Analyzed message {message.message_id}, "
                f"found {len(extractions)} extraction candidates"
            )

            return extractions

        except Exception as e:
            logger.error(f"Error analyzing message {message.message_id}: {e}", exc_info=True)
            return []

    def _parse_extraction_response(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Parse LLM extraction response into structured format.

        Args:
            response_text: LLM response text (should be JSON array)

        Returns:
            List of extraction dicts
        """
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'```(?:json)?\s*(\[[\s\S]*?\])\s*```', response_text)
            if json_match:
                json_text = json_match.group(1)
            else:
                # Try to find raw JSON array
                json_match = re.search(r'\[[\s\S]*\]', response_text)
                if json_match:
                    json_text = json_match.group(0)
                else:
                    return []

            import json
            extractions = json.loads(json_text)

            # Validate and normalize
            validated = []
            for extraction in extractions:
                if self._validate_extraction(extraction):
                    validated.append(extraction)

            return validated

        except Exception as e:
            logger.error(f"Error parsing extraction response: {e}")
            return []

    def _validate_extraction(self, extraction: Dict[str, Any]) -> bool:
        """Validate extraction has required fields."""
        required_fields = ["type", "title", "summary", "content"]
        return all(field in extraction for field in required_fields)

    # ===== CONVERSATION-LEVEL EXTRACTION =====

    async def analyze_conversation(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        messages: List[Message],
        project_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze complete conversation for higher-level knowledge patterns.

        Args:
            db: Database session
            conversation_id: Conversation ID
            messages: All messages in conversation
            project_id: Related project (optional)

        Returns:
            List of extraction candidates
        """
        try:
            if not messages or len(messages) < 3:
                return []  # Need sufficient conversation

            # Summarize conversation
            conversation_summary = self._summarize_conversation(messages)

            # Build analysis prompt
            analysis_prompt = f"""
Analyze this conversation for valuable organizational knowledge that should be preserved.

CONVERSATION SUMMARY:
{conversation_summary}

FULL CONVERSATION:
{self._format_messages_for_analysis(messages)}

INSTRUCTIONS:
Identify patterns across the conversation:

1. **Problem-Solution Pairs**: Problems discussed and how they were solved
2. **Decision Chains**: How decisions were made and why
3. **Preference Expressions**: User or organizational preferences mentioned
4. **Workflow Patterns**: Collaboration patterns or processes followed
5. **Key Insights**: Important realizations or discoveries
6. **Best Practices**: Effective approaches used

For each extractable knowledge unit, provide:
- type: Knowledge type from (solution|decision|preference|standard|lesson_learned|pattern|best_practice)
- title: Clear, searchable title
- summary: 2-3 sentences
- content: Detailed markdown content
- confidence: 0.0-1.0
- novelty: 0.0-1.0 (compared to typical knowledge)
- relevance: 0.0-1.0 (how broadly applicable)
- tags: Relevant tags
- problem_context: What problem this addresses (if applicable)
- applicable_scenarios: When to use this knowledge

Return JSON array of extractions.
"""

            # Call LLM
            response = await self.anthropic_client.messages.create(
                model=self.extraction_model,
                max_tokens=3000,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": analysis_prompt}
                ]
            )

            response_text = response.content[0].text
            extractions = self._parse_extraction_response(response_text)

            logger.info(
                f"Analyzed conversation {conversation_id}, "
                f"found {len(extractions)} extraction candidates"
            )

            return extractions

        except Exception as e:
            logger.error(f"Error analyzing conversation {conversation_id}: {e}", exc_info=True)
            return []

    def _summarize_conversation(self, messages: List[Message]) -> str:
        """Create brief summary of conversation."""
        return f"""
Participants: {len(set(msg.from_agent_id for msg in messages))} agents
Messages: {len(messages)}
Duration: {(messages[-1].timestamp - messages[0].timestamp).total_seconds() / 60:.1f} minutes
Topics: {', '.join(self._extract_topics(messages)[:5])}
"""

    def _format_messages_for_analysis(self, messages: List[Message], max_length: int = 8000) -> str:
        """Format messages for LLM analysis with length limit."""
        formatted = []
        total_length = 0

        for msg in messages:
            msg_text = f"\n[{msg.from_agent_id} → {msg.to_agent_id}] ({msg.message_type})\n{msg.content}\n"
            total_length += len(msg_text)

            if total_length > max_length:
                formatted.append("\n[... conversation truncated ...]")
                break

            formatted.append(msg_text)

        return "".join(formatted)

    def _extract_topics(self, messages: List[Message]) -> List[str]:
        """Extract key topics from messages using simple heuristics."""
        # Simple keyword extraction (could be enhanced with NLP)
        text = " ".join(msg.content for msg in messages)
        words = text.lower().split()

        # Count technical keywords
        technical_keywords = [
            "api", "database", "frontend", "backend", "security", "performance",
            "authentication", "authorization", "deploy", "test", "bug", "feature"
        ]

        topic_counts = {}
        for keyword in technical_keywords:
            count = words.count(keyword)
            if count > 0:
                topic_counts[keyword] = count

        # Return top topics
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        return [topic for topic, _ in sorted_topics]

    # ===== PROJECT-LEVEL EXTRACTION =====

    async def extract_from_completed_project(
        self,
        db: AsyncSession,
        project: Project,
        tasks: List[Task],
        decisions: List[Decision]
    ) -> List[Dict[str, Any]]:
        """
        Extract knowledge from a completed project.

        Args:
            db: Database session
            project: Completed project
            tasks: All project tasks
            decisions: All project decisions

        Returns:
            List of extraction candidates
        """
        try:
            analysis_prompt = f"""
Analyze this completed project to extract valuable organizational knowledge.

PROJECT:
Name: {project.name}
Description: {project.description}
Status: {project.status}
Duration: {project.agent_days_elapsed} agent-days
Tasks Completed: {len([t for t in tasks if t.status == 'COMPLETED'])} / {len(tasks)}

KEY DECISIONS:
{self._format_decisions(decisions)}

TASK BREAKDOWN:
{self._format_tasks(tasks[:10])}  # First 10 tasks

INSTRUCTIONS:
Extract knowledge about:

1. **Project Patterns**: Successful approaches for similar project types
2. **Task Breakdown Templates**: How projects like this should be decomposed
3. **Estimation Baselines**: Time/resource estimates for future similar projects
4. **Risk Patterns**: Challenges encountered and how they were handled
5. **Success Factors**: What made this project successful
6. **Process Learnings**: Process improvements discovered

For each extraction:
- type: (pattern|template|lesson_learned|best_practice)
- title: Clear title
- summary: Brief description
- content: Detailed markdown
- confidence: 0.0-1.0
- novelty: 0.0-1.0
- relevance: 0.0-1.0
- applicable_scenarios: When this applies
- tags: Relevant tags

Return JSON array.
"""

            response = await self.anthropic_client.messages.create(
                model=self.extraction_model,
                max_tokens=3000,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": analysis_prompt}
                ]
            )

            response_text = response.content[0].text
            extractions = self._parse_extraction_response(response_text)

            logger.info(
                f"Extracted {len(extractions)} knowledge items from project {project.project_id}"
            )

            return extractions

        except Exception as e:
            logger.error(f"Error extracting from project {project.project_id}: {e}", exc_info=True)
            return []

    def _format_decisions(self, decisions: List[Decision]) -> str:
        """Format decisions for analysis."""
        if not decisions:
            return "No decisions recorded"

        formatted = []
        for dec in decisions[:5]:  # First 5 decisions
            formatted.append(f"- {dec.question}\n  Decision: {dec.decision}\n  Rationale: {dec.rationale}")

        return "\n".join(formatted)

    def _format_tasks(self, tasks: List[Task]) -> str:
        """Format tasks for analysis."""
        if not tasks:
            return "No tasks"

        formatted = []
        for task in tasks:
            formatted.append(f"- [{task.status}] {task.title}: {task.description[:100] if task.description else 'No description'}")

        return "\n".join(formatted)

    # ===== EXTRACTION CANDIDATE CREATION =====

    async def create_extraction_candidate(
        self,
        db: AsyncSession,
        extraction_data: Dict[str, Any],
        trigger_type: ExtractionTriggerType,
        source_context: Dict[str, Any]
    ) -> Optional[ExtractionCandidate]:
        """
        Create an extraction candidate in the database.

        Args:
            db: Database session
            extraction_data: Structured extraction data from LLM
            trigger_type: What triggered the extraction
            source_context: Source context (conversation_id, project_id, etc.)

        Returns:
            Created ExtractionCandidate or None
        """
        try:
            # Determine entry type
            entry_type_str = extraction_data.get("type", "solution")
            entry_type = self._map_to_entry_type(entry_type_str)

            # Calculate scores
            confidence_score = float(extraction_data.get("confidence", 0.7))
            novelty_score = float(extraction_data.get("novelty", 0.5))
            relevance_score = float(extraction_data.get("relevance", 0.7))
            extraction_quality = (confidence_score + novelty_score + relevance_score) / 3

            # Create candidate
            candidate = ExtractionCandidate(
                conversation_id=source_context.get("conversation_id"),
                project_id=source_context.get("project_id"),
                task_id=source_context.get("task_id"),
                message_range_start=source_context.get("message_range_start"),
                message_range_end=source_context.get("message_range_end"),
                extracted_content=extraction_data,
                extraction_type=entry_type,
                primary_category_guess=self._guess_category(extraction_data),
                confidence_score=confidence_score,
                novelty_score=novelty_score,
                relevance_score=relevance_score,
                extraction_quality=extraction_quality,
                trigger_type=trigger_type,
                trigger_details=source_context,
                status=ExtractionStatus.PENDING
            )

            db.add(candidate)
            await db.commit()
            await db.refresh(candidate)

            logger.info(f"Created extraction candidate {candidate.candidate_id} (type: {entry_type})")

            return candidate

        except Exception as e:
            logger.error(f"Error creating extraction candidate: {e}", exc_info=True)
            await db.rollback()
            return None

    def _map_to_entry_type(self, type_str: str) -> KnowledgeEntryType:
        """Map string type to enum."""
        type_mapping = {
            "solution": KnowledgeEntryType.SOLUTION,
            "decision": KnowledgeEntryType.DECISION,
            "preference": KnowledgeEntryType.PREFERENCE,
            "standard": KnowledgeEntryType.STANDARD,
            "lesson_learned": KnowledgeEntryType.LESSON_LEARNED,
            "pattern": KnowledgeEntryType.PATTERN,
            "template": KnowledgeEntryType.TEMPLATE,
            "definition": KnowledgeEntryType.DEFINITION,
            "best_practice": KnowledgeEntryType.BEST_PRACTICE,
            "technical_insight": KnowledgeEntryType.TECHNICAL_INSIGHT
        }
        return type_mapping.get(type_str.lower(), KnowledgeEntryType.SOLUTION)

    def _guess_category(self, extraction_data: Dict[str, Any]) -> str:
        """Guess primary category from extraction data."""
        # Simple heuristic based on tags
        tags = extraction_data.get("tags", [])
        if not tags:
            return "general"

        # Map common tags to categories
        category_keywords = {
            "technical": ["api", "database", "code", "architecture", "security"],
            "project": ["planning", "estimation", "workflow", "process"],
            "user": ["preference", "communication", "feedback"],
            "organizational": ["policy", "standard", "guideline", "process"]
        }

        for category, keywords in category_keywords.items():
            if any(keyword in tag.lower() for tag in tags for keyword in keywords):
                return category

        return "general"

    # ===== BATCH PROCESSING =====

    async def process_pending_extractions(
        self,
        db: AsyncSession,
        limit: int = 50
    ) -> int:
        """
        Process pending extraction candidates (approve or reject based on quality).

        Args:
            db: Database session
            limit: Maximum candidates to process

        Returns:
            Number of candidates processed
        """
        try:
            # Get pending candidates with high quality scores
            query = select(ExtractionCandidate).where(
                and_(
                    ExtractionCandidate.status == ExtractionStatus.PENDING,
                    ExtractionCandidate.extraction_quality >= 0.7  # Auto-approve threshold
                )
            ).order_by(
                ExtractionCandidate.extraction_quality.desc()
            ).limit(limit)

            result = await db.execute(query)
            candidates = result.scalars().all()

            processed_count = 0
            for candidate in candidates:
                # Auto-approve high-quality candidates
                await self._auto_approve_candidate(db, candidate)
                processed_count += 1

            await db.commit()

            logger.info(f"Auto-processed {processed_count} extraction candidates")

            return processed_count

        except Exception as e:
            logger.error(f"Error processing extraction candidates: {e}", exc_info=True)
            await db.rollback()
            return 0

    async def _auto_approve_candidate(
        self,
        db: AsyncSession,
        candidate: ExtractionCandidate
    ) -> None:
        """Auto-approve a candidate and convert to knowledge entry."""
        try:
            # Create knowledge entry from candidate
            from app.services.knowledge_processing_service import KnowledgeProcessingService
            processing_service = KnowledgeProcessingService()

            entry = await processing_service.convert_candidate_to_entry(db, candidate)

            if entry:
                # Update candidate status
                candidate.status = ExtractionStatus.APPROVED
                candidate.converted_to_entry_id = entry.entry_id
                candidate.reviewed_by_type = "system"
                candidate.reviewed_by_id = "auto_approve"
                candidate.review_decision = "approve"
                candidate.reviewed_at = datetime.utcnow()

                logger.info(f"Auto-approved candidate {candidate.candidate_id} → entry {entry.entry_id}")

        except Exception as e:
            logger.error(f"Error auto-approving candidate {candidate.candidate_id}: {e}")

    # ===== EXPLICIT EXTRACTION TRIGGERS =====

    async def extract_on_user_request(
        self,
        db: AsyncSession,
        user_input: str,
        context: Dict[str, Any]
    ) -> Optional[ExtractionCandidate]:
        """
        Handle explicit user request to save knowledge.

        Example: "Remember this for future projects"

        Args:
            db: Database session
            user_input: User's input/request
            context: Current context (conversation, project, etc.)

        Returns:
            Created extraction candidate
        """
        # Parse user request to extract knowledge
        extraction_data = {
            "type": "preference",  # User explicitly wants this saved
            "title": f"User preference: {user_input[:50]}",
            "summary": user_input[:200],
            "content": user_input,
            "confidence": 1.0,  # Explicit request = high confidence
            "novelty": 0.5,
            "relevance": 0.8,
            "tags": ["user_requested", "explicit"],
            "applicable_scenarios": ["As stated by user"]
        }

        return await self.create_extraction_candidate(
            db=db,
            extraction_data=extraction_data,
            trigger_type=ExtractionTriggerType.EXPLICIT_REQUEST,
            source_context=context
        )


# Singleton instance
_knowledge_extraction_service: Optional[KnowledgeExtractionService] = None


def get_knowledge_extraction_service() -> KnowledgeExtractionService:
    """Get or create singleton knowledge extraction service."""
    global _knowledge_extraction_service
    if _knowledge_extraction_service is None:
        _knowledge_extraction_service = KnowledgeExtractionService()
    return _knowledge_extraction_service
