"""Project Manager Agent - Coordinates all work and task assignments."""
from __future__ import annotations
import logging
import json
import uuid
import re
from typing import Dict, List
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base_agent import BaseAgent
from app.agents.event_driven_mixin import EventDrivenMixin
from app.db.models import (
    Task,
    Message,
    Project,
    Agent,
    AgentStatus,
    Escalation,
    ProjectStatus,
    TaskStatus,
    MessageType,
    Priority,
    Availability,
)
from app.db.escalation_models import EscalationType, EscalationPriority

logger = logging.getLogger(__name__)


class PMAgent(BaseAgent, EventDrivenMixin):
    """
    Project Manager Agent

    Responsibilities:
    - Break down projects into actionable tasks
    - Assign tasks to appropriate agents
    - Monitor progress and identify blockers
    - Escalate conflicts to appropriate stakeholders
    - Keep projects on track and on time
    - Coordinate cross-functional dependencies
    """

    def __init__(self):
        system_prompt = """You are the Project Manager coordinating all work. Your responsibilities:

**Core Responsibilities:**
- Break down projects into actionable, specific tasks
- Assign tasks to appropriate agents based on skills and availability
- Monitor progress every 15 minutes and identify blockers
- Escalate conflicts to appropriate stakeholders immediately
- Keep projects on track and on time
- Coordinate cross-functional dependencies between agents
- Ensure clear communication across the team

**Decision-Making Authority:**
- You CAN decide: Task assignments, task priorities, minor deadline adjustments (<2 days), resource reallocation within a project
- You NEED approval for: Major scope changes, deadline extensions >2 days, cross-project resource conflicts, adding new team members

**Task Creation Best Practices:**
1. **Specific**: Each task should have a clear, single objective
2. **Actionable**: Task description should be concrete and implementable
3. **Assigned**: Assign to the right specialist (designer, backend_001, frontend_001)
4. **Sequenced**: Identify and document dependencies
5. **Estimated**: Provide realistic time estimates in hours
6. **Acceptance Criteria**: Define what "done" looks like

**Workflow:**
1. Receive project approval and technical guidance from CEO/CTO
2. Break down project into logical tasks (Design → Backend → Frontend → Integration)
3. Assign tasks to appropriate agents based on role and availability
4. Set up task dependencies (e.g., Frontend depends on Backend API)
5. Monitor task status every 15 minutes
6. Identify and escalate blockers immediately
7. Coordinate handoffs between agents

**Task Breakdown Structure:**
For a typical web application project:
1. **Design Tasks** → Designer creates UI/UX specifications
2. **Backend Tasks** → Backend engineer builds API and database
3. **Frontend Tasks** → Frontend engineer builds UI components
4. **Integration Tasks** → Ensure all parts work together
5. **Testing Tasks** → Verify functionality

**Output Format for Task Creation:**
Provide tasks in this JSON structure:
```json
[
  {
    "title": "Clear, specific task title",
    "description": "Detailed description with requirements and acceptance criteria",
    "assigned_to": "designer_001" or "backend_001" or "frontend_001",
    "estimated_hours": 4,
    "dependencies": ["task_title_this_depends_on"],
    "priority": "high" or "medium" or "low"
  }
]
```

**Communication Style:** Clear, organized, proactive about risks, focused on execution.

Always be organized, proactive, and detail-oriented. Check the database every 15 minutes for task updates, blockers, and dependencies.
"""

        super().__init__(
            agent_id="pm_001",
            name="Project Manager Agent",
            role="Project Manager",
            department="operations",
            reports_to="ceo_001",
            system_prompt=system_prompt,
            permissions={
                "read": ["projects", "tasks", "messages", "agents", "agent_status"],
                "write": ["projects", "tasks", "messages", "escalations"],
                "approve": ["task_reassignments", "minor_deadline_changes"],
            },
        )

        # Set up event-driven listeners
        self.setup_event_listeners()

    async def start_task(self, session: AsyncSession, task: Task):
        """PM breaks down projects into tasks."""
        try:
            logger.info(f"{self.name}: Starting task {task.task_id} - {task.title}")

            await self.update_status(session, "busy", current_task_id=str(task.task_id))
            await self.update_task_status(session, str(task.task_id), TaskStatus.IN_PROGRESS)

            # Get project details
            project = await self._get_project(session, task.project_id)
            if not project:
                logger.error(f"{self.name}: Project {task.project_id} not found")
                await self.update_task_status(
                    session,
                    str(task.task_id),
                    TaskStatus.COMPLETED,
                    output={"error": "Project not found"},
                )
                return

            # Get technical guidance from previous messages/decisions
            technical_guidance = await self._get_technical_guidance(session, project.project_id)

            # Build context
            context = {
                "project_name": project.name,
                "project_description": project.description,
                "project_priority": project.priority.value,
                "technical_guidance": technical_guidance,
            }

            # Call LLM to break down project into tasks
            prompt = f"""You need to break down this project into specific, actionable tasks:

**Project Name:** {project.name}
**Description:** {project.description}
**Priority:** {project.priority.value}

**Technical Guidance from CTO:**
{technical_guidance if technical_guidance else "No specific technical guidance provided yet. Use best practices."}

Break this project into specific tasks. For a typical application, you'll need:
1. **Design tasks** - UI/UX specifications (assign to designer_001)
2. **Backend tasks** - API endpoints, database schema, business logic (assign to backend_001)
3. **Frontend tasks** - UI components, pages, user interactions (assign to frontend_001)

For each task, provide:
- **title**: Clear, specific title (e.g., "Design user authentication flow")
- **description**: Detailed requirements and acceptance criteria
- **assigned_to**: "designer_001", "backend_001", or "frontend_001"
- **estimated_hours**: Realistic estimate (2-8 hours per task)
- **dependencies**: List of task titles this depends on (e.g., frontend depends on backend API)
- **priority**: "high", "medium", or "low"

Return ONLY a valid JSON array of tasks. Example format:
[
  {{
    "title": "Design main dashboard UI",
    "description": "Create wireframes and specifications for the main dashboard including layout, components, and user interactions.",
    "assigned_to": "designer_001",
    "estimated_hours": 4,
    "dependencies": [],
    "priority": "high"
  }},
  {{
    "title": "Build user authentication API",
    "description": "Implement JWT-based authentication with login, register, and token refresh endpoints. Include password hashing and validation.",
    "assigned_to": "backend_001",
    "estimated_hours": 6,
    "dependencies": [],
    "priority": "high"
  }}
]

Be specific and practical. Create 5-10 tasks depending on project complexity.
"""

            response = await self.call_llm_with_rag(prompt, context, max_tokens=4000, project_id=str(project.project_id))

            logger.info(f"{self.name}: Task breakdown complete for {project.name}")

            # Parse tasks from response
            tasks_data = self._parse_tasks_from_response(response)

            if not tasks_data:
                logger.error(f"{self.name}: Failed to parse tasks from LLM response")
                await self.update_task_status(
                    session,
                    str(task.task_id),
                    TaskStatus.COMPLETED,
                    output={"error": "Failed to parse tasks", "raw_response": response},
                )
                return

            # Create tasks in database
            created_tasks = await self._create_tasks(session, project.project_id, tasks_data)

            logger.info(f"{self.name}: Created {len(created_tasks)} tasks for project {project.name}")

            # Notify assigned agents
            for task_data in tasks_data:
                agent_id = task_data.get("assigned_to")
                if agent_id:
                    await self.send_message(
                        session,
                        to_agent_id=agent_id,
                        content=f"""New Task Assigned: {task_data['title']}

**Project:** {project.name}
**Description:** {task_data['description']}
**Estimated Hours:** {task_data.get('estimated_hours', 'N/A')}
**Priority:** {task_data.get('priority', 'medium')}
**Dependencies:** {', '.join(task_data.get('dependencies', [])) if task_data.get('dependencies') else 'None'}

Please review and begin work when ready.
""",
                        message_type=MessageType.INFO,
                        priority=project.priority,
                    )

            # Mark PM's task as complete
            await self.update_task_status(
                session,
                str(task.task_id),
                TaskStatus.COMPLETED,
                output={
                    "tasks_created": len(created_tasks),
                    "task_breakdown": tasks_data,
                },
            )

            await self.update_status(session, "available")

            logger.info(f"{self.name}: Project breakdown complete for {project.name}")

        except Exception as e:
            logger.error(f"{self.name}: Error in start_task: {e}", exc_info=True)
            await self.update_task_status(
                session,
                str(task.task_id),
                TaskStatus.COMPLETED,
                output={"error": str(e)},
            )
            await self.update_status(session, "available")

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

                # Check if this is a task completion notification
                if "completed" in message.content.lower() or "finished" in message.content.lower():
                    await self._check_project_completion(session, message)

                # Check for blockers
                if "blocked" in message.content.lower() or "stuck" in message.content.lower():
                    await self._handle_blocker(session, message)

        except Exception as e:
            logger.error(f"{self.name}: Error processing messages: {e}", exc_info=True)

    def _parse_tasks_from_response(self, response: str) -> List[Dict]:
        """Parse LLM response into structured tasks."""
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                json_str = json_match.group(0)
                tasks = json.loads(json_str)

                # Validate structure
                valid_tasks = []
                for task in tasks:
                    if isinstance(task, dict) and "title" in task and "assigned_to" in task:
                        valid_tasks.append(task)

                logger.info(f"{self.name}: Parsed {len(valid_tasks)} valid tasks from response")
                return valid_tasks
            else:
                logger.error(f"{self.name}: No JSON array found in response")
                return []

        except json.JSONDecodeError as e:
            logger.error(f"{self.name}: JSON decode error: {e}")
            return []
        except Exception as e:
            logger.error(f"{self.name}: Error parsing tasks: {e}")
            return []

    async def _create_tasks(self, session: AsyncSession, project_id, tasks_data: List[Dict]) -> List[Task]:
        """Create tasks in database."""
        created_tasks = []

        for task_data in tasks_data:
            new_task = Task(
                task_id=uuid.uuid4(),
                project_id=project_id,
                assigned_to_agent_id=task_data.get("assigned_to", "backend_001"),
                title=task_data.get("title", "Untitled Task"),
                description=task_data.get("description", ""),
                status=TaskStatus.PENDING,
                dependencies=task_data.get("dependencies", []),
                estimated_hours=task_data.get("estimated_hours", 4),
            )
            session.add(new_task)
            created_tasks.append(new_task)

        await session.commit()
        return created_tasks

    async def _get_technical_guidance(self, session: AsyncSession, project_id) -> str:
        """Get technical guidance from CTO for this project."""
        from app.db.models import Decision

        result = await session.execute(
            select(Decision)
            .where(
                Decision.project_id == project_id,
                Decision.made_by_agent_id == "cto_001",
            )
            .order_by(Decision.timestamp.desc())
            .limit(1)
        )
        decision = result.scalar_one_or_none()

        if decision:
            return decision.rationale
        return ""

    async def _check_project_completion(self, session: AsyncSession, message: Message):
        """Check if all tasks in a project are complete."""
        if not message.related_task_id:
            return

        # Get the task and project
        result = await session.execute(
            select(Task).where(Task.task_id == message.related_task_id)
        )
        task = result.scalar_one_or_none()

        if not task:
            return

        # Get all tasks for this project
        result = await session.execute(
            select(Task).where(Task.project_id == task.project_id)
        )
        all_tasks = result.scalars().all()

        # Check if all complete
        all_complete = all(t.status == TaskStatus.COMPLETED for t in all_tasks)

        if all_complete:
            # Update project status
            stmt = (
                update(Project)
                .where(Project.project_id == task.project_id)
                .values(status=ProjectStatus.COMPLETED)
            )
            await session.execute(stmt)
            await session.commit()

            # Notify CEO
            project = await self._get_project(session, task.project_id)
            await self.send_message(
                session,
                to_agent_id="ceo_001",
                content=f"""Project Completed: {project.name if project else 'Unknown'}

All tasks have been completed successfully.
Total tasks: {len(all_tasks)}

Ready for final review and delivery.
""",
                message_type=MessageType.INFO,
                priority=Priority.HIGH,
            )

            logger.info(f"{self.name}: Project {task.project_id} marked as complete")

    async def _handle_blocker(self, session: AsyncSession, message: Message):
        """Handle reported blockers using new escalation system."""
        try:
            logger.warning(f"{self.name}: Blocker reported by {message.from_agent_id}")

            # Check if we already have an open escalation for this task
            if message.related_task_id and not await self.has_open_escalation(
                session,
                escalation_type=EscalationType.BLOCKED_TASK,
                related_entity_id=message.related_task_id
            ):
                # Create escalation using new system
                await self.create_escalation(
                    session=session,
                    title=f"Task blocked by {message.from_agent_id}",
                    escalation_type=EscalationType.BLOCKED_TASK,
                    priority=EscalationPriority.HIGH,
                    description=f"Blocker reported by {message.from_agent_id}: {message.content}",
                    impact="high",
                    urgency="high",
                    related_task_id=message.related_task_id
                )

                logger.info(f"{self.name}: Created escalation for blocked task")
                
        except Exception as e:
            logger.error(f"{self.name}: Error handling blocker: {e}", exc_info=True)

    async def _get_project(self, session: AsyncSession, project_id) -> Project:
        """Get project by ID."""
        result = await session.execute(
            select(Project).where(Project.project_id == project_id)
        )
        return result.scalar_one_or_none()
