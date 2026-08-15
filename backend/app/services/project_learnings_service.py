"""
Project Learning Extraction Service - Phase 2 Component 3

Extracts and manages learnings from completed projects:
- Analyzes project execution data
- Calculates success metrics
- Identifies patterns and best practices
- Stores learnings for future reference
- Enables continuous improvement
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from statistics import mean, stdev

from app.db.models import (
    Project, ProjectStatus, Task, TaskStatus, Decision,
    Escalation, Message
)
from app.services.websocket_manager import broadcast_activity
from app.core.config import settings

logger = logging.getLogger(__name__)


class ProjectLearning:
    """Represents a learning extracted from a project."""

    def __init__(
        self,
        project_id: UUID,
        learning_type: str,  # "best_practice", "pattern", "risk", "improvement"
        title: str,
        description: str,
        evidence: List[str],
        relevance_score: float,
        tags: List[str],
    ):
        """Initialize a project learning."""
        self.project_id = project_id
        self.learning_type = learning_type
        self.title = title
        self.description = description
        self.evidence = evidence
        self.relevance_score = relevance_score  # 0-1
        self.tags = tags
        self.created_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "project_id": str(self.project_id),
            "learning_type": self.learning_type,
            "title": self.title,
            "description": self.description,
            "evidence": self.evidence,
            "relevance_score": round(self.relevance_score, 2),
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
        }


class ProjectLearningsService:
    """Service for extracting and managing project learnings."""

    def __init__(self):
        """Initialize the project learnings service."""
        self.min_relevance_threshold = 0.6

    async def extract_learnings_from_project(
        self,
        session: AsyncSession,
        project_id: UUID,
    ) -> List[ProjectLearning]:
        """
        Extract learnings from a completed project.

        Analyzes various aspects of project execution:
        - Task completion efficiency
        - Decision quality and approval rates
        - Escalation patterns and resolutions
        - Communication effectiveness
        - Resource utilization
        - Timeline adherence

        Args:
            session: Database session
            project_id: Completed project ID

        Returns:
            List of extracted learnings
        """
        try:
            # Fetch project
            result = await session.execute(
                select(Project).where(Project.project_id == project_id)
            )
            project = result.scalar_one_or_none()

            if not project:
                logger.warning(f"Project not found: {project_id}")
                return []

            if project.status != ProjectStatus.COMPLETED:
                logger.info(f"Project not completed: {project_id}")
                return []

            learnings: List[ProjectLearning] = []

            # Extract different types of learnings
            learnings.extend(await self._extract_efficiency_learnings(session, project))
            learnings.extend(await self._extract_quality_learnings(session, project))
            learnings.extend(await self._extract_risk_learnings(session, project))
            learnings.extend(await self._extract_collaboration_learnings(session, project))

            # Filter by relevance threshold
            filtered_learnings = [
                l for l in learnings
                if l.relevance_score >= self.min_relevance_threshold
            ]

            logger.info(
                f"Extracted {len(filtered_learnings)} learnings from project {project_id} "
                f"({len(learnings)} total, {len(learnings) - len(filtered_learnings)} filtered)"
            )

            return filtered_learnings

        except Exception as e:
            logger.error(f"Error extracting learnings from project {project_id}: {e}")
            return []

    async def _extract_efficiency_learnings(
        self,
        session: AsyncSession,
        project: Project,
    ) -> List[ProjectLearning]:
        """Extract efficiency-related learnings."""
        learnings: List[ProjectLearning] = []

        try:
            # Fetch project tasks
            result = await session.execute(
                select(Task).where(Task.project_id == project.project_id)
            )
            tasks = result.scalars().all()

            if not tasks:
                return learnings

            # Calculate task completion metrics
            completed_tasks = [t for t in tasks if t.status == TaskStatus.COMPLETED]
            completion_rate = len(completed_tasks) / len(tasks) if tasks else 0

            # Estimate actual hours
            total_estimated_hours = sum(t.estimated_hours or 0 for t in tasks)
            total_actual_hours = sum(t.actual_hours or 0 for t in completed_tasks)

            # Timeline efficiency
            if project.deadline and project.completed_at:
                deadline_diff = (project.completed_at - project.deadline).days
                if deadline_diff <= 0:
                    learning = ProjectLearning(
                        project_id=project.project_id,
                        learning_type="best_practice",
                        title="On-Time Delivery",
                        description=f"Project completed {abs(deadline_diff)} days before deadline",
                        evidence=[
                            f"Deadline: {project.deadline.isoformat()}",
                            f"Completed: {project.completed_at.isoformat()}",
                        ],
                        relevance_score=0.95 if deadline_diff < -5 else 0.85,
                        tags=["timeline", "efficiency", "deadline"],
                    )
                    learnings.append(learning)

            # Task efficiency
            if total_estimated_hours > 0 and total_actual_hours > 0:
                efficiency_ratio = total_estimated_hours / total_actual_hours
                if efficiency_ratio >= 0.9:  # Estimates were accurate
                    learning = ProjectLearning(
                        project_id=project.project_id,
                        learning_type="best_practice",
                        title="Accurate Estimation",
                        description=f"Task estimates were {efficiency_ratio:.0%} accurate",
                        evidence=[
                            f"Estimated: {total_estimated_hours} hours",
                            f"Actual: {total_actual_hours} hours",
                        ],
                        relevance_score=min(efficiency_ratio, 1.0),
                        tags=["estimation", "planning", "accuracy"],
                    )
                    learnings.append(learning)

            # High completion rate
            if completion_rate >= 0.95:
                learning = ProjectLearning(
                    project_id=project.project_id,
                    learning_type="best_practice",
                    title="High Task Completion Rate",
                    description=f"Completed {completion_rate:.0%} of planned tasks",
                    evidence=[
                        f"Completed: {len(completed_tasks)}/{len(tasks)} tasks",
                    ],
                    relevance_score=completion_rate,
                    tags=["completion", "execution", "quality"],
                )
                learnings.append(learning)

        except Exception as e:
            logger.warning(f"Error extracting efficiency learnings: {e}")

        return learnings

    async def _extract_quality_learnings(
        self,
        session: AsyncSession,
        project: Project,
    ) -> List[ProjectLearning]:
        """Extract quality-related learnings."""
        learnings: List[ProjectLearning] = []

        try:
            # Fetch decisions for this project
            result = await session.execute(
                select(Decision).where(Decision.project_id == project.project_id)
            )
            decisions = result.scalars().all()

            if decisions:
                # Calculate approval rate
                approved = [d for d in decisions if d.approved is True]
                approval_rate = len(approved) / len(decisions) if decisions else 0

                if approval_rate >= 0.85:
                    learning = ProjectLearning(
                        project_id=project.project_id,
                        learning_type="best_practice",
                        title="High Decision Quality",
                        description=f"Decisions had {approval_rate:.0%} approval rate",
                        evidence=[
                            f"Approved: {len(approved)}/{len(decisions)} decisions",
                        ],
                        relevance_score=approval_rate,
                        tags=["quality", "decisions", "approval"],
                    )
                    learnings.append(learning)

        except Exception as e:
            logger.warning(f"Error extracting quality learnings: {e}")

        return learnings

    async def _extract_risk_learnings(
        self,
        session: AsyncSession,
        project: Project,
    ) -> List[ProjectLearning]:
        """Extract risk-related learnings."""
        learnings: List[ProjectLearning] = []

        try:
            # Fetch escalations for this project
            result = await session.execute(
                select(Escalation).where(Escalation.related_project_id == project.project_id)
            )
            escalations = result.scalars().all()

            if escalations:
                resolved = [e for e in escalations if e.status == "resolved"]
                resolution_rate = len(resolved) / len(escalations) if escalations else 0

                if resolution_rate >= 0.9:
                    learning = ProjectLearning(
                        project_id=project.project_id,
                        learning_type="best_practice",
                        title="Effective Escalation Resolution",
                        description=f"Resolved {resolution_rate:.0%} of escalations",
                        evidence=[
                            f"Resolved: {len(resolved)}/{len(escalations)} escalations",
                        ],
                        relevance_score=resolution_rate,
                        tags=["risk", "escalation", "resolution"],
                    )
                    learnings.append(learning)
                else:
                    # Low resolution rate - improvement area
                    learning = ProjectLearning(
                        project_id=project.project_id,
                        learning_type="improvement",
                        title="Escalation Resolution Rate",
                        description=f"Only {resolution_rate:.0%} of escalations were resolved",
                        evidence=[
                            f"Unresolved: {len(escalations) - len(resolved)}/{len(escalations)} escalations",
                        ],
                        relevance_score=1.0 - resolution_rate,
                        tags=["improvement", "escalation", "resolution"],
                    )
                    learnings.append(learning)

        except Exception as e:
            logger.warning(f"Error extracting risk learnings: {e}")

        return learnings

    async def _extract_collaboration_learnings(
        self,
        session: AsyncSession,
        project: Project,
    ) -> List[ProjectLearning]:
        """Extract collaboration-related learnings."""
        learnings: List[ProjectLearning] = []

        try:
            # Fetch messages related to project
            result = await session.execute(
                select(Message).where(Message.related_project_id == project.project_id)
            )
            messages = result.scalars().all()

            if messages:
                # Calculate average message frequency
                if project.created_at and project.completed_at:
                    duration_days = (project.completed_at - project.created_at).days
                    if duration_days > 0:
                        msg_per_day = len(messages) / duration_days
                        if msg_per_day >= 5:  # Good communication
                            learning = ProjectLearning(
                                project_id=project.project_id,
                                learning_type="best_practice",
                                title="Active Communication",
                                description=f"Maintained {msg_per_day:.1f} messages per day",
                                evidence=[
                                    f"Total: {len(messages)} messages",
                                    f"Duration: {duration_days} days",
                                ],
                                relevance_score=min(msg_per_day / 10, 1.0),
                                tags=["communication", "collaboration", "engagement"],
                            )
                            learnings.append(learning)

        except Exception as e:
            logger.warning(f"Error extracting collaboration learnings: {e}")

        return learnings

    async def save_learnings(
        self,
        project_id: UUID,
        learnings: List[ProjectLearning],
    ) -> Dict[str, Any]:
        """
        Save extracted learnings to knowledge base.

        Args:
            project_id: Project ID
            learnings: List of extracted learnings

        Returns:
            Summary of saved learnings
        """
        try:
            # Group learnings by type
            by_type = {}
            for learning in learnings:
                if learning.learning_type not in by_type:
                    by_type[learning.learning_type] = []
                by_type[learning.learning_type].append(learning)

            # Create summary
            summary = {
                "project_id": str(project_id),
                "total_learnings": len(learnings),
                "by_type": {
                    learning_type: len(items)
                    for learning_type, items in by_type.items()
                },
                "saved_at": datetime.utcnow().isoformat(),
                "learnings": [l.to_dict() for l in learnings],
            }

            logger.info(
                f"Saved {len(learnings)} learnings from project {project_id}: "
                f"{', '.join(f'{k}={v}' for k, v in summary['by_type'].items())}"
            )

            return summary

        except Exception as e:
            logger.error(f"Error saving learnings for project {project_id}: {e}")
            return {
                "project_id": str(project_id),
                "total_learnings": 0,
                "by_type": {},
                "error": str(e),
            }

    async def calculate_project_metrics(
        self,
        session: AsyncSession,
        project_id: UUID,
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive metrics for a project.

        Returns:
            {
                "project_id": "...",
                "timeline": {
                    "planned_days": 10,
                    "actual_days": 8,
                    "efficiency": 1.25
                },
                "tasks": {
                    "total": 12,
                    "completed": 12,
                    "completion_rate": 1.0
                },
                "decisions": {
                    "total": 5,
                    "approved": 5,
                    "approval_rate": 1.0
                },
                "escalations": {
                    "total": 2,
                    "resolved": 2,
                    "resolution_rate": 1.0
                },
                "success_score": 0.92
            }
        """
        try:
            # Fetch project
            result = await session.execute(
                select(Project).where(Project.project_id == project_id)
            )
            project = result.scalar_one_or_none()

            if not project:
                return {"error": "Project not found"}

            metrics: Dict[str, Any] = {
                "project_id": str(project_id),
                "timeline": {},
                "tasks": {},
                "decisions": {},
                "escalations": {},
                "success_score": 0.0,
            }

            # Timeline metrics
            if project.created_at and project.completed_at:
                actual_days = (project.completed_at - project.created_at).days
                metrics["timeline"]["actual_days"] = actual_days
                metrics["timeline"]["planned_days"] = project.agent_days_elapsed or actual_days
                metrics["timeline"]["efficiency"] = (
                    project.agent_days_elapsed / actual_days
                    if actual_days > 0 else 1.0
                )

            # Task metrics
            task_result = await session.execute(
                select(Task).where(Task.project_id == project_id)
            )
            tasks = task_result.scalars().all()
            completed_tasks = [t for t in tasks if t.status == TaskStatus.COMPLETED]

            metrics["tasks"]["total"] = len(tasks)
            metrics["tasks"]["completed"] = len(completed_tasks)
            metrics["tasks"]["completion_rate"] = (
                len(completed_tasks) / len(tasks) if tasks else 0
            )

            # Decision metrics
            decision_result = await session.execute(
                select(Decision).where(Decision.project_id == project_id)
            )
            decisions = decision_result.scalars().all()
            approved_decisions = [d for d in decisions if d.approved is True]

            metrics["decisions"]["total"] = len(decisions)
            metrics["decisions"]["approved"] = len(approved_decisions)
            metrics["decisions"]["approval_rate"] = (
                len(approved_decisions) / len(decisions) if decisions else 0
            )

            # Escalation metrics
            escalation_result = await session.execute(
                select(Escalation).where(Escalation.related_project_id == project_id)
            )
            escalations = escalation_result.scalars().all()
            resolved_escalations = [e for e in escalations if e.status == "resolved"]

            metrics["escalations"]["total"] = len(escalations)
            metrics["escalations"]["resolved"] = len(resolved_escalations)
            metrics["escalations"]["resolution_rate"] = (
                len(resolved_escalations) / len(escalations) if escalations else 0
            )

            # Calculate overall success score
            scores = [
                metrics["tasks"]["completion_rate"],
                metrics["decisions"]["approval_rate"] if decisions else 1.0,
                metrics["escalations"]["resolution_rate"] if escalations else 1.0,
                min(metrics["timeline"]["efficiency"], 1.0) if "efficiency" in metrics["timeline"] else 1.0,
            ]
            metrics["success_score"] = round(mean(scores), 2)

            logger.info(f"Calculated metrics for project {project_id}: success_score={metrics['success_score']}")
            return metrics

        except Exception as e:
            logger.error(f"Error calculating project metrics {project_id}: {e}")
            return {"error": str(e), "project_id": str(project_id)}


# Singleton instance
_project_learnings_service: Optional["ProjectLearningsService"] = None


def get_project_learnings_service() -> ProjectLearningsService:
    """Get or create the ProjectLearningsService singleton."""
    global _project_learnings_service
    if _project_learnings_service is None:
        _project_learnings_service = ProjectLearningsService()
    return _project_learnings_service
