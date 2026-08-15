"""Business Domain Service for accessing and integrating business knowledge.

This service provides access to Deviant AI/Deviant business domain knowledge including:
- Company information and services
- Deviant system architecture and workflows
- Best practices and methodologies
- Agent expertise and capabilities
"""

from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Agent
from app.db.conversation_models import BusinessKnowledge
from app.services.rag_service import RAGService


class BusinessDomainService:
    """Service for business domain knowledge."""

    def __init__(self, rag_service: Optional[RAGService] = None):
        """
        Initialize business domain service.

        Args:
            rag_service: Optional RAG service instance (creates new if not provided)
        """
        self.rag_service = rag_service or RAGService()

    async def get_relevant_knowledge(
        self,
        query: str,
        limit: int = 5,
        category: Optional[str] = None
    ) -> List[Dict]:
        """
        Retrieve relevant business knowledge.

        Args:
            query: Query string (e.g., "Project Manager best practices")
            limit: Number of results to return
            category: Filter by category (optional)

        Returns:
            List of knowledge documents with title, summary, content
        """
        try:
            # Build filter based on category
            filters = {}
            if category:
                filters["category"] = category

            # Retrieve from RAG
            results = await self.rag_service.retrieve_context(
                query=query,
                collections=["business_knowledge"],
                top_k=limit
            )

            # Extract and format results
            knowledge_docs = []
            if "business_knowledge" in results:
                for result in results["business_knowledge"]:
                    knowledge_docs.append({
                        "title": result.get("metadata", {}).get("title", ""),
                        "summary": result.get("metadata", {}).get("summary", ""),
                        "content": result.get("document", ""),
                        "category": result.get("metadata", {}).get("category", ""),
                        "relevance_score": result.get("score", 0.0)
                    })

            return knowledge_docs

        except Exception as e:
            # If RAG fails, return empty (service should be resilient)
            return []

    async def get_agent_expertise(
        self,
        agent_id: str,
        db: AsyncSession
    ) -> Dict:
        """
        Get agent's expertise areas and best practices.

        Args:
            agent_id: The agent ID
            db: Database session

        Returns:
            {
                "specializations": ["area1", "area2"],
                "best_practices": ["practice1", "practice2"],
                "methodologies": ["method1", "method2"],
                "role_description": "..."
            }
        """
        try:
            # Get agent from DB
            agent = await self._get_agent(agent_id, db)
            if not agent:
                return {}

            # Get all departments for multi-department support
            departments = agent.all_departments if hasattr(agent, 'all_departments') else [agent.department]
            dept_query = " ".join(departments)

            # Get relevant knowledge for agent's role and departments
            knowledge = await self.get_relevant_knowledge(
                query=f"{agent.role} {dept_query}",
                limit=5
            )

            # Extract best practices from knowledge docs
            best_practices = [
                k["title"] for k in knowledge
                if "best practice" in k["title"].lower()
            ]

            # Build role description with multi-department support
            if len(departments) > 1:
                role_desc = f"{agent.role} across {', '.join(departments)}"
            else:
                role_desc = f"{agent.role} in {departments[0]}"

            return {
                "specializations": agent.specializations or [],
                "best_practices": best_practices,
                "methodologies": [],
                "role_description": role_desc
            }

        except Exception:
            return {}

    async def get_project_methodology(
        self,
        project_type: str,
        db: AsyncSession
    ) -> Optional[str]:
        """
        Get recommended methodology for project type.

        Args:
            project_type: Type of project
            db: Database session

        Returns:
            Methodology description or None
        """
        try:
            results = await self.get_relevant_knowledge(
                query=f"{project_type} project methodology",
                limit=1,
                category="methodology"
            )

            if results:
                return results[0]["content"]
            return None

        except Exception:
            return None

    async def get_best_practices(
        self,
        category: str
    ) -> List[Dict]:
        """
        Get best practices for a category.

        Args:
            category: e.g., "project management", "code review", "testing"

        Returns:
            List of best practice documents
        """
        try:
            results = await self.get_relevant_knowledge(
                query=f"{category} best practices",
                limit=5,
                category="best_practice"
            )

            return results

        except Exception:
            return []

    async def get_company_overview(self) -> Dict:
        """
        Get Deviant AI company overview.

        Returns:
            Company information dictionary
        """
        try:
            results = await self.get_relevant_knowledge(
                query="Deviant AI company overview mission services",
                limit=1,
                category="company_info"
            )

            if results:
                return {
                    "overview": results[0]["content"],
                    "summary": results[0]["summary"]
                }

            # Fallback to default if not in knowledge base yet
            return {
                "overview": "Deviant AI delivers AI-powered business solutions through intelligent automation.",
                "summary": "AI solutions company specializing in enterprise automation"
            }

        except Exception:
            return {}

    async def get_Deviant_system_info(self) -> Dict:
        """
        Get Deviant system architecture information.

        Returns:
            System information dictionary
        """
        try:
            results = await self.get_relevant_knowledge(
                query="Deviant system architecture workflow agents",
                limit=3,
                category="system_architecture"
            )

            if results:
                return {
                    "architecture": results[0]["content"] if len(results) > 0 else "",
                    "workflow": results[1]["content"] if len(results) > 1 else "",
                    "agents": results[2]["content"] if len(results) > 2 else ""
                }

            # Fallback to default
            return {
                "architecture": "Deviant is an AI-powered agent-based workflow system.",
                "workflow": "Projects are broken down into tasks and assigned to specialized agents.",
                "agents": "Multiple agent types collaborate to complete projects."
            }

        except Exception:
            return {}

    async def index_business_knowledge(
        self,
        document_id: str,
        title: str,
        content: str,
        category: str,
        subcategory: Optional[str] = None,
        summary: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> None:
        """
        Index a business knowledge document to RAG.

        Args:
            document_id: Unique document ID
            title: Document title
            content: Document content
            category: Category (e.g., "best_practice", "methodology")
            subcategory: Subcategory (optional)
            summary: Brief summary (optional)
            tags: List of tags (optional)
        """
        try:
            # For now, use the RAG service's generic index_message method
            # In the future, create a dedicated index_document method in RAG service
            await self.rag_service.index_message(
                message_id=document_id,
                content=content,
                from_agent_id="system",
                message_type="knowledge_document"
            )

        except Exception as e:
            # Log error but don't fail (indexing is background operation)
            pass

    async def _get_agent(self, agent_id: str, db: AsyncSession) -> Optional[Agent]:
        """Get agent by ID."""
        try:
            result = await db.execute(
                select(Agent).where(Agent.agent_id == agent_id)
            )
            return result.scalar_one_or_none()
        except Exception:
            return None


# Singleton instance
_business_domain_service = None


def get_business_domain_service() -> BusinessDomainService:
    """Get singleton instance of business domain service."""
    global _business_domain_service
    if _business_domain_service is None:
        _business_domain_service = BusinessDomainService()
    return _business_domain_service
