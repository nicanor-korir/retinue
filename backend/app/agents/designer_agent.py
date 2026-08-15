"""Product Designer Agent - Creates UI/UX specifications."""
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


class DesignerAgent(BaseAgent, EventDrivenMixin):
    """
    Product Designer Agent

    Responsibilities:
    - Create UI specifications and mockups
    - Design user flows and interactions
    - Ensure consistent visual design
    - Provide component specifications to engineers
    - Consider accessibility and usability
    """

    def __init__(self):
        system_prompt = """You are a Product Designer. Your responsibilities:

**Core Responsibilities:**
- Create comprehensive UI specifications and mockup descriptions
- Design intuitive user flows and interactions
- Ensure consistent, modern visual design
- Provide clear component specifications to Frontend Engineers
- Consider accessibility (WCAG AA) and usability in all designs
- Update task status in real-time as you progress

**Decision-Making Authority:**
- You CAN decide: Colors, typography, spacing, component layouts, icon choices, interaction patterns, responsive breakpoints, visual hierarchy
- You NEED approval for: Major UX changes, new user flows, branding decisions, design system changes, significant departures from requirements

**Workflow:**
1. Check for assigned tasks every 15 minutes
2. Understand project requirements and user needs thoroughly
3. Research similar applications for inspiration (industry best practices)
4. Create wireframes and visual specifications (described in text)
5. Specify component behavior, states, and interactions
6. Provide clear, detailed specs to Frontend Engineer
7. Request CTO review for approval
8. Mark task as complete after approval

**Design Standards:**
- **Modern Web Design**: Follow current trends (2024-2025)
- **Accessibility**: WCAG AA compliance, high contrast, clear labels
- **Grid System**: 8px grid for consistent spacing
- **Visual Hierarchy**: Clear information hierarchy
- **Mobile-First**: Design for smallest screens first, scale up
- **Consistency**: Reusable patterns and components
- **Performance**: Consider loading states, progressive enhancement

**Output Format:**
Since you output text descriptions (not actual mockups), provide detailed specifications:

1. **Design Overview**: 2-3 sentence summary of the design approach

2. **Layout Structure**:
   - Page/component hierarchy
   - Grid layout (columns, spacing)
   - Responsive behavior at different breakpoints

3. **Visual Design**:
   - **Color Palette**: Primary, secondary, accent, neutral colors (hex codes)
   - **Typography**: Font families, sizes, weights for headings/body
   - **Spacing**: Margins, padding values using 8px grid
   - **Borders & Shadows**: Border radius, box shadows

4. **Components**: For each major component:
   - Component name and purpose
   - Layout and structure
   - Content and text
   - Interactive states (default, hover, focus, active, disabled, error)
   - Responsive behavior

5. **User Flows**:
   - Step-by-step user journey
   - Key interactions and feedback
   - Error states and edge cases

6. **Accessibility**:
   - ARIA labels needed
   - Keyboard navigation flow
   - Focus management
   - Color contrast ratios

7. **Responsive Specifications**:
   - **Mobile** (<640px): Layout changes, simplifications
   - **Tablet** (640px-1024px): Intermediate state
   - **Desktop** (>1024px): Full-featured layout

**Example Output Structure:**
```
Design Overview:
A clean, modern dashboard with a card-based layout emphasizing key metrics and actions.
Uses a professional blue color scheme with high contrast for accessibility.

Layout Structure:
- Header: Fixed top navigation bar (64px height)
- Main: Grid layout with 3 columns on desktop, 1 column on mobile
- Sidebar: Left navigation (280px width on desktop, hidden mobile)

Visual Design:
Colors:
- Primary: #3B82F6 (blue-500)
- Secondary: #64748B (slate-500)
- Accent: #10B981 (green-500)
- Background: #F8FAFC (slate-50)
- Text: #1E293B (slate-900)

Typography:
- Font Family: Inter, system-ui, sans-serif
- Headings: 24px/32px/20px (font-weight: 600)
- Body: 16px (font-weight: 400)
- Small: 14px (font-weight: 400)

Component: Stats Card
- Container: White background, rounded-lg (8px), shadow-sm
- Padding: 24px
- Content:
  * Label: 14px, uppercase, gray-500, letter-spacing: 0.05em
  * Value: 36px, font-weight: 700, slate-900
  * Icon: 24x24px, positioned top-right, blue-500
- States:
  * Default: shadow-sm
  * Hover: shadow-md, slight scale (1.02)
  * Focus: ring-2 ring-blue-500
```

**Communication Style:** User-empathetic, detail-oriented, design-focused. Professional and user-centered.

**Time Compression:** 1 real hour = 1 agent day. Work efficiently and effectively.

Always be thorough, user-focused, and detail-oriented. Provide specifications that Frontend Engineers can implement directly.
"""

        super().__init__(
            agent_id="designer_001",
            name="Product Designer",
            role="Product Designer",
            department="engineering",
            reports_to="cto_001",
            system_prompt=system_prompt,
            permissions={
                "read": ["projects", "tasks", "messages", "knowledge_base"],
                "write": ["tasks", "messages", "knowledge_base"],
                "approve": [],
            },
        )

        # Set up event-driven listeners
        self.setup_event_listeners()

    async def start_task(self, session: AsyncSession, task: Task):
        """Designer creates UI specifications."""
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

            # Call LLM to create design specifications
            prompt = f"""Create comprehensive UI/UX specifications for this feature:

**Task:** {task.title}
**Description:** {task.description}
**Project:** {project.name if project else 'Unknown'}

Provide detailed design specifications following the structure outlined in your system prompt:

1. **Design Overview**: Brief summary of your design approach and philosophy

2. **Layout Structure**: Page organization, grid system, responsive behavior

3. **Visual Design**: Complete specifications for:
   - Color palette (hex codes for primary, secondary, accent, neutrals)
   - Typography (fonts, sizes, weights, line heights)
   - Spacing system (based on 8px grid)
   - Borders, shadows, and effects

4. **Components**: For EACH major UI component, specify:
   - Purpose and behavior
   - Layout and structure details
   - Content and text
   - ALL interactive states (default, hover, focus, active, disabled, error, loading)
   - Exact spacing, sizing, and positioning

5. **User Flows**: Step-by-step description of how users interact with this feature

6. **Accessibility**: WCAG AA compliance details:
   - ARIA labels and roles
   - Keyboard navigation
   - Focus management
   - Color contrast (ensure 4.5:1 minimum)

7. **Responsive Specifications**: Detailed breakdown for:
   - Mobile (<640px)
   - Tablet (640px-1024px)
   - Desktop (>1024px)

8. **Implementation Notes**: Guidance for Frontend Engineer on:
   - Component hierarchy
   - State management needs
   - Animation/transition suggestions
   - Edge cases to handle

Be extremely detailed and specific. The Frontend Engineer should be able to implement this exactly from your specifications without guessing.

Focus on:
- Modern, professional design (2024-2025 trends)
- Excellent usability and accessibility
- Clear visual hierarchy
- Responsive, mobile-first approach
- Consistency and reusability

This is for an MVP, so balance completeness with simplicity.
"""

            design_response = await self.call_llm_with_rag(prompt, context, max_tokens=6000, project_id=str(project.project_id) if project else str(task.project_id))

            logger.info(f"{self.name}: Design specifications complete for {task.title}")

            # Update task to review status
            await self.update_task_status(
                session,
                str(task.task_id),
                TaskStatus.REVIEW,
                output={
                    "design_specs": design_response,
                    "design_type": "ui_specifications",
                    "status": "awaiting_review",
                },
            )

            # Request review from CTO
            await self.send_message(
                session,
                to_agent_id="cto_001",
                content=f"""Design Review Request: {task.title}

I've completed the UI/UX specifications for:
**{task.title}**

**Design Overview:**
{design_response[:500]}... (see full specifications in task details)

Please review and approve, or provide feedback for improvements.

Task ID: {task.task_id}

- Product Designer
""",
                message_type=MessageType.APPROVAL,
                priority=Priority.MEDIUM,
                related_task_id=str(task.task_id),
            )

            # Also notify Frontend Engineer that specs are ready
            await self.send_message(
                session,
                to_agent_id="frontend_001",
                content=f"""Design Specifications Ready: {task.title}

UI/UX specifications are complete and awaiting CTO approval for:
**{task.title}**

Once approved, you can begin implementation using these specifications.

Task ID: {task.task_id}

- Product Designer
""",
                message_type=MessageType.INFO,
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
                output={"error": str(e), "blocking_reason": "Design error"},
            )
            await self.update_status(session, "available")

            # Notify PM about blocker
            await self.send_message(
                session,
                to_agent_id="pm_001",
                content=f"""Task Blocked: {task.title}

I encountered an error while creating design specifications:
{str(e)}

Please review and provide guidance.

- Product Designer
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
        """Handle design review feedback from CTO."""
        logger.info(f"{self.name}: Received review feedback from CTO")

        if "APPROVED" in message.content.upper():
            # Design was approved, mark task as complete
            if message.related_task_id:
                await self.update_task_status(
                    session,
                    str(message.related_task_id),
                    TaskStatus.COMPLETED,
                )

                # Notify PM and Frontend Engineer
                await self.send_message(
                    session,
                    to_agent_id="pm_001",
                    content=f"""Design Task Completed

Design specifications have been approved by CTO and are now complete.

Task ID: {message.related_task_id}

- Product Designer
""",
                    message_type=MessageType.INFO,
                    priority=Priority.MEDIUM,
                    related_task_id=message.related_task_id,
                )

                await self.send_message(
                    session,
                    to_agent_id="frontend_001",
                    content=f"""Design Approved - Ready for Implementation

The design specifications for this task have been approved by CTO.
You can now begin frontend implementation.

Task ID: {message.related_task_id}

- Product Designer
""",
                    message_type=MessageType.INFO,
                    priority=Priority.MEDIUM,
                    related_task_id=message.related_task_id,
                )

                logger.info(f"{self.name}: Task {message.related_task_id} marked as complete")

        elif "CHANGES REQUESTED" in message.content.upper():
            # Need to make changes
            logger.info(f"{self.name}: Changes requested for task {message.related_task_id}")

            await self.send_message(
                session,
                to_agent_id="cto_001",
                content=f"""Acknowledged: Changes Requested

I've reviewed your feedback on task {message.related_task_id}.
I'll revise the design specifications and resubmit.

- Product Designer
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
