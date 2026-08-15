"""
Add version and parent_id columns to projects and tasks tables.

This migration adds versioning support to the database schema.
Run this script once to update your existing database.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.db.database import engine
from sqlalchemy import text


async def add_version_columns():
    """Add version columns to projects and tasks tables."""

    print("=" * 60)
    print("  Deviant - Database Migration")
    print("  Adding version and parent_id columns")
    print("=" * 60)
    print("")

    async with engine.begin() as conn:
        try:
            # Add version column to projects table
            print("Adding 'version' column to 'projects' table...")
            await conn.execute(text("""
                ALTER TABLE projects
                ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1
            """))
            print("✅ Added 'version' column to 'projects'")

            # Add parent_project_id column to projects table
            print("Adding 'parent_project_id' column to 'projects' table...")
            await conn.execute(text("""
                ALTER TABLE projects
                ADD COLUMN IF NOT EXISTS parent_project_id UUID
            """))
            print("✅ Added 'parent_project_id' column to 'projects'")

            # Add version column to tasks table
            print("Adding 'version' column to 'tasks' table...")
            await conn.execute(text("""
                ALTER TABLE tasks
                ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1
            """))
            print("✅ Added 'version' column to 'tasks'")

            # Add parent_task_id column to tasks table
            print("Adding 'parent_task_id' column to 'tasks' table...")
            await conn.execute(text("""
                ALTER TABLE tasks
                ADD COLUMN IF NOT EXISTS parent_task_id UUID
            """))
            print("✅ Added 'parent_task_id' column to 'tasks'")

            # Update existing projects to have version 1
            print("Updating existing projects to version 1...")
            result = await conn.execute(text("""
                UPDATE projects
                SET version = 1
                WHERE version IS NULL
            """))
            print(f"✅ Updated {result.rowcount} existing projects")

            # Update existing tasks to have version 1
            print("Updating existing tasks to version 1...")
            result = await conn.execute(text("""
                UPDATE tasks
                SET version = 1
                WHERE version IS NULL
            """))
            print(f"✅ Updated {result.rowcount} existing tasks")

            print("")
            print("=" * 60)
            print("✨ Migration completed successfully!")
            print("=" * 60)
            print("")
            print("Database schema updated with:")
            print("  • projects.version (INTEGER, default 1)")
            print("  • projects.parent_project_id (UUID, nullable)")
            print("  • tasks.version (INTEGER, default 1)")
            print("  • tasks.parent_task_id (UUID, nullable)")
            print("")
            print("You can now use the restart functionality!")
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
        asyncio.run(add_version_columns())
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
