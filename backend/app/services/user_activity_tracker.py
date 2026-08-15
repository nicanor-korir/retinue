"""User Activity Tracker Service for tracking and analyzing user behavior.

This service provides:
- Activity logging (messages, views, interactions)
- User profiling (preferences, patterns)
- Activity-based context for chat intelligence
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.db.conversation_models import UserActivityLog


class UserActivityTracker:
    """Track and analyze user activity."""

    ACTIVITY_TYPES = [
        "message_sent",
        "project_viewed",
        "task_viewed",
        "agent_interacted",
        "conversation_created",
        "search_performed",
        "filter_applied",
        "project_created",
        "task_created"
    ]

    async def log_activity(
        self,
        user_id: str,
        activity_type: str,
        context: Dict,
        db: AsyncSession,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> None:
        """
        Log a user activity.

        Args:
            user_id: User identifier
            activity_type: Type of activity (from ACTIVITY_TYPES)
            context: Activity context (entities, metadata)
            db: Database session
            session_id: Optional session identifier
            ip_address: Optional IP address (anonymized)
        """
        try:
            # Validate activity type
            if activity_type not in self.ACTIVITY_TYPES:
                return

            # Create activity log entry
            activity = UserActivityLog(
                user_id=user_id,
                activity_type=activity_type,
                context=context,
                session_id=session_id,
                ip_address=ip_address,
                timestamp=datetime.utcnow()
            )

            db.add(activity)
            await db.commit()

        except Exception:
            # Activity logging should never fail the main operation
            await db.rollback()

    async def get_recent_activity(
        self,
        user_id: str,
        db: AsyncSession,
        limit: int = 50,
        activity_types: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Get user's recent activity.

        Args:
            user_id: User identifier
            limit: Maximum number of activities to return
            activity_types: Filter by activity types (optional)
            db: Database session

        Returns:
            List of activity records
        """
        try:
            # Build query
            query = select(UserActivityLog).where(
                UserActivityLog.user_id == user_id
            )

            # Add activity type filter if specified
            if activity_types:
                query = query.where(UserActivityLog.activity_type.in_(activity_types))

            # Order by timestamp descending and limit
            query = query.order_by(UserActivityLog.timestamp.desc()).limit(limit)

            # Execute query
            result = await db.execute(query)
            activities = result.scalars().all()

            # Convert to dict list
            return [
                {
                    "activity_id": str(activity.activity_id),
                    "activity_type": activity.activity_type,
                    "context": activity.context,
                    "timestamp": activity.timestamp.isoformat() if activity.timestamp else None
                }
                for activity in activities
            ]

        except Exception:
            return []

    async def get_user_profile(
        self,
        user_id: str,
        db: AsyncSession,
        days: int = 30
    ) -> Dict:
        """
        Build user profile from activity.

        Args:
            user_id: User identifier
            db: Database session
            days: Number of days to look back (default: 30)

        Returns:
            {
                "active_projects": ["project_id1", "project_id2"],
                "frequent_agents": ["agent1", "agent2"],
                "common_topics": ["topic1", "topic2"],
                "activity_summary": {
                    "messages_sent": 100,
                    "projects_viewed": 20,
                    "tasks_viewed": 50
                }
            }
        """
        try:
            # Get activities from last N days
            since = datetime.utcnow() - timedelta(days=days)
            activities = await self._get_activities_since(user_id, since, db)

            profile = {
                "active_projects": self._extract_active_projects(activities),
                "frequent_agents": self._extract_frequent_agents(activities),
                "common_topics": self._extract_common_topics(activities),
                "activity_summary": self._summarize_activities(activities)
            }

            return profile

        except Exception:
            return {}

    async def get_user_preferences(
        self,
        user_id: str,
        db: AsyncSession
    ) -> Dict:
        """
        Detect user preferences from activity patterns.

        Args:
            user_id: User identifier
            db: Database session

        Returns:
            {
                "response_format": "brief" | "detailed",
                "preferred_agents": ["agent1"],
                "topics_of_interest": ["topic1", "topic2"]
            }
        """
        try:
            # Get recent activities
            activities = await self.get_recent_activity(user_id, db, limit=100)

            # Analyze message length preference (brief vs detailed)
            message_activities = [
                a for a in activities
                if a["activity_type"] == "message_sent"
            ]

            avg_message_length = 0
            if message_activities:
                lengths = [
                    len(a["context"].get("message_content", ""))
                    for a in message_activities
                    if "message_content" in a["context"]
                ]
                avg_message_length = sum(lengths) / len(lengths) if lengths else 0

            response_format = "brief" if avg_message_length < 100 else "detailed"

            # Extract preferred agents
            agent_interactions = [
                a for a in activities
                if a["activity_type"] == "agent_interacted"
            ]
            agent_counts = {}
            for activity in agent_interactions:
                agent_id = activity["context"].get("agent_id")
                if agent_id:
                    agent_counts[agent_id] = agent_counts.get(agent_id, 0) + 1

            preferred_agents = sorted(
                agent_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            preferred_agents = [agent[0] for agent in preferred_agents]

            return {
                "response_format": response_format,
                "preferred_agents": preferred_agents,
                "topics_of_interest": self._extract_common_topics(activities)
            }

        except Exception:
            return {}

    async def get_activity_summary(
        self,
        user_id: str,
        db: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """
        Get activity summary for a time period.

        Args:
            user_id: User identifier
            db: Database session
            start_date: Start date (default: 30 days ago)
            end_date: End date (default: now)

        Returns:
            Summary dictionary with counts and statistics
        """
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()

            # Query activity counts by type
            query = select(
                UserActivityLog.activity_type,
                func.count(UserActivityLog.activity_id).label("count")
            ).where(
                and_(
                    UserActivityLog.user_id == user_id,
                    UserActivityLog.timestamp >= start_date,
                    UserActivityLog.timestamp <= end_date
                )
            ).group_by(UserActivityLog.activity_type)

            result = await db.execute(query)
            counts = {row.activity_type: row.count for row in result.all()}

            # Calculate total
            total = sum(counts.values())

            return {
                "total_activities": total,
                "by_type": counts,
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }
            }

        except Exception:
            return {}

    def _extract_active_projects(self, activities: List[Dict]) -> List[str]:
        """Extract projects user is actively engaged with."""
        project_counts = {}

        for activity in activities:
            context = activity.get("context", {})
            project_id = context.get("project_id")

            if project_id:
                project_counts[project_id] = project_counts.get(project_id, 0) + 1

        # Return top 5 by frequency
        sorted_projects = sorted(
            project_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return [p[0] for p in sorted_projects[:5]]

    def _extract_frequent_agents(self, activities: List[Dict]) -> List[str]:
        """Extract agents user interacts with most."""
        agent_counts = {}

        for activity in activities:
            if activity.get("activity_type") == "agent_interacted":
                context = activity.get("context", {})
                agent_id = context.get("agent_id")

                if agent_id:
                    agent_counts[agent_id] = agent_counts.get(agent_id, 0) + 1

        # Return top 5 by frequency
        sorted_agents = sorted(
            agent_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return [a[0] for a in sorted_agents[:5]]

    def _extract_common_topics(self, activities: List[Dict]) -> List[str]:
        """Extract common topics from activity."""
        topics = []

        for activity in activities:
            if activity.get("activity_type") == "search_performed":
                context = activity.get("context", {})
                query = context.get("query", "")
                if query:
                    # Extract words from search query
                    words = query.lower().split()
                    # Filter common words
                    common_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for"}
                    topics.extend([w for w in words if w not in common_words])

        # Return unique topics (up to 10)
        return list(set(topics))[:10]

    def _summarize_activities(self, activities: List[Dict]) -> Dict:
        """Summarize activity counts by type."""
        summary = {}

        for activity in activities:
            activity_type = activity.get("activity_type")
            if activity_type:
                summary[activity_type] = summary.get(activity_type, 0) + 1

        return summary

    async def _get_activities_since(
        self,
        user_id: str,
        since: datetime,
        db: AsyncSession
    ) -> List[Dict]:
        """Get activities since a timestamp."""
        try:
            query = select(UserActivityLog).where(
                and_(
                    UserActivityLog.user_id == user_id,
                    UserActivityLog.timestamp >= since
                )
            ).order_by(UserActivityLog.timestamp.desc())

            result = await db.execute(query)
            activities = result.scalars().all()

            return [
                {
                    "activity_id": str(activity.activity_id),
                    "activity_type": activity.activity_type,
                    "context": activity.context,
                    "timestamp": activity.timestamp.isoformat() if activity.timestamp else None
                }
                for activity in activities
            ]

        except Exception:
            return []


# Singleton instance
_user_activity_tracker = None


def get_user_activity_tracker() -> UserActivityTracker:
    """Get singleton instance of user activity tracker."""
    global _user_activity_tracker
    if _user_activity_tracker is None:
        _user_activity_tracker = UserActivityTracker()
    return _user_activity_tracker
