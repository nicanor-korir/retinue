"""
Multi-Agent Message Handler

Extends message handling to automatically detect and invite agents
when users request them in messages.
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.conversation_models import (
    ConversationMessage,
    SenderType,
    ContentType,
    MessageTypeConversation,
)
from app.services.message_handler import MessageHandler
from app.services.message_analyzer import MessageAnalyzer
from app.services.multi_agent_orchestrator import MultiAgentOrchestrator, InvitationRequest
from app.services.context_briefing_service import ContextBriefingService
from app.services.conversation_service import ConversationService
from app.db.conversation_models import ParticipantType

logger = logging.getLogger(__name__)


class MultiAgentMessageHandler:
    """
    Message handler with multi-agent capabilities.

    Automatically detects when users request other agents and invites them.
    """

    def __init__(self):
        self.message_handler = MessageHandler()
        self.analyzer = MessageAnalyzer()
        self.orchestrator = MultiAgentOrchestrator()
        self.briefing_service = ContextBriefingService()

    async def create_message_with_agent_detection(
        self,
        session: AsyncSession,
        conversation_id: UUID,
        sender_type: SenderType,
        sender_id: str,
        content: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a message and automatically detect/invite requested agents.

        Args:
            session: Database session
            conversation_id: Conversation ID
            sender_type: Type of sender (USER, AGENT, SYSTEM)
            sender_id: Sender ID
            content: Message content
            **kwargs: Additional message parameters

        Returns:
            Dict with message and invited_agents info
        """
        # 1. Create the message
        message = await self.message_handler.create_message(
            session=session,
            conversation_id=conversation_id,
            sender_type=sender_type,
            sender_id=sender_id,
            content=content,
            **kwargs
        )

        invited_agents = []

        # 2. Only analyze USER messages for agent requests
        if sender_type == SenderType.USER:
            # Get current participants
            current_participants = await ConversationService.get_participants(
                session, conversation_id, active_only=True
            )
            current_agent_ids = [
                p.participant_id_ref
                for p in current_participants
                if p.participant_type == ParticipantType.AGENT
            ]

            # 3. Analyze message for agent requests
            detected_agents = await self.analyzer.analyze_for_agent_requests(
                db=session,
                message_content=content,
                conversation_id=conversation_id,
                current_agent_ids=current_agent_ids
            )

            # 4. Invite detected agents
            if detected_agents:
                logger.info(
                    f"Detected {len(detected_agents)} agent requests in message {message.message_id}"
                )

                for agent_info in detected_agents:
                    try:
                        # Generate context briefing
                        briefing = await self.briefing_service.generate_briefing(
                            db=session,
                            conversation_id=conversation_id,
                            agent_id=agent_info['agent_id'],
                            specific_question=content
                        )

                        # Create invitation
                        invitation_request = InvitationRequest(
                            agent_id=agent_info['agent_id'],
                            invited_by_type='system',  # System detected the request
                            invited_by_id=sender_id,  # But on behalf of the user
                            reason=agent_info['reason'],
                            specific_question=content,
                            urgency='normal',
                            prediction_score=agent_info['confidence']
                        )

                        invitation = await self.orchestrator.invite_agent(
                            db=session,
                            conversation_id=conversation_id,
                            invitation_request=invitation_request,
                            context_summary=briefing
                        )

                        invited_agents.append({
                            'agent_id': agent_info['agent_id'],
                            'invitation_id': str(invitation.invitation_id),
                            'status': invitation.status,  # status is now a string
                            'auto_joined': invitation.auto_accept,
                            'confidence': agent_info['confidence'],
                            'reason': agent_info['reason']
                        })

                        # Log the invitation
                        logger.info(
                            f"Invited agent {agent_info['agent_id']} to conversation "
                            f"{conversation_id} (auto_join: {invitation.auto_accept})"
                        )

                    except Exception as e:
                        logger.error(
                            f"Failed to invite agent {agent_info['agent_id']}: {e}",
                            exc_info=True
                        )

        # 5. Return message with invitation info
        return {
            'message': message,
            'invited_agents': invited_agents,
            'invitation_count': len(invited_agents)
        }

    async def create_system_message(
        self,
        session: AsyncSession,
        conversation_id: UUID,
        content: str,
        **kwargs
    ) -> ConversationMessage:
        """Create a system message (notifications, etc.)."""
        return await self.message_handler.create_message(
            session=session,
            conversation_id=conversation_id,
            sender_type=SenderType.SYSTEM,
            sender_id='system',
            sender_name='System',
            content=content,
            message_type=MessageTypeConversation.SYSTEM,
            **kwargs
        )

    async def notify_agent_joined(
        self,
        session: AsyncSession,
        conversation_id: UUID,
        agent_id: str,
        agent_name: str
    ) -> ConversationMessage:
        """Create a notification message that an agent joined."""
        content = f"{agent_name} has joined the conversation"

        return await self.create_system_message(
            session=session,
            conversation_id=conversation_id,
            content=content,
            message_metadata={
                'event': 'agent_joined',
                'agent_id': agent_id,
                'agent_name': agent_name
            }
        )
