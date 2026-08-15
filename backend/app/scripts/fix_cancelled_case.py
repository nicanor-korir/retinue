"""Fix CANCELLED status to use uppercase in database enums."""
import asyncio
from sqlalchemy import text
from app.db.database import AsyncSessionLocal

async def fix_cancelled_case():
    """Add CANCELLED (uppercase) value to the database enums."""
    async with AsyncSessionLocal() as session:
        try:
            # Add CANCELLED (uppercase) to taskstatus enum if it doesn't exist
            print("Adding CANCELLED (uppercase) to taskstatus enum...")
            await session.execute(
                text("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_enum
                            WHERE enumlabel = 'CANCELLED'
                            AND enumtypid = (
                                SELECT oid FROM pg_type WHERE typname = 'taskstatus'
                            )
                        ) THEN
                            ALTER TYPE taskstatus ADD VALUE 'CANCELLED';
                        END IF;
                    END $$;
                """)
            )

            await session.commit()
            print("✅ Successfully added CANCELLED (uppercase) to taskstatus enum")

        except Exception as e:
            print(f"❌ Error adding CANCELLED status: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    print("Starting migration to fix CANCELLED case...")
    asyncio.run(fix_cancelled_case())
    print("Migration complete!")
