"""Event-driven RAG indexing service - automatically indexes entities when created."""

import asyncio
import json
import logging
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Task, Decision, Message
from app.services.rag_service import get_rag_service

logger = logging.getLogger(__name__)


class RAGIndexingService:
    """Service for indexing entities to RAG knowledge base."""

    def __init__(self):
        """Initialize the indexing service."""
        self.rag_service = get_rag_service()
        self.indexing_queue = asyncio.Queue()
        self.is_running = False

    async def start(self):
        """Start the background indexing worker."""
        if self.is_running:
            logger.warning("RAG indexing service is already running")
            return

        self.is_running = True
        logger.info("Starting RAG indexing service")

        # Start background worker
        asyncio.create_task(self._process_queue())

    async def stop(self):
        """Stop the background indexing worker."""
        self.is_running = False
        logger.info("Stopped RAG indexing service")

    async def _process_queue(self):
        """Process indexing tasks from the queue."""
        while self.is_running:
            try:
                # Get task from queue with timeout
                indexing_task = await asyncio.wait_for(
                    self.indexing_queue.get(), timeout=5.0
                )

                # Process the indexing task
                await self._execute_indexing_task(indexing_task)

                # Mark as done
                self.indexing_queue.task_done()

            except asyncio.TimeoutError:
                # Queue is empty, check if we should continue
                if not self.is_running:
                    break
                continue
            except Exception as e:
                logger.error(f"Error in indexing queue processor: {e}")

    async def _execute_indexing_task(self, task: Dict[str, Any]):
        """
        Execute a single indexing task.

        Args:
            task: Dictionary with 'type' and 'data' keys
        """
        try:
            task_type = task.get("type")
            data = task.get("data")

            if task_type == "index_task":
                await self.rag_service.index_task(**data)
            elif task_type == "index_decision":
                await self.rag_service.index_decision(**data)
            elif task_type == "index_message":
                await self.rag_service.index_message(**data)
            else:
                logger.warning(f"Unknown indexing task type: {task_type}")

        except Exception as e:
            logger.error(f"Error executing indexing task: {e}")

    async def queue_index_task(
        self,
        task_id: str,
        title: str,
        description: str,
        output: Optional[str] = None,
        completion_notes: Optional[str] = None,
        agent_id: Optional[str] = None,
        project_id: Optional[str] = None,
        status: str = "completed",
    ) -> None:
        """
        Queue a task for indexing.

        Args:
            task_id: Task ID
            title: Task title
            description: Task description
            output: Task output
            completion_notes: Completion notes
            agent_id: Agent ID
            project_id: Project ID
            status: Task status
        """
        try:
            await self.indexing_queue.put(
                {
                    "type": "index_task",
                    "data": {
                        "task_id": task_id,
                        "title": title,
                        "description": description,
                        "output": output,
                        "completion_notes": completion_notes,
                        "agent_id": agent_id,
                        "project_id": project_id,
                        "status": status,
                    },
                }
            )
            logger.debug(f"Queued task {task_id} for indexing")
        except Exception as e:
            logger.error(f"Error queuing task indexing: {e}")

    async def queue_index_decision(
        self,
        decision_id: str,
        question: str,
        decision: str,
        rationale: str,
        decision_type: str = "general",
        agent_id: Optional[str] = None,
        project_id: Optional[str] = None,
        approved: bool = False,
    ) -> None:
        """
        Queue a decision for indexing.

        Args:
            decision_id: Decision ID
            question: Decision question
            decision: The decision
            rationale: Decision rationale
            decision_type: Decision type
            agent_id: Agent ID
            project_id: Project ID
            approved: Whether approved
        """
        try:
            await self.indexing_queue.put(
                {
                    "type": "index_decision",
                    "data": {
                        "decision_id": decision_id,
                        "question": question,
                        "decision": decision,
                        "rationale": rationale,
                        "decision_type": decision_type,
                        "agent_id": agent_id,
                        "project_id": project_id,
                        "approved": approved,
                    },
                }
            )
            logger.debug(f"Queued decision {decision_id} for indexing")
        except Exception as e:
            logger.error(f"Error queuing decision indexing: {e}")

    async def queue_index_message(
        self,
        message_id: str,
        content: str,
        from_agent_id: str,
        to_agent_id: Optional[str] = None,
        message_type: str = "info",
        project_id: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> None:
        """
        Queue a message for indexing.

        Args:
            message_id: Message ID
            content: Message content
            from_agent_id: From agent ID
            to_agent_id: To agent ID
            message_type: Message type
            project_id: Project ID
            task_id: Task ID
        """
        try:
            await self.indexing_queue.put(
                {
                    "type": "index_message",
                    "data": {
                        "message_id": message_id,
                        "content": content,
                        "from_agent_id": from_agent_id,
                        "to_agent_id": to_agent_id,
                        "message_type": message_type,
                        "project_id": project_id,
                        "task_id": task_id,
                    },
                }
            )
            logger.debug(f"Queued message {message_id} for indexing")
        except Exception as e:
            logger.error(f"Error queuing message indexing: {e}")

    async def get_queue_size(self) -> int:
        """Get the size of the indexing queue."""
        return self.indexing_queue.qsize()


# Global instance
_indexing_service: Optional[RAGIndexingService] = None


def get_indexing_service() -> RAGIndexingService:
    """Get or create the global RAG indexing service instance."""
    global _indexing_service
    if _indexing_service is None:
        _indexing_service = RAGIndexingService()
    return _indexing_service


async def start_indexing_service():
    """Start the RAG indexing service."""
    service = get_indexing_service()
    await service.start()


async def stop_indexing_service():
    """Stop the RAG indexing service."""
    service = get_indexing_service()
    await service.stop()
