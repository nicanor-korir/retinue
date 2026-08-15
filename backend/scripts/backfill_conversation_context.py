"""Backfill context intelligence for existing conversations.

This script processes existing conversations and messages to extract context,
enabling context intelligence on historical data.

Features:
- Batch processing with configurable batch size
- Progress tracking
- Error handling and retry logic
- Dry-run mode for testing
- Conversation filtering by date
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.db.database import get_session
from app.db.conversation_models import Conversation, ConversationMessage, ConversationContext
from app.services.context_intelligence_service import ContextIntelligenceService
from sqlalchemy import select, func, and_
import argparse


class ConversationBackfiller:
    """Backfill context intelligence for existing conversations."""

    def __init__(self, batch_size: int = 10, dry_run: bool = False):
        """
        Initialize backfiller.

        Args:
            batch_size: Number of conversations to process in each batch
            dry_run: If True, don't commit changes to database
        """
        self.batch_size = batch_size
        self.dry_run = dry_run
        self.context_service = ContextIntelligenceService()

        # Statistics
        self.stats = {
            "conversations_processed": 0,
            "conversations_skipped": 0,
            "messages_processed": 0,
            "messages_skipped": 0,
            "errors": 0
        }

    async def backfill_all(
        self,
        days_back: Optional[int] = None,
        conversation_limit: Optional[int] = None
    ):
        """
        Backfill context for all conversations.

        Args:
            days_back: Only process conversations from last N days (None = all)
            conversation_limit: Maximum number of conversations to process
        """
        print("="*70)
        print("CONVERSATION CONTEXT BACKFILL")
        print("="*70)
        print(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE'}")
        print(f"Batch size: {self.batch_size}")
        if days_back:
            print(f"Date filter: Last {days_back} days")
        if conversation_limit:
            print(f"Conversation limit: {conversation_limit}")
        print("="*70)

        async for db in get_session():
            try:
                # Build query
                query = select(Conversation).where(
                    Conversation.status == "active"
                )

                # Add date filter if specified
                if days_back:
                    cutoff_date = datetime.utcnow() - timedelta(days=days_back)
                    query = query.where(Conversation.created_at >= cutoff_date)

                # Order by creation date
                query = query.order_by(Conversation.created_at.desc())

                # Apply limit if specified
                if conversation_limit:
                    query = query.limit(conversation_limit)

                # Get conversations
                result = await db.execute(query)
                conversations = result.scalars().all()

                total_conversations = len(conversations)
                print(f"\nFound {total_conversations} conversations to process")

                if total_conversations == 0:
                    print("No conversations to process")
                    return

                # Process in batches
                for i in range(0, total_conversations, self.batch_size):
                    batch = conversations[i:i + self.batch_size]
                    batch_num = (i // self.batch_size) + 1
                    total_batches = (total_conversations + self.batch_size - 1) // self.batch_size

                    print(f"\n--- Batch {batch_num}/{total_batches} ---")

                    for conv in batch:
                        await self._process_conversation(conv, db)

                    # Commit batch (if not dry run)
                    if not self.dry_run:
                        await db.commit()
                        print(f"✓ Batch {batch_num} committed to database")
                    else:
                        await db.rollback()
                        print(f"✓ Batch {batch_num} processed (dry run - not committed)")

                # Print final statistics
                self._print_statistics()

                break

            except Exception as e:
                print(f"\n✗ Fatal error during backfill: {e}")
                import traceback
                traceback.print_exc()
                await db.rollback()
                break

    async def _process_conversation(self, conversation: Conversation, db):
        """Process a single conversation."""
        try:
            conv_id = str(conversation.conversation_id)
            print(f"\nProcessing conversation: {conv_id}")
            print(f"  Type: {conversation.conversation_type}")
            print(f"  Created: {conversation.created_at}")

            # Check if conversation already has context
            result = await db.execute(
                select(ConversationContext).where(
                    ConversationContext.conversation_id == conversation.conversation_id
                )
            )
            existing_context = result.scalar_one_or_none()

            if existing_context and existing_context.indexed_message_count > 0:
                print(f"  ⊘ Skipping (already has context with {existing_context.indexed_message_count} messages)")
                self.stats["conversations_skipped"] += 1
                return

            # Get messages for this conversation
            result = await db.execute(
                select(ConversationMessage).where(
                    ConversationMessage.conversation_id == conversation.conversation_id
                ).order_by(ConversationMessage.created_at)
            )
            messages = result.scalars().all()

            if not messages:
                print(f"  ⊘ No messages found")
                self.stats["conversations_skipped"] += 1
                return

            print(f"  Found {len(messages)} messages")

            # Process messages
            processed_count = 0
            skipped_count = 0

            # Aggregate entities across all messages
            all_entities = {"projects": set(), "tasks": set(), "agents": set()}
            intents = []

            for message in messages:
                try:
                    # Skip if already has extracted entities
                    if message.extracted_entities:
                        skipped_count += 1
                        continue

                    # Extract deep context
                    context = await self.context_service.extract_deep_context(message, db)

                    # Update message
                    message.extracted_entities = context.get("entities", {})
                    message.intent_classification = context.get("intent")
                    message.semantic_summary = context.get("semantic", {}).get("summary")

                    # Aggregate for conversation context
                    entities = context.get("entities", {})
                    for entity_type in ["projects", "tasks", "agents"]:
                        if entity_type in entities:
                            all_entities[entity_type].update(entities[entity_type])

                    if context.get("intent"):
                        intents.append(context.get("intent"))

                    processed_count += 1
                    self.stats["messages_processed"] += 1

                except Exception as e:
                    print(f"    ✗ Error processing message {message.message_id}: {e}")
                    self.stats["errors"] += 1
                    continue

            # Update or create conversation context
            if processed_count > 0:
                # Convert sets to lists
                entities_dict = {k: list(v) for k, v in all_entities.items()}

                # Find dominant intent
                dominant_intent = max(set(intents), key=intents.count) if intents else None

                if existing_context:
                    # Update existing
                    existing_context.entities = entities_dict
                    existing_context.dominant_intent = dominant_intent
                    existing_context.indexed_message_count = processed_count
                    existing_context.last_indexed_at = datetime.utcnow()
                else:
                    # Create new
                    new_context = ConversationContext(
                        conversation_id=conversation.conversation_id,
                        entities=entities_dict,
                        dominant_intent=dominant_intent,
                        indexed_message_count=processed_count,
                        last_indexed_at=datetime.utcnow()
                    )
                    db.add(new_context)

            print(f"  ✓ Processed {processed_count} messages, skipped {skipped_count}")
            self.stats["conversations_processed"] += 1
            self.stats["messages_skipped"] += skipped_count

        except Exception as e:
            print(f"  ✗ Error processing conversation {conversation.conversation_id}: {e}")
            self.stats["errors"] += 1

    def _print_statistics(self):
        """Print final statistics."""
        print("\n" + "="*70)
        print("BACKFILL STATISTICS")
        print("="*70)
        print(f"Conversations processed: {self.stats['conversations_processed']}")
        print(f"Conversations skipped:   {self.stats['conversations_skipped']}")
        print(f"Messages processed:      {self.stats['messages_processed']}")
        print(f"Messages skipped:        {self.stats['messages_skipped']}")
        print(f"Errors encountered:      {self.stats['errors']}")
        print("="*70)

        if self.dry_run:
            print("\n⚠ DRY RUN MODE: No changes were committed to database")
        else:
            print("\n✓ Changes committed to database")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Backfill context intelligence for existing conversations"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of conversations to process in each batch (default: 10)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without committing changes to database"
    )
    parser.add_argument(
        "--days-back",
        type=int,
        help="Only process conversations from last N days (default: all)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of conversations to process (default: all)"
    )

    args = parser.parse_args()

    backfiller = ConversationBackfiller(
        batch_size=args.batch_size,
        dry_run=args.dry_run
    )

    await backfiller.backfill_all(
        days_back=args.days_back,
        conversation_limit=args.limit
    )


if __name__ == "__main__":
    asyncio.run(main())
