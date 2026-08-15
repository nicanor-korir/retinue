"""
WebSocket Manager for real-time event broadcasting.

Manages WebSocket connections and broadcasts agent activity events to connected clients.
"""
import asyncio
import logging
from typing import Dict, Set, Optional, Any
from uuid import UUID
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections for real-time updates.
    
    Supports:
    - Project-specific connections
    - Agent-specific connections
    - Broadcasting events to relevant subscribers
    """

    def __init__(self):
        # project_id -> set of WebSocket connections
        self.project_connections: Dict[str, Set[WebSocket]] = {}
        
        # agent_id -> set of WebSocket connections
        self.agent_connections: Dict[str, Set[WebSocket]] = {}
        
        # Global connections (receive all events)
        self.global_connections: Set[WebSocket] = set()
        
        # WebSocket -> subscription info
        self.connection_info: Dict[WebSocket, Dict[str, Any]] = {}

    async def connect(
        self,
        websocket: WebSocket,
        project_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        subscribe_all: bool = False,
    ):
        """Connect a WebSocket client and subscribe to events."""
        await websocket.accept()
        
        # Store connection info
        self.connection_info[websocket] = {
            "project_id": project_id,
            "agent_id": agent_id,
            "subscribe_all": subscribe_all,
            "connected_at": datetime.utcnow().isoformat(),
        }
        
        # Subscribe to project events
        if project_id:
            if project_id not in self.project_connections:
                self.project_connections[project_id] = set()
            self.project_connections[project_id].add(websocket)
            logger.info(f"WebSocket subscribed to project {project_id}")
        
        # Subscribe to agent events
        if agent_id:
            if agent_id not in self.agent_connections:
                self.agent_connections[agent_id] = set()
            self.agent_connections[agent_id].add(websocket)
            logger.info(f"WebSocket subscribed to agent {agent_id}")
        
        # Subscribe to all events
        if subscribe_all:
            self.global_connections.add(websocket)
            logger.info("WebSocket subscribed to all events")
        
        # Send welcome message (with error handling)
        try:
            await websocket.send_json({
                "type": "connection_established",
                "message": "Connected to Retinue real-time stream",
                "subscriptions": {
                    "project_id": project_id,
                    "agent_id": agent_id,
                    "all_events": subscribe_all,
                },
                "timestamp": datetime.utcnow().isoformat(),
            })
        except Exception as e:
            logger.warning(f"Could not send welcome message: {e}")
            # Connection failed, clean up and raise
            self.disconnect(websocket)
            raise

    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket client."""
        if websocket not in self.connection_info:
            return
        
        info = self.connection_info[websocket]
        
        # Remove from project subscriptions
        if info["project_id"]:
            project_id = info["project_id"]
            if project_id in self.project_connections:
                self.project_connections[project_id].discard(websocket)
                if not self.project_connections[project_id]:
                    del self.project_connections[project_id]
        
        # Remove from agent subscriptions
        if info["agent_id"]:
            agent_id = info["agent_id"]
            if agent_id in self.agent_connections:
                self.agent_connections[agent_id].discard(websocket)
                if not self.agent_connections[agent_id]:
                    del self.agent_connections[agent_id]
        
        # Remove from global subscriptions
        if info["subscribe_all"]:
            self.global_connections.discard(websocket)
        
        # Remove connection info
        del self.connection_info[websocket]
        
        logger.info("WebSocket disconnected")

    async def send_personal_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message to websocket: {e}")
            self.disconnect(websocket)

    async def broadcast_to_project(self, project_id: str, message: Dict[str, Any]):
        """Broadcast a message to all connections subscribed to a project."""
        message["timestamp"] = datetime.utcnow().isoformat()
        
        # Send to project-specific connections
        connections = self.project_connections.get(project_id, set()).copy()
        
        # Also send to global connections
        connections.update(self.global_connections)
        
        # Send to all relevant connections
        disconnected = []
        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to websocket: {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected websockets
        for websocket in disconnected:
            self.disconnect(websocket)

    async def broadcast_to_agent(self, agent_id: str, message: Dict[str, Any]):
        """Broadcast a message to all connections subscribed to an agent."""
        message["timestamp"] = datetime.utcnow().isoformat()
        
        # Send to agent-specific connections
        connections = self.agent_connections.get(agent_id, set()).copy()
        
        # Also send to global connections
        connections.update(self.global_connections)
        
        # Send to all relevant connections
        disconnected = []
        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to websocket: {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected websockets
        for websocket in disconnected:
            self.disconnect(websocket)

    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients."""
        message["timestamp"] = datetime.utcnow().isoformat()
        
        disconnected = []
        for websocket in self.connection_info.keys():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to websocket: {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected websockets
        for websocket in disconnected:
            self.disconnect(websocket)

    def get_connection_count(self, project_id: Optional[str] = None) -> int:
        """Get the number of active connections."""
        if project_id:
            return len(self.project_connections.get(project_id, set()))
        return len(self.connection_info)

    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics."""
        return {
            "total_connections": len(self.connection_info),
            "project_subscriptions": len(self.project_connections),
            "agent_subscriptions": len(self.agent_connections),
            "global_subscriptions": len(self.global_connections),
            "projects": {
                project_id: len(connections)
                for project_id, connections in self.project_connections.items()
            },
            "agents": {
                agent_id: len(connections)
                for agent_id, connections in self.agent_connections.items()
            },
        }


# Global WebSocket manager instance
ws_manager = WebSocketManager()


async def broadcast_activity(
    project_id: Optional[UUID],
    agent_id: str,
    event_type: str,
    data: Dict[str, Any],
):
    """
    Convenience function to broadcast an activity event.
    
    Args:
        project_id: Project ID (if applicable)
        agent_id: Agent ID that generated the event
        event_type: Type of event (activity_created, thought_recorded, etc.)
        data: Event data
    """
    message = {
        "type": event_type,
        "project_id": str(project_id) if project_id else None,
        "agent_id": agent_id,
        "data": data,
    }
    
    # Broadcast to project subscribers
    if project_id:
        await ws_manager.broadcast_to_project(str(project_id), message)
    
    # Also broadcast to agent subscribers
    await ws_manager.broadcast_to_agent(agent_id, message)


async def broadcast_handoff(
    project_id: UUID,
    from_agent_id: str,
    to_agent_id: str,
    data: Dict[str, Any],
):
    """Broadcast a handoff event."""
    message = {
        "type": "agent_handoff",
        "project_id": str(project_id),
        "from_agent_id": from_agent_id,
        "to_agent_id": to_agent_id,
        "data": data,
    }
    
    await ws_manager.broadcast_to_project(str(project_id), message)


async def broadcast_decision(
    project_id: UUID,
    agent_id: str,
    data: Dict[str, Any],
):
    """Broadcast a decision point event."""
    message = {
        "type": "decision_point",
        "project_id": str(project_id),
        "agent_id": agent_id,
        "data": data,
    }
    
    await ws_manager.broadcast_to_project(str(project_id), message)


async def broadcast_content_update(
    project_id: UUID,
    agent_id: str,
    generation_id: UUID,
    chunk: str,
    is_complete: bool = False,
):
    """Broadcast a content generation update (for streaming visualization)."""
    message = {
        "type": "content_stream",
        "project_id": str(project_id),
        "agent_id": agent_id,
        "data": {
            "generation_id": str(generation_id),
            "chunk": chunk,
            "is_complete": is_complete,
        },
    }
    
    await ws_manager.broadcast_to_project(str(project_id), message)


async def broadcast_llm_interaction(
    project_id: Optional[UUID],
    agent_id: str,
    interaction_data: Dict[str, Any],
):
    """Broadcast an LLM interaction event."""
    message = {
        "type": "llm_interaction",
        "project_id": str(project_id) if project_id else None,
        "agent_id": agent_id,
        "data": interaction_data,
    }
    
    if project_id:
        await ws_manager.broadcast_to_project(str(project_id), message)
    await ws_manager.broadcast_to_agent(agent_id, message)
