"""Initialize database with base data for business operations.

This script initializes the database with:
1. Department definitions
2. Deliverable type definitions
3. Agent metadata from AgentRegistry

Run with: python -m app.scripts.init_database
"""

import asyncio
import logging
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import engine, get_session, init_db
from app.db.models import Department, DeliverableType, Agent
from app.agents.agent_registry import AgentRegistry, Department as DeptEnum

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def init_database_data():
    """Initialize database with reference and agent data."""

    # Initialize database tables if needed
    await init_db()
    logger.info("Database tables initialized")

    async for session in get_session():
        try:
            # 1. Verify departments exist
            departments_count = await session.execute(
                select(func.count()).select_from(Department)
            )
            dept_count = departments_count.scalar()

            if dept_count == 0:
                logger.info("Initializing departments...")
                await init_departments(session)
                logger.info(f"Initialized {(await session.execute(select(func.count()).select_from(Department))).scalar()} departments")
            else:
                logger.info(f"Departments already exist ({dept_count})")

            # 2. Verify deliverable types exist
            types_count = await session.execute(
                select(func.count()).select_from(DeliverableType)
            )
            type_count = types_count.scalar()

            if type_count == 0:
                logger.info("Initializing deliverable types...")
                await init_deliverable_types(session)
                logger.info(f"Initialized {(await session.execute(select(func.count()).select_from(DeliverableType))).scalar()} deliverable types")
            else:
                logger.info(f"Deliverable types already exist ({type_count})")

            # 3. Update agents from registry
            logger.info("Syncing agents from AgentRegistry...")
            synced = await sync_agents_from_registry(session)
            logger.info(f"Synced {synced} agents with registry metadata")

            await session.commit()
            logger.info("Database initialization complete!")

        except Exception as e:
            await session.rollback()
            logger.error(f"Error initializing database: {e}", exc_info=True)
            raise


async def init_departments(session: AsyncSession):
    """Insert department records."""

    departments = [
        {
            'department_id': 'executive',
            'name': 'Executive Leadership',
            'description': 'C-suite strategic decision making',
            'icon': 'briefcase',
            'color': '#8B4513'
        },
        {
            'department_id': 'engineering',
            'name': 'Engineering',
            'description': 'Software development and technical solutions',
            'icon': 'code',
            'color': '#2563EB'
        },
        {
            'department_id': 'marketing',
            'name': 'Marketing & Growth',
            'description': 'Marketing campaigns and growth strategies',
            'icon': 'megaphone',
            'color': '#DC2626'
        },
        {
            'department_id': 'sales',
            'name': 'Sales & Business Development',
            'description': 'Revenue generation and client acquisition',
            'icon': 'dollar-sign',
            'color': '#059669'
        },
        {
            'department_id': 'finance',
            'name': 'Finance & Accounting',
            'description': 'Financial analysis and planning',
            'icon': 'chart-line',
            'color': '#7C3AED'
        },
        {
            'department_id': 'hr',
            'name': 'Human Resources',
            'description': 'People operations and talent management',
            'icon': 'users',
            'color': '#EA580C'
        },
        {
            'department_id': 'operations',
            'name': 'Operations',
            'description': 'Business operations and efficiency',
            'icon': 'settings',
            'color': '#64748B'
        },
        {
            'department_id': 'legal',
            'name': 'Legal & Compliance',
            'description': 'Legal advice and compliance',
            'icon': 'scale',
            'color': '#6B7280'
        },
        {
            'department_id': 'research',
            'name': 'Research & Analytics',
            'description': 'Data analysis and market research',
            'icon': 'search',
            'color': '#14B8A6'
        },
    ]

    for dept_data in departments:
        dept = Department(**dept_data)
        session.add(dept)
        logger.debug(f"Added department: {dept_data['department_id']}")


async def init_deliverable_types(session: AsyncSession):
    """Insert deliverable type records."""

    types = [
        {
            'type_id': 'software_mvp',
            'name': 'Software MVP',
            'description': 'Full stack application with code',
            'typical_agents': ['ceo_001', 'cto_001', 'pm_001', 'backend_001', 'frontend_001', 'designer_001'],
            'output_format': 'code'
        },
        {
            'type_id': 'marketing_campaign',
            'name': 'Marketing Campaign',
            'description': 'Complete marketing campaign with assets',
            'typical_agents': ['ceo_001', 'cmo_001', 'content_001', 'designer_001', 'social_media_001'],
            'output_format': 'pdf'
        },
        {
            'type_id': 'financial_analysis',
            'name': 'Financial Analysis Report',
            'description': 'Financial projections and analysis',
            'typical_agents': ['ceo_001', 'cfo_001', 'financial_analyst_001'],
            'output_format': 'xlsx'
        },
        {
            'type_id': 'business_proposal',
            'name': 'Business Proposal',
            'description': 'Professional business proposal',
            'typical_agents': ['ceo_001', 'sales_manager_001', 'designer_001'],
            'output_format': 'pdf'
        },
        {
            'type_id': 'hr_policy',
            'name': 'HR Policy Document',
            'description': 'Company policy documentation',
            'typical_agents': ['ceo_001', 'chro_001', 'hr_specialist_001', 'legal_001'],
            'output_format': 'docx'
        },
        {
            'type_id': 'market_research',
            'name': 'Market Research Report',
            'description': 'Comprehensive market analysis',
            'typical_agents': ['ceo_001', 'research_001', 'data_analyst_001'],
            'output_format': 'pdf'
        },
        {
            'type_id': 'api_development',
            'name': 'API Development',
            'description': 'RESTful API with documentation',
            'typical_agents': ['ceo_001', 'cto_001', 'pm_001', 'backend_001'],
            'output_format': 'code'
        },
        {
            'type_id': 'brand_strategy',
            'name': 'Brand Strategy',
            'description': 'Comprehensive brand positioning',
            'typical_agents': ['ceo_001', 'cmo_001', 'designer_001'],
            'output_format': 'pdf'
        },
        {
            'type_id': 'budget_planning',
            'name': 'Budget Planning',
            'description': 'Annual budget and allocation',
            'typical_agents': ['ceo_001', 'cfo_001'],
            'output_format': 'xlsx'
        },
        {
            'type_id': 'sales_strategy',
            'name': 'Sales Strategy',
            'description': 'Sales playbook and strategy',
            'typical_agents': ['ceo_001', 'sales_manager_001', 'cfo_001'],
            'output_format': 'pdf'
        },
    ]

    for type_data in types:
        dt = DeliverableType(**type_data)
        session.add(dt)
        logger.debug(f"Added deliverable type: {type_data['type_id']}")


async def sync_agents_from_registry(session: AsyncSession) -> int:
    """Sync agent metadata from AgentRegistry to database.

    Returns:
        Number of agents synced
    """

    synced_count = 0

    for agent_id, config in AgentRegistry.AGENT_CATALOG.items():
        # Query existing agent
        result = await session.execute(
            select(Agent).where(Agent.agent_id == agent_id)
        )
        agent = result.scalar_one_or_none()

        if agent:
            # Update existing agent with new metadata
            logger.debug(f"Updating agent: {agent_id}")

            # Convert enums to values if needed
            output_types = []
            for ot in config.get('output_types', []):
                if hasattr(ot, 'value'):
                    output_types.append(ot.value)
                else:
                    output_types.append(str(ot))

            specializations = []
            for spec in config.get('specializations', []):
                if hasattr(spec, 'value'):
                    specializations.append(spec.value)
                else:
                    specializations.append(str(spec))

            agent.output_types = output_types
            agent.specializations = specializations
            agent.required_for_types = config.get('required_for_types', [])

            synced_count += 1
        else:
            # Agent doesn't exist - this is expected (agents created by other scripts)
            logger.debug(f"Agent not found in database: {agent_id} (will be created by agent initialization)")

    return synced_count


async def main():
    """Main entry point."""
    logger.info("Starting database initialization...")
    try:
        await init_database_data()
        logger.info("Database initialization successful!")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
