"""Fix missing context intelligence columns.

Run this if the alembic migration didn't apply correctly.
This script directly adds the missing columns to the database.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.db.database import engine
from sqlalchemy import text


async def fix_missing_columns():
    """Add missing context intelligence columns."""
    print("="*60)
    print("Fixing Missing Context Intelligence Columns")
    print("="*60)

    async with engine.begin() as conn:
        print("\n1. Adding columns to 'conversations' table...")

        # Add context_summary column
        try:
            await conn.execute(text("""
                ALTER TABLE conversations
                ADD COLUMN IF NOT EXISTS context_summary JSONB DEFAULT '{}'::jsonb
            """))
            print("   ✓ Added context_summary column")
        except Exception as e:
            print(f"   ⚠ context_summary: {e}")

        # Add active_entities column
        try:
            await conn.execute(text("""
                ALTER TABLE conversations
                ADD COLUMN IF NOT EXISTS active_entities JSONB DEFAULT '{}'::jsonb
            """))
            print("   ✓ Added active_entities column")
        except Exception as e:
            print(f"   ⚠ active_entities: {e}")

        print("\n2. Adding columns to 'conversation_messages' table...")

        # Add extracted_entities column
        try:
            await conn.execute(text("""
                ALTER TABLE conversation_messages
                ADD COLUMN IF NOT EXISTS extracted_entities JSONB DEFAULT '{}'::jsonb
            """))
            print("   ✓ Added extracted_entities column")
        except Exception as e:
            print(f"   ⚠ extracted_entities: {e}")

        # Add intent_classification column
        try:
            await conn.execute(text("""
                ALTER TABLE conversation_messages
                ADD COLUMN IF NOT EXISTS intent_classification VARCHAR(50)
            """))
            print("   ✓ Added intent_classification column")
        except Exception as e:
            print(f"   ⚠ intent_classification: {e}")

        # Add semantic_summary column
        try:
            await conn.execute(text("""
                ALTER TABLE conversation_messages
                ADD COLUMN IF NOT EXISTS semantic_summary TEXT
            """))
            print("   ✓ Added semantic_summary column")
        except Exception as e:
            print(f"   ⚠ semantic_summary: {e}")

        print("\n3. Verifying columns...")

        # Verify conversations table
        result = await conn.execute(text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'conversations'
            AND column_name IN ('context_summary', 'active_entities')
            ORDER BY column_name
        """))
        conversations_cols = result.fetchall()

        print("\n   Conversations table columns:")
        for col_name, col_type in conversations_cols:
            print(f"   ✓ {col_name} ({col_type})")

        # Verify conversation_messages table
        result = await conn.execute(text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'conversation_messages'
            AND column_name IN ('extracted_entities', 'intent_classification', 'semantic_summary')
            ORDER BY column_name
        """))
        messages_cols = result.fetchall()

        print("\n   Conversation_messages table columns:")
        for col_name, col_type in messages_cols:
            print(f"   ✓ {col_name} ({col_type})")

    print("\n" + "="*60)
    print("Column Fix Complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Restart your FastAPI server")
    print("2. Test creating a conversation")
    print("="*60)


def main():
    """Main entry point."""
    try:
        asyncio.run(fix_missing_columns())
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
