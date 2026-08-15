"""
Verify database setup status and identify missing components.

Run with: python -m app.scripts.verify_database
"""

import asyncio
import sys
from pathlib import Path
from sqlalchemy import inspect, text, select, func

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.db.database import engine, AsyncSessionLocal
from app.db.models import (
    Agent, Project, Task, Department, DeliverableType,
    ProjectAgentAssignment, AgentStatus
)


async def check_migrations():
    """Check current migration status."""
    print("\n" + "=" * 60)
    print("1. MIGRATION STATUS")
    print("=" * 60)

    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                text("SELECT version_num FROM alembic_version ORDER BY version_num DESC LIMIT 1;")
            )
            current_version = result.scalar()
            print(f"✅ Current Migration: {current_version or 'None'}")

            # Expected: 003_business_ops
            if current_version and "003" in str(current_version):
                print("✅ Migration chain complete (all phases applied)")
                return True
            else:
                print("⚠️  WARNING: Not all migrations applied yet")
                print("   Run: alembic upgrade head")
                return False
        except Exception as e:
            print(f"❌ Error checking migrations: {e}")
            return False


async def check_schema_columns():
    """Verify Phase 0 columns exist in tables."""
    print("\n" + "=" * 60)
    print("2. SCHEMA COLUMNS CHECK")
    print("=" * 60)

    async with engine.connect() as conn:
        try:
            # Check agents table columns
            result = await conn.execute(
                text("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name='agents'
                    AND column_name IN ('output_types', 'specializations', 'required_for_types')
                    ORDER BY column_name;
                """)
            )
            agent_cols = [row[0] for row in result.fetchall()]

            if len(agent_cols) == 3:
                print("✅ agents table has all Phase 0 columns:")
                for col in agent_cols:
                    print(f"   • {col}")
            else:
                print(f"❌ agents table missing columns. Found {len(agent_cols)}/3:")
                for col in agent_cols:
                    print(f"   ✓ {col}")
                print("   ✗ Missing: output_types, specializations, required_for_types")
                return False

            # Check projects table columns
            result = await conn.execute(
                text("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name='projects'
                    AND column_name IN ('project_type', 'deliverable_type', 'selected_agents')
                    ORDER BY column_name;
                """)
            )
            project_cols = [row[0] for row in result.fetchall()]

            if len(project_cols) == 3:
                print("\n✅ projects table has all Phase 0 columns:")
                for col in project_cols:
                    print(f"   • {col}")
            else:
                print(f"\n❌ projects table missing columns. Found {len(project_cols)}/3")
                return False

            # Check tasks table columns
            result = await conn.execute(
                text("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name='tasks'
                    AND column_name IN ('output_format', 'output_metadata')
                    ORDER BY column_name;
                """)
            )
            task_cols = [row[0] for row in result.fetchall()]

            if len(task_cols) == 2:
                print("\n✅ tasks table has all Phase 0 columns:")
                for col in task_cols:
                    print(f"   • {col}")
            else:
                print(f"\n❌ tasks table missing columns. Found {len(task_cols)}/2")
                return False

            return True

        except Exception as e:
            print(f"❌ Error checking schema: {e}")
            return False


async def check_reference_data():
    """Check if reference data is initialized."""
    print("\n" + "=" * 60)
    print("3. REFERENCE DATA CHECK")
    print("=" * 60)

    async with AsyncSessionLocal() as session:
        try:
            # Check departments
            dept_count = await session.execute(select(func.count()).select_from(Department))
            dept_count = dept_count.scalar()

            if dept_count == 9:
                print(f"✅ Departments: {dept_count}/9 initialized")
            elif dept_count > 0:
                print(f"⚠️  Departments: {dept_count}/9 (incomplete)")
            else:
                print("❌ Departments: 0/9 (not initialized)")
                print("   Run: python -m app.scripts.init_database")
                return False

            # Check deliverable types
            type_count = await session.execute(select(func.count()).select_from(DeliverableType))
            type_count = type_count.scalar()

            if type_count == 10:
                print(f"✅ Deliverable Types: {type_count}/10 initialized")
            elif type_count > 0:
                print(f"⚠️  Deliverable Types: {type_count}/10 (incomplete)")
            else:
                print("❌ Deliverable Types: 0/10 (not initialized)")
                return False

            return dept_count == 9 and type_count == 10

        except Exception as e:
            print(f"❌ Error checking reference data: {e}")
            return False


async def check_agents():
    """Check if agents are initialized."""
    print("\n" + "=" * 60)
    print("4. AGENTS CHECK")
    print("=" * 60)

    async with AsyncSessionLocal() as session:
        try:
            # Check agents
            result = await session.execute(select(func.count()).select_from(Agent))
            agent_count = result.scalar()

            if agent_count == 7:
                print(f"✅ Agents: {agent_count}/7 created")

                # List agents
                agents = await session.execute(
                    select(Agent).order_by(Agent.agent_id)
                )
                print("\n   Agent Hierarchy:")
                for agent in agents.scalars():
                    indent = "      "
                    if agent.reports_to:
                        indent = "      ├─ "
                    print(f"   {indent}{agent.name} ({agent.agent_id})")
            elif agent_count > 0:
                print(f"⚠️  Agents: {agent_count}/7 (incomplete)")
            else:
                print("❌ Agents: 0/7 (not initialized)")
                print("   Run: python -m app.scripts.init_agents")
                return False

            # Check agent statuses
            status_result = await session.execute(select(func.count()).select_from(AgentStatus))
            status_count = status_result.scalar()

            if status_count == 7:
                print(f"\n✅ Agent Statuses: {status_count}/7 created")
            elif status_count > 0:
                print(f"\n⚠️  Agent Statuses: {status_count}/7 (incomplete)")
            else:
                print("\n❌ Agent Statuses: 0/7 (not created)")
                return False

            return agent_count == 7 and status_count == 7

        except Exception as e:
            print(f"❌ Error checking agents: {e}")
            return False


async def check_tables():
    """Check if Phase 0 tables exist."""
    print("\n" + "=" * 60)
    print("5. PHASE 0 TABLES CHECK")
    print("=" * 60)

    required_tables = ['departments', 'deliverable_types', 'project_agent_assignments']

    async with engine.connect() as conn:
        try:
            result = await conn.execute(
                text("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema='public'
                    ORDER BY table_name;
                """)
            )
            existing_tables = {row[0] for row in result.fetchall()}

            all_exist = True
            for table in required_tables:
                if table in existing_tables:
                    print(f"✅ {table}")
                else:
                    print(f"❌ {table} (missing)")
                    all_exist = False

            return all_exist

        except Exception as e:
            print(f"❌ Error checking tables: {e}")
            return False


async def main():
    """Run all verification checks."""
    print("\n" + "=" * 60)
    print("  Retinue Database Verification")
    print("=" * 60)

    results = {}

    # Run all checks
    results['migrations'] = await check_migrations()
    results['schema'] = await check_schema_columns()
    results['tables'] = await check_tables()
    results['reference'] = await check_reference_data()
    results['agents'] = await check_agents()

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    all_passed = all(results.values())

    if all_passed:
        print("\n✅ ALL CHECKS PASSED!")
        print("\nYour database is fully initialized and ready to use.")
        print("Start the server with:")
        print("  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        return 0
    else:
        print("\n⚠️  SOME CHECKS FAILED")
        print("\nNext steps based on what's missing:")

        if not results['migrations']:
            print("\n1. Apply migrations:")
            print("   alembic upgrade head")

        if not results['schema']:
            print("\n2. Verify migrations applied:")
            print("   alembic current")

        if not results['reference'] or not results['tables']:
            print("\n3. Initialize reference data:")
            print("   python -m app.scripts.init_database")

        if not results['agents']:
            print("\n4. Initialize agents:")
            print("   python -m app.scripts.init_agents")

        print("\nFor detailed help, see DATABASE_SETUP_GUIDE.md")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
