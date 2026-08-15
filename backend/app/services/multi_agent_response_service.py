"""
Multi-Agent Response Service

Handles detecting which agents should respond to a message and
coordinates their responses in multi-agent conversations.
"""

import logging
import re
from typing import List, Dict, Any, Optional, AsyncIterator, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.db.models import Agent
from app.db.conversation_models import (
    Conversation,
    ConversationMessage,
    ConversationParticipant,
    ParticipantType,
    SenderType,
)
from app.db.multi_agent_models import AgentPresence
from app.services.conversation_orchestrator import ConversationOrchestrator

logger = logging.getLogger(__name__)


class MultiAgentResponseService:
    """
    Service to coordinate multi-agent responses in conversations.

    Detects which agents should respond based on:
    1. Direct mentions (@agent, agent name, role)
    2. Expertise relevance
    3. Conversation context
    """

    # Agent mention patterns - maps keywords to agent IDs
    AGENT_PATTERNS = {
        'ceo': 'ceo_001',
        'chief executive': 'ceo_001',
        'cto': 'cto_001',
        'chief technology': 'cto_001',
        'tech lead': 'cto_001',
        'cfo': 'cfo_001',
        'chief financial': 'cfo_001',
        'finance officer': 'cfo_001',
        'chro': 'chro_001',
        'hr officer': 'chro_001',
        'pm': 'pm_001',
        'project manager': 'pm_001',
        'product manager': 'pm_001',
        'hr': 'hr_monitor_001',
        'human resources': 'hr_monitor_001',
        'backend': 'backend_001',
        'backend engineer': 'backend_001',
        'backend developer': 'backend_001',
        'frontend': 'frontend_001',
        'frontend engineer': 'frontend_001',
        'frontend developer': 'frontend_001',
        'designer': 'designer_001',
        'ui designer': 'designer_001',
        'ux designer': 'designer_001',
        'marketing': 'marketing_manager_001',
        'marketing manager': 'marketing_manager_001',
        'sales': 'sales_manager_001',
        'sales manager': 'sales_manager_001',
        'financial analyst': 'financial_analyst_001',
        'analyst': 'financial_analyst_001',
    }

    # Response trigger phrases that indicate an agent should respond
    RESPONSE_TRIGGERS = [
        'respond', 'answer', 'reply', 'tell me', 'what do you think',
        'your thoughts', 'your opinion', 'your input', 'can you',
        'please', 'help', 'explain', 'elaborate', 'join', 'contribute',
        'share', 'provide', 'give me', 'i need', 'we need'
    ]

    # Expertise keywords that trigger proactive agent responses
    # These are topics that agents should proactively contribute to
    EXPERTISE_KEYWORDS = {
        'cfo_001': {
            'keywords': [
                'budget', 'cost', 'financial', 'revenue', 'expense', 'profit',
                'pricing', 'investment', 'roi', 'cash flow', 'funding', 'money',
                'salary', 'compensation', 'payroll', 'invoice', 'payment',
                'accounting', 'tax', 'fiscal', 'capital', 'valuation', 'equity',
                'debt', 'loan', 'credit', 'finance', 'economic', 'spend', 'saving'
            ],
            'weight': 0.7  # Threshold for proactive response
        },
        'cto_001': {
            'keywords': [
                'technical', 'architecture', 'infrastructure', 'system', 'technology',
                'scalability', 'performance', 'security', 'database', 'api', 'server',
                'cloud', 'aws', 'azure', 'devops', 'deployment', 'integration',
                'microservices', 'monolith', 'tech stack', 'framework', 'library',
                'engineering', 'software', 'hardware', 'network', 'protocol',
                'algorithm', 'data structure', 'optimization', 'latency', 'throughput'
            ],
            'weight': 0.6
        },
        'ceo_001': {
            'keywords': [
                'strategy', 'vision', 'company', 'business', 'growth', 'market',
                'competition', 'leadership', 'direction', 'goals', 'objectives',
                'mission', 'partnership', 'acquisition', 'expansion', 'stakeholder',
                'board', 'executive', 'decision', 'priority', 'roadmap', 'initiative'
            ],
            'weight': 0.8  # Higher threshold - CEO speaks less frequently
        },
        'pm_001': {
            'keywords': [
                'project', 'timeline', 'task', 'milestone', 'sprint', 'deadline',
                'schedule', 'plan', 'scope', 'requirement', 'deliverable', 'phase',
                'backlog', 'story', 'epic', 'kanban', 'agile', 'scrum', 'standup',
                'blocker', 'dependency', 'resource', 'allocation', 'capacity',
                'progress', 'status', 'update', 'tracking', 'jira', 'ticket'
            ],
            'weight': 0.5  # Lower threshold - PM coordinates frequently
        },
        'chro_001': {
            'keywords': [
                'hiring', 'recruitment', 'hr', 'human resources', 'employee',
                'team', 'culture', 'onboarding', 'training', 'performance review',
                'compensation', 'benefits', 'policy', 'compliance', 'diversity',
                'retention', 'turnover', 'engagement', 'morale', 'workplace',
                'talent', 'staffing', 'headcount', 'interview', 'candidate'
            ],
            'weight': 0.6
        },
        'designer_001': {
            'keywords': [
                'design', 'ui', 'ux', 'interface', 'mockup', 'wireframe',
                'prototype', 'figma', 'sketch', 'user experience', 'visual',
                'layout', 'color', 'typography', 'brand', 'style', 'aesthetic',
                'responsive', 'mobile', 'accessibility', 'usability', 'interaction',
                'animation', 'icon', 'component', 'design system'
            ],
            'weight': 0.5
        },
        'backend_001': {
            'keywords': [
                'backend', 'api', 'database', 'server', 'endpoint', 'rest',
                'graphql', 'sql', 'nosql', 'postgres', 'mongodb', 'redis',
                'authentication', 'authorization', 'jwt', 'oauth', 'cache',
                'queue', 'worker', 'cron', 'migration', 'orm', 'model',
                'controller', 'service', 'repository', 'middleware'
            ],
            'weight': 0.5
        },
        'frontend_001': {
            'keywords': [
                'frontend', 'react', 'vue', 'angular', 'javascript', 'typescript',
                'css', 'html', 'component', 'state', 'redux', 'hook', 'render',
                'dom', 'browser', 'responsive', 'animation', 'bundle', 'webpack',
                'vite', 'nextjs', 'tailwind', 'styled', 'form', 'validation'
            ],
            'weight': 0.5
        },
        'marketing_manager_001': {
            'keywords': [
                'marketing', 'campaign', 'brand', 'advertising', 'promotion',
                'social media', 'content', 'seo', 'analytics', 'conversion',
                'audience', 'engagement', 'reach', 'impression', 'click',
                'email', 'newsletter', 'launch', 'announcement', 'pr',
                'public relations', 'influencer', 'viral', 'growth hacking'
            ],
            'weight': 0.6
        },
        'sales_manager_001': {
            'keywords': [
                'sales', 'revenue', 'customer', 'client', 'deal', 'contract',
                'proposal', 'pitch', 'demo', 'lead', 'prospect', 'pipeline',
                'quota', 'commission', 'closing', 'negotiation', 'pricing',
                'discount', 'upsell', 'cross-sell', 'retention', 'churn',
                'crm', 'salesforce', 'account', 'territory'
            ],
            'weight': 0.6
        },
    }

    # Maximum number of agents that can proactively respond to a single message
    MAX_PROACTIVE_RESPONDERS = 2

    def __init__(self):
        self.orchestrator = ConversationOrchestrator()

    async def detect_responding_agents(
        self,
        session: AsyncSession,
        conversation_id: UUID,
        message_content: str,
        sender_id: str
    ) -> List[Dict[str, Any]]:
        """
        Detect which agents should respond to this message.

        Returns list of agents that should respond, with priority order.

        Priority levels:
        1 - Directly mentioned agents (@agent or by name)
        2 - Primary agent (when response trigger detected)
        3 - Proactive agents (based on expertise match)
        4 - Default primary agent (fallback)
        """
        responding_agents = []
        responding_agent_ids = set()
        content_lower = message_content.lower()

        # Get conversation participants (agents who have joined)
        participants = await self._get_agent_participants(session, conversation_id)
        participant_agent_ids = {p['agent_id'] for p in participants}
        participant_map = {p['agent_id']: p for p in participants}

        # Get conversation for primary agent
        conversation = await self._get_conversation(session, conversation_id)
        if not conversation:
            return []

        # Add primary agent to participant set for consideration
        if conversation.primary_agent_id:
            participant_agent_ids.add(conversation.primary_agent_id)

        # 1. Check for direct agent mentions (highest priority)
        mentioned_agents = self._detect_mentioned_agents(content_lower)
        for agent_id in mentioned_agents:
            if agent_id in participant_agent_ids and agent_id not in responding_agent_ids:
                agent = await self._get_agent(session, agent_id)
                if agent:
                    responding_agents.append({
                        'agent_id': agent_id,
                        'agent_name': agent.name,
                        'reason': 'directly_mentioned',
                        'priority': 1
                    })
                    responding_agent_ids.add(agent_id)

        # 2. Check if message has response triggers - primary agent should respond
        has_response_trigger = any(trigger in content_lower for trigger in self.RESPONSE_TRIGGERS)
        if has_response_trigger and conversation.primary_agent_id:
            if conversation.primary_agent_id not in responding_agent_ids:
                agent = await self._get_agent(session, conversation.primary_agent_id)
                if agent:
                    responding_agents.append({
                        'agent_id': conversation.primary_agent_id,
                        'agent_name': agent.name,
                        'reason': 'primary_agent_triggered',
                        'priority': 2
                    })
                    responding_agent_ids.add(conversation.primary_agent_id)

        # 3. Check for proactive responses from participating agents based on expertise
        proactive_agents = await self._detect_proactive_responders(
            session,
            content_lower,
            participant_agent_ids,
            responding_agent_ids,
            sender_id
        )

        # Add proactive responders (limited by MAX_PROACTIVE_RESPONDERS)
        proactive_count = 0
        for agent_info in proactive_agents:
            if proactive_count >= self.MAX_PROACTIVE_RESPONDERS:
                break
            if agent_info['agent_id'] not in responding_agent_ids:
                responding_agents.append({
                    **agent_info,
                    'priority': 3
                })
                responding_agent_ids.add(agent_info['agent_id'])
                proactive_count += 1

        # 4. If still no agents responding, default to primary agent
        if not responding_agents and conversation.primary_agent_id:
            agent = await self._get_agent(session, conversation.primary_agent_id)
            if agent:
                responding_agents.append({
                    'agent_id': conversation.primary_agent_id,
                    'agent_name': agent.name,
                    'reason': 'default_primary',
                    'priority': 4
                })

        # Sort by priority
        responding_agents.sort(key=lambda x: x['priority'])

        logger.info(
            f"Detected {len(responding_agents)} responding agents for conversation "
            f"{conversation_id}: {[(a['agent_id'], a['reason']) for a in responding_agents]}"
        )

        return responding_agents

    async def _detect_proactive_responders(
        self,
        session: AsyncSession,
        content_lower: str,
        participant_agent_ids: set,
        already_responding: set,
        sender_id: str
    ) -> List[Dict[str, Any]]:
        """
        Detect agents who should proactively respond based on their expertise.

        Returns list of agents sorted by relevance score (highest first).
        """
        proactive_candidates = []

        for agent_id in participant_agent_ids:
            # Skip if already responding
            if agent_id in already_responding:
                continue

            # Skip if this is the sender (agents don't respond to themselves)
            if agent_id == sender_id:
                continue

            # Check expertise match
            if agent_id in self.EXPERTISE_KEYWORDS:
                expertise_config = self.EXPERTISE_KEYWORDS[agent_id]
                keywords = expertise_config['keywords']
                threshold = expertise_config['weight']

                # Calculate relevance score
                matched_keywords = []
                for keyword in keywords:
                    if keyword in content_lower:
                        matched_keywords.append(keyword)

                if matched_keywords:
                    # Score based on number of matches and keyword specificity
                    score = len(matched_keywords) / len(keywords)

                    # Boost score for longer/more specific keyword matches
                    specificity_boost = sum(len(kw) for kw in matched_keywords) / 100
                    score = min(1.0, score + specificity_boost)

                    if score >= threshold:
                        agent = await self._get_agent(session, agent_id)
                        if agent:
                            proactive_candidates.append({
                                'agent_id': agent_id,
                                'agent_name': agent.name,
                                'reason': f'expertise_match: {", ".join(matched_keywords[:3])}',
                                'score': score,
                                'matched_keywords': matched_keywords
                            })
                            logger.debug(
                                f"Agent {agent_id} matched keywords {matched_keywords} "
                                f"with score {score:.2f} (threshold: {threshold})"
                            )

        # Sort by score (highest first)
        proactive_candidates.sort(key=lambda x: x['score'], reverse=True)

        return proactive_candidates

    async def detect_responding_agents_to_agent_message(
        self,
        session: AsyncSession,
        conversation_id: UUID,
        message_content: str,
        sender_agent_id: str
    ) -> List[Dict[str, Any]]:
        """
        Detect which agents should respond to another agent's message.

        This enables agents to have natural conversations with each other.
        Only triggered when the agent's message contains questions or
        mentions other agents, or when their expertise is highly relevant.
        """
        responding_agents = []
        responding_agent_ids = set()
        content_lower = message_content.lower()

        # Get conversation participants
        participants = await self._get_agent_participants(session, conversation_id)
        participant_agent_ids = {p['agent_id'] for p in participants}

        # Get conversation for primary agent
        conversation = await self._get_conversation(session, conversation_id)
        if not conversation:
            return []

        if conversation.primary_agent_id:
            participant_agent_ids.add(conversation.primary_agent_id)

        # Check if agent message asks a question or requests input
        question_indicators = ['?', 'what do you think', 'your input', 'thoughts on',
                              'can you', 'would you', 'should we', 'do you agree',
                              'any concerns', 'feedback', 'opinion']
        is_question = any(indicator in content_lower for indicator in question_indicators)

        # 1. Check for direct mentions of other agents
        mentioned_agents = self._detect_mentioned_agents(content_lower)
        for agent_id in mentioned_agents:
            if agent_id != sender_agent_id and agent_id in participant_agent_ids:
                agent = await self._get_agent(session, agent_id)
                if agent:
                    responding_agents.append({
                        'agent_id': agent_id,
                        'agent_name': agent.name,
                        'reason': 'mentioned_by_agent',
                        'priority': 1
                    })
                    responding_agent_ids.add(agent_id)

        # 2. If question asked and no specific agent mentioned, check expertise match
        if is_question and not responding_agents:
            proactive_agents = await self._detect_proactive_responders(
                session,
                content_lower,
                participant_agent_ids,
                {sender_agent_id},  # Exclude the sender
                sender_agent_id
            )

            # Only add the most relevant agent for agent-to-agent conversations
            if proactive_agents:
                top_agent = proactive_agents[0]
                if top_agent['score'] >= 0.3:  # Lower threshold for agent questions
                    responding_agents.append({
                        **top_agent,
                        'priority': 2
                    })

        logger.info(
            f"Agent-to-agent: {len(responding_agents)} agents should respond to "
            f"{sender_agent_id}'s message in conversation {conversation_id}"
        )

        return responding_agents

    def _detect_mentioned_agents(self, content: str) -> List[str]:
        """Detect agents mentioned in the message content."""
        mentioned = []

        # Check for @ mentions first (e.g., @cfo, @pm)
        at_mentions = re.findall(r'@(\w+)', content)
        for mention in at_mentions:
            mention_lower = mention.lower()
            if mention_lower in self.AGENT_PATTERNS:
                agent_id = self.AGENT_PATTERNS[mention_lower]
                if agent_id not in mentioned:
                    mentioned.append(agent_id)

        # Check for role/name mentions
        for pattern, agent_id in self.AGENT_PATTERNS.items():
            if pattern in content and agent_id not in mentioned:
                mentioned.append(agent_id)

        return mentioned

    async def generate_multi_agent_responses(
        self,
        session: AsyncSession,
        conversation_id: UUID,
        responding_agents: List[Dict[str, Any]],
        user_message_content: str
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Generate responses from multiple agents.

        Yields response chunks for each agent in sequence.
        """
        for agent_info in responding_agents:
            agent_id = agent_info['agent_id']

            # Notify that this agent is typing
            yield {
                'type': 'agent_typing',
                'agent_id': agent_id,
                'agent_name': agent_info['agent_name']
            }

            # Generate response from this agent
            try:
                async for chunk in self.orchestrator.generate_agent_response(
                    session,
                    conversation_id,
                    agent_id
                ):
                    # Add agent info to chunk
                    chunk['responding_agent_id'] = agent_id
                    chunk['responding_agent_name'] = agent_info['agent_name']
                    yield chunk

            except Exception as e:
                logger.error(f"Error generating response from agent {agent_id}: {e}")
                yield {
                    'type': 'agent_error',
                    'agent_id': agent_id,
                    'agent_name': agent_info['agent_name'],
                    'error': str(e)
                }

    async def should_agent_respond(
        self,
        session: AsyncSession,
        conversation_id: UUID,
        agent_id: str,
        message_content: str
    ) -> Tuple[bool, str]:
        """
        Determine if a specific agent should respond to this message.

        Returns (should_respond, reason)
        """
        content_lower = message_content.lower()

        # Check if agent is mentioned
        mentioned_agents = self._detect_mentioned_agents(content_lower)
        if agent_id in mentioned_agents:
            return True, "directly_mentioned"

        # Check if agent is primary
        conversation = await self._get_conversation(session, conversation_id)
        if conversation and conversation.primary_agent_id == agent_id:
            return True, "primary_agent"

        # Check agent expertise match
        agent = await self._get_agent(session, agent_id)
        if agent:
            expertise_match = await self._check_expertise_match(agent, content_lower)
            if expertise_match:
                return True, f"expertise_match: {expertise_match}"

        return False, ""

    async def _check_expertise_match(self, agent: Agent, content: str) -> Optional[str]:
        """Check if message content matches agent's expertise."""
        # Get agent specializations
        specializations = agent.specializations or []

        for spec in specializations:
            if isinstance(spec, str) and spec.lower() in content:
                return spec

        # Check based on agent role
        role_keywords = {
            'cfo': ['budget', 'cost', 'financial', 'revenue', 'expense', 'profit'],
            'cto': ['technical', 'architecture', 'infrastructure', 'code', 'system'],
            'ceo': ['strategy', 'vision', 'company', 'business', 'growth'],
            'pm': ['project', 'timeline', 'task', 'milestone', 'sprint'],
            'designer': ['design', 'ui', 'ux', 'interface', 'mockup'],
        }

        agent_role_key = agent.agent_id.split('_')[0].lower()
        if agent_role_key in role_keywords:
            for keyword in role_keywords[agent_role_key]:
                if keyword in content:
                    return keyword

        return None

    async def _get_agent_participants(
        self,
        session: AsyncSession,
        conversation_id: UUID
    ) -> List[Dict[str, Any]]:
        """Get all agent participants in a conversation."""
        result = await session.execute(
            select(ConversationParticipant)
            .where(
                and_(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.participant_type == ParticipantType.AGENT,
                    ConversationParticipant.is_active == True
                )
            )
        )
        participants = result.scalars().all()

        agent_participants = []
        for p in participants:
            agent = await self._get_agent(session, p.participant_id_ref)
            if agent:
                agent_participants.append({
                    'agent_id': agent.agent_id,
                    'agent_name': agent.name,
                    'participant_id': str(p.participant_id)
                })

        return agent_participants

    async def _get_conversation(
        self,
        session: AsyncSession,
        conversation_id: UUID
    ) -> Optional[Conversation]:
        """Get conversation by ID."""
        result = await session.execute(
            select(Conversation).where(Conversation.conversation_id == conversation_id)
        )
        return result.scalar_one_or_none()

    async def _get_agent(
        self,
        session: AsyncSession,
        agent_id: str
    ) -> Optional[Agent]:
        """Get agent by ID."""
        result = await session.execute(
            select(Agent).where(Agent.agent_id == agent_id)
        )
        return result.scalar_one_or_none()


# Global instance
_multi_agent_response_service: Optional[MultiAgentResponseService] = None


def get_multi_agent_response_service() -> MultiAgentResponseService:
    """Get the global multi-agent response service instance."""
    global _multi_agent_response_service
    if _multi_agent_response_service is None:
        _multi_agent_response_service = MultiAgentResponseService()
    return _multi_agent_response_service
