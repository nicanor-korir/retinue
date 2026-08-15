"""
Add soft delete (deleted_at) columns to projects and tasks tables.

This migration adds soft delete support to the database schema.
Run this script once to update your existing database.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.db.database import engine
from sqlalchemy import text


async def add_soft_delete_columns():
    """Add deleted_at columns to projects and tasks tables."""

    print("=" * 60)
    print("  Deviant - Database Migration")
    print("  Adding soft delete (deleted_at) columns")
    print("=" * 60)
    print("")

    async with engine.begin() as conn:
        try:
            # Add deleted_at column to projects table
            print("Adding 'deleted_at' column to 'projects' table...")
            await conn.execute(text("""
                ALTER TABLE projects
                ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP
            """))
            print("✅ Added 'deleted_at' column to 'projects'")

            # Add deleted_at column to tasks table
            print("Adding 'deleted_at' column to 'tasks' table...")
            await conn.execute(text("""
                ALTER TABLE tasks
                ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP
            """))
            print("✅ Added 'deleted_at' column to 'tasks'")

            print("")
            print("=" * 60)
            print("✨ Migration completed successfully!")
            print("=" * 60)
            print("")
            print("Database schema updated with:")
            print("  • projects.deleted_at (TIMESTAMP, nullable)")
            print("  • tasks.deleted_at (TIMESTAMP, nullable)")
            print("")
            print("You can now use soft delete functionality!")
            print("")

        except Exception as e:
            print("")
            print(f"❌ Migration failed: {e}")
            print("")
            import traceback
            traceback.print_exc()
            raise


if __name__ == "__main__":
    try:
        asyncio.run(add_soft_delete_columns())
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
