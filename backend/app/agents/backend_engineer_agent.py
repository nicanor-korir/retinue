"""Backend Engineer Agent - Builds backend APIs and services."""
import logging
from typing import Dict, List
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base_agent import BaseAgent
from app.agents.event_driven_mixin import EventDrivenMixin
from app.db.models import (
    Task,
    Message,
    Project,
    TaskStatus,
    MessageType,
    Priority,
)

logger = logging.getLogger(__name__)


class BackendEngineerAgent(BaseAgent, EventDrivenMixin):
    """
    Senior Backend Engineer Agent

    Responsibilities:
    - Build backend APIs and services
    - Write clean, maintainable code
    - Implement database schemas and queries
    - Write tests for code
    - Review other backend code
    - Update task status in real-time
    """

    def __init__(self):
        system_prompt = """You are a Senior Backend Engineer. Your responsibilities:

**Core Responsibilities:**
- Build backend APIs and services with clean, maintainable code
- Implement database schemas and queries efficiently
- Write comprehensive tests for all code
- Review and improve code quality
- Update task status in real-time as you progress
- Follow best practices and design patterns

**Decision-Making Authority:**
- You CAN decide: Implementation details, code patterns, query optimization, refactoring your own code, variable/function naming, file structure
- You NEED approval for: New dependencies/packages, API contract changes, database schema changes, major architecture modifications

**Workflow:**
1. Check for assigned tasks every 15 minutes
2. Read task description and acceptance criteria carefully
3. Plan implementation approach before coding
4. Write code incrementally, updating task status
5. Write comprehensive tests (aim for 80%+ coverage)
6. Request peer review from CTO when complete
7. Mark task as complete only after approval

**Technical Standards:**
- **Python**: Follow PEP 8, use type hints, write docstrings
- **FastAPI**: RESTful design, proper status codes, request validation
- **Database**: Use SQLAlchemy ORM, write efficient queries, handle transactions properly
- **Testing**: Use pytest, test edge cases, mock external dependencies
- **Code Quality**: Functions under 50 lines, DRY principle, clear naming
- **Security**: Validate inputs, sanitize outputs, handle errors properly

**Output Format:**
When implementing a feature, provide:
1. **Implementation Summary**: What you built (2-3 sentences)
2. **Code**: Complete, working code with comments
3. **Database Changes**: Any schema changes needed
4. **API Endpoints**: List of endpoints created/modified
5. **Tests**: Description of test coverage
6. **Notes**: Any important implementation details or caveats

**Code Example Structure:**
```python
# Module docstring explaining purpose

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

class ItemCreate(BaseModel):
    \"\"\"Request model for creating items.\"\"\"
    name: str
    description: Optional[str] = None

@router.post("/items", response_model=Item)
async def create_item(
    item: ItemCreate,
    session: AsyncSession = Depends(get_session)
):
    \"\"\"
    Create a new item.

    Args:
        item: Item data
        session: Database session

    Returns:
        Created item

    Raises:
        HTTPException: If creation fails
    \"\"\"
    # Implementation here
    pass
```

**Communication Style:** Technical, collaborative, asks for clarification when needed. Professional and detail-oriented.

**Time Compression:** 1 real hour = 1 agent day. Work efficiently and effectively.

Always be thorough, professional, and quality-focused. Request CTO review when complete.
"""

        super().__init__(
            agent_id="backend_001",
            name="Senior Backend Engineer",
            role="Senior Backend Engineer",
            department="engineering",
            reports_to="cto_001",
            system_prompt=system_prompt,
            permissions={
                "read": ["projects", "tasks", "messages", "knowledge_base"],
                "write": ["tasks", "messages", "knowledge_base"],
                "approve": ["backend_code_reviews"],
            },
        )

        # Set up event-driven listeners
        self.setup_event_listeners()

    async def start_task(self, session: AsyncSession, task: Task):
        """Backend engineer implements features."""
        try:
            logger.info(f"{self.name}: Starting task {task.task_id} - {task.title}")

            await self.update_status(session, "busy", current_task_id=str(task.task_id))
            await self.update_task_status(session, str(task.task_id), TaskStatus.IN_PROGRESS)

            # Get project context
            project = await self._get_project(session, task.project_id)
            context = {
                "project_name": project.name if project else "Unknown",
                "task_title": task.title,
                "task_description": task.description,
            }

            # Call LLM to generate code
            prompt = f"""Implement this backend feature:

**Task:** {task.title}
**Description:** {task.description}

Provide a complete implementation including:

1. **Implementation Summary**: Brief overview of what you built

2. **Code**: Complete, production-ready Python/FastAPI code with:
   - Proper imports and dependencies
   - Type hints and docstrings
   - Input validation with Pydantic models
   - Error handling and logging
   - RESTful API design
   - Database operations if needed (using SQLAlchemy async)

3. **Database Schema** (if applicable):
   - SQLAlchemy model definitions
   - Any migration notes

4. **API Endpoints**: List endpoints created with:
   - Method and path
   - Request/response models
   - Brief description

5. **Tests**: pytest test examples covering:
   - Happy path
   - Edge cases
   - Error handling

6. **Implementation Notes**: Any important details, assumptions, or TODOs

Focus on:
- Clean, maintainable code
- Proper error handling
- Security best practices
- Performance considerations
- Comprehensive testing

Be specific and production-ready. This is for an MVP, so balance quality with speed.
"""

            # Use RAG-enhanced LLM call to retrieve relevant past implementations
            code_response = await self.call_llm_with_rag(
                prompt=prompt,
                context=context,
                max_tokens=6000,
                project_id=str(task.project_id),
                agent_specific_filter=True,
            )

            logger.info(f"{self.name}: Code generation complete for {task.title}")

            # Structure the output for better display
            output_data = {
                "content": code_response,
                "language": "python",
                "framework": "fastapi",
                "status": "awaiting_review",
                "task_type": "backend_implementation",
            }

            # Try to extract key sections from the response
            if "**Implementation Summary**" in code_response or "Implementation Summary:" in code_response:
                # Response is well-structured
                output_data["structured"] = True

            # Update task to review status (waiting for CTO approval)
            await self.update_task_status(
                session,
                str(task.task_id),
                TaskStatus.REVIEW,
                output=output_data,
            )

            # Request code review from CTO
            await self.send_message(
                session,
                to_agent_id="cto_001",
                content=f"""Code Review Request: {task.title}

I've completed the implementation for:
**{task.title}**

**Implementation:**
{code_response[:500]}... (see full output in task details)

Please review and approve, or provide feedback for improvements.

Task ID: {task.task_id}

- Backend Engineer
""",
                message_type=MessageType.APPROVAL,
                priority=Priority.MEDIUM,
                related_task_id=str(task.task_id),
            )

            await self.update_status(session, "available")

            logger.info(f"{self.name}: Task {task.task_id} ready for review")

        except Exception as e:
            logger.error(f"{self.name}: Error in start_task: {e}", exc_info=True)
            await self.update_task_status(
                session,
                str(task.task_id),
                TaskStatus.BLOCKED,
                output={"error": str(e), "blocking_reason": "Implementation error"},
            )
            await self.update_status(session, "available")

            # Notify PM about blocker
            await self.send_message(
                session,
                to_agent_id="pm_001",
                content=f"""Task Blocked: {task.title}

I encountered an error while implementing this task:
{str(e)}

Please review and provide guidance.

- Backend Engineer
""",
                message_type=MessageType.ALERT,
                priority=Priority.HIGH,
                related_task_id=str(task.task_id),
            )

    async def process_messages(self, session: AsyncSession, messages: List[Message]):
        """Process incoming messages."""
        try:
            logger.info(f"{self.name}: Processing {len(messages)} message(s)")

            for message in messages:
                # Mark as read
                stmt = (
                    update(Message)
                    .where(Message.message_id == message.message_id)
                    .values(read_status=True)
                )
                await session.execute(stmt)
                await session.commit()

                logger.info(
                    f"{self.name}: Processing {message.message_type.value} from {message.from_agent_id}"
                )

                # Check if it's approval/feedback from CTO
                if message.from_agent_id == "cto_001":
                    await self._handle_review_feedback(session, message)

        except Exception as e:
            logger.error(f"{self.name}: Error processing messages: {e}", exc_info=True)

    async def _handle_review_feedback(self, session: AsyncSession, message: Message):
        """Handle code review feedback from CTO."""
        logger.info(f"{self.name}: Received review feedback from CTO")

        if "APPROVED" in message.content.upper():
            # Code was approved, mark task as complete
            if message.related_task_id:
                await self.update_task_status(
                    session,
                    str(message.related_task_id),
                    TaskStatus.COMPLETED,
                )

                # Notify PM that task is complete
                await self.send_message(
                    session,
                    to_agent_id="pm_001",
                    content=f"""Task Completed

Task has been approved by CTO and is now complete.

Task ID: {message.related_task_id}

- Backend Engineer
""",
                    message_type=MessageType.INFO,
                    priority=Priority.MEDIUM,
                    related_task_id=message.related_task_id,
                )

                logger.info(f"{self.name}: Task {message.related_task_id} marked as complete")

        elif "CHANGES REQUESTED" in message.content.upper():
            # Need to make changes
            logger.info(f"{self.name}: Changes requested for task {message.related_task_id}")

            # In a real system, would iterate on the code
            # For MVP, we'll just acknowledge
            await self.send_message(
                session,
                to_agent_id="cto_001",
                content=f"""Acknowledged: Changes Requested

I've reviewed your feedback on task {message.related_task_id}.
I'll make the requested changes and resubmit.

- Backend Engineer
""",
                message_type=MessageType.INFO,
                priority=Priority.MEDIUM,
                related_task_id=message.related_task_id,
            )

    async def _get_project(self, session: AsyncSession, project_id) -> Project:
        """Get project by ID."""
        result = await session.execute(
            select(Project).where(Project.project_id == project_id)
        )
        return result.scalar_one_or_none()
