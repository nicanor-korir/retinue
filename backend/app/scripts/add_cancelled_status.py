"""Add CANCELLED status to TaskStatus and ProjectStatus enums."""
import asyncio
from sqlalchemy import text
from app.db.database import AsyncSessionLocal

async def add_cancelled_status():
    """Add CANCELLED value to the database enums."""
    async with AsyncSessionLocal() as session:
        try:
            # Add CANCELLED to taskstatus enum if it doesn't exist
            print("Adding CANCELLED to taskstatus enum...")
            await session.execute(
                text("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_enum
                            WHERE enumlabel = 'cancelled'
                            AND enumtypid = (
                                SELECT oid FROM pg_type WHERE typname = 'taskstatus'
                            )
                        ) THEN
                            ALTER TYPE taskstatus ADD VALUE 'cancelled';
                        END IF;
                    END $$;
                """)
            )

            # Add CANCELLED to projectstatus enum if it doesn't exist
            print("Adding CANCELLED to projectstatus enum...")
            await session.execute(
                text("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_enum
                            WHERE enumlabel = 'cancelled'
                            AND enumtypid = (
                                SELECT oid FROM pg_type WHERE typname = 'projectstatus'
                            )
                        ) THEN
                            ALTER TYPE projectstatus ADD VALUE 'cancelled';
                        END IF;
                    END $$;
                """)
            )

            await session.commit()
            print("✅ Successfully added CANCELLED status to enums")

        except Exception as e:
            print(f"❌ Error adding CANCELLED status: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    print("Starting migration to add CANCELLED status...")
    asyncio.run(add_cancelled_status())
    print("Migration complete!")
