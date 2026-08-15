"""
Backfill script to index historical data into RAG knowledge base.

This script indexes tasks, decisions, and messages from the last 3 months
into the RAG vector database for semantic search and context retrieval.

Usage:
    python -m app.scripts.backfill_rag_data [--limit N] [--days D]

Options:
    --limit N    Limit to N records per entity type (default: all)
    --days D     Only index records from last D days (default: 90)
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from typing import List, Optional
import argparse

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import AsyncSessionLocal, init_db
from app.db.models import Task, Decision, Message, TaskStatus
from app.services.rag_service import get_rag_service

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


async def backfill_tasks(
    session: AsyncSession,
    rag_service,
    limit: Optional[int] = None,
    days: int = 90,
) -> int:
    """
    Backfill tasks from the last N days.

    Args:
        session: Database session
        rag_service: RAG service instance
        limit: Maximum number of tasks to index
        days: Number of days to look back

    Returns:
        Number of tasks indexed
    """
    logger.info(f"🔄 Backfilling tasks from last {days} days...")

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Query completed or review tasks from last N days
    stmt = select(Task).where(
        and_(
            Task.created_at >= cutoff_date,
            Task.status.in_([TaskStatus.COMPLETED, TaskStatus.REVIEW])
        )
    )

    if limit:
        stmt = stmt.limit(limit)

    result = await session.execute(stmt)
    tasks = result.scalars().all()

    logger.info(f"Found {len(tasks)} tasks to index")

    indexed_count = 0
    for i, task in enumerate(tasks, 1):
        try:
            await rag_service.index_task(
                task_id=str(task.task_id),
                title=task.title,
                description=task.description or "",
                output=task.output or {},
                completion_notes=task.completion_notes or "",
                agent_id=str(task.assigned_to) if task.assigned_to else "unknown",
                project_id=str(task.project_id),
                status=task.status.value if task.status else "unknown",
            )
            indexed_count += 1

            if i % 10 == 0:
                logger.info(f"  ✓ Indexed {i}/{len(tasks)} tasks")
        except Exception as e:
            logger.warning(f"Failed to index task {task.task_id}: {e}")

    logger.info(f"✅ Indexed {indexed_count}/{len(tasks)} tasks")
    return indexed_count


async def backfill_decisions(
    session: AsyncSession,
    rag_service,
    limit: Optional[int] = None,
    days: int = 90,
) -> int:
    """
    Backfill decisions from the last N days.

    Args:
        session: Database session
        rag_service: RAG service instance
        limit: Maximum number of decisions to index
        days: Number of days to look back

    Returns:
        Number of decisions indexed
    """
    logger.info(f"🔄 Backfilling decisions from last {days} days...")

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Query decisions from last N days
    stmt = select(Decision).where(Decision.created_at >= cutoff_date)

    if limit:
        stmt = stmt.limit(limit)

    result = await session.execute(stmt)
    decisions = result.scalars().all()

    logger.info(f"Found {len(decisions)} decisions to index")

    indexed_count = 0
    for i, decision in enumerate(decisions, 1):
        try:
            await rag_service.index_decision(
                decision_id=str(decision.decision_id),
                question=decision.decision_type or "unknown",
                decision=decision.decision or "",
                rationale=decision.rationale or "",
                decision_type=decision.decision_type or "unknown",
                agent_id=str(decision.made_by_agent_id),
                project_id=str(decision.project_id),
                approved=decision.approved if decision.approved is not None else False,
            )
            indexed_count += 1

            if i % 10 == 0:
                logger.info(f"  ✓ Indexed {i}/{len(decisions)} decisions")
        except Exception as e:
            logger.warning(f"Failed to index decision {decision.decision_id}: {e}")

    logger.info(f"✅ Indexed {indexed_count}/{len(decisions)} decisions")
    return indexed_count


async def backfill_messages(
    session: AsyncSession,
    rag_service,
    limit: Optional[int] = None,
    days: int = 90,
) -> int:
    """
    Backfill messages from the last N days.

    Args:
        session: Database session
        rag_service: RAG service instance
        limit: Maximum number of messages to index
        days: Number of days to look back

    Returns:
        Number of messages indexed
    """
    logger.info(f"🔄 Backfilling messages from last {days} days...")

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Query messages from last N days
    stmt = select(Message).where(Message.created_at >= cutoff_date)

    if limit:
        stmt = stmt.limit(limit)

    result = await session.execute(stmt)
    messages = result.scalars().all()

    logger.info(f"Found {len(messages)} messages to index")

    indexed_count = 0
    for i, message in enumerate(messages, 1):
        try:
            await rag_service.index_message(
                message_id=str(message.message_id),
                content=message.content or "",
                from_agent_id=str(message.from_agent_id),
                to_agent_id=str(message.to_agent_id) if message.to_agent_id else "broadcast",
                message_type=message.message_type.value if message.message_type else "info",
                project_id=str(message.project_id) if message.project_id else None,
                task_id=str(message.task_id) if message.task_id else None,
            )
            indexed_count += 1

            if i % 25 == 0:
                logger.info(f"  ✓ Indexed {i}/{len(messages)} messages")
        except Exception as e:
            logger.warning(f"Failed to index message {message.message_id}: {e}")

    logger.info(f"✅ Indexed {indexed_count}/{len(messages)} messages")
    return indexed_count


async def main():
    """Main backfill function."""
    parser = argparse.ArgumentParser(
        description="Backfill RAG knowledge base with historical data"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of records to index per entity type",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=90,
        help="Number of days to look back (default: 90)",
    )

    args = parser.parse_args()

    try:
        logger.info("🚀 Starting RAG data backfill...")
        logger.info(f"   Looking back {args.days} days")
        if args.limit:
            logger.info(f"   Limiting to {args.limit} records per type")

        # Initialize database
        await init_db()

        # Get RAG service
        rag_service = get_rag_service()

        # Create session
        async with AsyncSessionLocal() as session:
            # Backfill each entity type
            tasks_indexed = await backfill_tasks(session, rag_service, args.limit, args.days)
            decisions_indexed = await backfill_decisions(session, rag_service, args.limit, args.days)
            messages_indexed = await backfill_messages(session, rag_service, args.limit, args.days)

        total_indexed = tasks_indexed + decisions_indexed + messages_indexed
        logger.info(f"\n✨ Backfill complete!")
        logger.info(f"   Tasks:     {tasks_indexed}")
        logger.info(f"   Decisions: {decisions_indexed}")
        logger.info(f"   Messages:  {messages_indexed}")
        logger.info(f"   Total:     {total_indexed} records indexed")

        # Get RAG stats
        stats = await rag_service.get_stats()
        logger.info(f"\n📊 RAG Knowledge Base Stats:")
        for entity_type, count in stats.items():
            logger.info(f"   {entity_type}: {count}")

    except Exception as e:
        logger.error(f"❌ Backfill failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
