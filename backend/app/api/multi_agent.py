"""
Multi-Agent Chat API Endpoints

Provides REST API for multi-agent conversation features:
- Agent discovery and suggestions
- Agent invitations
- Presence management
- Participant listing
- Turn management
"""

import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from datetime import datetime

from app.db.database import get_session
from app.services.agent_discovery_service import AgentDiscoveryService, AgentRecommendation
from app.services.multi_agent_orchestrator import MultiAgentOrchestrator, InvitationRequest
from app.services.context_briefing_service import ContextBriefingService
from app.services.predictive_agent_involvement_service import PredictiveAgentInvolvementService
from app.services.websocket_manager import broadcast_activity
from app.services.agent_chat_monitor import get_chat_monitor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/conversations", tags=["Multi-Agent Chat"])


# Pydantic Schemas

class AgentSuggestionResponse(BaseModel):
    """Agent suggestion response."""
    agent_id: str
    agent_name: str
    agent_role: str
    relevance_score: float
    expertise_match: List[str]
    reasoning: str
    prediction_factors: dict
    confidence: float


class InviteAgentRequest(BaseModel):
    """Request to invite an agent."""
    agent_id: str
    invited_by_type: str = Field(..., pattern="^(user|agent|system)$")
    invited_by_id: str
    invited_by_name: Optional[str] = None
    reason: Optional[str] = None
    specific_question: Optional[str] = None
    urgency: str = Field(default="normal", pattern="^(low|normal|high|urgent)$")


class InvitationResponse(BaseModel):
    """Invitation response."""
    invitation_id: UUID
    agent_id: str
    status: str
    invited_by_id: str
    invitation_reason: Optional[str]
    specific_question: Optional[str]
    auto_accept: bool
    created_at: datetime
    briefing: Optional[dict] = None

    class Config:
        from_attributes = True


class ParticipantPresenceResponse(BaseModel):
    """Participant with presence info."""
    participant_id: str
    agent_id: str
    agent_name: str
    agent_role: str
    joined_at: Optional[str]
    presence: Optional[dict]


class UpdatePresenceRequest(BaseModel):
    """Request to update agent presence."""
    agent_id: str
    status: str = Field(..., pattern="^(active|idle|thinking|typing|away)$")
    activity: Optional[str] = None


class TurnResponse(BaseModel):
    """Turn response."""
    turn_id: UUID
    turn_number: int
    assigned_agents: List[str]
    completed_agents: List[str]
    pending_agents: List[str]
    status: str
    turn_type: str

    class Config:
        from_attributes = True


# Endpoints

@router.get("/{conversation_id}/suggested-agents", response_model=List[AgentSuggestionResponse])
async def get_suggested_agents(
    conversation_id: UUID,
    user_id: str = Query(..., description="User requesting suggestions"),
    limit: int = Query(default=5, ge=1, le=10),
    min_relevance: float = Query(default=0.6, ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_session)
):
    """
    Get AI-suggested agents for a conversation based on context analysis.

    Returns agents ranked by relevance with detailed reasoning.
    """
    try:
        # Initialize services
        predictive_service = PredictiveAgentInvolvementService()
        discovery_service = AgentDiscoveryService(predictive_service)

        # Discover agents
        recommendations = await discovery_service.discover_agents(
            db=db,
            conversation_id=conversation_id,
            user_id=user_id,
            limit=limit,
            min_relevance=min_relevance
        )

        return [
            AgentSuggestionResponse(
                agent_id=rec.agent_id,
                agent_name=rec.agent_name,
                agent_role=rec.agent_role,
                relevance_score=rec.relevance_score,
                expertise_match=rec.expertise_match,
                reasoning=rec.reasoning,
                prediction_factors=rec.prediction_factors,
                confidence=rec.confidence
            )
            for rec in recommendations
        ]

    except Exception as e:
        logger.error(f"Error getting agent suggestions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{conversation_id}/invite-agent", response_model=InvitationResponse)
async def invite_agent(
    conversation_id: UUID,
    request: InviteAgentRequest,
    db: AsyncSession = Depends(get_session)
):
    """
    Invite an agent to join a conversation.

    If agent has high relevance score (>0.9), they will auto-join.
    Otherwise, invitation requires acceptance.
    """
    try:
        # Initialize services
        orchestrator = MultiAgentOrchestrator()
        briefing_service = ContextBriefingService()

        # Generate context briefing
        briefing = await briefing_service.generate_briefing(
            db=db,
            conversation_id=conversation_id,
            agent_id=request.agent_id,
            specific_question=request.specific_question
        )

        # Create invitation request
        invitation_request = InvitationRequest(
            agent_id=request.agent_id,
            invited_by_type=request.invited_by_type,
            invited_by_id=request.invited_by_id,
            invited_by_name=request.invited_by_name,
            reason=request.reason,
            specific_question=request.specific_question,
            urgency=request.urgency
        )

        # Invite agent
        invitation = await orchestrator.invite_agent(
            db=db,
            conversation_id=conversation_id,
            invitation_request=invitation_request,
            context_summary=briefing
        )

        # Broadcast invitation event via WebSocket
        await broadcast_activity(
            project_id=None,  # TODO: Get from conversation if available
            agent_id=request.agent_id,
            event_type="agent_invited",
            data={
                'conversation_id': str(conversation_id),
                'agent_id': request.agent_id,
                'invited_by': request.invited_by_id,
                'auto_join': invitation.auto_accept,
                'reason': request.reason
            }
        )

        # If auto-accepted, broadcast join event
        if invitation.auto_accept:
            await broadcast_activity(
                project_id=None,
                agent_id=request.agent_id,
                event_type="agent_joined",
                data={
                    'conversation_id': str(conversation_id),
                    'agent_id': request.agent_id,
                    'joined_at': datetime.utcnow().isoformat()
                }
            )

        return InvitationResponse(
            invitation_id=invitation.invitation_id,
            agent_id=invitation.agent_id,
            status=invitation.status,  # status is now a string
            invited_by_id=invitation.invited_by_id,
            invitation_reason=invitation.invitation_reason,
            specific_question=invitation.specific_question,
            auto_accept=invitation.auto_accept,
            created_at=invitation.created_at,
            briefing=briefing if not invitation.auto_accept else None
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error inviting agent: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}/participants", response_model=List[ParticipantPresenceResponse])
async def get_conversation_participants(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_session)
):
    """
    Get all participants in a conversation with real-time presence info.

    Returns both users and agents with their current status.
    """
    try:
        orchestrator = MultiAgentOrchestrator()

        # Get active agents with presence
        agents = await orchestrator.get_active_agents(db, conversation_id)

        return [
            ParticipantPresenceResponse(
                participant_id=agent['participant_id'],
                agent_id=agent['agent_id'],
                agent_name=agent['agent_name'],
                agent_role=agent['agent_role'],
                joined_at=agent['joined_at'],
                presence=agent['presence']
            )
            for agent in agents
        ]

    except Exception as e:
        logger.error(f"Error getting participants: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{conversation_id}/presence")
async def update_agent_presence(
    conversation_id: UUID,
    request: UpdatePresenceRequest,
    db: AsyncSession = Depends(get_session)
):
    """
    Update agent presence status in a conversation.

    Used to show real-time indicators (thinking, typing, etc.)
    """
    try:
        orchestrator = MultiAgentOrchestrator()

        await orchestrator.update_agent_presence(
            db=db,
            conversation_id=conversation_id,
            agent_id=request.agent_id,
            status=request.status,
            activity=request.activity
        )

        # Broadcast presence update via WebSocket
        await broadcast_activity(
            project_id=None,
            agent_id=request.agent_id,
            event_type="agent_presence_updated",
            data={
                'conversation_id': str(conversation_id),
                'agent_id': request.agent_id,
                'status': request.status,
                'activity': request.activity,
                'timestamp': datetime.utcnow().isoformat()
            }
        )

        return {"status": "success", "agent_id": request.agent_id, "presence": request.status}

    except Exception as e:
        logger.error(f"Error updating presence: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}/invitations", response_model=List[InvitationResponse])
async def get_conversation_invitations(
    conversation_id: UUID,
    status: Optional[str] = Query(default=None, pattern="^(pending|accepted|declined|expired)$"),
    db: AsyncSession = Depends(get_session)
):
    """
    Get invitation history for a conversation.

    Can filter by status (pending, accepted, declined, expired).
    """
    try:
        orchestrator = MultiAgentOrchestrator()

        if status == "pending" or not status:
            # Get pending invitations
            invitations = await orchestrator.get_pending_invitations(db, conversation_id)
        else:
            # TODO: Add method to get invitations by status
            invitations = await orchestrator.get_pending_invitations(db, conversation_id)

        return [
            InvitationResponse(
                invitation_id=inv.invitation_id,
                agent_id=inv.agent_id,
                status=inv.status,  # status is now a string
                invited_by_id=inv.invited_by_id,
                invitation_reason=inv.invitation_reason,
                specific_question=inv.specific_question,
                auto_accept=inv.auto_accept,
                created_at=inv.created_at
            )
            for inv in invitations
        ]

    except Exception as e:
        logger.error(f"Error getting invitations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/invitations/{invitation_id}/accept", response_model=dict)
async def accept_invitation(
    invitation_id: UUID,
    db: AsyncSession = Depends(get_session)
):
    """
    Accept an agent invitation.

    Agent joins the conversation immediately.
    """
    try:
        orchestrator = MultiAgentOrchestrator()

        participant = await orchestrator.accept_invitation(db, invitation_id)

        # Broadcast join event via WebSocket
        await broadcast_activity(
            project_id=None,
            agent_id=participant.participant_id_ref,
            event_type="agent_joined",
            data={
                'conversation_id': str(participant.conversation_id),
                'agent_id': participant.participant_id_ref,
                'joined_at': datetime.utcnow().isoformat()
            }
        )

        return {
            "status": "accepted",
            "invitation_id": str(invitation_id),
            "participant_id": str(participant.participant_id)
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error accepting invitation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/invitations/{invitation_id}/decline", response_model=dict)
async def decline_invitation(
    invitation_id: UUID,
    reason: Optional[str] = None,
    db: AsyncSession = Depends(get_session)
):
    """
    Decline an agent invitation.
    """
    try:
        orchestrator = MultiAgentOrchestrator()

        await orchestrator.decline_invitation(db, invitation_id, reason)

        return {
            "status": "declined",
            "invitation_id": str(invitation_id),
            "reason": reason
        }

    except Exception as e:
        logger.error(f"Error declining invitation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}/briefing/{agent_id}", response_model=dict)
async def get_agent_briefing(
    conversation_id: UUID,
    agent_id: str,
    specific_question: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_session)
):
    """
    Get a context briefing for an agent about a conversation.

    Useful for previewing what an agent will see before inviting them.
    """
    try:
        briefing_service = ContextBriefingService()

        briefing = await briefing_service.generate_briefing(
            db=db,
            conversation_id=conversation_id,
            agent_id=agent_id,
            specific_question=specific_question
        )

        return briefing

    except Exception as e:
        logger.error(f"Error generating briefing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{conversation_id}/leave", response_model=dict)
async def agent_leave_conversation(
    conversation_id: UUID,
    agent_id: str,
    reason: Optional[str] = None,
    db: AsyncSession = Depends(get_session)
):
    """
    Agent leaves a conversation.
    """
    try:
        orchestrator = MultiAgentOrchestrator()

        await orchestrator.handle_agent_leave(db, conversation_id, agent_id, reason)

        # Broadcast leave event via WebSocket
        await broadcast_activity(
            project_id=None,
            agent_id=agent_id,
            event_type="agent_left",
            data={
                'conversation_id': str(conversation_id),
                'agent_id': agent_id,
                'reason': reason,
                'left_at': datetime.utcnow().isoformat()
            }
        )

        return {
            "status": "left",
            "agent_id": agent_id,
            "conversation_id": str(conversation_id)
        }

    except Exception as e:
        logger.error(f"Error handling agent leave: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Agent Chat Monitor Endpoints - Autonomous Agent Joining
# ============================================================================

class ApproveJoinRequest(BaseModel):
    """Request to approve/reject an agent join request."""
    approving_agent_id: str
    approved: bool
    response_message: Optional[str] = None


class JoinRequestResponse(BaseModel):
    """Response for join request status."""
    request_id: str
    conversation_id: str
    requesting_agent_id: str
    requesting_agent_name: str
    approving_agent_id: str
    reason: str
    confidence: float
    detected_keywords: List[str]
    status: str
    created_at: str


@router.post("/{conversation_id}/join-requests/{target_agent_id}/respond", response_model=dict)
async def respond_to_join_request(
    conversation_id: UUID,
    target_agent_id: str,
    request: ApproveJoinRequest,
    db: AsyncSession = Depends(get_session)
):
    """
    Approve or reject an agent's request to join a conversation.

    This endpoint is used by approving agents (CEO, PM, etc.) to approve
    or reject requests from other agents who want to join the conversation.

    The monitoring system detects when agents are mentioned or needed,
    and creates join requests that need approval.
    """
    try:
        monitor = get_chat_monitor()

        success = await monitor.process_approval_response(
            session=db,
            conversation_id=conversation_id,
            approving_agent_id=request.approving_agent_id,
            target_agent_id=target_agent_id,
            approved=request.approved,
            response_message=request.response_message
        )

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"No pending join request found for agent {target_agent_id}"
            )

        # Broadcast approval/rejection event
        await broadcast_activity(
            project_id=None,
            agent_id=target_agent_id,
            event_type="join_request_responded",
            data={
                'conversation_id': str(conversation_id),
                'target_agent_id': target_agent_id,
                'approving_agent_id': request.approving_agent_id,
                'approved': request.approved,
                'response_message': request.response_message,
                'timestamp': datetime.utcnow().isoformat()
            }
        )

        return {
            "status": "approved" if request.approved else "rejected",
            "conversation_id": str(conversation_id),
            "target_agent_id": target_agent_id,
            "approving_agent_id": request.approving_agent_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error responding to join request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}/join-requests", response_model=List[JoinRequestResponse])
async def get_pending_join_requests(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_session)
):
    """
    Get all pending join requests for a conversation.

    Returns list of agents who have requested to join this conversation
    and are awaiting approval.
    """
    try:
        monitor = get_chat_monitor()

        # Filter pending requests for this conversation
        pending = [
            JoinRequestResponse(
                request_id=req.request_id,
                conversation_id=str(req.conversation_id),
                requesting_agent_id=req.requesting_agent_id,
                requesting_agent_name=req.requesting_agent_name,
                approving_agent_id=req.approving_agent_id,
                reason=req.reason,
                confidence=req.confidence,
                detected_keywords=req.detected_keywords,
                status=req.status.value,
                created_at=req.created_at.isoformat()
            )
            for key, req in monitor._pending_requests.items()
            if req.conversation_id == conversation_id
        ]

        return pending

    except Exception as e:
        logger.error(f"Error getting join requests: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitor/status", response_model=dict)
async def get_monitor_status():
    """
    Get the status of the agent chat monitoring service.

    Returns information about:
    - Whether monitoring is active
    - Number of conversations being monitored
    - Number of pending join requests
    """
    try:
        monitor = get_chat_monitor()

        return {
            "monitoring_active": monitor._monitoring_active,
            "monitored_conversations": len(monitor._monitored_conversations),
            "pending_requests": len(monitor._pending_requests),
            "monitor_interval_seconds": monitor.MONITOR_INTERVAL,
            "auto_approval_threshold": monitor.AUTO_APPROVAL_THRESHOLD,
            "approver_agents": monitor.APPROVER_AGENTS
        }

    except Exception as e:
        logger.error(f"Error getting monitor status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitor/trigger-analysis/{conversation_id}", response_model=dict)
async def trigger_conversation_analysis(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_session)
):
    """
    Manually trigger analysis of a conversation for agent needs.

    This forces the monitoring system to immediately analyze
    the conversation and identify agents who should join.

    Useful for testing or when you want immediate suggestions.
    """
    try:
        from app.db.conversation_models import Conversation
        from sqlalchemy import select

        monitor = get_chat_monitor()

        # Get the conversation
        result = await db.execute(
            select(Conversation).where(Conversation.conversation_id == conversation_id)
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Force analysis
        await monitor._analyze_conversation(db, conversation)

        # Get any new pending requests
        new_requests = [
            key for key in monitor._pending_requests.keys()
            if key.startswith(str(conversation_id))
        ]

        return {
            "status": "analysis_complete",
            "conversation_id": str(conversation_id),
            "new_pending_requests": len(new_requests),
            "request_keys": new_requests
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
