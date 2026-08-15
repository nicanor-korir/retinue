"""Context Intelligence Service for extracting entities, intent, and semantic meaning from messages.

This service provides:
- Entity extraction (projects, tasks, agents)
- Intent classification (question, command, discussion, etc.)
- Semantic analysis (summary, key phrases, sentiment)
- Relationship mapping between entities
"""

from typing import Dict, List, Optional, Set
from datetime import datetime
import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Agent, Project, Task
from app.db.conversation_models import ConversationMessage


class EntityExtractor:
    """Extract entities (projects, tasks, agents) from messages."""

    # Regex patterns for entity detection
    PROJECT_PATTERN = r'project[:\s]+([a-f0-9-]{36})|#([A-Z_]+)|/projects/([a-f0-9-]{36})'
    TASK_PATTERN = r'task[:\s]+([a-f0-9-]{36})|#TASK[_\s]+([0-9]+)|/tasks/([a-f0-9-]{36})'
    AGENT_PATTERN = r'@([a-z_]+)|agent[:\s]+([a-z_]+)'

    async def extract_entities(
        self,
        message: str,
        db: AsyncSession
    ) -> Dict[str, List[str]]:
        """
        Extract all entities from message text.

        Args:
            message: The message text to analyze
            db: Database session

        Returns:
            {
                "projects": ["uuid1", "uuid2"],
                "tasks": ["uuid3"],
                "agents": ["agent_id1", "agent_id2"]
            }
        """
        entities = {
            "projects": [],
            "tasks": [],
            "agents": []
        }

        # Extract project references
        project_matches = re.findall(self.PROJECT_PATTERN, message, re.IGNORECASE)
        for match in project_matches:
            project_id = match[0] or match[1] or match[2]
            if project_id and await self._validate_project(project_id, db):
                if project_id not in entities["projects"]:
                    entities["projects"].append(project_id)

        # Extract task references
        task_matches = re.findall(self.TASK_PATTERN, message, re.IGNORECASE)
        for match in task_matches:
            task_id = match[0] or match[1] or match[2]
            if task_id and await self._validate_task(task_id, db):
                if task_id not in entities["tasks"]:
                    entities["tasks"].append(task_id)

        # Extract agent mentions
        agent_matches = re.findall(self.AGENT_PATTERN, message, re.IGNORECASE)
        for match in agent_matches:
            agent_id = match[0] or match[1]
            if agent_id and await self._validate_agent(agent_id, db):
                if agent_id not in entities["agents"]:
                    entities["agents"].append(agent_id)

        return entities

    async def _validate_project(self, project_id: str, db: AsyncSession) -> bool:
        """Check if project exists in database."""
        try:
            result = await db.execute(
                select(Project).where(Project.project_id == project_id)
            )
            return result.scalar_one_or_none() is not None
        except Exception:
            return False

    async def _validate_task(self, task_id: str, db: AsyncSession) -> bool:
        """Check if task exists in database."""
        try:
            result = await db.execute(
                select(Task).where(Task.task_id == task_id)
            )
            return result.scalar_one_or_none() is not None
        except Exception:
            return False

    async def _validate_agent(self, agent_id: str, db: AsyncSession) -> bool:
        """Check if agent exists in database."""
        try:
            result = await db.execute(
                select(Agent).where(Agent.agent_id == agent_id)
            )
            return result.scalar_one_or_none() is not None
        except Exception:
            return False


class IntentClassifier:
    """Classify user intent from messages."""

    INTENT_KEYWORDS = {
        "question": ["what", "how", "why", "when", "where", "who", "can you tell", "could you explain", "?"],
        "command": ["create", "update", "delete", "start", "stop", "please", "add", "remove", "change", "modify"],
        "clarification": ["explain", "clarify", "elaborate", "details", "more info", "what do you mean"],
        "feedback": ["think", "suggest", "recommend", "opinion", "believe", "should"],
        "escalation": ["problem", "issue", "urgent", "help", "blocked", "error", "stuck", "critical", "emergency"],
        "discussion": []  # default
    }

    def classify_intent(self, message: str) -> str:
        """
        Classify message intent.

        Args:
            message: The message text to classify

        Returns:
            "question" | "command" | "clarification" | "feedback" | "escalation" | "discussion"
        """
        message_lower = message.lower()
        scores = {}

        for intent, keywords in self.INTENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in message_lower)
            scores[intent] = score

        # Return intent with highest score (or "discussion" if all zero)
        max_intent = max(scores, key=scores.get)
        return max_intent if scores[max_intent] > 0 else "discussion"


class SemanticAnalyzer:
    """Perform semantic analysis on messages."""

    async def analyze(self, message: str) -> Dict:
        """
        Analyze message semantics.

        Args:
            message: The message text to analyze

        Returns:
            {
                "summary": "Brief summary of message",
                "key_phrases": ["phrase1", "phrase2"],
                "sentiment": "neutral" | "positive" | "negative" | "urgent",
                "topics": ["topic1", "topic2"]
            }
        """
        return {
            "summary": self._create_summary(message),
            "key_phrases": self._extract_key_phrases(message),
            "sentiment": self._detect_sentiment(message),
            "topics": self._extract_topics(message)
        }

    def _create_summary(self, message: str) -> str:
        """Create brief summary of message."""
        # Simple truncation for now (can enhance with NLP)
        if len(message) <= 100:
            return message
        return message[:97] + "..."

    def _extract_key_phrases(self, message: str) -> List[str]:
        """Extract important phrases (simple noun phrase extraction)."""
        # Simple implementation: extract capitalized phrases and technical terms
        phrases = []

        # Extract quoted phrases
        quoted = re.findall(r'"([^"]+)"', message)
        phrases.extend(quoted)

        # Extract capitalized multi-word phrases (likely proper nouns/technical terms)
        capitalized = re.findall(r'\b([A-Z][a-z]+(?: [A-Z][a-z]+)+)\b', message)
        phrases.extend(capitalized)

        return list(set(phrases))[:5]  # Return up to 5 unique phrases

    def _detect_sentiment(self, message: str) -> str:
        """Detect message sentiment."""
        message_lower = message.lower()

        # Check for urgency indicators
        urgent_keywords = ["urgent", "asap", "emergency", "critical", "blocked", "stuck", "problem", "issue"]
        if any(kw in message_lower for kw in urgent_keywords):
            return "urgent"

        # Check for positive indicators
        positive_keywords = ["great", "excellent", "perfect", "thanks", "good", "awesome", "wonderful"]
        if any(kw in message_lower for kw in positive_keywords):
            return "positive"

        # Check for negative indicators
        negative_keywords = ["bad", "poor", "terrible", "wrong", "error", "failed", "broken"]
        if any(kw in message_lower for kw in negative_keywords):
            return "negative"

        return "neutral"

    def _extract_topics(self, message: str) -> List[str]:
        """Extract topics from message."""
        # Simple keyword-based topic extraction
        topics = []

        topic_keywords = {
            "project_management": ["project", "timeline", "deadline", "milestone", "plan"],
            "development": ["code", "implementation", "feature", "bug", "fix", "develop"],
            "testing": ["test", "qa", "quality", "verify", "validation"],
            "design": ["design", "ui", "ux", "mockup", "wireframe"],
            "deployment": ["deploy", "release", "production", "launch"]
        }

        message_lower = message.lower()
        for topic, keywords in topic_keywords.items():
            if any(kw in message_lower for kw in keywords):
                topics.append(topic)

        return topics


class RelationshipMapper:
    """Map relationships between entities."""

    async def map_relationships(
        self,
        entities: Dict[str, List[str]],
        db: AsyncSession
    ) -> Dict:
        """
        Build relationship graph for entities.

        Args:
            entities: Extracted entities dict
            db: Database session

        Returns:
            {
                "project_tasks": {"project_id": ["task1", "task2"]},
                "task_agents": {"task_id": ["agent1"]},
                "project_agents": {"project_id": ["agent1", "agent2"]}
            }
        """
        relationships = {
            "project_tasks": {},
            "task_agents": {},
            "project_agents": {}
        }

        # For each project, get its tasks
        for project_id in entities.get("projects", []):
            tasks = await self._get_project_tasks(project_id, db)
            relationships["project_tasks"][project_id] = [str(t.task_id) for t in tasks]

            # Get agents for each task
            for task in tasks:
                if task.assigned_to_agent_id:
                    relationships["task_agents"].setdefault(str(task.task_id), []).append(
                        task.assigned_to_agent_id
                    )

            # Get all agents involved in project
            agents = await self._get_project_agents(project_id, db)
            relationships["project_agents"][project_id] = [a.agent_id for a in agents]

        # For explicitly mentioned tasks, get their agents
        for task_id in entities.get("tasks", []):
            task = await self._get_task(task_id, db)
            if task and task.assigned_to_agent_id:
                relationships["task_agents"].setdefault(task_id, []).append(
                    task.assigned_to_agent_id
                )

        return relationships

    async def _get_project_tasks(self, project_id: str, db: AsyncSession) -> List[Task]:
        """Get all tasks for a project."""
        try:
            result = await db.execute(
                select(Task).where(Task.project_id == project_id)
            )
            return result.scalars().all()
        except Exception:
            return []

    async def _get_task(self, task_id: str, db: AsyncSession) -> Optional[Task]:
        """Get a single task."""
        try:
            result = await db.execute(
                select(Task).where(Task.task_id == task_id)
            )
            return result.scalar_one_or_none()
        except Exception:
            return None

    async def _get_project_agents(self, project_id: str, db: AsyncSession) -> List[Agent]:
        """Get all agents involved in project."""
        try:
            # Get project
            result = await db.execute(
                select(Project).where(Project.project_id == project_id)
            )
            project = result.scalar_one_or_none()
            if not project:
                return []

            agent_ids = set()

            # Add owner and requester
            if project.owner_agent_id:
                agent_ids.add(project.owner_agent_id)
            if project.requester_agent_id:
                agent_ids.add(project.requester_agent_id)

            # Add selected agents
            if project.selected_agents:
                agent_ids.update(project.selected_agents)

            # Fetch agents
            if agent_ids:
                result = await db.execute(
                    select(Agent).where(Agent.agent_id.in_(agent_ids))
                )
                return result.scalars().all()

            return []
        except Exception:
            return []


class ContextIntelligenceService:
    """Main service for context intelligence."""

    def __init__(self):
        self.entity_extractor = EntityExtractor()
        self.intent_classifier = IntentClassifier()
        self.semantic_analyzer = SemanticAnalyzer()
        self.relationship_mapper = RelationshipMapper()

    async def extract_quick_context(
        self,
        message: ConversationMessage,
        db: AsyncSession
    ) -> Dict:
        """
        Fast context extraction (< 50ms).

        Extracts basic entities and intent for immediate use.

        Args:
            message: The message object to analyze
            db: Database session

        Returns:
            {
                "entities": {"projects": [...], "tasks": [...], "agents": [...]},
                "intent": "question",
                "timestamp": "ISO timestamp"
            }
        """
        entities = await self.entity_extractor.extract_entities(message.content, db)
        intent = self.intent_classifier.classify_intent(message.content)

        return {
            "entities": entities,
            "intent": intent,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def extract_deep_context(
        self,
        message: ConversationMessage,
        db: AsyncSession
    ) -> Dict:
        """
        Deep context extraction (async, background).

        Performs full semantic analysis and relationship mapping.

        Args:
            message: The message object to analyze
            db: Database session

        Returns:
            {
                "entities": {...},
                "intent": "...",
                "semantic": {...},
                "relationships": {...},
                "timestamp": "..."
            }
        """
        entities = await self.entity_extractor.extract_entities(message.content, db)
        intent = self.intent_classifier.classify_intent(message.content)
        semantic = await self.semantic_analyzer.analyze(message.content)
        relationships = await self.relationship_mapper.map_relationships(entities, db)

        return {
            "entities": entities,
            "intent": intent,
            "semantic": semantic,
            "relationships": relationships,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def get_conversation_context(
        self,
        conversation_id: str,
        db: AsyncSession
    ) -> Dict:
        """
        Get aggregated context for entire conversation.

        Returns summary of all entities, intents, topics discussed.

        Args:
            conversation_id: The conversation ID
            db: Database session

        Returns:
            Aggregated context dictionary
        """
        # Get all messages in conversation
        result = await db.execute(
            select(ConversationMessage).where(
                ConversationMessage.conversation_id == conversation_id
            ).order_by(ConversationMessage.created_at)
        )
        messages = result.scalars().all()

        # Aggregate entities
        all_entities = {"projects": set(), "tasks": set(), "agents": set()}
        intents = []
        topics = set()

        for msg in messages:
            if msg.extracted_entities:
                for entity_type in ["projects", "tasks", "agents"]:
                    if entity_type in msg.extracted_entities:
                        all_entities[entity_type].update(msg.extracted_entities[entity_type])

            if msg.intent_classification:
                intents.append(msg.intent_classification)

        # Convert sets to lists
        all_entities = {k: list(v) for k, v in all_entities.items()}

        # Find dominant intent
        dominant_intent = max(set(intents), key=intents.count) if intents else "discussion"

        return {
            "entities": all_entities,
            "dominant_intent": dominant_intent,
            "message_count": len(messages),
            "topics": list(topics)
        }
