"""CEO Agent - Strategic orchestrator and decision maker."""
import logging
import json
from typing import Dict, List
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.agents.base_agent import BaseAgent
from app.agents.event_driven_mixin import EventDrivenMixin
from app.db.event_models import ActivityType, ThoughtType
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
from app.utils.notifications import (
    create_ceo_feedback_notification,
    create_project_completed_notification,
)

logger = logging.getLogger(__name__)


class CEOAgent(BaseAgent, EventDrivenMixin):
    """
    CEO Agent - Chief Executive Officer

    Responsibilities:
    - Receive strategic input from human founder
    - Convene and lead executive meetings
    - Make strategic decisions about project direction
    - Ensure alignment across all departments
    - Escalate critical issues to the human founder
    """

    def __init__(self):
        system_prompt = """You are the CEO of this AI agent company. Your responsibilities:

**Core Responsibilities:**
- Receive strategic input from the human founder
- Convene and lead executive meetings with CTO
- Make strategic decisions about project direction
- Ensure alignment across all departments
- Escalate critical issues to the human founder
- Oversee company operations and coordination

**Decision-Making Authority:**
- You CAN decide: Project priorities, resource allocation across departments, operational strategies, project approval/rejection
- You NEED human approval for: Major strategic pivots, budget decisions >$1000, new product directions, fundamental company changes

**Communication Style:** Executive-level, strategic, focused on outcomes and alignment.

**When you receive a new project request:**
1. Analyze the requirements thoroughly
2. Assess feasibility, scope, and resources needed
3. Convene meeting with CTO to discuss technical approach
4. Make approval decision based on strategic fit
5. Route approved projects to Project Manager for execution
6. Communicate decision clearly to stakeholders

**Decision Framework:**
- Strategic Fit: Does this align with company goals?
- Feasibility: Can we realistically deliver this?
- Resources: Do we have the right people/skills?
- Priority: How does this rank against other projects?
- Risk: What are the potential issues?

**Output Format:**
When analyzing a project, provide a structured response with:
1. **Analysis**: Brief assessment of the project
2. **Decision**: APPROVE or REJECT (clear statement)
3. **Reasoning**: Why this decision makes sense
4. **Next Steps**: What should happen next
5. **CTO Discussion Points**: Key technical questions for CTO

Always be concise, strategic, and action-oriented. Check the database every 15 minutes for executive meetings, escalations, and project updates.
"""

        super().__init__(
            agent_id="ceo_001",
            name="CEO Agent",
            role="Chief Executive Officer",
            department="executive",
            reports_to=None,  # CEO reports to no one (except human founder)
            system_prompt=system_prompt,
            permissions={
                "read": ["projects", "tasks", "messages", "decisions", "agents", "knowledge_base"],
                "write": ["projects", "decisions", "messages"],
                "approve": ["strategic_decisions", "executive_decisions"],
            },
        )

        # Set up event-driven listeners
        self.setup_event_listeners()

    async def start_task(self, session: AsyncSession, task: Task):
        """CEO processes strategic tasks."""
        activity = None
        try:
            logger.info(f"{self.name}: Starting task {task.task_id} - {task.title}")

            # Update status to busy
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
            
            # 🎬 START REAL-TIME EVENT EMISSION
            # Start activity tracking
            activity = await self.emit_activity_start(
                session=session,
                activity_type=ActivityType.THINKING,
                title=f"Evaluating Project: {project.name}",
                description=f"CEO is analyzing project proposal and making approval decision",
                project_id=project.project_id,
                task_id=task.task_id
            )
            
            # Emit initial thought
            await self.emit_thought(
                session=session,
                thought_type=ThoughtType.ANALYSIS,
                content=f"Received new project request: '{project.name}'. Beginning strategic evaluation...",
                project_id=project.project_id,
                task_id=task.task_id
            )
            
            # Update progress
            await self.emit_activity_progress(
                session=session,
                activity_id=activity.activity_id,
                progress=10,
                stage="Reading project description",
                project_id=project.project_id
            )

            # Build context for LLM
            context = {
                "project_name": project.name,
                "project_description": project.description,
                "project_priority": project.priority.value,
                "task_type": "new_project_evaluation",
            }

            # Emit thought about classification
            await self.emit_thought(
                session=session,
                thought_type=ThoughtType.ANALYSIS,
                content="Determining if this is a simple information request or a development project...",
                project_id=project.project_id
            )
            
            await self.emit_activity_progress(
                session, activity.activity_id, 20,
                "Classifying request type", project.project_id
            )
            
            # First, determine if this is a simple query/question that can be answered directly
            classification_prompt = f"""Analyze this project request and classify it:

**Project Name:** {project.name}
**Description:** {project.description}

Is this:
A) A simple question or information request that can be answered directly (e.g., "What's an AI agent?", "Explain machine learning", "How does authentication work?")
B) A development project that requires team coordination (e.g., "Build a todo app", "Create an API", "Develop a dashboard")

Respond with only: SIMPLE_QUERY or DEVELOPMENT_PROJECT
"""

            classification = await self.call_llm_with_rag(classification_prompt, context, max_tokens=50, project_id=str(project.project_id))
            is_simple_query = "SIMPLE_QUERY" in classification.upper()
            
            await self.emit_activity_progress(
                session, activity.activity_id, 30,
                "Request classified", project.project_id
            )

            if is_simple_query:
                await self.emit_thought(
                    session=session,
                    thought_type=ThoughtType.REASONING,
                    content="This is a simple information request. I can answer it directly without team coordination.",
                    project_id=project.project_id
                )
                
                await self.emit_activity_progress(
                    session, activity.activity_id, 50,
                    "Generating answer", project.project_id
                )
                # Handle simple query directly - CEO provides the answer
                answer_prompt = f"""The human founder has asked: {project.name}

Description: {project.description}

Provide a clear, comprehensive, and well-structured answer to this question.
Your response will be delivered directly to the user as the final output.

Structure your response with:
1. **Overview**: Brief introduction to the topic
2. **Key Points**: Main concepts explained clearly (use bullet points if helpful)
3. **Practical Context**: How this applies or why it matters
4. **Additional Resources** (if applicable): Where to learn more

Be informative, professional, and ensure the answer fully addresses their question.
"""

                response = await self.call_llm_with_tracking(
                    session=session,
                    prompt=answer_prompt,
                    context=context,
                    max_tokens=3000,
                    project_id=project.project_id,
                    task_id=task.task_id
                )
                
                await self.emit_activity_progress(
                    session, activity.activity_id, 90,
                    "Answer complete", project.project_id
                )
                
                # Complete activity
                if activity:
                    await self.emit_activity_complete(
                        session, activity.activity_id, project.project_id
                    )

                # Mark project as completed since we're providing direct answer
                stmt = (
                    update(Project)
                    .where(Project.project_id == project.project_id)
                    .values(status=ProjectStatus.COMPLETED, completed_at=func.now())
                )
                await session.execute(stmt)
                await session.commit()

                # Mark task as complete with the answer as output
                await self.update_task_status(
                    session,
                    str(task.task_id),
                    TaskStatus.COMPLETED,
                    output={
                        "query_type": "simple_query",
                        "question": project.name,
                        "answer": response,
                        "answered_by": "CEO Agent",
                        "can_continue": True,  # User can ask follow-up or expand
                    },
                )

                # Create notification for CEO feedback
                await create_ceo_feedback_notification(
                    session=session,
                    project_id=project.project_id,
                    project_name=project.name,
                    feedback=response,
                    priority=Priority.MEDIUM
                )

                # Update status to available
                await self.update_status(session, "available")

                logger.info(f"{self.name}: Answered simple query for project {project.name}")
                return  # Exit early - no need for team coordination

            # For development projects, use the standard approval flow
            await self.emit_thought(
                session=session,
                thought_type=ThoughtType.REASONING,
                content="This is a development project requiring team coordination. Analyzing feasibility and strategic fit...",
                project_id=project.project_id
            )
            
            await self.emit_activity_progress(
                session, activity.activity_id, 40,
                "Analyzing project feasibility", project.project_id
            )
            
            prompt = f"""You have a new development project request from the human founder:

**Project Name:** {project.name}
**Description:** {project.description}
**Priority Level:** {project.priority.value}

Analyze this project request and provide:
1. **Analysis**: Brief assessment (2-3 sentences)
2. **Decision**: APPROVE or REJECT (must be clear)
3. **Reasoning**: Why this decision makes sense (2-3 points)
4. **Next Steps**: What should happen next if approved
5. **CTO Discussion Points**: 2-3 key technical questions/concerns to discuss with CTO

Be strategic and concise. Focus on feasibility and alignment with company capabilities.
"""

            # Call LLM with tracking
            response = await self.call_llm_with_tracking(
                session=session,
                prompt=prompt,
                context=context,
                max_tokens=2000,
                project_id=project.project_id,
                task_id=task.task_id
            )
            
            await self.emit_activity_progress(
                session, activity.activity_id, 70,
                "Analysis complete, making decision", project.project_id
            )

            logger.info(f"{self.name}: LLM analysis complete for project {project.name}")

            # Parse the response to extract decision
            decision_approved = "APPROVE" in response.upper() and "REJECT" not in response.upper()
            
            # Emit decision thought
            await self.emit_thought(
                session=session,
                thought_type=ThoughtType.EVALUATION,
                content=f"Decision: {'APPROVE' if decision_approved else 'REJECT'}. {response[:200]}...",
                project_id=project.project_id
            )
            
            await self.emit_activity_progress(
                session, activity.activity_id, 85,
                f"Decision made: {'APPROVED' if decision_approved else 'REJECTED'}", project.project_id
            )

            # Create decision record
            decision = Decision(
                project_id=project.project_id,
                task_id=task.task_id,
                made_by_agent_id=self.agent_id,
                decision_type="executive",
                decision_category="strategic",
                question=f"Should we approve project: {project.name}?",
                rationale=response,
                decision="APPROVED" if decision_approved else "REJECTED",
                approved=decision_approved,
                approved_by=self.agent_id,
            )
            session.add(decision)
            await session.commit()

            if decision_approved:
                await self.emit_activity_progress(
                    session, activity.activity_id, 90,
                    "Coordinating with team", project.project_id
                )
                
                # Update project status to in_progress
                stmt = (
                    update(Project)
                    .where(Project.project_id == project.project_id)
                    .values(status=ProjectStatus.IN_PROGRESS)
                )
                await session.execute(stmt)
                await session.commit()

                # Emit handoff to CTO
                await self.emit_handoff(
                    session=session,
                    to_agent_id="cto_001",
                    message=f"Project '{project.name}' approved. Requesting technical evaluation.",
                    project_id=project.project_id,
                    task_id=task.task_id,
                    handoff_type="technical_review"
                )

                # Create task for CTO to review technical feasibility
                import uuid
                cto_task = Task(
                    task_id=uuid.uuid4(),
                    project_id=project.project_id,
                    assigned_to_agent_id="cto_001",
                    title=f"Technical evaluation: {project.name}",
                    description=f"""Project approved by CEO. Please evaluate:

{response}

Provide technical assessment and coordinate with PM for implementation.
""",
                    status=TaskStatus.PENDING,
                    estimated_hours=2,
                )
                session.add(cto_task)

                # Create task for PM to break down the project
                pm_task = Task(
                    task_id=uuid.uuid4(),
                    project_id=project.project_id,
                    assigned_to_agent_id="pm_001",
                    title=f"Break down project: {project.name}",
                    description=f"""CEO approved project. CTO is reviewing technical aspects.

Project: {project.name}
Description: {project.description}

Please create detailed task breakdown for implementation.
""",
                    status=TaskStatus.PENDING,
                    estimated_hours=3,
                    dependencies=[str(cto_task.task_id)],  # PM should wait for CTO
                )
                session.add(pm_task)

                # Commit tasks BEFORE sending messages that reference them
                await session.commit()
                await session.refresh(cto_task)
                await session.refresh(pm_task)

                # Now send messages with valid task IDs
                await self.send_message(
                    session,
                    to_agent_id="cto_001",
                    content=f"""Project Approved: {project.name}

{response}

Task created for technical review. Please assess feasibility and coordinate with PM.
""",
                    message_type=MessageType.REQUEST,
                    priority=project.priority,
                    related_task_id=str(cto_task.task_id),
                )

                # Emit handoff to PM
                await self.emit_handoff(
                    session=session,
                    to_agent_id="pm_001",
                    message=f"New project '{project.name}' approved. Prepare for task breakdown.",
                    project_id=project.project_id,
                    task_id=task.task_id,
                    handoff_type="project_assignment"
                )

                # Send message to PM
                await self.send_message(
                    session,
                    to_agent_id="pm_001",
                    content=f"""New Project Assignment: {project.name}

Project approved! Task created for breakdown after CTO review.

Priority: {project.priority.value}
""",
                    message_type=MessageType.INFO,
                    priority=project.priority,
                    related_task_id=str(pm_task.task_id),
                )

                # Final commit for messages
                await session.commit()
                
                # Add timeline event
                await self.emit_timeline_event(
                    session=session,
                    event_type="approval",
                    title=f"Project Approved: {project.name}",
                    project_id=project.project_id,
                    description="CEO approved project after strategic evaluation",
                    is_highlight=True,
                    highlight_type="key_decision"
                )

                logger.info(f"{self.name}: Project {project.name} APPROVED - notified CTO and PM")

            else:
                # Update project status to cancelled
                stmt = (
                    update(Project)
                    .where(Project.project_id == project.project_id)
                    .values(status=ProjectStatus.CANCELLED)
                )
                await session.execute(stmt)
                await session.commit()
                
                # Add timeline event for rejection
                await self.emit_timeline_event(
                    session=session,
                    event_type="rejection",
                    title=f"Project Rejected: {project.name}",
                    project_id=project.project_id,
                    description="CEO rejected project after strategic evaluation",
                    is_highlight=True,
                    highlight_type="key_decision"
                )

                logger.info(f"{self.name}: Project {project.name} REJECTED")
            
            # Complete activity
            if activity:
                await self.emit_activity_complete(
                    session, activity.activity_id, project.project_id
                )

            # Mark task as complete
            await self.update_task_status(
                session,
                str(task.task_id),
                TaskStatus.COMPLETED,
                output={
                    "decision": "approved" if decision_approved else "rejected",
                    "analysis": response,
                    "project_status": "in_progress" if decision_approved else "cancelled",
                },
            )

            # Create notification for CEO decision
            decision_text = "approved" if decision_approved else "rejected"
            await create_ceo_feedback_notification(
                session=session,
                project_id=project.project_id,
                project_name=project.name,
                feedback=f"Project {decision_text}. {response[:300]}",
                priority=Priority.HIGH if decision_approved else Priority.MEDIUM
            )

            # Update status to available
            await self.update_status(session, "available")

            logger.info(f"{self.name}: Completed task {task.task_id}")

        except Exception as e:
            logger.error(f"{self.name}: Error in start_task: {e}", exc_info=True)
            # Rollback any uncommitted changes
            await session.rollback()
            try:
                await self.update_task_status(
                    session,
                    str(task.task_id),
                    TaskStatus.COMPLETED,
                    output={"error": str(e)},
                )
                await self.update_status(session, "available")
            except Exception as cleanup_error:
                logger.error(f"{self.name}: Error during cleanup: {cleanup_error}", exc_info=True)

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
                    await self._handle_approval_request(session, message)
                elif message.message_type == MessageType.ALERT:
                    await self._handle_alert(session, message)
                elif message.message_type == MessageType.REQUEST:
                    await self._handle_request(session, message)
                else:
                    # Info message - just log it
                    logger.info(f"{self.name}: Info message from {message.from_agent_id}: {message.content[:100]}")

        except Exception as e:
            logger.error(f"{self.name}: Error processing messages: {e}", exc_info=True)

    async def _handle_approval_request(self, session: AsyncSession, message: Message):
        """Handle approval requests from other agents."""
        logger.info(f"{self.name}: Handling approval request from {message.from_agent_id}")

        # Build prompt for decision
        prompt = f"""You received an approval request from {message.from_agent_id}:

{message.content}

Analyze this request and decide whether to approve or reject it. Consider:
- Strategic alignment
- Risk level
- Resource implications
- Priority

Provide:
1. **Decision**: APPROVE or REJECT
2. **Reasoning**: Brief explanation (2-3 sentences)
3. **Guidance**: Any additional guidance for the requesting agent
"""

        response = await self.call_llm_with_rag(prompt, max_tokens=1000, project_id=str(message.related_task_id) if message.related_task_id else None)
        approved = "APPROVE" in response.upper() and "REJECT" not in response.upper()

        # Send response back
        await self.send_message(
            session,
            to_agent_id=message.from_agent_id,
            content=f"""Re: Your approval request

{response}

Decision: {"APPROVED" if approved else "REJECTED"}
""",
            message_type=MessageType.INFO,
            priority=message.priority,
            related_task_id=message.related_task_id,
        )

        logger.info(f"{self.name}: Responded to approval request - {'APPROVED' if approved else 'REJECTED'}")

    async def _handle_alert(self, session: AsyncSession, message: Message):
        """Handle alert messages."""
        logger.warning(f"{self.name}: Alert from {message.from_agent_id}: {message.content}")

        # For critical alerts, might need to escalate to human
        if message.priority == Priority.URGENT:
            logger.error(f"{self.name}: URGENT alert - may need human intervention")
            # In a real system, this would trigger a notification to the human founder

    async def _handle_request(self, session: AsyncSession, message: Message):
        """Handle general requests."""
        logger.info(f"{self.name}: Request from {message.from_agent_id}")

        # Use LLM to formulate response
        prompt = f"""You received a request from {message.from_agent_id}:

{message.content}

Provide a brief, strategic response addressing their request.
"""

        response = await self.call_llm_with_rag(prompt, max_tokens=1000, project_id=str(message.related_task_id) if message.related_task_id else None)

        # Send response
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
