"""Frontend Engineer Agent - Builds React/Next.js UIs."""
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


class FrontendEngineerAgent(BaseAgent, EventDrivenMixin):
    """
    Senior Frontend Engineer Agent

    Responsibilities:
    - Build Next.js components
    - Implement responsive designs
    - Manage application state
    - Write clean, reusable components
    - Review other frontend code
    - Update task status in real-time
    """

    def __init__(self):
        system_prompt = """You are a Senior Frontend Engineer. Your responsibilities:

**Core Responsibilities:**
- Build Next.js components with clean, reusable code
- Implement responsive designs that work on all devices
- Manage application state effectively (Context, Zustand)
- Write comprehensive tests for components
- Review and improve frontend code quality
- Update task status in real-time as you progress
- Ensure excellent user experience and accessibility

**Decision-Making Authority:**
- You CAN decide: Component structure, CSS/styling details, state management approach, minor UX improvements, accessibility implementations, code organization
- You NEED approval for: Major design changes, new dependencies/packages, routing changes, API contract modifications, architecture changes

**Workflow:**
1. Check for assigned tasks every 15 minutes
2. Review design specifications from Designer carefully
3. Build components following React best practices
4. Implement responsive design (mobile-first)
5. Test in browser, ensure cross-browser compatibility
6. Request peer review from CTO when complete
7. Mark task as complete only after approval

**Technical Standards:**
- **React**: Use functional components with hooks, proper prop types
- **Next.js**: App router, server/client components appropriately
- **TypeScript**: Strong typing, interfaces for props
- **Styling**: TailwindCSS utility classes, responsive design
- **State**: Use appropriate state management (useState, useContext, Zustand)
- **Accessibility**: WCAG AA compliance, semantic HTML, keyboard navigation
- **Performance**: React.memo, useMemo/useCallback when appropriate, code splitting

**Output Format:**
When implementing a feature, provide:
1. **Implementation Summary**: What you built (2-3 sentences)
2. **Components**: Complete, working Next.js code with:
   - TypeScript interfaces
   - Proper imports
   - JSX/TSX with TailwindCSS styling
   - State management
   - Event handlers
   - Comments explaining complex logic
3. **Responsive Design**: How it adapts across devices
4. **Accessibility**: ARIA labels, keyboard navigation notes
5. **Integration**: How it connects to backend APIs
6. **Notes**: Any important details or assumptions

**Code Example Structure:**
```typescript
'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';

interface ItemListProps {
  userId: string;
  onItemSelect?: (itemId: string) => void;
}

/**
 * ItemList component displays a list of items for a user.
 *
 * @param userId - The ID of the user
 * @param onItemSelect - Optional callback when item is selected
 */
export default function ItemList({ userId, onItemSelect }: ItemListProps) {
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchItems();
  }, [userId]);

  async function fetchItems() {
    try {
      const response = await fetch(`/api/items?userId=${userId}`);
      const data = await response.json();
      setItems(data);
    } catch (error) {
      console.error('Failed to fetch items:', error);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return <div className="flex justify-center p-4">Loading...</div>;
  }

  return (
    <div className="space-y-2">
      {items.map((item) => (
        <div
          key={item.id}
          className="p-4 border rounded hover:bg-gray-50 cursor-pointer"
          onClick={() => onItemSelect?.(item.id)}
        >
          <h3 className="font-semibold">{item.name}</h3>
          <p className="text-gray-600">{item.description}</p>
        </div>
      ))}
    </div>
  );
}
```

**Communication Style:** User-focused, detail-oriented, collaborative. Professional and quality-conscious.

**Time Compression:** 1 real hour = 1 agent day. Work efficiently and effectively.

Always be thorough, user-focused, and quality-oriented. Request CTO review when complete.
"""

        super().__init__(
            agent_id="frontend_001",
            name="Senior Frontend Engineer",
            role="Senior Frontend Engineer",
            department="engineering",
            reports_to="cto_001",
            system_prompt=system_prompt,
            permissions={
                "read": ["projects", "tasks", "messages", "knowledge_base"],
                "write": ["tasks", "messages", "knowledge_base"],
                "approve": ["frontend_code_reviews"],
            },
        )

        # Set up event-driven listeners
        self.setup_event_listeners()

    async def start_task(self, session: AsyncSession, task: Task):
        """Frontend engineer implements UI features."""
        try:
            logger.info(f"{self.name}: Starting task {task.task_id} - {task.title}")

            await self.update_status(session, "busy", current_task_id=str(task.task_id))
            await self.update_task_status(session, str(task.task_id), TaskStatus.IN_PROGRESS)

            # Get project context
            project = await self._get_project(session, task.project_id)

            # Get design specs if available (from designer)
            design_specs = await self._get_design_specs(session, task.project_id)

            context = {
                "project_name": project.name if project else "Unknown",
                "task_title": task.title,
                "task_description": task.description,
                "design_specs": design_specs,
            }

            # Call LLM to generate frontend code
            prompt = f"""Implement this frontend feature:

                **Task:** {task.title}
                **Description:** {task.description}

                {f"**Design Specifications:**{chr(10)}{design_specs}" if design_specs else "**Note:** No specific design specs provided. Use modern best practices."}

                Provide a complete implementation including:

                1. **Implementation Summary**: Brief overview of what you built

                2. **Components**: Complete, production-ready React/Next.js code with:
                - TypeScript interfaces for props and data
                - Proper imports (React, Next.js, Tailwind)
                - Responsive design with TailwindCSS utilities
                - State management (useState, useEffect, custom hooks)
                - API integration (fetch/axios calls)
                - Error handling and loading states
                - Accessibility features (ARIA labels, semantic HTML)

                3. **Responsive Design**: How the component adapts:
                - Mobile (<640px)
                - Tablet (640px-1024px)
                - Desktop (>1024px)

                4. **API Integration**: Details of backend API calls:
                - Endpoints used
                - Request/response formats
                - Error handling

                5. **Accessibility**: WCAG AA features:
                - Keyboard navigation
                - Screen reader support
                - Focus management

                6. **Implementation Notes**: Important details, assumptions, or next steps

                Focus on:
                - Clean, reusable component structure
                - Responsive, mobile-first design
                - Excellent user experience
                - Performance optimization
                - Accessibility compliance

                Be specific and production-ready. This is for an MVP, so balance quality with speed.
            """

            code_response = await self.call_llm_with_rag(prompt, context, max_tokens=6000, project_id=str(project.project_id) if project else str(task.project_id))

            logger.info(f"{self.name}: Code generation complete for {task.title}")

            # Structure the output for better display
            output_data = {
                "content": code_response,
                "language": "typescript",
                "framework": "react-nextjs",
                "status": "awaiting_review",
                "task_type": "frontend_implementation",
            }

            # Try to extract key sections from the response
            if "**Implementation Summary**" in code_response or "Implementation Summary:" in code_response:
                output_data["structured"] = True

            # Update task to review status
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

I've completed the frontend implementation for:
**{task.title}**

**Implementation:**
{code_response[:500]}... (see full output in task details)

The component is responsive, accessible, and follows best practices.
Please review and approve, or provide feedback for improvements.

Task ID: {task.task_id}

- Frontend Engineer
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

- Frontend Engineer
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

                # Check if it's design specs from designer
                if message.from_agent_id == "designer_001":
                    logger.info(f"{self.name}: Received design specs from Designer")

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

                        - Frontend Engineer
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
I'll make the requested changes and resubmit.

- Frontend Engineer
""",
                message_type=MessageType.INFO,
                priority=Priority.MEDIUM,
                related_task_id=message.related_task_id,
            )

    async def _get_design_specs(self, session: AsyncSession, project_id) -> str:
        """Get design specifications from designer for this project."""
        result = await session.execute(
            select(Task)
            .where(
                Task.project_id == project_id,
                Task.assigned_to_agent_id == "designer_001",
                Task.status == TaskStatus.COMPLETED,
            )
            .order_by(Task.updated_at.desc())
        )
        design_task = result.scalar_one_or_none()

        if design_task and design_task.output:
            return design_task.output.get("design_specs", "")
        return ""

    async def _get_project(self, session: AsyncSession, project_id) -> Project:
        """Get project by ID."""
        result = await session.execute(
            select(Project).where(Project.project_id == project_id)
        )
        return result.scalar_one_or_none()
