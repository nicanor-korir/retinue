"""Seed business knowledge documents.

This script populates the business_knowledge table with initial documents about:
- Retinue AI company overview
- Retinue system architecture
- Best practices for various roles
- Project management methodologies
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.db.database import get_session
from app.db.conversation_models import BusinessKnowledge
from app.services.business_domain_service import get_business_domain_service


# Business knowledge documents to seed
KNOWLEDGE_DOCUMENTS = [
    {
        "category": "company_info",
        "subcategory": "overview",
        "title": "Retinue AI Company Overview",
        "content": """# Retinue AI Company Overview

## Mission
Retinue AI delivers AI-powered business solutions that transform enterprise operations through intelligent automation and data-driven insights.

## Services
- Custom AI Agent Development: Building specialized AI agents for business workflows
- Business Process Automation: Streamlining operations with intelligent automation
- AI-Powered Analytics: Data-driven insights and predictive analytics
- Enterprise Integration Services: Seamless integration with existing systems

## Target Industries
- Financial Services: Risk assessment, fraud detection, automated trading
- Healthcare: Patient management, diagnostic assistance, workflow optimization
- Retail & E-commerce: Inventory management, customer insights, personalization
- Manufacturing: Supply chain optimization, quality control, predictive maintenance

## Methodology
We follow an agile approach with 2-week sprints, continuous client communication, and iterative delivery. Our focus is on rapid prototyping, user feedback integration, and scalable solutions.

## Values
- Innovation: Pushing boundaries of AI capabilities
- Quality: Delivering robust, reliable solutions
- Collaboration: Working closely with clients
- Transparency: Clear communication and expectations""",
        "summary": "Retinue AI delivers AI-powered business solutions through intelligent automation and data-driven insights.",
        "tags": ["company", "mission", "services", "values"]
    },
    {
        "category": "system_architecture",
        "subcategory": "overview",
        "title": "Retinue System Architecture Overview",
        "content": """# Retinue System Architecture

## Overview
Retinue is an AI-powered agent-based workflow system that automates project management and task execution through specialized AI agents.

## Core Components
1. **Agent System**: Specialized AI agents with defined roles and capabilities
2. **Project Management**: Automated project planning and breakdown
3. **Task Orchestration**: Intelligent task distribution and execution
4. **Communication Layer**: Inter-agent messaging and user interaction
5. **Knowledge Base**: RAG-powered context and learning system

## Agent Types
- **Project Manager**: Coordinates projects, manages timelines, stakeholder communication
- **Developer/Engineer**: Executes development tasks, writes code, implements features
- **QA Tester**: Tests deliverables, validates quality, reports issues
- **Designer**: Creates visual assets, designs interfaces, maintains brand consistency
- **HR Manager**: Monitors agent performance, intervenes when needed, optimizes workflows

## Workflow
1. User creates project with requirements
2. System selects appropriate agents based on deliverable type
3. Project Manager breaks down project into tasks
4. Tasks are assigned to specialized agents
5. Agents execute tasks with automatic dependency management
6. QA validates deliverables
7. Project is delivered to user

## Key Features
- Automated task breakdown and assignment
- Dependency management
- Escalation system for blockers
- Real-time progress tracking
- Context-aware agent collaboration""",
        "summary": "Retinue is an AI-powered agent-based workflow system for automated project management and task execution.",
        "tags": ["architecture", "agents", "workflow", "system"]
    },
    {
        "category": "best_practice",
        "subcategory": "project_management",
        "title": "Project Management Best Practices",
        "content": """# Project Management Best Practices at Retinue AI

## Planning Phase
- Define clear project objectives and success criteria
- Identify all stakeholders early in the process
- Create realistic timelines with buffer for unknowns (15-20%)
- Document assumptions and constraints
- Break down work into manageable milestones

## Execution Phase
- Maintain daily communication with team members
- Track progress against milestones regularly
- Proactively identify and mitigate risks
- Document all decisions and their rationale
- Keep stakeholders informed with regular updates

## Communication Guidelines
- Weekly status updates to all stakeholders
- Immediate escalation of blockers or critical issues
- Clear, concise written communication
- Regular team sync meetings (daily standups recommended)
- Document important discussions and decisions

## Quality Management
- Define quality standards upfront
- Implement review checkpoints at key milestones
- Collect feedback early and often
- Learn from past projects and apply lessons
- Maintain quality over rushing to deadline

## Risk Management
- Identify risks early in the project lifecycle
- Maintain a risk register with mitigation strategies
- Regular risk reviews (weekly for high-risk projects)
- Have contingency plans for critical paths
- Communicate risks to stakeholders transparently

## Timeline Management
- Use realistic estimates based on historical data
- Add buffer time for integration and testing
- Monitor actual vs. estimated hours
- Adjust timelines proactively when issues arise
- Never commit to impossible deadlines""",
        "summary": "Comprehensive project management best practices covering planning, execution, communication, quality, and risk management.",
        "tags": ["best_practice", "project_management", "planning", "execution", "quality"]
    },
    {
        "category": "best_practice",
        "subcategory": "software_development",
        "title": "Software Development Best Practices",
        "content": """# Software Development Best Practices

## Code Quality
- Write clean, readable code with clear naming conventions
- Follow established coding standards and style guides
- Keep functions small and focused (single responsibility)
- Comment complex logic, not obvious code
- Use meaningful variable and function names

## Testing
- Write unit tests for all business logic
- Aim for at least 80% code coverage
- Include integration tests for critical paths
- Test edge cases and error conditions
- Automate testing in CI/CD pipeline

## Version Control
- Make frequent, small commits with clear messages
- Use feature branches for new development
- Review code before merging to main
- Keep commits atomic and focused
- Tag releases appropriately

## Security
- Never commit secrets or credentials
- Validate all user inputs
- Use parameterized queries to prevent SQL injection
- Implement proper authentication and authorization
- Keep dependencies up to date

## Performance
- Profile before optimizing
- Optimize database queries
- Implement caching where appropriate
- Minimize network requests
- Use async operations for I/O-bound tasks

## Documentation
- Document API endpoints clearly
- Maintain up-to-date README files
- Document deployment procedures
- Keep architecture diagrams current
- Write clear commit messages""",
        "summary": "Essential software development best practices covering code quality, testing, version control, security, and performance.",
        "tags": ["best_practice", "development", "code_quality", "testing", "security"]
    },
    {
        "category": "methodology",
        "subcategory": "agile",
        "title": "Agile Development Methodology",
        "content": """# Agile Development Methodology at Retinue AI

## Sprint Structure
- 2-week sprints (standard duration)
- Sprint planning at the start
- Daily standups (15 minutes max)
- Sprint review/demo at the end
- Sprint retrospective for continuous improvement

## Sprint Planning
- Review and prioritize backlog
- Select work for the sprint
- Break down stories into tasks
- Estimate effort for each task
- Commit to sprint goals

## Daily Standups
- What did I complete yesterday?
- What will I work on today?
- Are there any blockers?
- Keep it brief and focused

## Sprint Review
- Demo completed work to stakeholders
- Gather feedback
- Discuss what was accomplished
- Adjust backlog based on feedback

## Retrospective
- What went well?
- What could be improved?
- Action items for next sprint
- Celebrate wins
- Address challenges

## Key Principles
- Deliver working software frequently
- Welcome changing requirements
- Business and developers work together daily
- Face-to-face communication when possible
- Reflect and adjust regularly""",
        "summary": "Agile development methodology with 2-week sprints, daily standups, and continuous improvement focus.",
        "tags": ["methodology", "agile", "sprint", "development_process"]
    }
]


async def seed_business_knowledge():
    """Seed business knowledge documents to database."""
    print("Seeding business knowledge documents...")

    async for db in get_session():
        try:
            documents_created = 0
            documents_skipped = 0

            for doc_data in KNOWLEDGE_DOCUMENTS:
                try:
                    # Check if document already exists
                    from sqlalchemy import select
                    result = await db.execute(
                        select(BusinessKnowledge).where(
                            BusinessKnowledge.title == doc_data["title"]
                        )
                    )
                    existing = result.scalar_one_or_none()

                    if existing:
                        print(f"✓ Document already exists: {doc_data['title']}")
                        documents_skipped += 1
                        continue

                    # Create new document
                    document = BusinessKnowledge(
                        category=doc_data["category"],
                        subcategory=doc_data.get("subcategory"),
                        title=doc_data["title"],
                        content=doc_data["content"],
                        summary=doc_data.get("summary"),
                        tags=doc_data.get("tags", []),
                        is_active=True,
                        created_at=datetime.utcnow()
                    )

                    db.add(document)
                    await db.commit()
                    await db.refresh(document)

                    print(f"✓ Created document: {doc_data['title']}")
                    print(f"  - ID: {document.document_id}")
                    print(f"  - Category: {document.category}")

                    documents_created += 1

                    # TODO: Index to RAG (will be done by background worker in production)
                    # For now, we can index manually after this script
                    # business_service = get_business_domain_service()
                    # await business_service.index_business_knowledge(...)

                except Exception as e:
                    print(f"✗ Error creating document {doc_data['title']}: {e}")
                    await db.rollback()
                    continue

            print("\n" + "="*60)
            print("Business Knowledge Seeding Complete")
            print("="*60)
            print(f"Documents created: {documents_created}")
            print(f"Documents skipped: {documents_skipped}")
            print(f"Total documents: {len(KNOWLEDGE_DOCUMENTS)}")

            if documents_created > 0:
                print("\nNext step: Index documents to RAG vector store")
                print("Run: python scripts/index_business_knowledge_to_rag.py")

            # Only process one session
            break

        except Exception as e:
            print(f"Error during seeding: {e}")
            await db.rollback()
            break


def main():
    """Main entry point."""
    print("="*60)
    print("Business Knowledge Seeding Script")
    print("="*60)
    print(f"Documents to seed: {len(KNOWLEDGE_DOCUMENTS)}")
    print("="*60)

    # Run async seeding
    asyncio.run(seed_business_knowledge())


if __name__ == "__main__":
    main()
