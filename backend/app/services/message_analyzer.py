"""
Message Analyzer for Multi-Agent Detection

Analyzes user messages to detect when they're requesting other agents
to join the conversation.
"""

import logging
import re
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import Agent

logger = logging.getLogger(__name__)


class MessageAnalyzer:
    """Analyzes messages for multi-agent requests."""

    # Agent role keywords mapping
    AGENT_KEYWORDS = {
        'ceo': ['ceo', 'chief executive', 'executive officer', 'leadership', 'strategy'],
        'cto': ['cto', 'chief technology', 'technology officer', 'technical lead', 'tech lead'],
        'cfo': ['cfo', 'chief financial', 'financial officer', 'finance', 'budget', 'cost', 'financial'],
        'chro': ['chro', 'chief hr', 'hr officer', 'talent', 'people officer'],
        'pm': ['pm', 'project manager', 'product manager', 'scrum master'],
        'hr': ['hr', 'human resources', 'recruiter', 'hiring manager', 'people ops'],
        'backend': ['backend', 'backend engineer', 'backend developer', 'api developer'],
        'frontend': ['frontend', 'frontend engineer', 'frontend developer', 'ui developer'],
        'designer': ['designer', 'ui designer', 'ux designer', 'design lead'],
        'marketing': ['marketing', 'marketing manager', 'campaign'],
        'sales': ['sales', 'sales manager', 'business development'],
        'financial_analyst': ['financial analyst', 'analyst', 'forecasting'],
    }

    # Request patterns
    REQUEST_PATTERNS = [
        # Direct requests
        r'pull\s+(?:the\s+)?(\w+(?:\s+\w+)?)\s+(?:and\s+(\w+(?:\s+\w+)?)\s+)?into\s+(?:this\s+)?(?:conversation|chat)',
        r'invite\s+(?:the\s+)?(\w+(?:\s+\w+)?)',
        r'bring\s+(?:in\s+)?(?:the\s+)?(\w+(?:\s+\w+)?)',
        r'add\s+(?:the\s+)?(\w+(?:\s+\w+)?)\s+to\s+(?:this\s+)?(?:conversation|chat)',
        r'get\s+(?:the\s+)?(\w+(?:\s+\w+)?)\s+(?:in\s+here|on\s+this)',
        r'need\s+(?:the\s+)?(\w+(?:\s+\w+)?)\s+(?:in\s+here|on\s+this|to\s+join)',

        # Multiple agents
        r'pull\s+in\s+(\w+(?:\s+\w+)?)\s+and\s+(\w+(?:\s+\w+)?)',
        r'invite\s+(\w+(?:\s+\w+)?)\s+and\s+(\w+(?:\s+\w+)?)',

        # Questions needing expertise
        r"(?:can|could)\s+(?:the\s+)?(\w+(?:\s+\w+)?)\s+(?:help|assist|join|weigh in)",
        r"(?:need|want)\s+(?:input|help)\s+from\s+(?:the\s+)?(\w+(?:\s+\w+)?)",
    ]

    @classmethod
    async def analyze_for_agent_requests(
        cls,
        db: AsyncSession,
        message_content: str,
        conversation_id: UUID,
        current_agent_ids: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze a message to detect agent invitation requests.

        Args:
            db: Database session
            message_content: The message to analyze
            conversation_id: Conversation ID
            current_agent_ids: Currently participating agent IDs

        Returns:
            List of agent recommendations with reasons
        """
        current_agent_ids = current_agent_ids or []
        detected_agents = []
        message_lower = message_content.lower()

        # 1. Check for explicit agent requests using patterns
        for pattern in cls.REQUEST_PATTERNS:
            matches = re.finditer(pattern, message_lower, re.IGNORECASE)
            for match in matches:
                # Extract mentioned roles from all captured groups
                for group in match.groups():
                    if group:
                        agent_id = await cls._identify_agent_from_text(db, group, current_agent_ids)
                        if agent_id and agent_id not in [a['agent_id'] for a in detected_agents]:
                            detected_agents.append({
                                'agent_id': agent_id,
                                'confidence': 0.95,  # High confidence for explicit mentions
                                'reason': f'User explicitly requested {group}',
                                'trigger': 'explicit_request'
                            })

        # 2. Check for role keywords (lower confidence)
        for role, keywords in cls.AGENT_KEYWORDS.items():
            for keyword in keywords:
                # Look for keywords in context of needing help/input
                context_patterns = [
                    f'need.*{keyword}',
                    f'want.*{keyword}',
                    f'{keyword}.*help',
                    f'{keyword}.*input',
                    f'{keyword}.*perspective',
                ]

                for ctx_pattern in context_patterns:
                    if re.search(ctx_pattern, message_lower):
                        # Get the actual agent with this role
                        agent = await cls._get_agent_by_role(db, role)
                        if agent and agent.agent_id not in current_agent_ids:
                            if agent.agent_id not in [a['agent_id'] for a in detected_agents]:
                                detected_agents.append({
                                    'agent_id': agent.agent_id,
                                    'confidence': 0.75,  # Medium confidence for keywords
                                    'reason': f'Message mentions need for {keyword}',
                                    'trigger': 'keyword_match'
                                })
                        break  # Found this role, move to next

        # 3. Log detected agents
        if detected_agents:
            logger.info(
                f"Detected {len(detected_agents)} agent requests in message: "
                f"{[a['agent_id'] for a in detected_agents]}"
            )
        else:
            logger.debug("No agent requests detected in message")

        return detected_agents

    @staticmethod
    async def _identify_agent_from_text(
        db: AsyncSession,
        text: str,
        exclude_ids: List[str]
    ) -> Optional[str]:
        """Identify which agent is being referred to from text."""
        text_lower = text.lower().strip()

        # Direct role matches
        role_mapping = {
            'ceo': 'ceo',
            'chief executive': 'ceo',
            'cto': 'cto',
            'chief technology officer': 'cto',
            'tech lead': 'cto',
            'cfo': 'cfo',
            'chief financial officer': 'cfo',
            'finance': 'cfo',
            'financial': 'cfo',
            'chro': 'chro',
            'chief hr officer': 'chro',
            'chief human resources': 'chro',
            'pm': 'pm',
            'project manager': 'pm',
            'product manager': 'pm',
            'hr': 'hr',
            'human resources': 'hr',
            'backend': 'backend',
            'backend engineer': 'backend',
            'frontend': 'frontend',
            'frontend engineer': 'frontend',
            'designer': 'designer',
            'ux designer': 'designer',
            'ui designer': 'designer',
            'marketing': 'marketing',
            'marketing manager': 'marketing',
            'sales': 'sales',
            'sales manager': 'sales',
            'financial analyst': 'financial_analyst',
            'analyst': 'financial_analyst',
        }

        # Check if text matches a known role
        for phrase, role in role_mapping.items():
            if phrase in text_lower:
                # Get agent with this role
                agent = await MessageAnalyzer._get_agent_by_role(db, role)
                if agent and agent.agent_id not in exclude_ids:
                    return agent.agent_id

        return None

    @staticmethod
    async def _get_agent_by_role(db: AsyncSession, role_key: str) -> Optional[Agent]:
        """Get agent by role keyword."""
        # Map role keys to actual agent IDs (based on your system)
        role_to_agent_id = {
            'ceo': 'ceo_001',
            'cto': 'cto_001',
            'cfo': 'cfo_001',
            'chro': 'chro_001',
            'pm': 'pm_001',
            'hr': 'hr_monitor_001',
            'backend': 'backend_001',
            'frontend': 'frontend_001',
            'designer': 'designer_001',
            'marketing': 'marketing_manager_001',
            'sales': 'sales_manager_001',
            'financial_analyst': 'financial_analyst_001',
        }

        agent_id = role_to_agent_id.get(role_key)
        if not agent_id:
            return None

        result = await db.execute(
            select(Agent).where(Agent.agent_id == agent_id)
        )
        return result.scalar_one_or_none()

    @classmethod
    async def should_auto_invite(
        cls,
        detected_agents: List[Dict[str, Any]],
        confidence_threshold: float = 0.9
    ) -> List[str]:
        """
        Determine which agents should be auto-invited based on confidence.

        Args:
            detected_agents: List of detected agent dicts
            confidence_threshold: Minimum confidence for auto-invite

        Returns:
            List of agent IDs to auto-invite
        """
        return [
            agent['agent_id']
            for agent in detected_agents
            if agent['confidence'] >= confidence_threshold
        ]
