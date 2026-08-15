"""Service to analyze project content availability for intelligent export options."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from typing import Dict, List, Any
import logging

from app.db.models import Task, Message, Project, Agent

logger = logging.getLogger(__name__)


class ExportContentAnalyzer:
    """Analyze project content to determine which export types are relevant."""

    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self.session = session

    async def analyze_project_content(self, project_id: UUID) -> Dict[str, Any]:
        """
        Analyze project content and determine available export options.

        Args:
            project_id: Project to analyze

        Returns:
            Dictionary with:
            - available_export_types: List of recommended export types
            - content_flags: Boolean flags indicating what content exists
            - recommendations: Human-readable recommendations
        """
        try:
            # Check if project exists
            project = await self._get_project(project_id)
            if not project:
                return self._empty_analysis()

            # Analyze each content type
            has_tasks = await self._has_tasks(project_id)
            has_completed_tasks = await self._has_completed_tasks(project_id)
            has_code_files = await self._has_code_files(project_id)
            has_images = await self._has_images(project_id)
            has_conversations = await self._has_conversations(project_id)
            has_agent_activity = await self._has_agent_activity(project_id)
            has_documentation = await self._has_documentation(project_id)

            # Build content flags
            content_flags = {
                "has_tasks": has_tasks,
                "has_completed_tasks": has_completed_tasks,
                "has_code_files": has_code_files,
                "has_images": has_images,
                "has_conversations": has_conversations,
                "has_agent_activity": has_agent_activity,
                "has_documentation": has_documentation,
            }

            # Determine available export types based on content
            available_types = self._determine_available_export_types(content_flags)

            # Generate recommendations
            recommendations = self._generate_recommendations(content_flags)

            return {
                "available_export_types": available_types,
                "content_flags": content_flags,
                "recommendations": recommendations,
            }

        except Exception as e:
            logger.error(f"Error analyzing project content: {e}")
            return self._empty_analysis()

    def _determine_available_export_types(self, content_flags: Dict[str, bool]) -> List[str]:
        """
        Determine which export types are relevant based on content.

        Rules:
        - project_summary: Always available (minimum viable export)
        - full_documentation: Only if has_documentation OR has_tasks OR has_code_files
        - task_report: Only if has_tasks
        - agent_activity_report: Only if has_agent_activity
        - code_documentation: Only if has_code_files
        - analytics_metrics: Only if has_tasks OR has_completed_tasks
        """
        available = ["project_summary"]  # Always available

        if (
            content_flags["has_documentation"]
            or content_flags["has_tasks"]
            or content_flags["has_code_files"]
        ):
            available.append("full_documentation")

        if content_flags["has_tasks"]:
            available.append("task_report")

        if content_flags["has_agent_activity"]:
            available.append("agent_activity_report")

        if content_flags["has_code_files"]:
            available.append("code_documentation")

        if content_flags["has_tasks"] or content_flags["has_completed_tasks"]:
            available.append("analytics_metrics")

        return available

    def _generate_recommendations(self, content_flags: Dict[str, bool]) -> Dict[str, str]:
        """Generate human-readable recommendations for unavailable options."""
        recommendations = {}

        # Recommendations for disabled options
        if not content_flags["has_code_files"]:
            recommendations["code_documentation"] = (
                "No code files found in this project. Code documentation will be empty."
            )

        if not content_flags["has_tasks"]:
            recommendations["task_report"] = (
                "No tasks found in this project. Task report will be empty."
            )
            recommendations["analytics_metrics"] = (
                "No tasks found in this project. Analytics will be unavailable."
            )

        if not content_flags["has_agent_activity"]:
            recommendations["agent_activity_report"] = (
                "No agent activity recorded for this project. Activity report will be empty."
            )

        if (
            not content_flags["has_documentation"]
            and not content_flags["has_tasks"]
            and not content_flags["has_code_files"]
        ):
            recommendations["full_documentation"] = (
                "Insufficient content for full documentation. Use project summary instead."
            )

        # Recommendations for enabled options
        if content_flags["has_tasks"] and content_flags["has_agent_activity"]:
            recommendations["_recommended"] = ["task_report", "analytics_metrics"]

        return recommendations

    async def _get_project(self, project_id: UUID) -> Any:
        """Get project by ID."""
        query = select(Project).where(Project.project_id == project_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def _has_tasks(self, project_id: UUID) -> bool:
        """Check if project has any tasks."""
        query = select(func.count(Task.task_id)).where(
            Task.project_id == project_id, Task.deleted_at.is_(None)
        )
        result = await self.session.execute(query)
        count = result.scalar() or 0
        return count > 0

    async def _has_completed_tasks(self, project_id: UUID) -> bool:
        """Check if project has any completed tasks."""
        from app.db.models import TaskStatus

        query = select(func.count(Task.task_id)).where(
            Task.project_id == project_id,
            Task.status == TaskStatus.COMPLETED,
            Task.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        count = result.scalar() or 0
        return count > 0

    async def _has_code_files(self, project_id: UUID) -> bool:
        """
        Check if project has code files.

        This checks for task outputs that contain code-related content
        or tasks with code-related descriptions.
        """
        query = select(func.count(Task.task_id)).where(
            Task.project_id == project_id,
            Task.deleted_at.is_(None),
            # Check for code-related keywords in description or output
            (
                Task.description.ilike("%code%")
                | Task.description.ilike("%file%")
                | Task.description.ilike("%script%")
                | Task.output.isnot(None)
            ),
        )
        result = await self.session.execute(query)
        count = result.scalar() or 0
        return count > 0

    async def _has_images(self, project_id: UUID) -> bool:
        """
        Check if project has images.

        This checks for task outputs that contain image-related content.
        """
        query = select(func.count(Task.task_id)).where(
            Task.project_id == project_id,
            Task.deleted_at.is_(None),
            Task.output.isnot(None),
        )
        result = await self.session.execute(query)
        count = result.scalar() or 0
        return count > 0

    async def _has_conversations(self, project_id: UUID) -> bool:
        """Check if project has messages/conversations."""
        query = select(func.count(Message.message_id)).where(
            Message.related_project_id == project_id
        )
        result = await self.session.execute(query)
        count = result.scalar() or 0
        return count > 0

    async def _has_agent_activity(self, project_id: UUID) -> bool:
        """
        Check if project has agent activity.

        This checks for:
        - Tasks assigned to agents
        - Messages related to project
        - Agents who have worked on tasks
        """
        query = select(func.count(Task.task_id)).where(
            Task.project_id == project_id,
            Task.assigned_to_agent_id.isnot(None),
            Task.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        task_count = result.scalar() or 0
        return task_count > 0

    async def _has_documentation(self, project_id: UUID) -> bool:
        """
        Check if project has documentation.

        This checks for:
        - Project description
        - Task descriptions
        - Knowledge base entries
        """
        project = await self._get_project(project_id)
        if project and project.description:
            return True

        query = select(func.count(Task.task_id)).where(
            Task.project_id == project_id,
            Task.description.isnot(None),
            Task.description != "",
            Task.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        count = result.scalar() or 0
        return count > 0

    def _empty_analysis(self) -> Dict[str, Any]:
        """Return empty analysis for non-existent projects."""
        return {
            "available_export_types": ["project_summary"],
            "content_flags": {
                "has_tasks": False,
                "has_completed_tasks": False,
                "has_code_files": False,
                "has_images": False,
                "has_conversations": False,
                "has_agent_activity": False,
                "has_documentation": False,
            },
            "recommendations": {
                "note": "Project not found or has no content yet. Only project summary available."
            },
        }
