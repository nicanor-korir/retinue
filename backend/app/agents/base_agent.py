"""Base agent class for all AI agents in the system."""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from anthropic import AsyncAnthropic
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import os

from app.agents.event_mixin import AgentEventMixin
from app.db.models import (
    Agent,
    AgentStatus,
    Project,
    ProjectStatus,
    Task,
    Message,
    Decision,
    AuditLog,
    Escalation,
    TaskStatus,
    MessageType,
    Priority,
    Availability,
)
from app.db.database import AsyncSessionLocal
from app.services.escalation_service import EscalationService
from app.db.escalation_models import EscalationType, EscalationPriority
from app.utils.llm_error_handler import handle_llm_errors, extract_llm_error_message
from app.exceptions import LLMError
from app.core.config import settings
from app.services.rag_service import get_rag_service
from app.services.rag_agent_strategies import retrieve_agent_context, format_agent_context

logger = logging.getLogger(__name__)


class BaseAgent(AgentEventMixin):
    """
    Base class for all AI agents in the system.

    Each agent runs in an infinite loop checking for new work every 15 minutes.
    Agents communicate via database messages and update their status regularly.
    
    Inherits from AgentEventMixin to provide real-time event emission capabilities
    for the Glass Box AI visualization feature.
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        role: str,
        department: str,
        reports_to: Optional[str],
        system_prompt: str,
        permissions: Dict[str, List[str]],
        llm_model: str = "claude-sonnet-4-20250514",
    ):
        # Initialize AgentEventMixin first
        super().__init__()
        
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.department = department
        self.reports_to = reports_to
        self.system_prompt = system_prompt
        self.permissions = permissions
        self.llm_model = llm_model
        self.check_interval = 900  # 15 minutes in seconds

        # Initialize Anthropic client
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(f"ANTHROPIC_API_KEY environment variable not set for {self.name}")
        self.client = AsyncAnthropic(api_key=api_key)

        logger.info(f"Initialized {self.name} ({self.agent_id})")

    async def start(self):
        """
        Start the agent's main check cycle.
        Runs indefinitely, checking for work every 15 minutes.
        """
        logger.info(f"🤖 {self.name} starting main loop...")

        while True:
            try:
                await self.check_cycle()
            except Exception as e:
                logger.error(f"❌ Error in {self.name} check cycle: {e}", exc_info=True)
                await self.log_error(str(e))
                # Continue running even after errors

            # Wait for next check cycle
            await asyncio.sleep(self.check_interval)

    async def check_cycle(self):
        """
        Main check cycle - runs every 15 minutes.

        Priority order:
        1. Check for project completion (mark completed projects)
        2. New pending tasks
        3. Unread messages
        4. Approved items ready to proceed
        5. Check if blocked too long (escalate)
        6. Update status
        """
        async with AsyncSessionLocal() as session:
            try:
                # Update last check time
                await self.update_last_check(session)

                # 0. Check for project completion (only PM agent does this to avoid duplicate checks)
                if self.agent_id == "pm_001":
                    from app.utils.project_completion import check_and_complete_project

                    # Get all active projects
                    active_projects_result = await session.execute(
                        select(Project).where(
                            Project.status.in_([
                                ProjectStatus.IN_PROGRESS,
                                ProjectStatus.PLANNING,
                                ProjectStatus.REVIEW,
                                ProjectStatus.BLOCKED
                            ])
                        )
                    )
                    active_projects = active_projects_result.scalars().all()

                    for project in active_projects:
                        result = await check_and_complete_project(session, str(project.project_id))
                        if result.get("completed"):
                            logger.info(
                                f"{self.name}: Auto-completed project {project.name} - "
                                f"{result.get('reason')}"
                            )

                # 1. Check for new tasks
                new_tasks = await self.get_new_tasks(session)
                if new_tasks:
                    logger.info(f"{self.name}: Found {len(new_tasks)} new task(s)")
                    await self.start_task(session, new_tasks[0])
                    return

                # 2. Check for messages
                unread_messages = await self.get_unread_messages(session)
                if unread_messages:
                    logger.info(f"{self.name}: Processing {len(unread_messages)} message(s)")
                    await self.process_messages(session, unread_messages)
                    return

                # 3. Check for approved items
                approved_items = await self.get_approved_items(session)
                if approved_items:
                    logger.info(f"{self.name}: Continuing with approved item")
                    await self.continue_approved_work(session, approved_items[0])
                    return

                # 4. Check if blocked too long
                if await self.is_blocked_too_long(session):
                    logger.warning(f"{self.name}: Blocked too long, escalating...")
                    await self.escalate_blockage(session)
                    return

                # 5. Update status to available
                await self.update_status(session, Availability.AVAILABLE)
                logger.debug(f"{self.name}: Check cycle complete, no work found")

            except Exception as e:
                logger.error(f"Error in {self.name} check cycle: {e}", exc_info=True)
                await session.rollback()
                raise

    async def call_llm(
        self,
        prompt: str,
        context: Optional[Dict] = None,
        max_tokens: int = 4000,
        stream: bool = False,
        project_id: Optional[str] = None,
    ) -> str:
        """
        Call the LLM with the agent's system prompt.

        Args:
            prompt: The user prompt/task description
            context: Additional context to include
            max_tokens: Maximum tokens in response
            stream: Whether to stream the response (default False for backward compatibility)
            project_id: Project ID for broadcasting streaming chunks

        Returns:
            LLM response as string
        """
        try:
            full_prompt = self._build_prompt(prompt, context)

            logger.debug(f"{self.name}: Calling LLM with {len(full_prompt)} char prompt (stream={stream})")

            if stream and project_id:
                # Streaming mode with real-time broadcasting
                from app.services.websocket_manager import broadcast_activity
                
                result = ""
                async with self.client.messages.stream(
                    model=self.llm_model,
                    max_tokens=max_tokens,
                    system=self.system_prompt,
                    messages=[
                        {
                            "role": "user",
                            "content": full_prompt,
                        }
                    ],
                ) as stream:
                    async for text in stream.text_stream:
                        result += text
                        # Broadcast each chunk in real-time
                        await broadcast_activity(
                            project_id=project_id,
                            agent_id=self.agent_id,
                            event_type="llm_stream_chunk",
                            data={
                                "agent_id": self.agent_id,
                                "chunk": text,
                                "total_length": len(result),
                            }
                        )
                
                logger.debug(f"{self.name}: LLM streaming complete, {len(result)} chars")
                return result
            else:
                # Non-streaming mode (original behavior)
                response = await self.client.messages.create(
                    model=self.llm_model,
                    max_tokens=max_tokens,
                    system=self.system_prompt,
                    messages=[
                        {
                            "role": "user",
                            "content": full_prompt,
                        }
                    ],
                )

                result = response.content[0].text
                logger.debug(f"{self.name}: LLM returned {len(result)} char response")

                return result

        except LLMError:
            # Already a formatted LLM error, re-raise
            raise
        except Exception as e:
            logger.error(f"LLM call failed for {self.name}: {e}")
            # Convert to user-friendly LLM error
            user_message = extract_llm_error_message(e)
            raise LLMError(
                message=user_message,
                details={"error_type": type(e).__name__, "agent": self.name}
            ) from e

    async def call_llm_with_rag(
        self,
        prompt: str,
        context: Optional[Dict] = None,
        max_tokens: int = 4000,
        stream: bool = False,
        project_id: Optional[str] = None,
        agent_specific_filter: bool = True,
    ) -> str:
        """
        Call the LLM with RAG-enhanced context from past work using agent-specific strategy.

        Args:
            prompt: The user prompt/task description
            context: Additional context to include
            max_tokens: Maximum tokens in response
            stream: Whether to stream the response
            project_id: Project ID for broadcasting streaming chunks
            agent_specific_filter: Use agent-specific retrieval strategy

        Returns:
            LLM response as string
        """
        try:
            # 1. Retrieve relevant context from RAG using agent-specific strategy
            rag_context = {}
            if settings.RAG_ENABLED:
                try:
                    if agent_specific_filter:
                        # Use agent-specific strategy
                        rag_results = await retrieve_agent_context(
                            agent_id=self.agent_id,
                            query=prompt,
                            project_id=project_id,
                        )
                    else:
                        # Use generic retrieval
                        rag_service = get_rag_service()
                        rag_results = await rag_service.retrieve_context(
                            query=prompt,
                            agent_id=None,
                            project_id=project_id,
                            collections=["tasks", "decisions", "messages"],
                            top_k=settings.RAG_TOP_K,
                        )

                    # Format RAG results using agent-specific formatting
                    if agent_specific_filter:
                        rag_context["rag_context"] = await format_agent_context(
                            agent_id=self.agent_id,
                            results=rag_results,
                        )
                    else:
                        rag_service = get_rag_service()
                        rag_context["rag_context"] = await rag_service.format_context_for_prompt(
                            rag_results,
                            max_tokens=max_tokens // 2,
                        )

                    logger.info(f"{self.name}: Retrieved RAG context using {self.agent_id} strategy")
                except Exception as e:
                    logger.warning(f"{self.name}: RAG retrieval failed, continuing without context: {e}")
                    # If RAG fails, continue without it (graceful degradation)

            # 2. Build enhanced context combining user context and RAG context
            enhanced_context = {**(context or {}), **rag_context}

            # 3. Call LLM with enhanced context
            return await self.call_llm(
                prompt=prompt,
                context=enhanced_context,
                max_tokens=max_tokens,
                stream=stream,
                project_id=project_id,
            )

        except Exception as e:
            logger.error(f"Error in RAG-enhanced LLM call: {e}")
            # Fallback to regular call_llm if RAG fails
            return await self.call_llm(
                prompt=prompt,
                context=context,
                max_tokens=max_tokens,
                stream=stream,
                project_id=project_id,
            )

    def _build_prompt(self, prompt: str, context: Optional[Dict]) -> str:
        """Build the full prompt with context."""
        if not context:
            return prompt

        context_str = "\n\n**Current Context:**\n"
        for key, value in context.items():
            context_str += f"- {key}: {value}\n"

        return f"{context_str}\n\n**Task:**\n{prompt}"

    async def get_new_tasks(self, session: AsyncSession) -> List[Task]:
        """Get tasks assigned to this agent with status 'pending'."""
        result = await session.execute(
            select(Task)
            .where(
                Task.assigned_to_agent_id == self.agent_id,
                Task.status == TaskStatus.PENDING,
            )
            .order_by(Task.created_at)
        )
        return list(result.scalars().all())

    async def get_unread_messages(self, session: AsyncSession) -> List[Message]:
        """Get unread messages for this agent."""
        result = await session.execute(
            select(Message)
            .where(
                Message.to_agent_id == self.agent_id,
                Message.read_status == False,  # noqa: E712
            )
            .order_by(Message.timestamp)
        )
        return list(result.scalars().all())

    async def get_approved_items(self, session: AsyncSession) -> List[Any]:
        """Get items that have been approved and are ready to proceed."""
        # Implementation depends on specific agent type
        return []

    async def is_blocked_too_long(self, session: AsyncSession) -> bool:
        """Check if agent has been blocked for more than 2 hours."""
        result = await session.execute(
            select(AgentStatus).where(AgentStatus.agent_id == self.agent_id)
        )
        status = result.scalar_one_or_none()

        if not status or status.availability != Availability.BLOCKED:
            return False

        # Check if blocked for >2 hours
        blocked_duration = datetime.utcnow() - status.last_active
        return blocked_duration > timedelta(hours=2)

    async def send_message(
        self,
        session: AsyncSession,
        to_agent_id: str,
        content: str,
        message_type: MessageType = MessageType.INFO,
        priority: Priority = Priority.MEDIUM,
        related_task_id: Optional[str] = None,
    ):
        """Send a message to another agent."""
        message = Message(
            from_agent_id=self.agent_id,
            to_agent_id=to_agent_id,
            content=content,
            message_type=message_type,
            priority=priority,
            related_task_id=related_task_id,
        )
        session.add(message)
        await session.commit()
        logger.info(f"{self.name} → {to_agent_id}: {message_type.value} message sent")

    async def update_task_status(
        self,
        session: AsyncSession,
        task_id: str,
        status: TaskStatus,
        output: Optional[Dict] = None,
    ):
        """Update task status and optionally store output."""
        stmt = (
            update(Task)
            .where(Task.task_id == task_id)
            .values(
                status=status,
                updated_at=datetime.utcnow(),
                output=output if output is not None else Task.output,
            )
        )
        await session.execute(stmt)
        await session.commit()

        # Log the update
        await self.log_action(
            session,
            action="task_status_updated",
            entity_type="task",
            entity_id=task_id,
            new_value={"status": status.value, "output": output},
        )
        logger.info(f"{self.name}: Updated task {task_id} to {status.value}")

    async def update_status(
        self,
        session: AsyncSession,
        availability: Availability,
        current_task_id: Optional[str] = None,
    ):
        """Update agent status."""
        stmt = (
            update(AgentStatus)
            .where(AgentStatus.agent_id == self.agent_id)
            .values(
                availability=availability,
                last_active=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                current_task_id=current_task_id,
            )
        )
        await session.execute(stmt)
        await session.commit()

    async def update_last_check(self, session: AsyncSession):
        """Update the last check time for this agent."""
        stmt = (
            update(AgentStatus)
            .where(AgentStatus.agent_id == self.agent_id)
            .values(last_check_time=datetime.utcnow())
        )
        await session.execute(stmt)
        await session.commit()

    async def log_action(
        self,
        session: AsyncSession,
        action: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        old_value: Optional[Dict] = None,
        new_value: Optional[Dict] = None,
    ):
        """Log an action to audit log."""
        log = AuditLog(
            actor=self.agent_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=old_value,
            new_value=new_value,
        )
        session.add(log)
        await session.commit()

    async def log_error(self, error_message: str):
        """Log an error to the audit log."""
        async with AsyncSessionLocal() as session:
            await self.log_action(
                session,
                action="agent_error",
                new_value={"error": error_message, "timestamp": datetime.utcnow().isoformat()},
            )

    async def create_escalation(
        self,
        session: AsyncSession,
        title: str,
        escalation_type: EscalationType,
        priority: EscalationPriority,
        description: str,
        impact: str = "medium",
        urgency: str = "medium",
        **kwargs
    ):
        """
        Helper method for agents to create escalations automatically.
        
        Args:
            session: Database session
            title: Brief summary of the issue
            escalation_type: Type from EscalationType enum
            priority: Priority from EscalationPriority enum
            description: Detailed description
            impact: Impact level (low, medium, high, critical)
            urgency: Urgency level (low, medium, high, critical)
            **kwargs: Additional fields (related_agent_id, related_task_id, etc.)
        
        Returns:
            Created escalation object
        """
        try:
            escalation_service = EscalationService(session)
            
            escalation = await escalation_service.create_escalation(
                title=title,
                description=description,
                escalation_type=escalation_type,
                priority=priority,
                impact=impact,
                urgency=urgency,
                created_by_type="agent",
                created_by_id=self.agent_id,
                **kwargs
            )
            
            logger.info(
                f"Agent {self.agent_id} created escalation {escalation.escalation_number}: {title}"
            )
            
            return escalation
            
        except Exception as e:
            logger.error(f"Agent {self.agent_id} failed to create escalation: {str(e)}")
            raise

    async def has_open_escalation(
        self,
        session: AsyncSession,
        escalation_type: EscalationType = None,
        related_entity_id: str = None
    ) -> bool:
        """
        Check if there's already an open escalation for this issue.
        Prevents duplicate escalations.
        
        Args:
            session: Database session
            escalation_type: Type of escalation to check
            related_entity_id: ID of related entity (task, project, agent)
        
        Returns:
            True if open escalation exists, False otherwise
        """
        try:
            escalation_service = EscalationService(session)
            
            filters = {
                "status": ["open", "in_progress", "pending_agent", "pending_human"],
                "created_by_id": self.agent_id
            }
            
            if escalation_type:
                filters["type"] = [escalation_type]
            
            escalations = await escalation_service.get_escalations(**filters)
            
            if related_entity_id:
                return any(
                    e.related_task_id == related_entity_id or
                    e.related_project_id == related_entity_id or
                    e.related_agent_id == related_entity_id
                    for e in escalations
                )
            
            return len(escalations) > 0
            
        except Exception as e:
            logger.error(f"Error checking open escalations: {str(e)}")
            return False

    async def escalate_blockage(self, session: AsyncSession):
        """Escalate when blocked too long."""
        escalation = Escalation(
            issue_type="agent_blocked",
            severity=Priority.HIGH,
            escalated_by_agent_id=self.agent_id,
            escalated_to_agent_id=self.reports_to or "hr_001",
            description=f"{self.name} has been blocked for more than 2 hours",
        )
        session.add(escalation)
        await session.commit()
        logger.warning(f"{self.name}: Escalated blockage to {escalation.escalated_to_agent_id}")

    # Methods to be implemented by subclasses
    async def start_task(self, session: AsyncSession, task: Task):
        """Start working on a task - must be implemented by subclasses."""
        raise NotImplementedError(f"{self.__class__.__name__} must implement start_task()")

    async def process_messages(self, session: AsyncSession, messages: List[Message]):
        """Process messages - must be implemented by subclasses."""
        raise NotImplementedError(f"{self.__class__.__name__} must implement process_messages()")

    async def continue_approved_work(self, session: AsyncSession, item: Any):
        """Continue work after approval - can be overridden by subclasses."""
        logger.debug(f"{self.name}: No approved work handler implemented")
        pass
