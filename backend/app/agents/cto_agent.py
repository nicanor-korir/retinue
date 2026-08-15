"""CTO Agent - Technical oversight and architecture decisions."""
import logging
import json
from typing import Dict, List
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base_agent import BaseAgent
from app.agents.event_driven_mixin import EventDrivenMixin
from app.db.models import (
    Task,
    Message,
    Project,
    Decision,
    ProjectStatus,
    TaskStatus,
    MessageType,
    Priority,
)

logger = logging.getLogger(__name__)


class CTOAgent(BaseAgent, EventDrivenMixin):
    """
    CTO Agent - Chief Technology Officer

    Responsibilities:
    - Discuss technical feasibility with CEO
    - Make architectural and technology decisions
    - Coordinate with PM on project breakdowns
    - Review engineering output for quality
    - Approve technical designs from engineers
    - Escalate resource conflicts or technical blockers
    """

    def __init__(self):
        system_prompt = """You are the CTO overseeing the engineering team. Your responsibilities:

**Core Responsibilities:**
- Discuss technical feasibility with CEO
- Make architectural and technology decisions
- Coordinate with PM on project breakdowns
- Review engineering output for quality
- Approve technical designs from engineers
- Escalate resource conflicts or technical blockers
- Mentor engineers and maintain code quality standards

**Decision-Making Authority:**
- You CAN decide: Tech stack choices, architecture patterns, code standards, task assignments to engineers, code review approvals
- You NEED CEO approval for: Major architecture changes, new technology adoption, timeline extensions >1 week, significant resource additions

**Technical Expertise:**
- Full-stack development (backend, frontend, databases)
- System design and architecture
- Best practices and design patterns
- DevOps and deployment strategies
- Performance optimization
- Security best practices

**Communication Style:** Technical but clear, mentoring engineers, solution-oriented, pragmatic.

**When reviewing a project:**
1. Assess technical feasibility thoroughly
2. Recommend appropriate technology stack
3. Identify technical risks and mitigation strategies
4. Estimate engineering effort accurately
5. Provide clear architectural guidance
6. Consider scalability and maintainability

**Technical Review Checklist:**
- Is the architecture sound and scalable?
- Are we using appropriate technologies?
- Are there any technical risks?
- Is the timeline realistic?
- Do we have the right skills on the team?
- Are there security considerations?

**Output Format:**
When providing technical guidance, structure as:
1. **Technical Assessment**: Brief technical evaluation
2. **Recommended Stack**: Technologies to use
3. **Architecture**: High-level architecture approach
4. **Risks**: Potential technical challenges
5. **Estimate**: Realistic time estimate
6. **Next Steps**: What PM and engineers should do

Always be technical, pragmatic, and focused on quality. Check the database every 15 minutes for engineering tasks, code reviews, and technical decisions.
"""

        super().__init__(
            agent_id="cto_001",
            name="CTO Agent",
            role="Chief Technology Officer",
            department="executive",
            reports_to="ceo_001",
            system_prompt=system_prompt,
            permissions={
                "read": ["projects", "tasks", "messages", "decisions", "agents", "knowledge_base"],
                "write": ["tasks", "decisions", "messages", "knowledge_base"],
                "approve": ["technical_decisions", "architecture_decisions"],
            },
        )

        # Set up event-driven listeners
        self.setup_event_listeners()

    async def start_task(self, session: AsyncSession, task: Task):
        """CTO processes technical tasks."""
        try:
            logger.info(f"{self.name}: Starting task {task.task_id} - {task.title}")

            await self.update_status(session, "busy", current_task_id=str(task.task_id))
            await self.update_task_status(session, str(task.task_id), TaskStatus.IN_PROGRESS)

            # Get project context
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

            # Build context
            context = {
                "project_name": project.name,
                "project_description": project.description,
                "project_priority": project.priority.value,
                "task_type": "technical_feasibility_review",
            }

            # Call LLM for technical analysis
            prompt = f"""You need to provide technical guidance for this approved project:

**Project Name:** {project.name}
**Description:** {project.description}
**Priority:** {project.priority.value}

Provide a comprehensive technical analysis:

1. **Technical Assessment**:
   - Is this technically feasible?
   - What are the main technical challenges?

2. **Recommended Stack**:
   - Backend technologies (specify languages, frameworks)
   - Frontend technologies (specify frameworks, libraries)
   - Database choice (specify database type and reasoning)
   - Any other tools or services needed

3. **Architecture Approach**:
   - High-level architecture (2-3 sentences)
   - Key components and how they interact
   - API design approach

4. **Technical Risks**:
   - What could go wrong technically?
   - Mitigation strategies

5. **Time Estimate**:
   - Realistic estimate in agent-hours
   - Breakdown by component (Design, Backend, Frontend)

6. **Engineer Assignments**:
   - Which roles are needed (Designer, Backend Engineer, Frontend Engineer)
   - What each should focus on

Be specific and practical. Consider that we're building an MVP, so prioritize simplicity and speed while maintaining quality.
"""

            response = await self.call_llm_with_rag(prompt, context, max_tokens=3000, project_id=str(project.project_id))

            logger.info(f"{self.name}: Technical analysis complete for {project.name}")

            # Create decision record
            decision = Decision(
                project_id=project.project_id,
                task_id=task.task_id,
                made_by_agent_id=self.agent_id,
                decision_type="technical",
                decision_category="architecture",
                question=f"Technical approach for: {project.name}",
                rationale=response,
                decision="Technical guidance provided",
                approved=True,
                approved_by=self.agent_id,
            )
            session.add(decision)
            await session.commit()

            # Send technical guidance to PM
            await self.send_message(
                session,
                to_agent_id="pm_001",
                content=f"""Technical Guidance for: {project.name}

{response}

Please break down the project into specific tasks based on this technical guidance. Assign tasks to the appropriate engineers (Designer, Backend, Frontend) with clear requirements.

The estimates above should help with task planning.
""",
                message_type=MessageType.REQUEST,
                priority=project.priority,
                related_task_id=str(task.task_id),
            )

            # Update task as complete
            await self.update_task_status(
                session,
                str(task.task_id),
                TaskStatus.COMPLETED,
                output={
                    "technical_guidance": response,
                    "status": "completed",
                },
            )

            await self.update_status(session, "available")

            logger.info(f"{self.name}: Completed technical review for {project.name}")

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

                # Process based on message type
                if message.message_type == MessageType.APPROVAL:
                    await self._handle_code_review(session, message)
                elif message.message_type == MessageType.ALERT:
                    await self._handle_technical_alert(session, message)
                elif message.message_type == MessageType.REQUEST:
                    await self._handle_technical_question(session, message)
                else:
                    # Info message
                    logger.info(f"{self.name}: Info from {message.from_agent_id}")

        except Exception as e:
            logger.error(f"{self.name}: Error processing messages: {e}", exc_info=True)

    async def _handle_code_review(self, session: AsyncSession, message: Message):
        """Handle code review requests from engineers."""
        logger.info(f"{self.name}: Reviewing code from {message.from_agent_id}")

        # Build review prompt
        prompt = f"""You received a code review request from {message.from_agent_id}:

{message.content}

Review this code/design submission. Check for:
1. **Code Quality**: Is it well-structured and maintainable?
2. **Best Practices**: Does it follow coding standards?
3. **Functionality**: Does it meet the requirements?
4. **Performance**: Are there any obvious performance issues?
5. **Security**: Any security concerns?

Provide:
- **Decision**: APPROVE or REQUEST_CHANGES
- **Feedback**: Specific, constructive feedback
- **Suggestions**: Any improvements or best practices to apply

Be constructive and mentoring in your feedback.
"""

        response = await self.call_llm_with_rag(prompt, max_tokens=2000, project_id=str(message.related_task_id) if message.related_task_id else None)
        approved = "APPROVE" in response.upper() and "REQUEST_CHANGES" not in response.upper()

        # Send review feedback
        await self.send_message(
            session,
            to_agent_id=message.from_agent_id,
            content=f"""Code Review Feedback

{response}

Status: {"APPROVED ✓" if approved else "CHANGES REQUESTED"}

{"You may proceed with this implementation." if approved else "Please address the feedback and resubmit when ready."}
""",
            message_type=MessageType.INFO,
            priority=message.priority,
            related_task_id=message.related_task_id,
        )

        logger.info(f"{self.name}: Code review complete - {'APPROVED' if approved else 'CHANGES REQUESTED'}")

    async def _handle_technical_alert(self, session: AsyncSession, message: Message):
        """Handle technical alerts."""
        logger.warning(f"{self.name}: Technical alert from {message.from_agent_id}")

        # Analyze the alert and provide guidance
        prompt = f"""Technical alert from {message.from_agent_id}:

{message.content}

Provide:
1. **Analysis**: What's the technical issue?
2. **Solution**: How to resolve it?
3. **Prevention**: How to avoid this in the future?

Be specific and actionable.
"""

        response = await self.call_llm_with_rag(prompt, max_tokens=1500, project_id=str(message.related_task_id) if message.related_task_id else None)

        # Send guidance
        await self.send_message(
            session,
            to_agent_id=message.from_agent_id,
            content=f"""Technical Guidance

{response}

Let me know if you need additional support.
""",
            message_type=MessageType.INFO,
            priority=message.priority,
            related_task_id=message.related_task_id,
        )

        # If critical, also notify CEO
        if message.priority == Priority.URGENT:
            await self.send_message(
                session,
                to_agent_id="ceo_001",
                content=f"""Technical Alert from {message.from_agent_id}:

{message.content}

My analysis and response:
{response}

Monitoring the situation.
""",
                message_type=MessageType.ALERT,
                priority=Priority.HIGH,
            )

    async def _handle_technical_question(self, session: AsyncSession, message: Message):
        """Handle technical questions from team."""
        logger.info(f"{self.name}: Technical question from {message.from_agent_id}")

        prompt = f"""Technical question from {message.from_agent_id}:

{message.content}

Provide a clear, technical answer with:
1. **Answer**: Direct response to their question
2. **Reasoning**: Why this is the right approach
3. **Example**: If applicable, a brief example
4. **Resources**: Any additional guidance

Be helpful and educational.
"""

        response = await self.call_llm_with_rag(prompt, max_tokens=1500, project_id=str(message.related_task_id) if message.related_task_id else None)

        await self.send_message(
            session,
            to_agent_id=message.from_agent_id,
            content=response,
            message_type=MessageType.INFO,
            priority=message.priority,
            related_task_id=message.related_task_id,
        )

    async def _get_project(self, session: AsyncSession, project_id) -> Project:
        """Get project by ID."""
        result = await session.execute(
            select(Project).where(Project.project_id == project_id)
        )
        return result.scalar_one_or_none()
