"""Add missing status values to enums."""
import asyncio
from sqlalchemy import text
from app.db.database import AsyncSessionLocal

async def add_missing_statuses():
    """Add missing uppercase values to the database enums."""
    async with AsyncSessionLocal() as session:
        try:
            # Add FAILED to taskstatus if missing
            print("Adding FAILED to taskstatus enum...")
            await session.execute(
                text("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_enum
                            WHERE enumlabel = 'FAILED'
                            AND enumtypid = (
                                SELECT oid FROM pg_type WHERE typname = 'taskstatus'
                            )
                        ) THEN
                            ALTER TYPE taskstatus ADD VALUE 'FAILED';
                        END IF;
                    END $$;
                """)
            )

            # Add ON_HOLD to projectstatus if missing
            print("Adding ON_HOLD to projectstatus enum...")
            await session.execute(
                text("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_enum
                            WHERE enumlabel = 'ON_HOLD'
                            AND enumtypid = (
                                SELECT oid FROM pg_type WHERE typname = 'projectstatus'
                            )
                        ) THEN
                            ALTER TYPE projectstatus ADD VALUE 'ON_HOLD';
                        END IF;
                    END $$;
                """)
            )

            # Add FAILED to projectstatus if missing
            print("Adding FAILED to projectstatus enum...")
            await session.execute(
                text("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_enum
                            WHERE enumlabel = 'FAILED'
                            AND enumtypid = (
                                SELECT oid FROM pg_type WHERE typname = 'projectstatus'
                            )
                        ) THEN
                            ALTER TYPE projectstatus ADD VALUE 'FAILED';
                        END IF;
                    END $$;
                """)
            )

            await session.commit()
            print("✅ Successfully added missing status values")

        except Exception as e:
            print(f"❌ Error: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    print("Starting migration...")
    asyncio.run(add_missing_statuses())
    print("Migration complete!")
