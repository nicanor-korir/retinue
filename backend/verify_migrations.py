#!/usr/bin/env python
"""Verify that all database tables have been created successfully."""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

expected_tables = [
    'agents',
    'agent_status',
    'projects',
    'tasks',
    'messages',
    'decisions',
    'knowledge_base',
    'escalations',
    'audit_log',
    'human_interactions',
    'notifications',
    'system_settings',
    'user_profiles',
    'settings_audit_log',
]

def verify_tables():
    """Verify all expected tables exist in the database."""

    try:
        # Parse connection string
        database_url = os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://nicanor:admin@localhost:5432/deviant_dev"
        )

        # Convert asyncpg URL to psycopg2 format
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")

        # Connect to database
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        # Get list of existing tables
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)

        existing_tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()

        print("=" * 70)
        print("DATABASE MIGRATION VERIFICATION")
        print("=" * 70)
        print()
        print(f"Total tables found in database: {len(existing_tables)}")
        print(f"Tables: {', '.join(existing_tables)}")
        print()

        all_created = True
        for table_name in expected_tables:
            if table_name in existing_tables:
                print(f"OK - {table_name:35}")
            else:
                print(f"MISSING - {table_name:35}")
                all_created = False

        print()
        print("=" * 70)
        if all_created:
            print("SUCCESS: ALL EXPECTED TABLES CREATED!")
            print(f"Total: {len(expected_tables)} tables")
            print("Migration is complete and ready for use.")
        else:
            missing = len(expected_tables) - sum(1 for t in expected_tables if t in existing_tables)
            print(f"ERROR: {missing} tables are missing. Check migration logs.")
        print("=" * 70)

        return all_created

    except Exception as e:
        print(f"ERROR: {str(e)}")
        print("Make sure PostgreSQL is running and the database is accessible.")
        return False

if __name__ == "__main__":
    success = verify_tables()
    exit(0 if success else 1)
