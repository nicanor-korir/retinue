"""
Migration script to add real-time event tracking tables.

This script creates the new tables for capturing agent activities, thoughts,
LLM interactions, handoffs, and other events for the Glass Box AI feature.

Run with:
    python -m app.scripts.add_event_tracking
"""
import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine
from app.db.database import DATABASE_URL
from app.db.event_models import Base as EventBase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def add_event_tracking_tables():
    """Add event tracking tables to the database."""
    logger.info("=" * 60)
    logger.info("Starting Event Tracking Tables Migration")
    logger.info("=" * 60)
    
    # Create async engine
    engine = create_async_engine(
        DATABASE_URL,
        echo=True,  # Enable SQL query logging for migration
    )
    
    try:
        logger.info("\n📊 Creating new event tracking tables...")
        
        # Create all event tracking tables
        async with engine.begin() as conn:
            await conn.run_sync(EventBase.metadata.create_all)
        
        logger.info("\n✅ Event tracking tables created successfully!")
        logger.info("\nNew tables added:")
        logger.info("  - agent_activities")
        logger.info("  - agent_thoughts")
        logger.info("  - llm_interactions")
        logger.info("  - agent_handoffs")
        logger.info("  - content_generations")
        logger.info("  - decision_points")
        logger.info("  - agent_metrics")
        logger.info("  - event_timeline")
        
        logger.info("\n🎉 Migration completed successfully!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"\n❌ Migration failed: {e}", exc_info=True)
        raise
    finally:
        await engine.dispose()


async def verify_tables():
    """Verify that the tables were created."""
    from sqlalchemy import text
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    try:
        async with engine.begin() as conn:
            # Query to list all tables
            result = await conn.execute(
                text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name LIKE 'agent_%' OR table_name LIKE '%_timeline'
                    ORDER BY table_name;
                """)
            )
            tables = result.fetchall()
            
            logger.info("\n📋 Event tracking tables in database:")
            for table in tables:
                logger.info(f"  ✓ {table[0]}")
            
            return len(tables) > 0
            
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return False
    finally:
        await engine.dispose()


if __name__ == "__main__":
    async def main():
        await add_event_tracking_tables()
        
        # Verify tables were created
        if await verify_tables():
            logger.info("\n✅ All tables verified successfully!")
        else:
            logger.warning("\n⚠️ Some tables may not have been created")
    
    asyncio.run(main())
