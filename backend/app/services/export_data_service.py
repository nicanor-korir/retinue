"""Service for collecting data needed for exports."""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.db.models import (
    Project, Task, Agent, Message, Decision, Escalation,
    AuditLog, KnowledgeBase, TaskStatus, ProjectStatus,
    MessageType, Priority
)
from app.db.event_models import (
    AgentActivity, AgentMetric, LLMInteraction, ContentGeneration,
    EventTimeline
)
from app.db.escalation_models import AdvancedEscalation, EscalationAnalytics


class ExportDataService:
    """Collects and transforms data for various export types."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def collect_project_summary(self, project_id: UUID) -> Dict[str, Any]:
        """Collect data for project summary export."""
        project = await self._fetch_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        try:
            return {
                "project": await self._serialize_project(project),
                "overview": await self._safely_get(self._get_project_overview(project_id), {}),
                "agent_involvement": await self._safely_get(self._get_agent_involvement(project_id), []),
                "timeline": await self._safely_get(self._get_project_timeline(project_id), []),
                "key_metrics": await self._safely_get(self._get_project_metrics(project_id), {}),
                "status_summary": await self._safely_get(self._get_status_summary(project_id), ""),
                "next_steps": await self._safely_get(self._get_next_steps(project_id), []),
            }
        except Exception as e:
            import logging
            logging.error(f"Error collecting project summary: {e}", exc_info=True)
            # Return minimal data even if collection fails
            return {
                "project": await self._serialize_project(project),
                "overview": {},
                "agent_involvement": [],
                "timeline": [],
                "key_metrics": {"total_tasks": 0},
                "status_summary": project.status.value,
                "next_steps": [],
            }

    async def collect_full_documentation(self, project_id: UUID) -> Dict[str, Any]:
        """Collect comprehensive data for full documentation export."""
        project = await self._fetch_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        try:
            return {
                **await self.collect_project_summary(project_id),
                "tasks": await self._safely_get(self._get_all_tasks(project_id), []),
                "agent_conversations": await self._safely_get(self._get_agent_conversations(project_id), []),
                "decisions": await self._safely_get(self._get_decisions(project_id), []),
                "code_documentation": await self._safely_get(self._get_code_documentation(project_id), []),
                "design_assets": await self._safely_get(self._get_design_assets(project_id), []),
                "technical_specs": await self._safely_get(self._get_technical_specifications(project_id), {}),
                "escalations": await self._safely_get(self._get_escalations(project_id), []),
                "testing_reports": await self._safely_get(self._get_testing_reports(project_id), {}),
                "deployment_info": await self._safely_get(self._get_deployment_instructions(project_id), {}),
            }
        except Exception as e:
            import logging
            logging.error(f"Error collecting full documentation: {e}", exc_info=True)
            # Return project summary at minimum
            return await self.collect_project_summary(project_id)

    async def collect_task_report(self, project_id: UUID, date_range: Optional[Dict[str, datetime]] = None) -> Dict[str, Any]:
        """Collect task-focused data for task report export."""
        try:
            return {
                "project": await self._fetch_project(project_id),
                "tasks": await self._safely_get(self._get_all_tasks(project_id, date_range), []),
                "task_timeline": await self._safely_get(self._get_task_timeline(project_id), []),
                "dependencies": await self._safely_get(self._get_task_dependencies(project_id), []),
                "completion_metrics": await self._safely_get(self._get_task_completion_metrics(project_id), {}),
                "blockers": await self._safely_get(self._get_task_blockers(project_id), []),
                "escalations": await self._safely_get(self._get_task_escalations(project_id), []),
            }
        except Exception as e:
            import logging
            logging.error(f"Error collecting task report: {e}", exc_info=True)
            return {"project": await self._fetch_project(project_id), "tasks": []}

    async def collect_agent_activity_report(self, project_id: UUID, date_range: Optional[Dict[str, datetime]] = None) -> Dict[str, Any]:
        """Collect agent-focused data for activity report export."""
        try:
            return {
                "project": await self._fetch_project(project_id),
                "agent_metrics": await self._safely_get(self._get_agent_metrics(project_id, date_range), []),
                "llm_usage": await self._safely_get(self._get_llm_usage(project_id, date_range), {}),
                "agent_timeline": await self._safely_get(self._get_agent_activity_timeline(project_id, date_range), []),
                "message_statistics": await self._safely_get(self._get_message_statistics(project_id), {}),
                "task_breakdown": await self._safely_get(self._get_task_breakdown_by_agent(project_id), {}),
                "collaboration_patterns": await self._safely_get(self._get_collaboration_patterns(project_id), {}),
                "performance_metrics": await self._safely_get(self._get_performance_metrics(project_id), {}),
            }
        except Exception as e:
            import logging
            logging.error(f"Error collecting agent activity report: {e}", exc_info=True)
            return {"project": await self._fetch_project(project_id), "agent_metrics": []}

    async def collect_code_documentation(self, project_id: UUID) -> Dict[str, Any]:
        """Collect code-focused data for code documentation export."""
        try:
            return {
                "project": await self._fetch_project(project_id),
                "project_structure": await self._safely_get(self._get_project_structure(project_id), {}),
                "code_files": await self._safely_get(self._get_code_files(project_id), []),
                "api_documentation": await self._safely_get(self._get_api_documentation(project_id), {}),
                "database_schema": await self._safely_get(self._get_database_schema(project_id), {}),
                "configuration": await self._safely_get(self._get_configuration(project_id), {}),
                "dependencies": await self._safely_get(self._get_dependencies(project_id), []),
                "setup_instructions": await self._safely_get(self._get_setup_instructions(project_id), ""),
            }
        except Exception as e:
            import logging
            logging.error(f"Error collecting code documentation: {e}", exc_info=True)
            return {"project": await self._fetch_project(project_id)}

    async def collect_analytics_metrics(self, project_id: UUID, date_range: Optional[Dict[str, datetime]] = None) -> Dict[str, Any]:
        """Collect analytics and metrics data."""
        try:
            return {
                "project": await self._fetch_project(project_id),
                "timeline_visualization": await self._safely_get(self._get_timeline_visualization(project_id), []),
                "velocity_metrics": await self._safely_get(self._get_velocity_metrics(project_id, date_range), {}),
                "budget_tracking": await self._safely_get(self._get_budget_tracking(project_id), {}),
                "agent_utilization": await self._safely_get(self._get_agent_utilization(project_id), {}),
                "task_completion_trends": await self._safely_get(self._get_task_completion_trends(project_id), []),
                "escalation_metrics": await self._safely_get(self._get_escalation_metrics(project_id), {}),
                "quality_metrics": await self._safely_get(self._get_quality_metrics(project_id), {}),
            }
        except Exception as e:
            import logging
            logging.error(f"Error collecting analytics metrics: {e}", exc_info=True)
            return {"project": await self._fetch_project(project_id)}

    # ==================== Helper Methods ====================

    async def _safely_get(self, coro, default: Any = None) -> Any:
        """Safely execute an async operation with fallback.

        Args:
            coro: Async coroutine to execute
            default: Default value if operation fails

        Returns:
            Result of coroutine or default value on error
        """
        try:
            return await coro
        except Exception as e:
            import logging
            logging.warning(f"Error in data collection: {e}", exc_info=False)
            return default if default is not None else {}

    async def _fetch_project(self, project_id: UUID) -> Optional[Dict[str, Any]]:
        """Fetch project by ID."""
        query = select(Project).where(Project.project_id == project_id)
        result = await self.session.execute(query)
        project = result.scalars().first()
        return project

    async def _serialize_project(self, project) -> Dict[str, Any]:
        """Serialize project to dictionary."""
        return {
            "id": str(project.project_id),
            "name": project.name,
            "description": project.description,
            "status": project.status.value,
            "priority": project.priority.value,
            "owner_id": project.owner_agent_id,
            "requester_id": project.requester_agent_id,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None,
            "completed_at": project.completed_at.isoformat() if project.completed_at else None,
            "deadline": project.deadline.isoformat() if project.deadline else None,
            "metadata": project.meta_data or {},
        }

    async def _get_project_overview(self, project_id: UUID) -> Dict[str, Any]:
        """Get high-level project overview."""
        project = await self._fetch_project(project_id)
        if not project:
            return {}

        # Task statistics - simplified to avoid casting issues
        try:
            query = select(
                func.count(Task.task_id),
                func.coalesce(func.sum(Task.estimated_hours), 0)
            ).where(Task.project_id == project_id)
            result = await self.session.execute(query)
            total_tasks, estimated_hours = result.first()
        except Exception as e:
            import logging
            logging.warning(f"Error getting task statistics: {e}")
            total_tasks, estimated_hours = 0, 0

        return {
            "title": project.name,
            "description": project.description,
            "status": project.status.value,
            "total_tasks": total_tasks or 0,
            "estimated_hours": estimated_hours or 0,
            "started_date": project.created_at,
            "deadline": project.deadline,
            "completed_date": project.completed_at,
        }

    async def _get_agent_involvement(self, project_id: UUID) -> List[Dict[str, Any]]:
        """Get list of agents involved in the project."""
        query = select(Task.assigned_to_agent_id).distinct().where(Task.project_id == project_id)
        result = await self.session.execute(query)
        agent_ids = result.scalars().all()

        involvement = []
        for agent_id in agent_ids:
            agent = await self.session.get(Agent, agent_id)
            if agent:
                task_count = await self.session.execute(
                    select(func.count(Task.task_id)).where(
                        and_(Task.project_id == project_id, Task.assigned_to_agent_id == agent_id)
                    )
                )
                count = task_count.scalar()
                involvement.append({
                    "agent_id": agent_id,
                    "agent_name": agent.name,
                    "role": agent.role,
                    "tasks_assigned": count,
                })

        return involvement

    async def _get_project_timeline(self, project_id: UUID) -> List[Dict[str, Any]]:
        """Get project timeline of events."""
        query = select(EventTimeline).where(
            EventTimeline.project_id == project_id
        ).order_by(EventTimeline.event_timestamp)

        result = await self.session.execute(query)
        events = result.scalars().all()

        return [
            {
                "timestamp": event.event_timestamp,
                "title": event.title,
                "description": event.description,
                "agent_id": event.agent_id,
                "is_highlight": event.is_highlight,
            }
            for event in events
        ]

    async def _get_project_metrics(self, project_id: UUID) -> Dict[str, Any]:
        """Get key project metrics."""
        # Task completion
        completed = await self.session.execute(
            select(func.count(Task.task_id)).where(
                and_(Task.project_id == project_id, Task.status == TaskStatus.COMPLETED)
            )
        )
        completed_count = completed.scalar() or 0

        in_progress = await self.session.execute(
            select(func.count(Task.task_id)).where(
                and_(Task.project_id == project_id, Task.status == TaskStatus.IN_PROGRESS)
            )
        )
        in_progress_count = in_progress.scalar() or 0

        blocked = await self.session.execute(
            select(func.count(Task.task_id)).where(
                and_(Task.project_id == project_id, Task.status == TaskStatus.BLOCKED)
            )
        )
        blocked_count = blocked.scalar() or 0

        total = completed_count + in_progress_count + blocked_count

        return {
            "total_tasks": total,
            "completed_tasks": completed_count,
            "in_progress_tasks": in_progress_count,
            "blocked_tasks": blocked_count,
            "completion_percentage": (completed_count / total * 100) if total > 0 else 0,
        }

    async def _get_status_summary(self, project_id: UUID) -> str:
        """Get current status summary."""
        project = await self._fetch_project(project_id)
        if not project:
            return ""

        metrics = await self._get_project_metrics(project_id)
        status = project.status.value
        return f"Project is {status.lower()} with {metrics['completion_percentage']:.1f}% task completion"

    async def _get_next_steps(self, project_id: UUID) -> List[str]:
        """Get recommended next steps."""
        # Get pending tasks
        query = select(Task).where(
            and_(Task.project_id == project_id, Task.status == TaskStatus.PENDING)
        ).limit(5)
        result = await self.session.execute(query)
        pending_tasks = result.scalars().all()

        return [f"Start: {task.title}" for task in pending_tasks]

    async def _get_all_tasks(self, project_id: UUID, date_range: Optional[Dict[str, datetime]] = None) -> List[Dict[str, Any]]:
        """Get all tasks for the project with optional date filtering."""
        query = select(Task).where(Task.project_id == project_id)

        if date_range:
            if 'start' in date_range:
                query = query.where(Task.created_at >= date_range['start'])
            if 'end' in date_range:
                query = query.where(Task.created_at <= date_range['end'])

        query = query.order_by(Task.created_at)
        result = await self.session.execute(query)
        tasks = result.scalars().all()

        return [
            {
                "id": str(task.task_id),
                "title": task.title,
                "description": task.description,
                "status": task.status.value,
                "assigned_to": task.assigned_to_agent_id,
                "estimated_hours": task.estimated_hours,
                "actual_hours": task.actual_hours,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "updated_at": task.updated_at.isoformat() if task.updated_at else None,
                "dependencies": task.dependencies or [],
                "output": task.output or {},
            }
            for task in tasks
        ]

    async def _get_agent_conversations(self, project_id: UUID) -> List[Dict[str, Any]]:
        """Get agent conversations related to the project."""
        query = select(Message).where(
            Message.related_project_id == project_id
        ).order_by(Message.timestamp)

        result = await self.session.execute(query)
        messages = result.scalars().all()

        return [
            {
                "from_agent": message.from_agent_id,
                "to_agent": message.to_agent_id,
                "type": message.message_type.value if message.message_type else None,
                "content": message.content,
                "priority": message.priority.value,
                "timestamp": message.timestamp.isoformat() if message.timestamp else None,
            }
            for message in messages
        ]

    async def _get_decisions(self, project_id: UUID) -> List[Dict[str, Any]]:
        """Get decisions made during the project."""
        query = select(Decision).where(
            Decision.project_id == project_id
        ).order_by(Decision.timestamp)

        result = await self.session.execute(query)
        decisions = result.scalars().all()

        return [
            {
                "type": decision.decision_type,
                "category": decision.decision_category,
                "question": decision.question,
                "rationale": decision.rationale,
                "decision": decision.decision,
                "made_by": decision.made_by_agent_id,
                "approved": decision.approved,
                "timestamp": decision.timestamp.isoformat() if decision.timestamp else None,
            }
            for decision in decisions
        ]

    async def _get_code_documentation(self, project_id: UUID) -> List[Dict[str, Any]]:
        """Get code files and documentation."""
        # Get code from ContentGeneration or Tasks
        query = select(ContentGeneration).where(
            and_(
                ContentGeneration.project_id == project_id,
                ContentGeneration.content_type.in_(['code', 'document'])
            )
        )

        result = await self.session.execute(query)
        content = result.scalars().all()

        return [
            {
                "type": item.content_type,
                "title": f"Generated {item.content_type}",
                "content": item.content[:500] if item.content else "",  # Truncate for summary
                "language": "python" if item.content_type == "code" else "markdown",
                "tokens_generated": item.tokens_generated or 0,
            }
            for item in content
        ]

    async def _get_design_assets(self, project_id: UUID) -> List[Dict[str, Any]]:
        """Get design assets related to the project."""
        # Design assets from KnowledgeBase marked as design
        query = select(KnowledgeBase).where(
            and_(KnowledgeBase.category == "design")
        )

        result = await self.session.execute(query)
        assets = result.scalars().all()

        return [
            {
                "title": asset.title,
                "category": asset.category,
                "content": asset.content[:200],
                "created_at": asset.created_at.isoformat() if asset.created_at else None,
            }
            for asset in assets[:10]  # Limit to 10 most recent
        ]

    async def _get_technical_specifications(self, project_id: UUID) -> Dict[str, Any]:
        """Get technical specifications."""
        project = await self._fetch_project(project_id)
        if not project:
            return {}

        return {
            "framework": project.meta_data.get("framework", "Not specified") if project.meta_data else "Not specified",
            "database": project.meta_data.get("database", "PostgreSQL") if project.meta_data else "PostgreSQL",
            "architecture": project.meta_data.get("architecture", "Not specified") if project.meta_data else "Not specified",
            "key_technologies": project.meta_data.get("technologies", []) if project.meta_data else [],
        }

    async def _get_escalations(self, project_id: UUID) -> List[Dict[str, Any]]:
        """Get escalations in the project."""
        query = select(AdvancedEscalation).where(
            AdvancedEscalation.related_project_id == project_id
        )

        result = await self.session.execute(query)
        escalations = result.scalars().all()

        return [
            {
                "id": str(escalation.id),
                "type": escalation.escalation_type,
                "priority": escalation.priority.value if escalation.priority else None,
                "status": escalation.status,
                "created_at": escalation.created_at.isoformat() if escalation.created_at else None,
                "resolved_at": escalation.resolved_at.isoformat() if escalation.resolved_at else None,
            }
            for escalation in escalations
        ]

    async def _get_testing_reports(self, project_id: UUID) -> Dict[str, Any]:
        """Get testing information."""
        # Get test-related tasks
        query = select(Task).where(
            and_(Task.project_id == project_id, Task.title.ilike("%test%"))
        )

        result = await self.session.execute(query)
        test_tasks = result.scalars().all()

        return {
            "test_count": len(test_tasks),
            "tests": [
                {
                    "title": task.title,
                    "status": task.status.value,
                    "assigned_to": task.assigned_to_agent_id,
                }
                for task in test_tasks
            ]
        }

    async def _get_deployment_instructions(self, project_id: UUID) -> Dict[str, Any]:
        """Get deployment instructions."""
        project = await self._fetch_project(project_id)
        if not project:
            return {}

        return {
            "instructions": "See deployment guide section",
            "platforms": ["Vercel", "Netlify"],
            "environment_variables": project.meta_data.get("env_vars", {}) if project.meta_data else {},
        }

    async def _get_task_timeline(self, project_id: UUID) -> List[Dict[str, Any]]:
        """Get task timeline for Gantt chart."""
        tasks = await self._get_all_tasks(project_id)
        return tasks

    async def _get_task_dependencies(self, project_id: UUID) -> List[Dict[str, Any]]:
        """Get task dependency graph."""
        query = select(Task).where(Task.project_id == project_id)
        result = await self.session.execute(query)
        tasks = result.scalars().all()

        return [
            {
                "task_id": str(task.task_id),
                "task_title": task.title,
                "dependencies": task.dependencies or [],
            }
            for task in tasks if task.dependencies
        ]

    async def _get_task_completion_metrics(self, project_id: UUID) -> Dict[str, Any]:
        """Get task completion metrics."""
        return await self._get_project_metrics(project_id)

    async def _get_task_blockers(self, project_id: UUID) -> List[Dict[str, Any]]:
        """Get blocked tasks."""
        query = select(Task).where(
            and_(Task.project_id == project_id, Task.status == TaskStatus.BLOCKED)
        )

        result = await self.session.execute(query)
        blocked_tasks = result.scalars().all()

        return [
            {
                "task_id": str(task.task_id),
                "task_title": task.title,
                "blocking_reason": task.blocking_reason,
                "blocked_at": task.updated_at.isoformat() if task.updated_at else None,
            }
            for task in blocked_tasks
        ]

    async def _get_task_escalations(self, project_id: UUID) -> List[Dict[str, Any]]:
        """Get escalations related to tasks."""
        return await self._get_escalations(project_id)

    async def _get_agent_metrics(self, project_id: UUID, date_range: Optional[Dict[str, datetime]] = None) -> List[Dict[str, Any]]:
        """Get agent performance metrics."""
        query = select(AgentMetric).where(AgentMetric.project_id == project_id)

        if date_range:
            if 'start' in date_range:
                query = query.where(AgentMetric.metric_date >= date_range['start'].date())
            if 'end' in date_range:
                query = query.where(AgentMetric.metric_date <= date_range['end'].date())

        result = await self.session.execute(query)
        metrics = result.scalars().all()

        return [
            {
                "agent_id": metric.agent_id,
                "tasks_completed": metric.tasks_completed or 0,
                "success_rate": metric.success_rate or 0,
                "active_time_minutes": metric.active_time_minutes or 0,
                "idle_time_minutes": metric.idle_time_minutes or 0,
                "total_tokens": metric.total_tokens or 0,
                "total_cost": metric.total_cost or 0,
                "metric_date": metric.metric_date.isoformat() if metric.metric_date else None,
            }
            for metric in metrics
        ]

    async def _get_llm_usage(self, project_id: UUID, date_range: Optional[Dict[str, datetime]] = None) -> Dict[str, Any]:
        """Get LLM API usage statistics."""
        query = select(LLMInteraction).where(
            LLMInteraction.project_id == project_id
        ) if hasattr(LLMInteraction, 'project_id') else select(LLMInteraction)

        result = await self.session.execute(query)
        interactions = result.scalars().all()

        total_tokens = sum(interaction.total_tokens or 0 for interaction in interactions)
        total_cost = sum(interaction.cost or 0 for interaction in interactions)

        return {
            "total_calls": len(interactions),
            "total_prompt_tokens": sum(interaction.prompt_tokens or 0 for interaction in interactions),
            "total_completion_tokens": sum(interaction.completion_tokens or 0 for interaction in interactions),
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "models_used": list(set(interaction.model for interaction in interactions)),
        }

    async def _get_agent_activity_timeline(self, project_id: UUID, date_range: Optional[Dict[str, datetime]] = None) -> List[Dict[str, Any]]:
        """Get agent activity timeline."""
        query = select(AgentActivity).where(
            AgentActivity.project_id == project_id
        ).order_by(AgentActivity.started_at.desc())

        if date_range:
            if 'start' in date_range:
                query = query.where(AgentActivity.started_at >= date_range['start'])
            if 'end' in date_range:
                query = query.where(AgentActivity.started_at <= date_range['end'])

        result = await self.session.execute(query)
        activities = result.scalars().all()

        return [
            {
                "agent_id": activity.agent_id,
                "activity_type": activity.activity_type,
                "progress": activity.progress_percentage or 0,
                "started_at": activity.started_at.isoformat() if activity.started_at else None,
                "completed_at": activity.completed_at.isoformat() if activity.completed_at else None,
            }
            for activity in activities[:100]  # Limit to recent 100
        ]

    async def _get_message_statistics(self, project_id: UUID) -> Dict[str, Any]:
        """Get message statistics."""
        query = select(Message).where(Message.related_project_id == project_id)
        result = await self.session.execute(query)
        messages = result.scalars().all()

        message_types = {}
        for msg in messages:
            msg_type = msg.message_type.value if msg.message_type else "unknown"
            message_types[msg_type] = message_types.get(msg_type, 0) + 1

        return {
            "total_messages": len(messages),
            "by_type": message_types,
            "average_per_agent": len(messages) / max(len(await self._get_agent_involvement(project_id)), 1),
        }

    async def _get_task_breakdown_by_agent(self, project_id: UUID) -> Dict[str, Any]:
        """Get task breakdown by agent."""
        agents = await self._get_agent_involvement(project_id)
        return {agent["agent_id"]: agent["tasks_assigned"] for agent in agents}

    async def _get_collaboration_patterns(self, project_id: UUID) -> Dict[str, Any]:
        """Get collaboration patterns between agents."""
        return {
            "most_active_pairs": [],
            "communication_volume": await self._get_message_statistics(project_id),
        }

    async def _get_performance_metrics(self, project_id: UUID) -> Dict[str, Any]:
        """Get overall performance metrics."""
        return {
            "project_metrics": await self._get_project_metrics(project_id),
            "agent_involvement": await self._get_agent_involvement(project_id),
        }

    async def _get_project_structure(self, project_id: UUID) -> Dict[str, Any]:
        """Get project file structure."""
        return {
            "root": "project_name",
            "structure": {
                "src": ["components", "pages", "api", "utils"],
                "tests": ["unit", "integration", "e2e"],
                "docs": ["API", "ARCHITECTURE"],
                "public": ["images", "fonts"],
            }
        }

    async def _get_code_files(self, project_id: UUID) -> List[Dict[str, Any]]:
        """Get code files for documentation."""
        return await self._get_code_documentation(project_id)

    async def _get_api_documentation(self, project_id: UUID) -> Dict[str, Any]:
        """Get API documentation."""
        return {
            "endpoints": [],
            "models": [],
            "authentication": "JWT",
        }

    async def _get_database_schema(self, project_id: UUID) -> Dict[str, Any]:
        """Get database schema information."""
        return {
            "database": "PostgreSQL",
            "tables": [],
            "relationships": [],
        }

    async def _get_configuration(self, project_id: UUID) -> Dict[str, Any]:
        """Get configuration information."""
        project = await self._fetch_project(project_id)
        if not project:
            return {}

        return project.meta_data.get("configuration", {}) if project.meta_data else {}

    async def _get_dependencies(self, project_id: UUID) -> List[str]:
        """Get project dependencies."""
        project = await self._fetch_project(project_id)
        if not project:
            return []

        return project.meta_data.get("dependencies", []) if project.meta_data else []

    async def _get_setup_instructions(self, project_id: UUID) -> str:
        """Get setup instructions."""
        return "1. Install dependencies\n2. Configure environment\n3. Run migrations\n4. Start server"

    async def _get_timeline_visualization(self, project_id: UUID) -> Dict[str, Any]:
        """Get timeline data for visualization."""
        return await self._get_project_timeline(project_id)

    async def _get_velocity_metrics(self, project_id: UUID, date_range: Optional[Dict[str, datetime]] = None) -> Dict[str, Any]:
        """Get velocity metrics (tasks completed over time)."""
        return {
            "velocity": await self._get_project_metrics(project_id),
            "trend": "stable",
        }

    async def _get_budget_tracking(self, project_id: UUID) -> Dict[str, Any]:
        """Get budget and cost tracking."""
        return {
            "estimated_cost": 0,
            "actual_cost": 0,
            "variance": 0,
        }

    async def _get_agent_utilization(self, project_id: UUID) -> Dict[str, Any]:
        """Get agent utilization rates."""
        return {
            "agents": await self._get_agent_involvement(project_id),
        }

    async def _get_task_completion_trends(self, project_id: UUID) -> List[Dict[str, Any]]:
        """Get task completion trends over time."""
        return []

    async def _get_escalation_metrics(self, project_id: UUID) -> Dict[str, Any]:
        """Get escalation metrics."""
        escalations = await self._get_escalations(project_id)
        return {
            "total_escalations": len(escalations),
            "open_escalations": sum(1 for e in escalations if e.get("status") == "open"),
            "resolved_escalations": sum(1 for e in escalations if e.get("status") == "resolved"),
        }

    async def _get_quality_metrics(self, project_id: UUID) -> Dict[str, Any]:
        """Get quality metrics."""
        return {
            "test_coverage": 0,
            "bugs_found": 0,
            "defect_rate": 0,
        }
