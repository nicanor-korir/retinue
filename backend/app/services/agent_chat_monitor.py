"""
Agent Chat Monitor Service

Background service that allows agents to autonomously monitor conversations
and request to join when they detect they're needed.

Features:
- Async monitoring of all active conversations
- Agent self-detection based on mentions, expertise needs
- Approval workflow through responsible agent (e.g., CEO/PM)
- Auto-assignment to projects/tasks upon joining
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set, Any
from uuid import UUID
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.db.database import AsyncSessionLocal
from app.db.models import Agent, Project, Task
from app.db.conversation_models import (
    Conversation, ConversationMessage, ConversationParticipant,
    SenderType, ParticipantType
)
from app.db.multi_agent_models import AgentInvitation, AgentPresence
from app.services.message_analyzer import MessageAnalyzer
from app.services.multi_agent_orchestrator import MultiAgentOrchestrator, InvitationRequest
from app.services.context_briefing_service import ContextBriefingService
from app.services.websocket_manager import broadcast_activity

logger = logging.getLogger(__name__)


class JoinRequestStatus(str, Enum):
    """Status of agent join request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"


@dataclass
class AgentJoinRequest:
    """Request from an agent to join a conversation."""
    request_id: str
    conversation_id: UUID
    requesting_agent_id: str
    requesting_agent_name: str
    approving_agent_id: str  # Agent who can approve (e.g., CEO, PM)
    reason: str
    confidence: float
    detected_keywords: List[str]
    relevant_message_ids: List[str]
    status: JoinRequestStatus = JoinRequestStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    responded_at: Optional[datetime] = None
    response_message: Optional[str] = None


class AgentChatMonitor:
    """
    Background service for agents to monitor conversations autonomously.

    Agents can:
    1. Monitor conversations for mentions or expertise needs
    2. Request to join conversations
    3. Get approved by responsible agent (CEO/PM)
    4. Auto-join projects/tasks upon approval
    """

    # Agents that can approve other agents joining
    APPROVER_AGENTS = ['ceo_001', 'cto_001', 'pm_001', 'chro_001']

    # Default approver if no specific one is found
    DEFAULT_APPROVER = 'ceo_001'

    # Confidence threshold for auto-approval
    AUTO_APPROVAL_THRESHOLD = 0.95

    # How often to check for new messages (seconds)
    MONITOR_INTERVAL = 10

    # How many recent messages to analyze
    MESSAGES_TO_ANALYZE = 10

    def __init__(self):
        self.analyzer = MessageAnalyzer()
        self.orchestrator = MultiAgentOrchestrator()
        self.briefing_service = ContextBriefingService()

        # Track active monitoring
        self._monitoring_active = False
        self._monitored_conversations: Set[UUID] = set()
        self._pending_requests: Dict[str, AgentJoinRequest] = {}
        self._last_checked: Dict[UUID, datetime] = {}

        # Agent expertise cache
        self._agent_expertise: Dict[str, List[str]] = {}

    async def start_monitoring(self):
        """Start the background monitoring service."""
        if self._monitoring_active:
            logger.warning("Agent monitoring is already active")
            return

        self._monitoring_active = True
        logger.info("Starting agent chat monitoring service")

        # Start the monitoring loop
        asyncio.create_task(self._monitoring_loop())

    async def stop_monitoring(self):
        """Stop the background monitoring service."""
        self._monitoring_active = False
        logger.info("Stopping agent chat monitoring service")

    async def _monitoring_loop(self):
        """Main monitoring loop that runs in background."""
        while self._monitoring_active:
            try:
                async with AsyncSessionLocal() as session:
                    # Get all active conversations
                    conversations = await self._get_active_conversations(session)

                    for conversation in conversations:
                        try:
                            await self._analyze_conversation(session, conversation)
                        except Exception as conv_error:
                            # Log but continue with other conversations
                            logger.warning(
                                f"Error analyzing conversation {conversation.conversation_id}: {conv_error}"
                            )
                            continue

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)

            # Wait before next check
            await asyncio.sleep(self.MONITOR_INTERVAL)

    async def _get_active_conversations(
        self,
        session: AsyncSession
    ) -> List[Conversation]:
        """Get all active conversations to monitor."""
        # Get conversations that have had activity in last hour
        cutoff = datetime.utcnow() - timedelta(hours=1)

        result = await session.execute(
            select(Conversation)
            .where(
                and_(
                    Conversation.status == 'active',
                    or_(
                        Conversation.last_message_at >= cutoff,
                        Conversation.last_message_at.is_(None)
                    )
                )
            )
        )
        return list(result.scalars().all())

    async def _analyze_conversation(
        self,
        session: AsyncSession,
        conversation: Conversation
    ):
        """Analyze a conversation for agent needs."""
        conversation_id = conversation.conversation_id

        # Check if we've analyzed this recently
        last_check = self._last_checked.get(conversation_id)
        if last_check and (datetime.utcnow() - last_check).seconds < self.MONITOR_INTERVAL:
            return

        self._last_checked[conversation_id] = datetime.utcnow()

        # Get recent messages since last check
        messages = await self._get_recent_messages(
            session, conversation_id, self.MESSAGES_TO_ANALYZE
        )

        if not messages:
            return

        # Get current participants
        current_participants = await self._get_current_participants(session, conversation_id)
        current_agent_ids = [p.participant_id_ref for p in current_participants if p.participant_type == ParticipantType.AGENT]

        # Get all available agents
        all_agents = await self._get_all_agents(session)

        # Check each agent not in conversation
        for agent in all_agents:
            if agent.agent_id in current_agent_ids:
                continue

            # Analyze if this agent should join
            should_join, reason, confidence, keywords = await self._should_agent_join(
                session, agent, messages, current_agent_ids
            )

            if should_join:
                await self._create_join_request(
                    session,
                    conversation,
                    agent,
                    reason,
                    confidence,
                    keywords,
                    [str(m.message_id) for m in messages[-3:]]  # Last 3 relevant messages
                )

    async def _should_agent_join(
        self,
        session: AsyncSession,
        agent: Agent,
        messages: List[ConversationMessage],
        current_agent_ids: List[str]
    ) -> tuple[bool, str, float, List[str]]:
        """
        Determine if an agent should request to join based on messages.

        Returns:
            Tuple of (should_join, reason, confidence, detected_keywords)
        """
        combined_content = ' '.join(m.content.lower() for m in messages)

        # 1. Check for direct mentions
        agent_mentions = self._check_agent_mentions(agent, combined_content)
        if agent_mentions:
            return True, f"Directly mentioned: {', '.join(agent_mentions)}", 0.95, agent_mentions

        # 2. Check for expertise/role keywords
        expertise_match = self._check_expertise_match(agent, combined_content)
        if expertise_match['score'] > 0.7:
            return True, expertise_match['reason'], expertise_match['score'], expertise_match['keywords']

        # 3. Check for department/topic relevance
        topic_match = self._check_topic_relevance(agent, combined_content)
        if topic_match['score'] > 0.8:
            return True, topic_match['reason'], topic_match['score'], topic_match['keywords']

        return False, "", 0.0, []

    def _check_agent_mentions(self, agent: Agent, content: str) -> List[str]:
        """Check if agent is directly mentioned."""
        mentions = []

        # Check agent name
        if agent.name.lower() in content:
            mentions.append(agent.name)

        # Check role
        if agent.role.lower() in content:
            mentions.append(agent.role)

        # Check common variations
        role_variations = {
            'cfo': ['cfo', 'chief financial', 'finance officer', 'financial officer'],
            'cto': ['cto', 'chief technology', 'tech officer', 'technology officer'],
            'ceo': ['ceo', 'chief executive', 'executive officer'],
            'chro': ['chro', 'chief hr', 'hr officer', 'human resources officer'],
            'pm': ['project manager', 'product manager', 'pm'],
            'designer': ['designer', 'ux designer', 'ui designer'],
            'backend': ['backend', 'backend engineer', 'backend developer'],
            'frontend': ['frontend', 'frontend engineer', 'frontend developer'],
        }

        agent_role_key = agent.agent_id.replace('_001', '').lower()
        if agent_role_key in role_variations:
            for variation in role_variations[agent_role_key]:
                if variation in content:
                    mentions.append(variation)

        return list(set(mentions))

    def _check_expertise_match(self, agent: Agent, content: str) -> Dict[str, Any]:
        """Check if content matches agent expertise."""
        expertise_keywords = {
            'cfo_001': {
                'keywords': ['budget', 'cost', 'financial', 'revenue', 'expense', 'profit', 'loss', 'roi', 'investment', 'funding'],
                'weight': 0.85
            },
            'cto_001': {
                'keywords': ['technical', 'architecture', 'infrastructure', 'scalability', 'technology', 'system design', 'engineering'],
                'weight': 0.85
            },
            'ceo_001': {
                'keywords': ['strategy', 'vision', 'leadership', 'company', 'executive', 'decision', 'direction'],
                'weight': 0.80
            },
            'chro_001': {
                'keywords': ['hiring', 'recruitment', 'employee', 'talent', 'team', 'culture', 'hr', 'human resources', 'staffing'],
                'weight': 0.85
            },
            'pm_001': {
                'keywords': ['project', 'timeline', 'milestone', 'deliverable', 'scope', 'requirement', 'sprint', 'backlog'],
                'weight': 0.85
            },
            'designer_001': {
                'keywords': ['design', 'ui', 'ux', 'user experience', 'interface', 'mockup', 'wireframe', 'visual'],
                'weight': 0.85
            },
            'backend_001': {
                'keywords': ['api', 'database', 'server', 'backend', 'endpoint', 'query', 'performance'],
                'weight': 0.85
            },
            'frontend_001': {
                'keywords': ['frontend', 'ui', 'component', 'react', 'css', 'javascript', 'user interface'],
                'weight': 0.85
            },
            'marketing_manager_001': {
                'keywords': ['marketing', 'campaign', 'brand', 'promotion', 'advertising', 'social media', 'content'],
                'weight': 0.85
            },
            'sales_manager_001': {
                'keywords': ['sales', 'customer', 'deal', 'pipeline', 'revenue', 'client', 'prospect', 'conversion'],
                'weight': 0.85
            },
            'financial_analyst_001': {
                'keywords': ['analysis', 'forecast', 'model', 'projection', 'metrics', 'kpi', 'data'],
                'weight': 0.80
            },
        }

        agent_config = expertise_keywords.get(agent.agent_id, {'keywords': [], 'weight': 0.5})
        matched_keywords = [kw for kw in agent_config['keywords'] if kw in content]

        if not matched_keywords:
            return {'score': 0.0, 'reason': '', 'keywords': []}

        # Calculate score based on number of matches
        match_ratio = len(matched_keywords) / len(agent_config['keywords'])
        score = min(agent_config['weight'] + (match_ratio * 0.15), 0.95)

        return {
            'score': score,
            'reason': f"Expertise match: {', '.join(matched_keywords[:3])}",
            'keywords': matched_keywords
        }

    def _check_topic_relevance(self, agent: Agent, content: str) -> Dict[str, Any]:
        """Check topic relevance for agent."""
        # Department-topic mapping
        department_topics = {
            'finance': ['budget', 'cost', 'money', 'financial', 'payment', 'invoice'],
            'engineering': ['code', 'bug', 'feature', 'technical', 'development', 'deploy'],
            'hr': ['hire', 'team', 'employee', 'culture', 'interview', 'onboard'],
            'marketing': ['campaign', 'brand', 'content', 'social', 'promotion'],
            'sales': ['customer', 'deal', 'sale', 'client', 'lead', 'prospect'],
            'design': ['design', 'ui', 'ux', 'visual', 'mockup', 'prototype'],
        }

        # Map agents to departments
        agent_departments = {
            'cfo_001': ['finance'],
            'cto_001': ['engineering'],
            'ceo_001': ['finance', 'engineering', 'hr', 'marketing', 'sales'],  # CEO oversees all
            'chro_001': ['hr'],
            'pm_001': ['engineering'],
            'designer_001': ['design'],
            'backend_001': ['engineering'],
            'frontend_001': ['engineering', 'design'],
            'marketing_manager_001': ['marketing'],
            'sales_manager_001': ['sales'],
            'financial_analyst_001': ['finance'],
        }

        agent_depts = agent_departments.get(agent.agent_id, [])
        matched_topics = []

        for dept in agent_depts:
            topics = department_topics.get(dept, [])
            for topic in topics:
                if topic in content:
                    matched_topics.append(topic)

        if not matched_topics:
            return {'score': 0.0, 'reason': '', 'keywords': []}

        score = min(0.7 + (len(matched_topics) * 0.05), 0.9)
        unique_topics = list(set(matched_topics))

        return {
            'score': score,
            'reason': f"Topic relevance: {', '.join(unique_topics[:3])}",
            'keywords': unique_topics
        }

    async def _create_join_request(
        self,
        session: AsyncSession,
        conversation: Conversation,
        agent: Agent,
        reason: str,
        confidence: float,
        keywords: List[str],
        message_ids: List[str]
    ):
        """Create a join request and notify approving agent."""
        conversation_id = conversation.conversation_id

        # Check if there's already a pending request
        request_key = f"{conversation_id}:{agent.agent_id}"
        if request_key in self._pending_requests:
            existing = self._pending_requests[request_key]
            if existing.status == JoinRequestStatus.PENDING:
                return  # Already pending

        # Determine approving agent
        approving_agent_id = await self._determine_approver(session, conversation)

        # Create the request
        import uuid
        request = AgentJoinRequest(
            request_id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            requesting_agent_id=agent.agent_id,
            requesting_agent_name=agent.name,
            approving_agent_id=approving_agent_id,
            reason=reason,
            confidence=confidence,
            detected_keywords=keywords,
            relevant_message_ids=message_ids
        )

        # Check for auto-approval
        if confidence >= self.AUTO_APPROVAL_THRESHOLD:
            request.status = JoinRequestStatus.AUTO_APPROVED
            await self._process_approved_request(session, request, conversation)
            logger.info(f"Auto-approved {agent.agent_id} to join conversation {conversation_id}")
        else:
            # Store pending request
            self._pending_requests[request_key] = request

            # Notify approving agent
            await self._notify_approver(session, request, conversation)
            logger.info(f"Created join request for {agent.agent_id} to conversation {conversation_id}, awaiting approval from {approving_agent_id}")

    async def _determine_approver(
        self,
        session: AsyncSession,
        conversation: Conversation
    ) -> str:
        """Determine which agent should approve join requests."""
        # If primary agent is an approver, use them
        if conversation.primary_agent_id in self.APPROVER_AGENTS:
            return conversation.primary_agent_id

        # Check current participants for an approver
        participants = await self._get_current_participants(session, conversation.conversation_id)
        for p in participants:
            if p.participant_type == ParticipantType.AGENT and p.participant_id_ref in self.APPROVER_AGENTS:
                return p.participant_id_ref

        # Default to CEO
        return self.DEFAULT_APPROVER

    async def _notify_approver(
        self,
        session: AsyncSession,
        request: AgentJoinRequest,
        conversation: Conversation
    ):
        """Notify the approving agent about a join request."""
        # Create a system message in the conversation
        from app.services.message_handler import MessageHandler

        notification_content = (
            f"**Agent Join Request**\n\n"
            f"**{request.requesting_agent_name}** is requesting to join this conversation.\n\n"
            f"**Reason:** {request.reason}\n"
            f"**Confidence:** {request.confidence:.0%}\n"
            f"**Detected keywords:** {', '.join(request.detected_keywords[:5])}\n\n"
            f"To approve, reply: `@approve {request.requesting_agent_id}`\n"
            f"To reject, reply: `@reject {request.requesting_agent_id}`"
        )

        await MessageHandler.create_message(
            session=session,
            conversation_id=request.conversation_id,
            sender_type=SenderType.SYSTEM,
            sender_id='agent_monitor',
            sender_name='Agent Monitor',
            content=notification_content,
            message_metadata={
                'type': 'join_request',
                'request_id': request.request_id,
                'requesting_agent_id': request.requesting_agent_id,
                'approving_agent_id': request.approving_agent_id
            }
        )

        # Broadcast via WebSocket
        await broadcast_activity(
            project_id=str(conversation.project_id) if conversation.project_id else None,
            agent_id=request.approving_agent_id,
            event_type="agent_join_request",
            data={
                'request_id': request.request_id,
                'conversation_id': str(request.conversation_id),
                'requesting_agent_id': request.requesting_agent_id,
                'requesting_agent_name': request.requesting_agent_name,
                'reason': request.reason,
                'confidence': request.confidence
            }
        )

    async def _process_approved_request(
        self,
        session: AsyncSession,
        request: AgentJoinRequest,
        conversation: Conversation
    ):
        """Process an approved join request."""
        try:
            # 1. Add agent to conversation
            invitation_request = InvitationRequest(
                agent_id=request.requesting_agent_id,
                invited_by_type='agent',
                invited_by_id=request.approving_agent_id,
                reason=request.reason,
                urgency='normal',
                prediction_score=request.confidence
            )

            # Generate briefing (with error handling)
            briefing = None
            try:
                briefing = await self.briefing_service.generate_briefing(
                    db=session,
                    conversation_id=request.conversation_id,
                    agent_id=request.requesting_agent_id
                )
            except Exception as briefing_error:
                logger.warning(f"Failed to generate briefing: {briefing_error}")
                briefing = {"error": "Briefing generation failed"}

            # Create invitation
            invitation = await self.orchestrator.invite_agent(
                db=session,
                conversation_id=request.conversation_id,
                invitation_request=invitation_request,
                context_summary=briefing
            )

            # Auto-accept the invitation (since it's already approved)
            if invitation and invitation.status == "pending":
                await self.orchestrator.accept_invitation(session, invitation.invitation_id)

            # 2. If conversation has a project, add agent to project
            if conversation.project_id:
                try:
                    await self._add_agent_to_project(session, request.requesting_agent_id, conversation.project_id)
                except Exception as project_error:
                    logger.warning(f"Failed to add agent to project: {project_error}")

            # 3. Create join notification message
            from app.services.message_handler import MessageHandler

            join_message = (
                f"**{request.requesting_agent_name}** has joined the conversation.\n"
                f"*Reason: {request.reason}*"
            )

            try:
                await MessageHandler.create_message(
                    session=session,
                    conversation_id=request.conversation_id,
                    sender_type=SenderType.SYSTEM,
                    sender_id='agent_monitor',
                    sender_name='Agent Monitor',
                    content=join_message,
                    message_metadata={
                        'type': 'agent_joined',
                        'agent_id': request.requesting_agent_id,
                        'auto_approved': request.status == JoinRequestStatus.AUTO_APPROVED
                    }
                )
            except Exception as msg_error:
                logger.warning(f"Failed to create join message: {msg_error}")

            # 4. Broadcast join event
            try:
                await broadcast_activity(
                    project_id=str(conversation.project_id) if conversation.project_id else None,
                    agent_id=request.requesting_agent_id,
                    event_type="agent_joined_conversation",
                    data={
                        'conversation_id': str(request.conversation_id),
                        'agent_id': request.requesting_agent_id,
                        'agent_name': request.requesting_agent_name,
                        'reason': request.reason,
                        'joined_at': datetime.utcnow().isoformat()
                    }
                )
            except Exception as broadcast_error:
                logger.warning(f"Failed to broadcast join event: {broadcast_error}")

            logger.info(f"Successfully processed join request for {request.requesting_agent_id}")

        except Exception as e:
            logger.error(f"Error processing approved request: {e}", exc_info=True)
            raise

    async def _add_agent_to_project(
        self,
        session: AsyncSession,
        agent_id: str,
        project_id: UUID
    ):
        """Add agent to project team."""
        # Check if already assigned
        project = await session.get(Project, project_id)
        if not project:
            return

        # Update project's assigned agents
        assigned_agents = project.assigned_agents or []
        if agent_id not in assigned_agents:
            assigned_agents.append(agent_id)
            project.assigned_agents = assigned_agents
            await session.commit()

            logger.info(f"Added agent {agent_id} to project {project_id}")

    async def process_approval_response(
        self,
        session: AsyncSession,
        conversation_id: UUID,
        approving_agent_id: str,
        target_agent_id: str,
        approved: bool,
        response_message: Optional[str] = None
    ) -> bool:
        """
        Process an approval/rejection response from an approving agent.

        Args:
            session: Database session
            conversation_id: Conversation ID
            approving_agent_id: Agent making the decision
            target_agent_id: Agent requesting to join
            approved: Whether approved or rejected
            response_message: Optional response message

        Returns:
            True if processed successfully
        """
        request_key = f"{conversation_id}:{target_agent_id}"
        request = self._pending_requests.get(request_key)

        if not request:
            logger.warning(f"No pending request found for {request_key}")
            return False

        if request.approving_agent_id != approving_agent_id:
            logger.warning(f"Agent {approving_agent_id} not authorized to approve this request")
            return False

        request.responded_at = datetime.utcnow()
        request.response_message = response_message

        if approved:
            request.status = JoinRequestStatus.APPROVED

            # Get conversation
            result = await session.execute(
                select(Conversation).where(Conversation.conversation_id == conversation_id)
            )
            conversation = result.scalar_one_or_none()

            if conversation:
                await self._process_approved_request(session, request, conversation)
        else:
            request.status = JoinRequestStatus.REJECTED

            # Send rejection message
            from app.services.message_handler import MessageHandler

            rejection_message = (
                f"**{request.requesting_agent_name}**'s request to join was declined.\n"
                f"*{response_message or 'No reason provided'}*"
            )

            await MessageHandler.create_message(
                session=session,
                conversation_id=conversation_id,
                sender_type=SenderType.SYSTEM,
                sender_id='agent_monitor',
                sender_name='Agent Monitor',
                content=rejection_message
            )

        # Remove from pending
        del self._pending_requests[request_key]

        return True

    # Helper methods

    async def _get_recent_messages(
        self,
        session: AsyncSession,
        conversation_id: UUID,
        limit: int
    ) -> List[ConversationMessage]:
        """Get recent messages from conversation."""
        result = await session.execute(
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation_id)
            .order_by(ConversationMessage.created_at.desc())
            .limit(limit)
        )
        messages = list(result.scalars().all())
        messages.reverse()
        return messages

    async def _get_current_participants(
        self,
        session: AsyncSession,
        conversation_id: UUID
    ) -> List[ConversationParticipant]:
        """Get current participants."""
        result = await session.execute(
            select(ConversationParticipant)
            .where(
                and_(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.is_active == True
                )
            )
        )
        return list(result.scalars().all())

    async def _get_all_agents(self, session: AsyncSession) -> List[Agent]:
        """Get all available agents."""
        result = await session.execute(
            select(Agent).where(Agent.status == "active")
        )
        return list(result.scalars().all())


# Global instance
_chat_monitor: Optional[AgentChatMonitor] = None


def get_chat_monitor() -> AgentChatMonitor:
    """Get the global chat monitor instance."""
    global _chat_monitor
    if _chat_monitor is None:
        _chat_monitor = AgentChatMonitor()
    return _chat_monitor


async def start_agent_monitoring():
    """Start the agent chat monitoring service."""
    monitor = get_chat_monitor()
    await monitor.start_monitoring()


async def stop_agent_monitoring():
    """Stop the agent chat monitoring service."""
    monitor = get_chat_monitor()
    await monitor.stop_monitoring()
