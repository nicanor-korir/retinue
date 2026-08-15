"""Add HR Monitor agent to the database."""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.db.models import Agent, AgentType, AgentStatus
from app.db.database import get_database_url

async def add_hr_agent():
    """Add HR Monitor agent if it doesn't exist."""
    # Get database URL
    database_url = get_database_url()

    # Create async engine
    engine = create_async_engine(database_url, echo=True)

    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # Check if agent already exists
        from sqlalchemy import select
        result = await session.execute(
            select(Agent).where(Agent.agent_id == "hr_monitor_001")
        )
        existing = result.scalar_one_or_none()

        if existing:
            print("✅ Agent 'hr_monitor_001' already exists!")
            return

        # Create the agent
        hr_agent = Agent(
            agent_id="hr_monitor_001",
            name="HR Monitor",
            role="HR",
            llm_model="claude-sonnet-4-20250514",
            system_prompt="""You are an HR monitoring assistant. You help with:
- Employee queries and HR-related questions
- HR policy information
- Benefits and compensation questions
- Leave and attendance matters
- General HR support

Be professional, helpful, and maintain confidentiality.""",
            agent_type=AgentType.SPECIALIST,
            status=AgentStatus.AVAILABLE,
            max_concurrent_tasks=5,
            thinking_budget=10.0,
            available_tools=["search", "calendar", "email"],
            capabilities=["hr_support", "policy_guidance", "employee_assistance"],
        )

        session.add(hr_agent)
        await session.commit()

        print("✅ Successfully added agent 'hr_monitor_001'!")
        print(f"   Name: {hr_agent.name}")
        print(f"   Role: {hr_agent.role}")
        print(f"   Status: {hr_agent.status}")

if __name__ == "__main__":
    asyncio.run(add_hr_agent())
