"""WebSocket endpoints for real-time agent activity streaming."""

import logging
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from app.services.websocket_manager import ws_manager
from app.db.database import get_session, AsyncSessionLocal
from app.services.conversation_orchestrator import ConversationOrchestrator
from app.services.multi_agent_response_service import get_multi_agent_response_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/activity")
async def websocket_activity_endpoint(
    websocket: WebSocket,
    project_id: Optional[str] = Query(None),
    task_id: Optional[str] = Query(None),
    agent_id: Optional[str] = Query(None),
    subscribe_all: bool = Query(False),
):
    """
    WebSocket endpoint for real-time agent activity streaming.

    Clients can subscribe to:
    - project_id: All activity for a specific project
    - task_id: Activity for a specific task
    - agent_id: All activity from a specific agent
    - subscribe_all: All activity across the entire system

    Query Parameters:
    - project_id: (optional) Project UUID to subscribe to
    - task_id: (optional) Task UUID to subscribe to
    - agent_id: (optional) Agent ID to subscribe to
    - subscribe_all: (optional) Subscribe to all events (default: False)

    Example connections:
    - ws://localhost:8000/ws/activity?project_id=abc-123
    - ws://localhost:8000/ws/activity?task_id=def-456
    - ws://localhost:8000/ws/activity?agent_id=backend_001
    - ws://localhost:8000/ws/activity?subscribe_all=true

    Message Format (sent to client):
    {
        "type": "activity_created|activity_progress|activity_complete|thought_recorded|llm_interaction|...",
        "project_id": "project-uuid or null",
        "task_id": "task-uuid or null",
        "agent_id": "agent-id",
        "timestamp": "2025-11-01T12:34:56.789Z",
        "data": {
            "activity_type": "THINKING|GENERATING|DECIDING|...",
            "progress_percentage": 0-100,
            "description": "Human-readable description",
            "details": {...},
            ...
        }
    }
    """

    # Connect client with appropriate subscriptions
    # Use project_id as primary subscription, but also support task_id
    await ws_manager.connect(
        websocket=websocket,
        project_id=project_id or task_id,  # Use task_id as project_id for task-specific streams
        agent_id=agent_id,
        subscribe_all=subscribe_all,
    )

    logger.info(
        f"WebSocket connected - project: {project_id}, task: {task_id}, "
        f"agent: {agent_id}, all: {subscribe_all}"
    )

    try:
        while True:
            # Keep connection alive and receive any client messages
            # (for future: could support client-initiated actions like task pause/resume)
            data = await websocket.receive_json()

            # Handle client commands (if any)
            if data.get("type") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
                })
            else:
                logger.debug(f"Received client message: {data}")

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)


@router.websocket("/ws/task/{task_id}")
async def websocket_task_endpoint(
    websocket: WebSocket,
    task_id: str,
    include_all: bool = Query(False),
):
    """
    WebSocket endpoint for real-time updates on a specific task.

    Streams:
    - Agent activity while executing the task
    - Task status changes
    - Thoughts and reasoning
    - LLM interactions
    - Content generation
    - Decision points
    - Blocking/unblocking events

    Path Parameters:
    - task_id: Task UUID

    Query Parameters:
    - include_all: Include all events (default: only task-specific)

    Example: ws://localhost:8000/ws/task/abc-123-def-456
    """

    await ws_manager.connect(
        websocket=websocket,
        project_id=task_id,  # Use task_id as project_id for filtering
        subscribe_all=include_all,
    )

    logger.info(f"WebSocket connected to task: {task_id}")

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
                })
            elif data.get("type") == "pause_task":
                # Future: Handle task pause command
                logger.info(f"Task pause requested for {task_id}")
            elif data.get("type") == "resume_task":
                # Future: Handle task resume command
                logger.info(f"Task resume requested for {task_id}")
            elif data.get("type") == "cancel_task":
                # Future: Handle task cancel command
                logger.info(f"Task cancel requested for {task_id}")
            else:
                logger.debug(f"Received task message: {data}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected from task: {task_id}")
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error on task {task_id}: {e}")
        ws_manager.disconnect(websocket)


@router.websocket("/ws/project/{project_id}")
async def websocket_project_endpoint(
    websocket: WebSocket,
    project_id: str,
):
    """
    WebSocket endpoint for real-time updates on a specific project.

    Streams all activity happening within a project:
    - Task status changes
    - Agent handoffs
    - Decision points
    - Escalations
    - Agent activity
    - Progress updates

    Path Parameters:
    - project_id: Project UUID

    Example: ws://localhost:8000/ws/project/proj-123-456
    """

    await ws_manager.connect(
        websocket=websocket,
        project_id=project_id,
    )

    logger.info(f"WebSocket connected to project: {project_id}")

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
                })
            elif data.get("type") == "pause_project":
                logger.info(f"Project pause requested for {project_id}")
            elif data.get("type") == "resume_project":
                logger.info(f"Project resume requested for {project_id}")
            else:
                logger.debug(f"Received project message: {data}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected from project: {project_id}")
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error on project {project_id}: {e}")
        ws_manager.disconnect(websocket)


@router.websocket("/ws/agent/{agent_id}")
async def websocket_agent_endpoint(
    websocket: WebSocket,
    agent_id: str,
):
    """
    WebSocket endpoint for real-time updates on a specific agent.

    Streams all activity from a specific agent across all projects:
    - Task assignments
    - Activity updates
    - Thoughts and reasoning
    - LLM interactions
    - Status changes
    - Handoffs (incoming and outgoing)

    Path Parameters:
    - agent_id: Agent ID (e.g., backend_001, frontend_001)

    Example: ws://localhost:8000/ws/agent/backend_001
    """

    await ws_manager.connect(
        websocket=websocket,
        agent_id=agent_id,
    )

    logger.info(f"WebSocket connected to agent: {agent_id}")

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
                })
            else:
                logger.debug(f"Received agent message: {data}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected from agent: {agent_id}")
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error on agent {agent_id}: {e}")
        ws_manager.disconnect(websocket)


@router.get("/ws/stats")
async def get_websocket_stats():
    """
    Get WebSocket connection statistics.

    Returns:
    {
        "total_connections": 5,
        "project_subscriptions": 2,
        "agent_subscriptions": 3,
        "global_subscriptions": 1,
        "projects": {
            "proj-123": 2,
            "proj-456": 1
        },
        "agents": {
            "backend_001": 1,
            "frontend_001": 2
        }
    }
    """
    return ws_manager.get_stats()


@router.websocket("/ws/conversations/{conversation_id}")
async def websocket_conversation_endpoint(
    websocket: WebSocket,
    conversation_id: str,
    user_id: str = Query(default="user_1"),
):
    """
    WebSocket endpoint for real-time conversation chat.

    Streams:
    - User messages
    - Agent responses (streaming)
    - Agent thinking process
    - Typing indicators
    - Read receipts

    Path Parameters:
    - conversation_id: Conversation UUID

    Query Parameters:
    - user_id: User ID (default: user_1)

    Message Format (client -> server):
    {
        "type": "user_message",
        "content": "Can you help me build a website?"
    }
    {
        "type": "ping"
    }

    Message Format (server -> client):
    {
        "type": "agent_typing",
        "agent_id": "ceo_001"
    }
    {
        "type": "agent_thinking_chunk",
        "thinking": "User wants to build a website..."
    }
    {
        "type": "agent_message_chunk",
        "content": "I'd be happy to help with your website!",
        "is_complete": false
    }
    {
        "type": "agent_message_complete",
        "message_id": "uuid",
        "content": "Full message content",
        "is_complete": true
    }
    {
        "type": "error",
        "error": "Error message"
    }

    Example: ws://localhost:8000/ws/conversations/abc-123-def-456?user_id=user_1
    """
    await websocket.accept()

    logger.info(f"WebSocket connected to conversation: {conversation_id} for user: {user_id}")

    orchestrator = ConversationOrchestrator()

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
                })

            elif data.get("type") == "user_message":
                content = data.get("content")
                if not content:
                    await websocket.send_json({
                        "type": "error",
                        "error": "Message content is required"
                    })
                    continue

                # Process user message
                async with AsyncSessionLocal() as session:
                    try:
                        # Create user message
                        from app.services.message_handler import MessageHandler
                        from app.db.conversation_models import SenderType

                        user_message = await MessageHandler.create_message(
                            session=session,
                            conversation_id=UUID(conversation_id),
                            sender_type=SenderType.USER,
                            sender_id=user_id,
                            content=content,
                            sender_name="User",
                        )

                        # Echo user message back
                        await websocket.send_json({
                            "type": "user_message_created",
                            "message_id": str(user_message.message_id),
                            "content": content,
                        })

                        # Use multi-agent response service to detect which agents should respond
                        multi_agent_service = get_multi_agent_response_service()
                        responding_agents = await multi_agent_service.detect_responding_agents(
                            session,
                            UUID(conversation_id),
                            content,
                            user_id
                        )

                        if not responding_agents:
                            # Fallback: Get conversation to determine primary agent
                            from app.services.conversation_service import ConversationService
                            conversation = await ConversationService.get_conversation(
                                session, UUID(conversation_id)
                            )

                            if not conversation or not conversation.primary_agent_id:
                                await websocket.send_json({
                                    "type": "error",
                                    "error": "No agent assigned to conversation"
                                })
                                continue

                            # Use primary agent as fallback
                            responding_agents = [{
                                'agent_id': conversation.primary_agent_id,
                                'agent_name': 'Agent',
                                'reason': 'primary_agent',
                                'priority': 1
                            }]

                        # Generate responses from all responding agents
                        # Track the last agent response for potential follow-up responses
                        last_agent_response_content = None
                        last_responding_agent_id = None

                        for agent_info in responding_agents:
                            agent_id = agent_info['agent_id']
                            agent_name = agent_info['agent_name']

                            # Send typing indicator for this agent
                            await websocket.send_json({
                                "type": "agent_typing",
                                "agent_id": agent_id,
                                "agent_name": agent_name,
                            })

                            # Generate agent response (streaming)
                            try:
                                full_response_content = ""
                                async for chunk in orchestrator.generate_agent_response(
                                    session,
                                    UUID(conversation_id),
                                    agent_id,
                                ):
                                    # Add agent info to chunk
                                    chunk['responding_agent_id'] = agent_id
                                    chunk['responding_agent_name'] = agent_name
                                    await websocket.send_json(chunk)

                                    # Track the content for potential agent-to-agent follow-up
                                    if chunk.get('type') == 'agent_message_complete':
                                        full_response_content = chunk.get('content', '')

                                # Track for agent-to-agent response detection
                                if full_response_content:
                                    last_agent_response_content = full_response_content
                                    last_responding_agent_id = agent_id

                            except Exception as agent_error:
                                logger.error(f"Error generating response from {agent_id}: {agent_error}")
                                await websocket.send_json({
                                    "type": "agent_error",
                                    "agent_id": agent_id,
                                    "agent_name": agent_name,
                                    "error": str(agent_error)
                                })

                        # Check if any agents should respond to the last agent's message
                        # (enables natural agent-to-agent conversation)
                        if last_agent_response_content and last_responding_agent_id:
                            follow_up_agents = await multi_agent_service.detect_responding_agents_to_agent_message(
                                session,
                                UUID(conversation_id),
                                last_agent_response_content,
                                last_responding_agent_id
                            )

                            # Generate follow-up responses (limit to 1 to prevent infinite loops)
                            for follow_up_agent in follow_up_agents[:1]:
                                follow_up_id = follow_up_agent['agent_id']
                                follow_up_name = follow_up_agent['agent_name']

                                logger.info(f"Agent {follow_up_id} responding to {last_responding_agent_id}'s message")

                                await websocket.send_json({
                                    "type": "agent_typing",
                                    "agent_id": follow_up_id,
                                    "agent_name": follow_up_name,
                                })

                                try:
                                    async for chunk in orchestrator.generate_agent_response(
                                        session,
                                        UUID(conversation_id),
                                        follow_up_id,
                                    ):
                                        chunk['responding_agent_id'] = follow_up_id
                                        chunk['responding_agent_name'] = follow_up_name
                                        await websocket.send_json(chunk)
                                except Exception as follow_up_error:
                                    logger.error(f"Error in follow-up response from {follow_up_id}: {follow_up_error}")
                                    await websocket.send_json({
                                        "type": "agent_error",
                                        "agent_id": follow_up_id,
                                        "agent_name": follow_up_name,
                                        "error": str(follow_up_error)
                                    })

                    except Exception as e:
                        logger.error(f"Error processing message: {e}", exc_info=True)
                        await websocket.send_json({
                            "type": "error",
                            "error": str(e)
                        })

            else:
                logger.debug(f"Received unknown message type: {data.get('type')}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected from conversation: {conversation_id}")
    except Exception as e:
        logger.error(f"WebSocket error on conversation {conversation_id}: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "error": str(e)
            })
        except:
            pass
