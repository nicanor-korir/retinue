"""List all agents in the database."""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.db.models import Agent
from app.db.database import get_database_url

async def list_agents():
    """List all agents in the database."""
    # Get database URL
    database_url = get_database_url()

    # Create async engine
    engine = create_async_engine(database_url, echo=False)

    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # Get all agents
        result = await session.execute(
            select(Agent).order_by(Agent.agent_id)
        )
        agents = result.scalars().all()

        if not agents:
            print("❌ No agents found in the database!")
            print("\nYou can add agents by running the seed script or manually.")
            return

        print(f"\n✅ Found {len(agents)} agent(s) in the database:\n")
        print("-" * 80)

        for agent in agents:
            print(f"Agent ID:  {agent.agent_id}")
            print(f"Name:      {agent.name}")
            print(f"Role:      {agent.role}")
            print(f"Type:      {agent.agent_type}")
            print(f"Status:    {agent.status}")
            print(f"Model:     {agent.llm_model or 'Not specified'}")
            print("-" * 80)

        print(f"\n💡 You can chat with any of these agents using their Agent ID")
        print(f"   Example: http://localhost:3000/agents/{agents[0].agent_id}\n")

if __name__ == "__main__":
    asyncio.run(list_agents())
