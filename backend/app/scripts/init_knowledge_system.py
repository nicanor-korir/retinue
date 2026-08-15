"""
Initialize Intelligent Knowledge Base System

Sets up default categories, creates initial knowledge entries,
and verifies system functionality.
"""

import asyncio
import logging
import sys
import uuid
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import async_session_maker
from app.db.knowledge_models import (
    KnowledgeCategory,
    KnowledgeEntry,
    KnowledgeEntryType,
    ValidationStatus,
    KnowledgeStatus
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_default_categories(db: AsyncSession) -> None:
    """Create default knowledge categories."""
    logger.info("Creating default knowledge categories...")

    categories = [
        # Top-level categories
        {
            "name": "Technical",
            "slug": "technical",
            "description": "Technical knowledge including code, architecture, and infrastructure",
            "level": 0,
            "path": ["technical"],
            "icon": "code",
            "color": "#3B82F6"
        },
        {
            "name": "Business",
            "slug": "business",
            "description": "Business processes, strategy, and requirements",
            "level": 0,
            "path": ["business"],
            "icon": "briefcase",
            "color": "#8B5CF6"
        },
        {
            "name": "Process",
            "slug": "process",
            "description": "Workflows, procedures, and operational processes",
            "level": 0,
            "path": ["process"],
            "icon": "workflow",
            "color": "#10B981"
        },
        {
            "name": "User Preferences",
            "slug": "user-preferences",
            "description": "User-specific preferences and communication styles",
            "level": 0,
            "path": ["user-preferences"],
            "icon": "user",
            "color": "#F59E0B"
        },
        # Technical sub-categories
        {
            "name": "Backend",
            "slug": "technical-backend",
            "description": "Backend development patterns and practices",
            "level": 1,
            "path": ["technical", "backend"],
            "icon": "server",
            "color": "#3B82F6",
            "parent_slug": "technical"
        },
        {
            "name": "Frontend",
            "slug": "technical-frontend",
            "description": "Frontend development and UI patterns",
            "level": 1,
            "path": ["technical", "frontend"],
            "icon": "layout",
            "color": "#3B82F6",
            "parent_slug": "technical"
        },
        {
            "name": "Database",
            "slug": "technical-database",
            "description": "Database design and optimization",
            "level": 1,
            "path": ["technical", "database"],
            "icon": "database",
            "color": "#3B82F6",
            "parent_slug": "technical"
        },
        {
            "name": "DevOps",
            "slug": "technical-devops",
            "description": "Deployment, infrastructure, and operations",
            "level": 1,
            "path": ["technical", "devops"],
            "icon": "cloud",
            "color": "#3B82F6",
            "parent_slug": "technical"
        },
    ]

    # Create categories with parent resolution
    created_categories = {}

    # First pass: create top-level categories
    for cat_data in categories:
        if cat_data["level"] == 0:
            category = KnowledgeCategory(
                category_id=uuid.uuid4(),
                name=cat_data["name"],
                slug=cat_data["slug"],
                description=cat_data["description"],
                level=cat_data["level"],
                path=cat_data["path"],
                icon=cat_data.get("icon"),
                color=cat_data.get("color"),
                display_order=len(created_categories)
            )

            db.add(category)
            created_categories[cat_data["slug"]] = category

    await db.flush()

    # Second pass: create sub-categories with parent references
    for cat_data in categories:
        if cat_data["level"] > 0:
            parent_slug = cat_data.get("parent_slug")
            parent_category = created_categories.get(parent_slug)

            category = KnowledgeCategory(
                category_id=uuid.uuid4(),
                name=cat_data["name"],
                slug=cat_data["slug"],
                description=cat_data["description"],
                level=cat_data["level"],
                path=cat_data["path"],
                parent_category_id=parent_category.category_id if parent_category else None,
                icon=cat_data.get("icon"),
                color=cat_data.get("color"),
                display_order=len(created_categories)
            )

            db.add(category)
            created_categories[cat_data["slug"]] = category

    await db.commit()

    logger.info(f"Created {len(created_categories)} knowledge categories")


async def create_seed_knowledge(db: AsyncSession) -> None:
    """Create seed knowledge entries."""
    logger.info("Creating seed knowledge entries...")

    # Get categories
    query = select(KnowledgeCategory)
    result = await db.execute(query)
    categories = {cat.slug: cat for cat in result.scalars().all()}

    seed_entries = [
        {
            "title": "API Design Best Practices",
            "summary": "Guidelines for designing RESTful APIs with proper versioning, error handling, and documentation.",
            "content": """# API Design Best Practices

## Key Principles

1. **Use RESTful conventions**: GET for retrieval, POST for creation, PUT for updates, DELETE for removal
2. **Version your API**: Use URL versioning (e.g., /api/v1/) for breaking changes
3. **Proper error handling**: Return meaningful HTTP status codes and error messages
4. **Authentication**: Implement proper authentication (JWT, OAuth) for secure endpoints
5. **Rate limiting**: Protect your API from abuse with rate limiting
6. **Documentation**: Use OpenAPI/Swagger for comprehensive API documentation

## Example

```python
@router.post("/api/v1/users", status_code=201)
async def create_user(user: UserCreate, db: Session):
    # Validation
    if await db.get(User, user.email):
        raise HTTPException(status_code=409, detail="User already exists")

    # Creation
    new_user = User(**user.dict())
    db.add(new_user)
    await db.commit()

    return new_user
```

## Common Pitfalls

- Not handling errors properly
- Exposing internal implementation details
- Inconsistent naming conventions
- Missing authentication on sensitive endpoints
""",
            "entry_type": KnowledgeEntryType.BEST_PRACTICE,
            "category_slug": "technical-backend",
            "tags": ["api", "rest", "backend", "best-practice"],
            "domain": "technical"
        },
        {
            "title": "Database Connection Pooling",
            "summary": "Understanding and implementing connection pooling for optimal database performance.",
            "content": """# Database Connection Pooling

Connection pooling reuses database connections instead of creating new ones for each query, significantly improving performance.

## Benefits

- **Reduced overhead**: Avoid connection creation/destruction costs
- **Better resource management**: Control max connections
- **Improved performance**: Faster query execution

## Implementation (SQLAlchemy)

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    "postgresql://user:pass@localhost/db",
    poolclass=QueuePool,
    pool_size=20,  # Normal connections
    max_overflow=10,  # Extra connections when needed
    pool_timeout=30,  # Wait time for connection
    pool_recycle=3600  # Recycle connections every hour
)
```

## Best Practices

- Set `pool_size` based on concurrent users
- Monitor connection usage
- Use `pool_recycle` to avoid stale connections
- Handle connection errors gracefully
""",
            "entry_type": KnowledgeEntryType.TECHNICAL_INSIGHT,
            "category_slug": "technical-database",
            "tags": ["database", "performance", "postgresql", "sqlalchemy"],
            "domain": "technical"
        },
        {
            "title": "User Prefers Concise Responses",
            "summary": "This user prefers brief, to-the-point responses without excessive detail.",
            "content": """User communication preference: concise and direct.

- Keep responses brief
- Focus on actionable information
- Avoid lengthy explanations unless asked
- Use bullet points for clarity
""",
            "entry_type": KnowledgeEntryType.PREFERENCE,
            "category_slug": "user-preferences",
            "tags": ["communication", "user-preference", "concise"],
            "domain": "user"
        },
        {
            "title": "Code Review Checklist",
            "summary": "Standard checklist for code review to ensure quality and consistency.",
            "content": """# Code Review Checklist

## Functionality
- [ ] Code does what it's supposed to do
- [ ] Edge cases are handled
- [ ] Error handling is appropriate

## Code Quality
- [ ] Code is readable and self-documenting
- [ ] No code duplication (DRY principle)
- [ ] Functions are single-purpose (SRP)
- [ ] Variable names are descriptive
- [ ] Comments explain "why", not "what"

## Testing
- [ ] Unit tests are included
- [ ] Tests cover edge cases
- [ ] Tests are meaningful and maintainable

## Security
- [ ] No sensitive data in code
- [ ] Input validation is present
- [ ] SQL injection prevention
- [ ] XSS prevention for user input

## Performance
- [ ] No obvious performance issues
- [ ] Database queries are optimized
- [ ] No N+1 query problems

## Style
- [ ] Follows project style guide
- [ ] Code is properly formatted
- [ ] No linting errors
""",
            "entry_type": KnowledgeEntryType.STANDARD,
            "category_slug": "process",
            "tags": ["code-review", "quality", "checklist", "standard"],
            "domain": "process"
        },
    ]

    for entry_data in seed_entries:
        category = categories.get(entry_data["category_slug"])

        entry = KnowledgeEntry(
            entry_id=uuid.uuid4(),
            title=entry_data["title"],
            summary=entry_data["summary"],
            content=entry_data["content"],
            content_format="markdown",
            entry_type=entry_data["entry_type"],
            primary_category_id=category.category_id if category else None,
            tags=entry_data["tags"],
            domain=entry_data["domain"],
            confidence_score=0.9,
            novelty_score=0.5,
            relevance_score=0.8,
            quality_score=0.85,
            validation_status=ValidationStatus.ORGANIZATIONAL_STANDARD,
            source_type="manual",
            created_by_type="system",
            created_by_id="init_script",
            status=KnowledgeStatus.ACTIVE,
            version=1
        )

        db.add(entry)

        # Update category entry count
        if category:
            category.entry_count += 1

    await db.commit()

    logger.info(f"Created {len(seed_entries)} seed knowledge entries")


async def verify_system(db: AsyncSession) -> None:
    """Verify knowledge system is working."""
    logger.info("Verifying knowledge system...")

    # Check categories
    query = select(KnowledgeCategory)
    result = await db.execute(query)
    categories = result.scalars().all()
    logger.info(f"✓ Found {len(categories)} categories")

    # Check entries
    query = select(KnowledgeEntry)
    result = await db.execute(query)
    entries = result.scalars().all()
    logger.info(f"✓ Found {len(entries)} knowledge entries")

    # Test search (basic)
    from app.services.knowledge_repository_service import get_knowledge_repository_service

    repository = get_knowledge_repository_service()

    try:
        results = await repository.hybrid_search(
            db=db,
            query="API design",
            top_k=5
        )
        logger.info(f"✓ Search working: found {len(results)} results for 'API design'")
    except Exception as e:
        logger.error(f"✗ Search failed: {e}")

    logger.info("✓ Knowledge system verification complete")


async def main():
    """Main initialization function."""
    logger.info("===== Initializing Intelligent Knowledge Base System =====")

    try:
        async with async_session_maker() as db:
            # Create default categories
            await create_default_categories(db)

            # Create seed knowledge
            await create_seed_knowledge(db)

            # Verify system
            await verify_system(db)

        logger.info("===== Knowledge system initialized successfully! =====")

    except Exception as e:
        logger.error(f"Error initializing knowledge system: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
