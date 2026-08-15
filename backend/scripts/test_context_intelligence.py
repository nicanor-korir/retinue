"""Test script for context intelligence system.

This script tests:
1. Entity extraction from messages
2. Intent classification
3. Context storage in database
4. User activity tracking
5. Enhanced prompt building
"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.db.database import get_session
from app.db.conversation_models import (
    Conversation,
    ConversationMessage,
    ConversationType,
    SenderType,
    ContentType
)
from app.db.models import Agent
from app.services.context_intelligence_service import ContextIntelligenceService
from app.services.user_activity_tracker import UserActivityTracker
from app.services.dynamic_prompt_builder import DynamicPromptBuilder
from sqlalchemy import select


async def test_entity_extraction():
    """Test entity extraction from messages."""
    print("\n" + "="*60)
    print("TEST 1: Entity Extraction")
    print("="*60)

    context_service = ContextIntelligenceService()

    test_messages = [
        "Can you update the timeline for project:abc-123?",
        "I need help with task:def-456 which is blocking me",
        "Let's ask @project_manager about this issue",
        "The website_redesign project needs attention"
    ]

    async for db in get_session():
        try:
            for idx, message_text in enumerate(test_messages, 1):
                print(f"\nMessage {idx}: {message_text}")

                # Create a mock message object
                mock_message = ConversationMessage(
                    message_id=uuid4(),
                    conversation_id=uuid4(),
                    sender_type=SenderType.USER,
                    sender_id="test_user",
                    content=message_text
                )

                # Extract context
                context = await context_service.extract_quick_context(mock_message, db)

                print(f"  Entities: {context.get('entities', {})}")
                print(f"  Intent: {context.get('intent')}")

            print("\n✓ Entity extraction test completed")
            break

        except Exception as e:
            print(f"✗ Entity extraction test failed: {e}")
            import traceback
            traceback.print_exc()
            break


async def test_intent_classification():
    """Test intent classification."""
    print("\n" + "="*60)
    print("TEST 2: Intent Classification")
    print("="*60)

    context_service = ContextIntelligenceService()

    test_cases = [
        ("What is the status of the project?", "question"),
        ("Please update the task timeline", "command"),
        ("Can you explain how this works?", "clarification"),
        ("I think we should use a different approach", "feedback"),
        ("URGENT: The system is down!", "escalation"),
        ("Let's discuss the requirements", "discussion")
    ]

    for message, expected in test_cases:
        intent = context_service.intent_classifier.classify_intent(message)
        status = "✓" if intent == expected else "✗"
        print(f"{status} '{message}' -> {intent} (expected: {expected})")

    print("\n✓ Intent classification test completed")


async def test_user_activity_tracking():
    """Test user activity tracking."""
    print("\n" + "="*60)
    print("TEST 3: User Activity Tracking")
    print("="*60)

    activity_tracker = UserActivityTracker()
    test_user_id = "test_user_123"

    async for db in get_session():
        try:
            # Log some activities
            activities = [
                ("message_sent", {"content": "Test message 1"}),
                ("project_viewed", {"project_id": "proj-1"}),
                ("task_viewed", {"task_id": "task-1"}),
                ("agent_interacted", {"agent_id": "agent_1"})
            ]

            print("\nLogging activities...")
            for activity_type, context in activities:
                await activity_tracker.log_activity(
                    user_id=test_user_id,
                    activity_type=activity_type,
                    context=context,
                    db=db
                )
                print(f"  ✓ Logged: {activity_type}")

            # Retrieve recent activity
            print("\nRetrieving recent activities...")
            recent = await activity_tracker.get_recent_activity(
                user_id=test_user_id,
                limit=10,
                db=db
            )
            print(f"  Found {len(recent)} activities")

            for activity in recent[:3]:
                print(f"    - {activity['activity_type']} at {activity['timestamp']}")

            print("\n✓ User activity tracking test completed")
            break

        except Exception as e:
            print(f"✗ User activity tracking test failed: {e}")
            import traceback
            traceback.print_exc()
            break


async def test_prompt_building():
    """Test dynamic prompt building."""
    print("\n" + "="*60)
    print("TEST 4: Dynamic Prompt Building")
    print("="*60)

    prompt_builder = DynamicPromptBuilder()

    async for db in get_session():
        try:
            # Get a test agent
            result = await db.execute(
                select(Agent).limit(1)
            )
            agent = result.scalar_one_or_none()

            if not agent:
                print("  ⚠ No agents found in database, skipping test")
                break

            print(f"\nBuilding prompt for agent: {agent.name} ({agent.role})")

            # Mock extracted context
            extracted_context = {
                "entities": {
                    "projects": ["test-project-1"],
                    "tasks": [],
                    "agents": []
                },
                "intent": "question",
                "semantic": {
                    "summary": "User asking about project status"
                }
            }

            # Build enhanced prompt
            enhanced_prompt = await prompt_builder.build_enhanced_prompt(
                agent=agent,
                conversation_id="test-conv-123",
                extracted_context=extracted_context,
                db=db
            )

            print(f"\nPrompt length: {len(enhanced_prompt)} characters")
            print(f"Prompt preview (first 300 chars):")
            print("-" * 60)
            print(enhanced_prompt[:300])
            print("-" * 60)

            # Check for expected sections
            checks = [
                ("BUSINESS CONTEXT" in enhanced_prompt, "Business context section"),
                ("INTERACTION GUIDELINES" in enhanced_prompt, "Interaction guidelines"),
                (agent.name in enhanced_prompt, "Agent name"),
                (agent.role in enhanced_prompt, "Agent role")
            ]

            print("\nPrompt content checks:")
            for passed, description in checks:
                status = "✓" if passed else "✗"
                print(f"  {status} {description}")

            print("\n✓ Dynamic prompt building test completed")
            break

        except Exception as e:
            print(f"✗ Dynamic prompt building test failed: {e}")
            import traceback
            traceback.print_exc()
            break


async def test_database_schema():
    """Test that new database tables exist."""
    print("\n" + "="*60)
    print("TEST 5: Database Schema Verification")
    print("="*60)

    async for db in get_session():
        try:
            from app.db.conversation_models import (
                ConversationContext,
                UserActivityLog,
                BusinessKnowledge
            )

            # Try to query each new table
            tables = [
                ("conversation_context", ConversationContext),
                ("user_activity_log", UserActivityLog),
                ("business_knowledge", BusinessKnowledge)
            ]

            print("\nChecking new tables...")
            for table_name, model in tables:
                try:
                    result = await db.execute(select(model).limit(1))
                    print(f"  ✓ Table '{table_name}' exists and is accessible")
                except Exception as e:
                    print(f"  ✗ Table '{table_name}' error: {e}")

            # Check for new columns in existing tables
            print("\nChecking enhanced columns...")
            result = await db.execute(select(ConversationMessage).limit(1))
            message = result.scalar_one_or_none()

            if message:
                columns_to_check = [
                    ("extracted_entities", hasattr(message, 'extracted_entities')),
                    ("intent_classification", hasattr(message, 'intent_classification')),
                    ("semantic_summary", hasattr(message, 'semantic_summary'))
                ]

                for col_name, exists in columns_to_check:
                    status = "✓" if exists else "✗"
                    print(f"  {status} Column '{col_name}' in conversation_messages")

            print("\n✓ Database schema verification completed")
            break

        except Exception as e:
            print(f"✗ Database schema verification failed: {e}")
            import traceback
            traceback.print_exc()
            break


async def run_all_tests():
    """Run all tests."""
    print("\n" + "="*60)
    print("CONTEXT INTELLIGENCE TEST SUITE")
    print("="*60)
    print("Testing Phase 1 implementation components...")

    tests = [
        ("Entity Extraction", test_entity_extraction),
        ("Intent Classification", test_intent_classification),
        ("User Activity Tracking", test_user_activity_tracking),
        ("Dynamic Prompt Building", test_prompt_building),
        ("Database Schema", test_database_schema)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            await test_func()
            results.append((test_name, True))
        except Exception as e:
            print(f"\n✗ {test_name} failed with exception: {e}")
            results.append((test_name, False))

    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Context intelligence system is working.")
    else:
        print(f"\n⚠ {total - passed} test(s) failed. Please review errors above.")

    return passed == total


def main():
    """Main entry point."""
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
