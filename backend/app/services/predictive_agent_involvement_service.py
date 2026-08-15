"""
Predictive Agent Involvement Service

Predicts which agents should be involved in conversations/projects based on:
- Historical patterns of agent expertise
- Topic/domain matching
- User satisfaction with past agent involvement
- Conversation context and trajectory

Implements the predictive system from INTELLIGENT_KNOWLEDGE_BASE.md.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from uuid import UUID
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from anthropic import AsyncAnthropic

from app.db.knowledge_models import (
    AgentInvolvementPrediction,
    AgentInvolvementOutcome,
    UserKnowledgeProfile,
    KnowledgeEntry,
    AgentInvolvementType,
    InvolvementTiming,
    InvolvementApproach
)
from app.db.models import Agent, Message, Project, Task
from app.services.rag_embedding_service import get_embedding_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class PredictiveAgentInvolvementService:
    """
    Service for predicting optimal agent involvement in conversations and projects.
    """

    def __init__(self):
        """Initialize the predictive agent involvement service."""
        self.embedding_service = get_embedding_service()
        self.anthropic_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.prediction_model = settings.DEFAULT_LLM_MODEL
        self.confidence_threshold = 0.7  # Minimum confidence to suggest

    # ===== MAIN PREDICTION =====

    async def predict_agent_involvement(
        self,
        db: AsyncSession,
        conversation_id: Optional[UUID],
        messages: List[Message],
        project_id: Optional[UUID] = None,
        current_agents: Optional[List[str]] = None,
        user_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Predict which agents should be involved in conversation/project.

        Args:
            db: Database session
            conversation_id: Conversation ID (optional)
            messages: Recent conversation messages
            project_id: Project ID (optional)
            current_agents: Currently involved agent IDs
            user_id: User ID for preference matching

        Returns:
            List of agent predictions with confidence scores
        """
        try:
            if not messages:
                return []

            current_agents = current_agents or []

            # Extract conversation signals
            signals = await self._extract_conversation_signals(db, messages)

            # Get candidate agents
            all_agents = await self._get_candidate_agents(db, current_agents)

            # Score each agent
            predictions = []

            for agent in all_agents:
                prediction = await self._score_agent_relevance(
                    db=db,
                    agent=agent,
                    signals=signals,
                    messages=messages,
                    user_id=user_id,
                    current_agents=current_agents
                )

                if prediction and prediction["involvement_probability"] >= self.confidence_threshold:
                    predictions.append(prediction)

                    # Store prediction in database
                    await self._store_prediction(
                        db=db,
                        conversation_id=conversation_id,
                        project_id=project_id,
                        prediction_data=prediction
                    )

            # Sort by probability
            predictions.sort(key=lambda x: x["involvement_probability"], reverse=True)

            logger.info(
                f"Generated {len(predictions)} agent involvement predictions "
                f"for conversation {conversation_id}"
            )

            return predictions[:5]  # Top 5 suggestions

        except Exception as e:
            logger.error(f"Error predicting agent involvement: {e}", exc_info=True)
            return []

    # ===== SIGNAL EXTRACTION =====

    async def _extract_conversation_signals(
        self,
        db: AsyncSession,
        messages: List[Message]
    ) -> Dict[str, Any]:
        """
        Extract signals from conversation that indicate needed expertise.

        Args:
            db: Database session
            messages: Conversation messages

        Returns:
            Dict of extracted signals
        """
        try:
            # Combine recent messages
            conversation_text = " ".join([msg.content for msg in messages[-10:]])

            # Use LLM to extract topics and signals
            analysis_prompt = f"""
Analyze this conversation to identify what expertise or agent roles might be needed.

CONVERSATION:
{conversation_text}

INSTRUCTIONS:
Identify:
1. **Topics Discussed**: Key topics, technologies, or domains mentioned
2. **Problems/Questions**: Issues that need solving or questions raised
3. **Required Expertise**: What expertise domains are needed (technical, design, business, etc.)
4. **Complexity Level**: How complex is the discussion (simple, moderate, complex, expert-level)
5. **Urgency**: Is there time pressure indicated?

Return as JSON with these keys:
{{
    "topics": ["topic1", "topic2", ...],
    "problems": ["problem1", "problem2", ...],
    "required_expertise": ["domain1", "domain2", ...],
    "complexity": "simple|moderate|complex|expert",
    "urgency": "low|medium|high",
    "technical_keywords": ["keyword1", "keyword2", ...]
}}
"""

            response = await self.anthropic_client.messages.create(
                model=self.prediction_model,
                max_tokens=1000,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": analysis_prompt}
                ]
            )

            # Parse response
            import json
            import re

            response_text = response.content[0].text

            # Extract JSON
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                signals = json.loads(json_match.group(0))
            else:
                # Fallback to simple keyword extraction
                signals = self._extract_simple_signals(conversation_text)

            # Add message metadata
            signals["message_count"] = len(messages)
            signals["conversation_length_minutes"] = (
                (messages[-1].timestamp - messages[0].timestamp).total_seconds() / 60
                if len(messages) > 1 else 0
            )

            return signals

        except Exception as e:
            logger.error(f"Error extracting conversation signals: {e}")
            # Fallback to simple extraction
            return self._extract_simple_signals(" ".join([msg.content for msg in messages]))

    def _extract_simple_signals(self, text: str) -> Dict[str, Any]:
        """Simple keyword-based signal extraction as fallback."""
        import re

        text_lower = text.lower()

        # Technical domains
        technical_keywords = {
            "backend": ["api", "database", "server", "backend", "python", "fastapi"],
            "frontend": ["ui", "react", "component", "frontend", "interface"],
            "design": ["design", "ux", "ui", "mockup", "wireframe"],
            "devops": ["deploy", "docker", "kubernetes", "ci/cd", "infrastructure"],
            "security": ["security", "authentication", "authorization", "encryption"],
            "data": ["data", "analytics", "ml", "model", "dataset"]
        }

        detected_domains = []
        detected_keywords = []

        for domain, keywords in technical_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                detected_domains.append(domain)
                detected_keywords.extend([kw for kw in keywords if kw in text_lower])

        # Complexity heuristics
        if len(text.split()) > 500 or "complex" in text_lower or "advanced" in text_lower:
            complexity = "complex"
        elif len(text.split()) > 200:
            complexity = "moderate"
        else:
            complexity = "simple"

        # Urgency heuristics
        if any(word in text_lower for word in ["urgent", "asap", "immediately", "critical"]):
            urgency = "high"
        elif any(word in text_lower for word in ["soon", "quick", "fast"]):
            urgency = "medium"
        else:
            urgency = "low"

        return {
            "topics": detected_domains,
            "problems": [],
            "required_expertise": detected_domains,
            "complexity": complexity,
            "urgency": urgency,
            "technical_keywords": list(set(detected_keywords))
        }

    # ===== AGENT CANDIDATE RETRIEVAL =====

    async def _get_candidate_agents(
        self,
        db: AsyncSession,
        exclude_agents: List[str]
    ) -> List[Agent]:
        """Get candidate agents (excluding already involved ones)."""
        try:
            query = select(Agent).where(
                and_(
                    Agent.status == "active",
                    ~Agent.agent_id.in_(exclude_agents) if exclude_agents else True
                )
            )

            result = await db.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error getting candidate agents: {e}")
            return []

    # ===== AGENT SCORING =====

    async def _score_agent_relevance(
        self,
        db: AsyncSession,
        agent: Agent,
        signals: Dict[str, Any],
        messages: List[Message],
        user_id: Optional[UUID],
        current_agents: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Score an agent's relevance to the conversation.

        Args:
            db: Database session
            agent: Agent to score
            signals: Extracted conversation signals
            messages: Conversation messages
            user_id: User ID
            current_agents: Currently involved agents

        Returns:
            Prediction dict or None
        """
        try:
            scores = {
                "expertise_match": 0.0,
                "historical_success": 0.0,
                "user_preference": 0.0,
                "context_fit": 0.0,
                "availability": 0.0
            }

            # 1. Expertise Match (40% weight)
            scores["expertise_match"] = await self._score_expertise_match(
                db, agent, signals
            )

            # 2. Historical Success (30% weight)
            scores["historical_success"] = await self._score_historical_success(
                db, agent, signals
            )

            # 3. User Preference (15% weight)
            if user_id:
                scores["user_preference"] = await self._score_user_preference(
                    db, agent, user_id
                )
            else:
                scores["user_preference"] = 0.5  # Neutral

            # 4. Context Fit (10% weight)
            scores["context_fit"] = self._score_context_fit(
                agent, signals, current_agents
            )

            # 5. Availability (5% weight)
            scores["availability"] = await self._score_availability(db, agent)

            # Weighted average
            weights = {
                "expertise_match": 0.4,
                "historical_success": 0.3,
                "user_preference": 0.15,
                "context_fit": 0.1,
                "availability": 0.05
            }

            involvement_probability = sum(
                scores[key] * weights[key] for key in weights.keys()
            )

            # Determine involvement type and timing
            involvement_type, timing, approach = self._determine_involvement_strategy(
                involvement_probability,
                scores,
                signals
            )

            # Build prediction
            prediction = {
                "agent_id": agent.agent_id,
                "agent_name": agent.name,
                "agent_role": agent.role,
                "involvement_probability": round(involvement_probability, 3),
                "confidence": self._calculate_confidence(scores),
                "predicted_contribution_type": involvement_type.value,
                "suggested_timing": timing.value,
                "introduction_approach": approach.value,
                "trigger_reasons": self._generate_trigger_reasons(scores, signals),
                "signal_strength": round(max(scores.values()), 3),
                "score_breakdown": {k: round(v, 3) for k, v in scores.items()}
            }

            return prediction

        except Exception as e:
            logger.error(f"Error scoring agent {agent.agent_id}: {e}")
            return None

    async def _score_expertise_match(
        self,
        db: AsyncSession,
        agent: Agent,
        signals: Dict[str, Any]
    ) -> float:
        """Score how well agent's expertise matches conversation needs."""
        score = 0.0

        # Match agent specializations with required expertise
        agent_specializations = agent.specializations if hasattr(agent, 'specializations') else []
        required_expertise = signals.get("required_expertise", [])

        if agent_specializations and required_expertise:
            matches = sum(
                1 for spec in agent_specializations
                if any(req.lower() in str(spec).lower() for req in required_expertise)
            )
            score += min(1.0, matches / len(required_expertise))

        # Match role with discussion topics
        role_lower = agent.role.lower()
        topics = signals.get("topics", [])

        role_topic_matches = {
            "backend": ["backend", "api", "database", "server"],
            "frontend": ["frontend", "ui", "interface", "react"],
            "designer": ["design", "ux", "ui", "visual"],
            "cto": ["architecture", "technical", "strategy", "complex"],
            "ceo": ["business", "strategy", "decision", "priority"],
            "pm": ["planning", "project", "task", "workflow"]
        }

        for role_key, role_topics in role_topic_matches.items():
            if role_key in role_lower:
                topic_matches = sum(
                    1 for topic in topics
                    if any(rt in topic.lower() for rt in role_topics)
                )
                score += min(1.0, topic_matches / max(len(topics), 1))
                break

        return min(1.0, score)

    async def _score_historical_success(
        self,
        db: AsyncSession,
        agent: Agent,
        signals: Dict[str, Any]
    ) -> float:
        """Score based on agent's historical success in similar contexts."""
        try:
            # Get past involvement outcomes for this agent
            query = select(AgentInvolvementOutcome).where(
                and_(
                    AgentInvolvementOutcome.agent_id == agent.agent_id,
                    AgentInvolvementOutcome.user_satisfaction_rating.isnot(None)
                )
            ).order_by(
                AgentInvolvementOutcome.created_at.desc()
            ).limit(20)

            result = await db.execute(query)
            outcomes = result.scalars().all()

            if not outcomes:
                return 0.5  # Neutral score for new agent

            # Calculate average satisfaction
            avg_satisfaction = sum(
                o.user_satisfaction_rating for o in outcomes
            ) / len(outcomes)

            # Boost for recent successful involvements
            recent_outcomes = [o for o in outcomes if
                              (datetime.utcnow() - o.created_at).days < 30]

            if recent_outcomes:
                recent_satisfaction = sum(
                    o.user_satisfaction_rating for o in recent_outcomes
                ) / len(recent_outcomes)
                avg_satisfaction = (avg_satisfaction + recent_satisfaction) / 2

            return min(1.0, avg_satisfaction)

        except Exception as e:
            logger.error(f"Error scoring historical success: {e}")
            return 0.5

    async def _score_user_preference(
        self,
        db: AsyncSession,
        agent: Agent,
        user_id: UUID
    ) -> float:
        """Score based on user's preference for this agent."""
        try:
            # Get user knowledge profile
            query = select(UserKnowledgeProfile).where(
                UserKnowledgeProfile.user_id == user_id
            )

            result = await db.execute(query)
            profile = result.scalar_one_or_none()

            if not profile or not profile.preferred_agents:
                return 0.5  # Neutral

            agent_pref = profile.preferred_agents.get(agent.agent_id)

            if not agent_pref:
                return 0.5

            # Use interaction count and satisfaction
            satisfaction = agent_pref.get("satisfaction", 0.5)
            interactions = agent_pref.get("interactions", 0)

            # Boost for more interactions (shows preference)
            interaction_factor = min(1.0, interactions / 10)  # Cap at 10 interactions

            return (satisfaction + interaction_factor) / 2

        except Exception as e:
            logger.error(f"Error scoring user preference: {e}")
            return 0.5

    def _score_context_fit(
        self,
        agent: Agent,
        signals: Dict[str, Any],
        current_agents: List[str]
    ) -> float:
        """Score how well agent fits current conversation context."""
        score = 0.5  # Base score

        # Prefer diverse expertise (don't add duplicate roles)
        # This would require checking current agents' roles
        # Simplified version:
        if len(current_agents) > 3:
            score -= 0.2  # Reduce score if many agents already involved

        # Match complexity
        complexity = signals.get("complexity", "moderate")
        if complexity == "expert" and ("cto" in agent.role.lower() or "senior" in agent.role.lower()):
            score += 0.3
        elif complexity == "simple" and ("junior" in agent.role.lower() or "assistant" in agent.role.lower()):
            score += 0.2

        return max(0.0, min(1.0, score))

    async def _score_availability(
        self,
        db: AsyncSession,
        agent: Agent
    ) -> float:
        """Score agent's current availability."""
        try:
            from app.db.models import AgentStatus, Availability

            query = select(AgentStatus).where(
                AgentStatus.agent_id == agent.agent_id
            )

            result = await db.execute(query)
            status = result.scalar_one_or_none()

            if not status:
                return 0.5

            availability_scores = {
                Availability.AVAILABLE: 1.0,
                Availability.BUSY: 0.5,
                Availability.BLOCKED: 0.2,
                Availability.OFFLINE: 0.0
            }

            return availability_scores.get(status.availability, 0.5)

        except Exception as e:
            logger.error(f"Error scoring availability: {e}")
            return 0.5

    def _calculate_confidence(self, scores: Dict[str, float]) -> float:
        """Calculate overall confidence in prediction."""
        # Confidence is higher when scores are consistent
        score_values = list(scores.values())
        avg_score = sum(score_values) / len(score_values)
        variance = sum((s - avg_score) ** 2 for s in score_values) / len(score_values)

        # Low variance = high confidence
        confidence = 1.0 - min(1.0, variance)

        return max(0.5, confidence)  # Min confidence of 0.5

    def _determine_involvement_strategy(
        self,
        probability: float,
        scores: Dict[str, float],
        signals: Dict[str, Any]
    ) -> Tuple[AgentInvolvementType, InvolvementTiming, InvolvementApproach]:
        """Determine how and when to involve the agent."""
        # Determine type
        if probability > 0.9 and scores["expertise_match"] > 0.8:
            inv_type = AgentInvolvementType.PRIMARY_EXPERT
        elif probability > 0.75:
            inv_type = AgentInvolvementType.SECONDARY_SUPPORT
        elif probability > 0.6:
            inv_type = AgentInvolvementType.REVIEWER
        else:
            inv_type = AgentInvolvementType.OPTIONAL

        # Determine timing
        urgency = signals.get("urgency", "medium")

        if urgency == "high" and probability > 0.8:
            timing = InvolvementTiming.IMMEDIATE
        elif probability > 0.85:
            timing = InvolvementTiming.AFTER_INITIAL_DISCUSSION
        elif probability > 0.7:
            timing = InvolvementTiming.WHEN_TOPIC_ARISES
        else:
            timing = InvolvementTiming.ON_DEMAND

        # Determine approach
        if probability > 0.9 and urgency == "high":
            approach = InvolvementApproach.AUTO_JOIN
        elif probability > 0.75:
            approach = InvolvementApproach.SUGGEST_TO_USER
        else:
            approach = InvolvementApproach.PREPARE_STANDBY

        return inv_type, timing, approach

    def _generate_trigger_reasons(
        self,
        scores: Dict[str, float],
        signals: Dict[str, Any]
    ) -> List[str]:
        """Generate human-readable reasons for the prediction."""
        reasons = []

        if scores["expertise_match"] > 0.7:
            required = ", ".join(signals.get("required_expertise", [])[:3])
            reasons.append(f"Strong expertise match for: {required}")

        if scores["historical_success"] > 0.8:
            reasons.append("High historical success rate in similar contexts")

        if scores["user_preference"] > 0.7:
            reasons.append("User has preferred this agent in the past")

        topics = signals.get("topics", [])
        if topics:
            reasons.append(f"Relevant topics detected: {', '.join(topics[:3])}")

        if signals.get("complexity") == "expert":
            reasons.append("Complex discussion requiring expert-level input")

        if signals.get("urgency") == "high":
            reasons.append("High urgency indicated")

        return reasons[:5]  # Max 5 reasons

    # ===== PERSISTENCE =====

    async def _store_prediction(
        self,
        db: AsyncSession,
        conversation_id: Optional[UUID],
        project_id: Optional[UUID],
        prediction_data: Dict[str, Any]
    ) -> None:
        """Store prediction in database for learning."""
        try:
            prediction = AgentInvolvementPrediction(
                conversation_id=conversation_id,
                project_id=project_id,
                agent_id=prediction_data["agent_id"],
                involvement_probability=prediction_data["involvement_probability"],
                confidence=prediction_data["confidence"],
                predicted_contribution_type=AgentInvolvementType(prediction_data["predicted_contribution_type"]),
                suggested_timing=InvolvementTiming(prediction_data["suggested_timing"]),
                introduction_approach=InvolvementApproach(prediction_data["introduction_approach"]),
                trigger_reasons=prediction_data["trigger_reasons"],
                signal_strength=prediction_data["signal_strength"]
            )

            db.add(prediction)
            await db.commit()

        except Exception as e:
            logger.error(f"Error storing prediction: {e}")
            await db.rollback()

    # ===== OUTCOME TRACKING =====

    async def record_involvement_outcome(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        agent_id: str,
        involvement_type: str,
        user_feedback: Dict[str, Any],
        prediction_id: Optional[UUID] = None
    ) -> None:
        """Record actual outcome of agent involvement for learning."""
        try:
            outcome = AgentInvolvementOutcome(
                conversation_id=conversation_id,
                agent_id=agent_id,
                involvement_type=involvement_type,
                joined_at=datetime.utcnow(),
                user_satisfaction_rating=user_feedback.get("satisfaction", 0.5),
                contribution_helpfulness=user_feedback.get("helpfulness", 0.5),
                response_quality_score=user_feedback.get("quality", 0.5),
                timing_appropriateness=user_feedback.get("timing", 0.5),
                was_predicted=prediction_id is not None,
                prediction_id=prediction_id,
                user_feedback=user_feedback
            )

            db.add(outcome)

            # Calculate prediction accuracy if this was predicted
            if prediction_id:
                await self._update_prediction_accuracy(db, prediction_id, outcome)

            await db.commit()

        except Exception as e:
            logger.error(f"Error recording involvement outcome: {e}")
            await db.rollback()

    async def _update_prediction_accuracy(
        self,
        db: AsyncSession,
        prediction_id: UUID,
        outcome: AgentInvolvementOutcome
    ) -> None:
        """Update prediction with actual outcome accuracy."""
        try:
            prediction = await db.get(AgentInvolvementPrediction, prediction_id)

            if prediction:
                # Calculate accuracy based on user satisfaction
                prediction.prediction_accuracy = outcome.user_satisfaction_rating
                prediction.actual_involvement = outcome.involvement_type
                prediction.involvement_timing = outcome.joined_at
                prediction.user_satisfaction = outcome.user_satisfaction_rating
                prediction.contribution_quality = outcome.contribution_helpfulness
                prediction.resolved_at = datetime.utcnow()

        except Exception as e:
            logger.error(f"Error updating prediction accuracy: {e}")


# Singleton instance
_predictive_involvement_service: Optional[PredictiveAgentInvolvementService] = None


def get_predictive_involvement_service() -> PredictiveAgentInvolvementService:
    """Get or create singleton predictive involvement service."""
    global _predictive_involvement_service
    if _predictive_involvement_service is None:
        _predictive_involvement_service = PredictiveAgentInvolvementService()
    return _predictive_involvement_service
