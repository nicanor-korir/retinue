"""
Multi-Agent Orchestrator Service

Orchestrates multi-agent conversations including:
- Agent invitation and joining
- Presence management
- Turn-based coordination
- Response coordination
- Broadcast notifications
"""

import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func
from pydantic import BaseModel

from app.db.models import Agent
from app.db.conversation_models import (
    Conversation,
    ConversationMessage,
    ConversationParticipant,
    ParticipantType,
    ParticipantRole,
    SenderType
)
from app.db.multi_agent_models import (
    AgentInvitation,
    AgentPresence,
    ConversationTurn,
    AgentCollaborationSession,
    # Enums are now strings in the database, keeping imports for type hints only
    InvitationStatus,
    InvitationType,
    InvitedByType,
    Urgency,
    AgentPresenceStatus,
    TurnStatus,
    TurnType,
    CoordinationStrategy
)

logger = logging.getLogger(__name__)


class InvitationRequest(BaseModel):
    """Request to invite an agent."""
    agent_id: str
    invited_by_type: str  # 'user', 'agent', 'system'
    invited_by_id: str
    invited_by_name: Optional[str] = None
    reason: Optional[str] = None
    specific_question: Optional[str] = None
    urgency: str = "normal"
    auto_accept: bool = False
    prediction_score: Optional[float] = None


class MultiAgentOrchestrator:
    """Service for orchestrating multi-agent conversations."""

    # Auto-join threshold for highly relevant agents
    AUTO_JOIN_THRESHOLD = 0.9

    # Instant turn timeout (5 seconds for processing)
    TURN_TIMEOUT_SECONDS = 5

    def __init__(self):
        """Initialize orchestrator."""
        pass

    async def invite_agent(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        invitation_request: InvitationRequest,
        context_summary: Optional[Dict[str, Any]] = None
    ) -> AgentInvitation:
        """
        Invite an agent to join a conversation.

        Args:
            db: Database session
            conversation_id: Conversation to invite to
            invitation_request: Invitation details
            context_summary: Optional context briefing

        Returns:
            Created AgentInvitation
        """
        logger.info(
            f"Inviting agent {invitation_request.agent_id} to conversation {conversation_id}"
        )

        # Check if agent already participating
        existing_participant = await self._get_participant(
            db, conversation_id, invitation_request.agent_id
        )
        if existing_participant and existing_participant.is_active:
            logger.warning(f"Agent {invitation_request.agent_id} already in conversation")
            raise ValueError("Agent is already participating in this conversation")

        # Check for pending invitation
        existing_invitation = await self._get_pending_invitation(
            db, conversation_id, invitation_request.agent_id
        )
        if existing_invitation:
            logger.info("Pending invitation exists, returning it")
            return existing_invitation

        # Determine if should auto-accept based on score
        auto_accept = invitation_request.auto_accept
        if invitation_request.prediction_score and invitation_request.prediction_score >= self.AUTO_JOIN_THRESHOLD:
            auto_accept = True
            logger.info(f"Auto-accept enabled for high relevance score: {invitation_request.prediction_score}")

        # Create invitation
        invitation = AgentInvitation(
            conversation_id=conversation_id,
            agent_id=invitation_request.agent_id,
            invited_by_type=invitation_request.invited_by_type,  # Already a string
            invited_by_id=invitation_request.invited_by_id,
            invited_by_name=invitation_request.invited_by_name,
            invitation_reason=invitation_request.reason,
            specific_question=invitation_request.specific_question,
            context_summary=context_summary or {},
            prediction_score=invitation_request.prediction_score,
            invitation_type="auto" if auto_accept else "suggested",  # Using string values
            urgency=invitation_request.urgency,  # Already a string
            auto_accept=auto_accept,
            requires_user_approval=not auto_accept,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )

        db.add(invitation)
        await db.commit()
        await db.refresh(invitation)

        # If auto-accept, immediately join the agent
        if auto_accept:
            logger.info(f"Auto-joining agent {invitation_request.agent_id}")
            await self.handle_agent_join(
                db, conversation_id, invitation_request.agent_id, invitation.invitation_id
            )
            invitation.status = "accepted"
            invitation.accepted_at = datetime.utcnow()
            invitation.resulted_in_participation = True
            await db.commit()

        logger.info(f"Created invitation {invitation.invitation_id}")
        return invitation

    async def handle_agent_join(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        agent_id: str,
        invitation_id: Optional[UUID] = None
    ) -> ConversationParticipant:
        """
        Handle an agent joining a conversation.

        Args:
            db: Database session
            conversation_id: Conversation ID
            agent_id: Agent joining
            invitation_id: Related invitation ID

        Returns:
            Created ConversationParticipant
        """
        logger.info(f"Agent {agent_id} joining conversation {conversation_id}")

        # Get agent details for participant name
        agent = await self._get_agent(db, agent_id)
        participant_name = agent.name if agent else agent_id

        # Create participant record
        participant = ConversationParticipant(
            conversation_id=conversation_id,
            participant_type=ParticipantType.AGENT,
            participant_id_ref=agent_id,
            participant_name=participant_name,
            participant_role=ParticipantRole.AGENT,
            is_active=True,
            meta_data={"invitation_id": str(invitation_id) if invitation_id else None}
        )

        db.add(participant)

        # Update conversation participant count
        await db.execute(
            update(Conversation)
            .where(Conversation.conversation_id == conversation_id)
            .values(
                participant_count=Conversation.participant_count + 1,
                updated_at=datetime.utcnow()
            )
        )

        # Create presence record
        presence = AgentPresence(
            conversation_id=conversation_id,
            agent_id=agent_id,
            status="active",  # Using string value instead of enum
            activity="just_joined",
            is_online=True
        )
        db.add(presence)

        # Check if this starts a collaboration session
        active_agents = await self._get_active_agent_count(db, conversation_id)
        if active_agents >= 2:  # Multiple agents now present
            await self._ensure_collaboration_session(db, conversation_id)

        await db.commit()
        await db.refresh(participant)

        logger.info(f"Agent {agent_id} successfully joined conversation")
        return participant

    async def handle_agent_leave(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        agent_id: str,
        reason: Optional[str] = None
    ):
        """
        Handle an agent leaving a conversation.

        Args:
            db: Database session
            conversation_id: Conversation ID
            agent_id: Agent leaving
            reason: Optional reason for leaving
        """
        logger.info(f"Agent {agent_id} leaving conversation {conversation_id}: {reason}")

        # Mark participant as inactive
        await db.execute(
            update(ConversationParticipant)
            .where(
                and_(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.participant_id_ref == agent_id
                )
            )
            .values(
                is_active=False,
                left_at=datetime.utcnow()
            )
        )

        # Update presence to away
        await db.execute(
            update(AgentPresence)
            .where(
                and_(
                    AgentPresence.conversation_id == conversation_id,
                    AgentPresence.agent_id == agent_id
                )
            )
            .values(
                status="away",  # Using string value instead of enum
                is_online=False,
                activity=f"left: {reason}" if reason else "left"
            )
        )

        # Update conversation participant count
        await db.execute(
            update(Conversation)
            .where(Conversation.conversation_id == conversation_id)
            .values(
                participant_count=Conversation.participant_count - 1,
                updated_at=datetime.utcnow()
            )
        )

        await db.commit()
        logger.info(f"Agent {agent_id} left conversation")

    async def update_agent_presence(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        agent_id: str,
        status: str,
        activity: Optional[str] = None
    ):
        """
        Update agent presence status.

        Args:
            db: Database session
            conversation_id: Conversation ID
            agent_id: Agent ID
            status: New status (active, thinking, typing, idle, away)
            activity: Optional activity description
        """
        await db.execute(
            update(AgentPresence)
            .where(
                and_(
                    AgentPresence.conversation_id == conversation_id,
                    AgentPresence.agent_id == agent_id
                )
            )
            .values(
                status=AgentPresenceStatus(status),
                activity=activity,
                last_active_at=datetime.utcnow(),
                last_status_change_at=datetime.utcnow()
            )
        )
        await db.commit()

        logger.debug(f"Updated presence for {agent_id}: {status}")

    async def create_turn(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        triggered_by_message_id: UUID,
        assigned_agents: List[str],
        turn_type: str = "parallel"
    ) -> ConversationTurn:
        """
        Create a conversation turn for coordinated agent responses.

        Args:
            db: Database session
            conversation_id: Conversation ID
            triggered_by_message_id: Message that triggered this turn
            assigned_agents: Agent IDs expected to respond
            turn_type: Type of turn (single, parallel, sequential)

        Returns:
            Created ConversationTurn
        """
        # Get next turn number
        result = await db.execute(
            select(func.max(ConversationTurn.turn_number))
            .where(ConversationTurn.conversation_id == conversation_id)
        )
        max_turn = result.scalar()
        turn_number = (max_turn or 0) + 1

        # Create turn
        turn = ConversationTurn(
            conversation_id=conversation_id,
            turn_number=turn_number,
            triggered_by_message_id=triggered_by_message_id,
            assigned_agents=assigned_agents,
            pending_agents=assigned_agents,
            turn_type=TurnType(turn_type),
            coordination_strategy=CoordinationStrategy.PARALLEL if turn_type == "parallel" else CoordinationStrategy.SEQUENTIAL,
            max_response_time_seconds=self.TURN_TIMEOUT_SECONDS,
            expected_completion_at=datetime.utcnow() + timedelta(seconds=self.TURN_TIMEOUT_SECONDS)
        )

        db.add(turn)
        await db.commit()
        await db.refresh(turn)

        logger.info(f"Created turn {turn.turn_id} with {len(assigned_agents)} assigned agents")
        return turn

    async def complete_agent_response(
        self,
        db: AsyncSession,
        turn_id: UUID,
        agent_id: str,
        message_id: UUID
    ):
        """
        Mark an agent's response as complete for a turn.

        Args:
            db: Database session
            turn_id: Turn ID
            agent_id: Agent that responded
            message_id: Message ID of response
        """
        # Get turn
        result = await db.execute(
            select(ConversationTurn).where(ConversationTurn.turn_id == turn_id)
        )
        turn = result.scalar_one_or_none()

        if not turn:
            logger.warning(f"Turn {turn_id} not found")
            return

        # Update turn
        completed_agents = turn.completed_agents or []
        pending_agents = turn.pending_agents or []
        response_message_ids = turn.response_message_ids or []

        if agent_id not in completed_agents:
            completed_agents.append(agent_id)

        if agent_id in pending_agents:
            pending_agents.remove(agent_id)

        response_message_ids.append(str(message_id))

        # Check if turn is complete
        is_complete = len(pending_agents) == 0
        status = "completed" if is_complete else "active"  # Using string values

        await db.execute(
            update(ConversationTurn)
            .where(ConversationTurn.turn_id == turn_id)
            .values(
                completed_agents=completed_agents,
                pending_agents=pending_agents,
                response_message_ids=response_message_ids,
                status=status,
                completed_at=datetime.utcnow() if is_complete else None
            )
        )

        await db.commit()
        logger.info(f"Agent {agent_id} completed response for turn {turn_id}")

    async def get_active_agents(
        self,
        db: AsyncSession,
        conversation_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        Get all active agents in a conversation with presence.

        Args:
            db: Database session
            conversation_id: Conversation ID

        Returns:
            List of agent details with presence info
        """
        # Get active agent participants
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
        participants = result.scalars().all()

        # Get presence for each agent
        agents_with_presence = []
        for participant in participants:
            agent = await self._get_agent(db, participant.participant_id_ref)
            if not agent:
                continue

            presence = await self._get_agent_presence(
                db, conversation_id, participant.participant_id_ref
            )

            agents_with_presence.append({
                'participant_id': str(participant.participant_id),
                'agent_id': agent.agent_id,
                'agent_name': agent.name,
                'agent_role': agent.role,
                'joined_at': participant.joined_at.isoformat() if participant.joined_at else None,
                'presence': {
                    'status': presence.status if presence else 'idle',  # status is now a string
                    'activity': presence.activity if presence else None,
                    'last_active': presence.last_active_at.isoformat() if presence and presence.last_active_at else None
                } if presence else None
            })

        return agents_with_presence

    async def get_pending_invitations(
        self,
        db: AsyncSession,
        conversation_id: UUID
    ) -> List[AgentInvitation]:
        """Get pending invitations for a conversation."""
        result = await db.execute(
            select(AgentInvitation)
            .where(
                and_(
                    AgentInvitation.conversation_id == conversation_id,
                    AgentInvitation.status == "pending"
                )
            )
            .order_by(AgentInvitation.created_at.desc())
        )
        return list(result.scalars().all())

    async def accept_invitation(
        self,
        db: AsyncSession,
        invitation_id: UUID
    ) -> ConversationParticipant:
        """
        Accept an agent invitation.

        Args:
            db: Database session
            invitation_id: Invitation to accept

        Returns:
            Created ConversationParticipant
        """
        # Get invitation
        result = await db.execute(
            select(AgentInvitation).where(AgentInvitation.invitation_id == invitation_id)
        )
        invitation = result.scalar_one_or_none()

        if not invitation:
            raise ValueError("Invitation not found")

        if invitation.status != "pending":
            raise ValueError(f"Invitation already {invitation.status}")

        # Join the agent
        participant = await self.handle_agent_join(
            db,
            invitation.conversation_id,
            invitation.agent_id,
            invitation_id
        )

        # Update invitation
        await db.execute(
            update(AgentInvitation)
            .where(AgentInvitation.invitation_id == invitation_id)
            .values(
                status="accepted",
                accepted_at=datetime.utcnow(),
                resulted_in_participation=True
            )
        )
        await db.commit()

        logger.info(f"Accepted invitation {invitation_id}")
        return participant

    async def decline_invitation(
        self,
        db: AsyncSession,
        invitation_id: UUID,
        reason: Optional[str] = None
    ):
        """
        Decline an agent invitation.

        Args:
            db: Database session
            invitation_id: Invitation to decline
            reason: Optional reason for declining
        """
        await db.execute(
            update(AgentInvitation)
            .where(AgentInvitation.invitation_id == invitation_id)
            .values(
                status="declined",
                declined_at=datetime.utcnow(),
                response_message=reason
            )
        )
        await db.commit()

        logger.info(f"Declined invitation {invitation_id}")

    # Helper methods

    async def _get_participant(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        agent_id: str
    ) -> Optional[ConversationParticipant]:
        """Get participant record."""
        result = await db.execute(
            select(ConversationParticipant)
            .where(
                and_(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.participant_id_ref == agent_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def _get_pending_invitation(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        agent_id: str
    ) -> Optional[AgentInvitation]:
        """Get pending invitation for agent."""
        result = await db.execute(
            select(AgentInvitation)
            .where(
                and_(
                    AgentInvitation.conversation_id == conversation_id,
                    AgentInvitation.agent_id == agent_id,
                    AgentInvitation.status == "pending"
                )
            )
        )
        return result.scalar_one_or_none()

    async def _get_agent(self, db: AsyncSession, agent_id: str) -> Optional[Agent]:
        """Get agent by ID."""
        result = await db.execute(
            select(Agent).where(Agent.agent_id == agent_id)
        )
        return result.scalar_one_or_none()

    async def _get_agent_presence(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        agent_id: str
    ) -> Optional[AgentPresence]:
        """Get agent presence."""
        result = await db.execute(
            select(AgentPresence)
            .where(
                and_(
                    AgentPresence.conversation_id == conversation_id,
                    AgentPresence.agent_id == agent_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def _get_active_agent_count(
        self,
        db: AsyncSession,
        conversation_id: UUID
    ) -> int:
        """Get count of active agents."""
        from sqlalchemy import func

        result = await db.execute(
            select(func.count(ConversationParticipant.participant_id))
            .where(
                and_(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.participant_type == ParticipantType.AGENT,
                    ConversationParticipant.is_active == True
                )
            )
        )
        return result.scalar() or 0

    async def _ensure_collaboration_session(
        self,
        db: AsyncSession,
        conversation_id: UUID
    ):
        """Create collaboration session if multiple agents present."""
        # Check if session already exists
        result = await db.execute(
            select(AgentCollaborationSession)
            .where(
                and_(
                    AgentCollaborationSession.conversation_id == conversation_id,
                    AgentCollaborationSession.ended_at.is_(None)
                )
            )
        )
        existing_session = result.scalar_one_or_none()

        if existing_session:
            return  # Session already exists

        # Get all active agents
        agents = await self.get_active_agents(db, conversation_id)
        agent_ids = [a['agent_id'] for a in agents]

        # Create session
        session = AgentCollaborationSession(
            conversation_id=conversation_id,
            participating_agents=agent_ids,
            primary_agent_id=agent_ids[0] if agent_ids else None,
            supporting_agents=agent_ids[1:] if len(agent_ids) > 1 else [],
            collaboration_type="parallel"
        )

        db.add(session)
        await db.commit()

        logger.info(f"Created collaboration session for {len(agent_ids)} agents")
