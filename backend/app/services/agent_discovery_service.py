"""
Agent Discovery Service

Discovers and recommends agents for conversations based on:
- Conversation content analysis
- Knowledge base predictions
- Agent expertise matching
- Historical performance
"""

import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from pydantic import BaseModel

from app.db.models import Agent
from app.db.conversation_models import ConversationMessage, ConversationParticipant, Conversation
from app.db.multi_agent_models import AgentExpertiseTag, ConversationAgentSuggestion
from app.services.predictive_agent_involvement_service import PredictiveAgentInvolvementService

logger = logging.getLogger(__name__)


class AgentRecommendation(BaseModel):
    """Agent recommendation with scoring details."""
    agent_id: str
    agent_name: str
    agent_role: str
    relevance_score: float
    expertise_match: List[str]
    reasoning: str
    prediction_factors: Dict[str, float]
    confidence: float


class AgentDiscoveryService:
    """Service for discovering and recommending agents for conversations."""

    def __init__(self, predictive_service: PredictiveAgentInvolvementService):
        self.predictive_service = predictive_service

    async def discover_agents(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        user_id: str,
        limit: int = 5,
        min_relevance: float = 0.6
    ) -> List[AgentRecommendation]:
        """
        Discover relevant agents for a conversation.

        Args:
            db: Database session
            conversation_id: Conversation to analyze
            user_id: User requesting suggestions
            limit: Maximum number of suggestions
            min_relevance: Minimum relevance score (0.0-1.0)

        Returns:
            List of agent recommendations sorted by relevance
        """
        logger.info(f"Discovering agents for conversation {conversation_id}")

        # 1. Get conversation context
        conversation = await self._get_conversation(db, conversation_id)
        if not conversation:
            logger.warning(f"Conversation {conversation_id} not found")
            return []

        # 2. Get recent messages for analysis
        messages = await self._get_recent_messages(db, conversation_id, limit=20)
        if not messages:
            logger.info("No messages to analyze for agent discovery")
            return []

        # 3. Get current participants to exclude
        current_participants = await self._get_current_agent_participants(db, conversation_id)
        current_agent_ids = [p.participant_id_ref for p in current_participants]

        # 4. Use predictive service to get agent suggestions
        try:
            predictions = await self.predictive_service.predict_agent_involvement(
                db=db,
                conversation_id=conversation_id,
                messages=[self._message_to_dict(m) for m in messages],
                current_agent_ids=current_agent_ids,
                user_id=user_id,
                project_id=str(conversation.project_id) if conversation.project_id else None,
                exclude_current=True,
                limit=limit * 2  # Get more to filter
            )
        except Exception as e:
            logger.error(f"Error getting predictions: {e}")
            predictions = []

        # 5. Get expertise gaps
        expertise_gaps = await self.get_expertise_gaps(db, conversation_id, current_agent_ids)

        # 6. Enhance predictions with expertise matching
        recommendations = []
        for pred in predictions:
            # Filter by minimum relevance
            if pred.get('probability', 0) < min_relevance:
                continue

            # Get agent details
            agent = await self._get_agent(db, pred['agent_id'])
            if not agent:
                continue

            # Get agent expertise
            expertise = await self._get_agent_expertise(db, pred['agent_id'])
            expertise_areas = [e.expertise_area for e in expertise]

            # Calculate expertise gap match
            gap_match_score = self._calculate_gap_match(expertise_areas, expertise_gaps)

            # Create recommendation
            recommendation = AgentRecommendation(
                agent_id=agent.agent_id,
                agent_name=agent.name,
                agent_role=agent.role,
                relevance_score=pred.get('probability', 0.0),
                expertise_match=expertise_areas,
                reasoning=pred.get('reasoning', 'Relevant based on conversation context'),
                prediction_factors={
                    'expertise_match': pred.get('expertise_match_score', 0.0),
                    'historical_success': pred.get('historical_performance', 0.0),
                    'user_preference': pred.get('user_preference_score', 0.0),
                    'context_fit': pred.get('contextual_fit', 0.0),
                    'gap_filling': gap_match_score
                },
                confidence=pred.get('confidence', 0.0)
            )

            recommendations.append(recommendation)

        # 7. Sort by relevance score
        recommendations.sort(key=lambda x: x.relevance_score, reverse=True)

        # 8. Store suggestions for tracking
        await self._store_suggestions(db, conversation_id, recommendations[:limit])

        logger.info(f"Found {len(recommendations)} agent recommendations")
        return recommendations[:limit]

    async def get_expertise_gaps(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        current_agent_ids: List[str]
    ) -> List[str]:
        """
        Identify expertise areas missing from current participants.

        Args:
            db: Database session
            conversation_id: Conversation to analyze
            current_agent_ids: Current participating agent IDs

        Returns:
            List of missing expertise areas
        """
        # 1. Analyze conversation to identify needed expertise
        messages = await self._get_recent_messages(db, conversation_id, limit=10)
        needed_expertise = await self._extract_needed_expertise(messages)

        # 2. Get expertise of current participants
        current_expertise = set()
        for agent_id in current_agent_ids:
            agent_expertise = await self._get_agent_expertise(db, agent_id)
            current_expertise.update(e.expertise_area for e in agent_expertise)

        # 3. Identify gaps
        gaps = [expertise for expertise in needed_expertise if expertise not in current_expertise]

        logger.debug(f"Identified expertise gaps: {gaps}")
        return gaps

    async def score_agent_relevance(
        self,
        db: AsyncSession,
        agent_id: str,
        conversation_context: Dict[str, Any],
        current_participants: List[str]
    ) -> float:
        """
        Score how relevant an agent is for a conversation (0.0-1.0).

        Args:
            db: Database session
            agent_id: Agent to score
            conversation_context: Context dict with messages, topics, etc.
            current_participants: Current agent IDs in conversation

        Returns:
            Relevance score between 0.0 and 1.0
        """
        # Avoid suggesting agents already in conversation
        if agent_id in current_participants:
            return 0.0

        # Get agent expertise
        expertise = await self._get_agent_expertise(db, agent_id)
        expertise_areas = set(e.expertise_area for e in expertise)

        # Extract needed expertise from context
        needed_expertise = set(conversation_context.get('needed_expertise', []))

        # Calculate expertise match
        if not needed_expertise:
            expertise_score = 0.5  # Neutral if can't determine
        else:
            matches = expertise_areas.intersection(needed_expertise)
            expertise_score = len(matches) / len(needed_expertise) if needed_expertise else 0.0

        # Get historical success rate for this agent
        # This could query past conversations where agent participated
        historical_score = await self._get_agent_historical_score(db, agent_id)

        # Combine scores with weights
        relevance = (
            expertise_score * 0.6 +  # Expertise match most important
            historical_score * 0.4   # Historical performance
        )

        return min(1.0, max(0.0, relevance))

    async def find_agents_by_expertise(
        self,
        db: AsyncSession,
        expertise_areas: List[str],
        limit: int = 10
    ) -> List[str]:
        """
        Find agents with specific expertise areas.

        Args:
            db: Database session
            expertise_areas: List of expertise areas to match
            limit: Maximum number of agents to return

        Returns:
            List of agent IDs
        """
        result = await db.execute(
            select(AgentExpertiseTag.agent_id, func.count(AgentExpertiseTag.tag_id).label('match_count'))
            .where(AgentExpertiseTag.expertise_area.in_(expertise_areas))
            .group_by(AgentExpertiseTag.agent_id)
            .order_by(func.count(AgentExpertiseTag.tag_id).desc())
            .limit(limit)
        )

        rows = result.all()
        return [row.agent_id for row in rows]

    # Helper methods

    async def _get_conversation(
        self,
        db: AsyncSession,
        conversation_id: UUID
    ) -> Optional[Conversation]:
        """Get conversation by ID."""
        result = await db.execute(
            select(Conversation).where(Conversation.conversation_id == conversation_id)
        )
        return result.scalar_one_or_none()

    async def _get_recent_messages(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        limit: int = 20
    ) -> List[ConversationMessage]:
        """Get recent messages from conversation."""
        result = await db.execute(
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation_id)
            .order_by(ConversationMessage.created_at.desc())
            .limit(limit)
        )
        messages = list(result.scalars().all())
        messages.reverse()  # Return in chronological order
        return messages

    async def _get_current_agent_participants(
        self,
        db: AsyncSession,
        conversation_id: UUID
    ) -> List[ConversationParticipant]:
        """Get current agent participants."""
        from app.db.conversation_models import ParticipantType

        result = await db.execute(
            select(ConversationParticipant)
            .where(
                and_(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.participant_type == ParticipantType.AGENT,
                    ConversationParticipant.is_active == True
                )
            )
        )
        return list(result.scalars().all())

    async def _get_agent(self, db: AsyncSession, agent_id: str) -> Optional[Agent]:
        """Get agent by ID."""
        result = await db.execute(
            select(Agent).where(Agent.agent_id == agent_id)
        )
        return result.scalar_one_or_none()

    async def _get_agent_expertise(
        self,
        db: AsyncSession,
        agent_id: str
    ) -> List[AgentExpertiseTag]:
        """Get expertise tags for an agent."""
        result = await db.execute(
            select(AgentExpertiseTag)
            .where(AgentExpertiseTag.agent_id == agent_id)
            .order_by(AgentExpertiseTag.proficiency_level.desc())
        )
        return list(result.scalars().all())

    async def _extract_needed_expertise(
        self,
        messages: List[ConversationMessage]
    ) -> List[str]:
        """
        Extract needed expertise from messages.

        This is a simplified version. In production, this would use
        NLP/LLM to analyze message content and identify expertise areas.
        """
        # Keywords that map to expertise areas
        expertise_keywords = {
            'legal': ['legal', 'contract', 'compliance', 'regulation', 'gdpr', 'law'],
            'marketing': ['marketing', 'campaign', 'brand', 'promotion', 'advertising'],
            'design': ['design', 'ui', 'ux', 'visual', 'graphic', 'layout'],
            'technical': ['technical', 'code', 'development', 'engineering', 'bug'],
            'finance': ['finance', 'budget', 'cost', 'revenue', 'financial'],
            'hr': ['hr', 'hiring', 'recruitment', 'employee', 'personnel'],
            'sales': ['sales', 'revenue', 'customer', 'deal', 'pipeline']
        }

        needed_expertise = set()
        combined_text = ' '.join(m.content.lower() for m in messages)

        for expertise, keywords in expertise_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                needed_expertise.add(expertise)

        return list(needed_expertise)

    def _calculate_gap_match(
        self,
        agent_expertise: List[str],
        expertise_gaps: List[str]
    ) -> float:
        """Calculate how well agent fills expertise gaps."""
        if not expertise_gaps:
            return 0.5  # Neutral if no gaps

        matches = set(agent_expertise).intersection(set(expertise_gaps))
        return len(matches) / len(expertise_gaps) if expertise_gaps else 0.0

    async def _get_agent_historical_score(
        self,
        db: AsyncSession,
        agent_id: str
    ) -> float:
        """
        Get historical performance score for agent.

        In production, this would query past conversation outcomes,
        user satisfaction ratings, etc.
        """
        # Simplified version - return neutral score
        # TODO: Implement actual historical analysis
        return 0.7

    def _message_to_dict(self, message: ConversationMessage) -> Dict[str, Any]:
        """Convert message model to dict for predictions."""
        return {
            'message_id': str(message.message_id),
            'content': message.content,
            'sender_type': message.sender_type.value,
            'sender_id': message.sender_id,
            'created_at': message.created_at.isoformat() if message.created_at else None,
            'extracted_entities': message.extracted_entities or {},
            'intent_classification': message.intent_classification
        }

    async def _store_suggestions(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        recommendations: List[AgentRecommendation]
    ):
        """Store agent suggestions for tracking and learning."""
        try:
            for rec in recommendations:
                suggestion = ConversationAgentSuggestion(
                    conversation_id=conversation_id,
                    agent_id=rec.agent_id,
                    relevance_score=rec.relevance_score,
                    reasoning=rec.reasoning,
                    expertise_match_score=rec.prediction_factors.get('expertise_match'),
                    historical_success_score=rec.prediction_factors.get('historical_success'),
                    user_preference_score=rec.prediction_factors.get('user_preference'),
                    context_fit_score=rec.prediction_factors.get('context_fit'),
                    matched_expertise_areas=rec.expertise_match
                )
                db.add(suggestion)

            await db.commit()
            logger.debug(f"Stored {len(recommendations)} agent suggestions")
        except Exception as e:
            logger.error(f"Error storing suggestions: {e}")
            await db.rollback()
