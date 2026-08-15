"""
Seed Agent Expertise Tags

Populates initial expertise tags for all agents based on their roles and responsibilities.
This enables the multi-agent discovery system to match agents to conversation needs.

Run with:
    python -m app.scripts.seed_agent_expertise
"""

import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import AsyncSessionLocal
from app.db.models import Agent
from app.db.multi_agent_models import AgentExpertiseTag

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Agent expertise mappings based on roles
AGENT_EXPERTISE = {
    'ceo_001': {
        'expertise': [
            ('strategic_planning', 10, ['strategy', 'planning', 'vision', 'leadership']),
            ('business_development', 9, ['business', 'growth', 'expansion', 'partnerships']),
            ('decision_making', 10, ['decisions', 'choices', 'direction', 'priorities']),
            ('stakeholder_management', 9, ['stakeholders', 'communication', 'relationships']),
            ('company_direction', 10, ['direction', 'goals', 'objectives', 'mission']),
            ('resource_allocation', 8, ['resources', 'budget', 'allocation', 'investment']),
            ('risk_management', 8, ['risk', 'mitigation', 'assessment', 'threats']),
        ]
    },
    'cto_001': {
        'expertise': [
            ('technical_architecture', 10, ['architecture', 'system design', 'infrastructure', 'scalability']),
            ('technology_strategy', 10, ['tech stack', 'technology', 'innovation', 'technical direction']),
            ('engineering_leadership', 9, ['engineering', 'technical leadership', 'development', 'teams']),
            ('system_design', 10, ['design', 'architecture', 'patterns', 'solutions']),
            ('code_quality', 9, ['quality', 'standards', 'best practices', 'review']),
            ('security', 9, ['security', 'cybersecurity', 'vulnerabilities', 'protection']),
            ('performance', 8, ['performance', 'optimization', 'efficiency', 'speed']),
            ('devops', 8, ['devops', 'ci/cd', 'deployment', 'automation']),
        ]
    },
    'pm_001': {
        'expertise': [
            ('project_management', 10, ['project', 'management', 'planning', 'execution']),
            ('agile_methodologies', 9, ['agile', 'scrum', 'sprint', 'ceremonies']),
            ('task_coordination', 10, ['tasks', 'coordination', 'scheduling', 'tracking']),
            ('stakeholder_communication', 9, ['communication', 'updates', 'status', 'reporting']),
            ('resource_planning', 8, ['resources', 'capacity', 'allocation', 'planning']),
            ('risk_mitigation', 8, ['risk', 'issues', 'blockers', 'mitigation']),
            ('timeline_management', 9, ['timeline', 'schedule', 'deadlines', 'milestones']),
            ('team_collaboration', 8, ['collaboration', 'teamwork', 'coordination', 'synergy']),
        ]
    },
    'hr_001': {
        'expertise': [
            ('recruitment', 10, ['hiring', 'recruitment', 'candidates', 'interviews']),
            ('talent_management', 9, ['talent', 'development', 'retention', 'growth']),
            ('employee_relations', 9, ['employee', 'relations', 'engagement', 'satisfaction']),
            ('performance_management', 8, ['performance', 'reviews', 'feedback', 'goals']),
            ('compensation', 8, ['salary', 'compensation', 'benefits', 'packages']),
            ('compliance', 9, ['compliance', 'regulations', 'labor law', 'policies']),
            ('organizational_culture', 8, ['culture', 'values', 'workplace', 'environment']),
            ('conflict_resolution', 8, ['conflict', 'resolution', 'mediation', 'disputes']),
        ]
    },
    'backend_001': {
        'expertise': [
            ('backend_development', 10, ['backend', 'server', 'api', 'services']),
            ('database_design', 9, ['database', 'schema', 'sql', 'nosql', 'data modeling']),
            ('api_development', 10, ['api', 'rest', 'graphql', 'endpoints']),
            ('microservices', 8, ['microservices', 'distributed', 'services', 'architecture']),
            ('python', 10, ['python', 'fastapi', 'django', 'flask']),
            ('authentication', 9, ['auth', 'authentication', 'authorization', 'security']),
            ('data_processing', 8, ['data', 'processing', 'etl', 'pipelines']),
            ('testing', 8, ['testing', 'unit tests', 'integration tests', 'tdd']),
        ]
    },
    'frontend_001': {
        'expertise': [
            ('frontend_development', 10, ['frontend', 'ui', 'interface', 'web']),
            ('react', 10, ['react', 'jsx', 'hooks', 'components']),
            ('ui_ux', 9, ['ui', 'ux', 'user interface', 'user experience']),
            ('responsive_design', 9, ['responsive', 'mobile', 'desktop', 'adaptive']),
            ('typescript', 9, ['typescript', 'types', 'type safety']),
            ('state_management', 8, ['state', 'redux', 'context', 'zustand']),
            ('performance_optimization', 8, ['performance', 'optimization', 'rendering', 'speed']),
            ('accessibility', 8, ['accessibility', 'a11y', 'wcag', 'inclusive']),
        ]
    },
    'designer_001': {
        'expertise': [
            ('ui_design', 10, ['ui design', 'interface', 'visual design', 'layouts']),
            ('ux_design', 10, ['ux', 'user experience', 'usability', 'interaction']),
            ('visual_design', 10, ['visual', 'graphics', 'aesthetics', 'branding']),
            ('prototyping', 9, ['prototypes', 'wireframes', 'mockups', 'figma']),
            ('design_systems', 9, ['design systems', 'components', 'guidelines', 'consistency']),
            ('user_research', 8, ['research', 'user testing', 'interviews', 'feedback']),
            ('branding', 8, ['brand', 'identity', 'logo', 'style guide']),
            ('animation', 7, ['animation', 'transitions', 'micro-interactions', 'motion']),
        ]
    },
}


async def seed_expertise_for_agent(
    db: AsyncSession,
    agent_id: str,
    expertise_list: list
):
    """
    Seed expertise tags for a single agent.

    Args:
        db: Database session
        agent_id: Agent ID
        expertise_list: List of (expertise_area, proficiency_level, keywords) tuples
    """
    logger.info(f"Seeding expertise for agent {agent_id}")

    # Check if agent exists
    result = await db.execute(
        select(Agent).where(Agent.agent_id == agent_id)
    )
    agent = result.scalar_one_or_none()

    if not agent:
        logger.warning(f"Agent {agent_id} not found, skipping")
        return

    # Check if expertise already exists
    result = await db.execute(
        select(AgentExpertiseTag).where(AgentExpertiseTag.agent_id == agent_id)
    )
    existing_expertise = result.scalars().all()

    if existing_expertise:
        logger.info(f"Agent {agent_id} already has {len(existing_expertise)} expertise tags, skipping")
        return

    # Create expertise tags
    tags_created = 0
    for expertise_area, proficiency_level, keywords in expertise_list:
        tag = AgentExpertiseTag(
            agent_id=agent_id,
            expertise_area=expertise_area,
            proficiency_level=proficiency_level,
            confidence_score=0.9,  # High confidence for manually assigned
            related_keywords=keywords,
            manually_assigned=True,
            learned_from_knowledge_base=False
        )
        db.add(tag)
        tags_created += 1

    await db.commit()
    logger.info(f"Created {tags_created} expertise tags for {agent_id}")


async def seed_all_agent_expertise():
    """Seed expertise tags for all agents."""
    logger.info("Starting agent expertise seeding...")

    async with AsyncSessionLocal() as db:
        try:
            # Seed expertise for each agent
            for agent_id, agent_data in AGENT_EXPERTISE.items():
                await seed_expertise_for_agent(
                    db,
                    agent_id,
                    agent_data['expertise']
                )

            logger.info("✅ Agent expertise seeding completed successfully!")

        except Exception as e:
            logger.error(f"❌ Error seeding agent expertise: {e}", exc_info=True)
            await db.rollback()
            raise


async def main():
    """Main entry point."""
    logger.info("=" * 60)
    logger.info("Agent Expertise Seeding Script")
    logger.info("=" * 60)

    await seed_all_agent_expertise()

    logger.info("=" * 60)
    logger.info("Seeding complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
