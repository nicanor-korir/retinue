
### 7.1.2: Content Storage & Retrieval System

**User Story:**  
*As an agent, I need to store knowledge in a structured format so that it can be easily retrieved and used in future tasks.*

**Backend Implementation:**

**1. Knowledge Document Model:**
```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum

class DocumentType(str, Enum):
    DECISION = "decision"
    SOLUTION = "solution"
    STANDARD = "standard"
    TEMPLATE = "template"
    LESSON = "lesson"
    BEST_PRACTICE = "best_practice"

class AccessLevel(str, Enum):
    PUBLIC = "public"
    DEPARTMENT = "department"
    EXECUTIVE = "executive"
    CONFIDENTIAL = "confidential"

class KBDocument(BaseModel):
    document_id: Optional[str] = None
    title: str = Field(..., min_length=10, max_length=500)
    content: str = Field(..., min_length=50)
    summary: Optional[str] = None
    category: str
    subcategory: Optional[str] = None
    document_type: DocumentType
    
    created_by_agent_id: str
    created_by_user_id: Optional[str] = None
    tags: List[str] = []
    keywords: List[str] = []
    
    access_level: AccessLevel = AccessLevel.PUBLIC
    allowed_departments: List[str] = []
    allowed_agents: List[str] = []
    
    related_projects: List[str] = []
    related_tasks: List[str] = []
    
    metadata: Dict = {}

class KBSearchQuery(BaseModel):
    query: str
    category: Optional[str] = None
    document_type: Optional[DocumentType] = None
    tags: List[str] = []
    limit: int = 10
    offset: int = 0
    search_type: str = "hybrid"  # 'keyword', 'semantic', 'hybrid'
    agent_id: Optional[str] = None  # For access control
```

**2. Knowledge Base Service:**
```python
import openai
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

class KnowledgeBaseService:
    """Service for managing knowledge base operations"""
    
    def __init__(self, db: AsyncSession, openai_client):
        self.db = db
        self.openai = openai_client
    
    async def create_document(
        self, 
        document: KBDocument,
        auto_generate_summary: bool = True,
        extract_keywords: bool = True
    ) -> KBDocument:
        """Create a new knowledge base document"""
        
        # Generate embedding for semantic search
        embedding = await self._generate_embedding(document.content)
        
        # Auto-generate summary if requested
        if auto_generate_summary and not document.summary:
            document.summary = await self._generate_summary(document.content)
        
        # Extract keywords if requested
        if extract_keywords and not document.keywords:
            document.keywords = await self._extract_keywords(document.content)
        
        # Create document in database
        kb_doc = KnowledgeBase(
            title=document.title,
            content=document.content,
            summary=document.summary,
            category=document.category,
            subcategory=document.subcategory,
            document_type=document.document_type.value,
            created_by_agent_id=document.created_by_agent_id,
            created_by_user_id=document.created_by_user_id,
            tags=document.tags,
            keywords=document.keywords,
            access_level=document.access_level.value,
            allowed_departments=document.allowed_departments,
            allowed_agents=document.allowed_agents,
            related_projects=document.related_projects,
            related_tasks=document.related_tasks,
            content_embedding=embedding,
            metadata=document.metadata
        )
        
        self.db.add(kb_doc)
        await self.db.commit()
        await self.db.refresh(kb_doc)
        
        # Create version history entry
        await self._create_version(kb_doc, "created")
        
        # Auto-discover relationships
        await self._discover_relationships(kb_doc.document_id)
        
        # Log creation
        await self._log_action("document_created", kb_doc.document_id)
        
        return kb_doc
    
    async def search_documents(
        self, 
        query: KBSearchQuery
    ) -> List[KBDocument]:
        """Search knowledge base using hybrid approach"""
        
        results = []
        
        if query.search_type in ["keyword", "hybrid"]:
            # Full-text search
            keyword_results = await self._keyword_search(query)
            results.extend(keyword_results)
        
        if query.search_type in ["semantic", "hybrid"]:
            # Vector similarity search
            semantic_results = await self._semantic_search(query)
            results.extend(semantic_results)
        
        # Merge and rank results
        ranked_results = await self._rank_results(
            results, 
            query,
            agent_id=query.agent_id
        )
        
        # Apply access control
        filtered_results = await self._filter_by_access(
            ranked_results,
            agent_id=query.agent_id
        )
        
        return filtered_results[:query.limit]
    
    async def _keyword_search(self, query: KBSearchQuery) -> List[KBDocument]:
        """Full-text search using PostgreSQL tsvector"""
        
        stmt = select(KnowledgeBase).where(
            func.to_tsvector('english', 
                KnowledgeBase.title + ' ' + KnowledgeBase.content
            ).match(query.query)
        ).where(
            KnowledgeBase.status == 'active'
        )
        
        # Apply filters
        if query.category:
            stmt = stmt.where(KnowledgeBase.category == query.category)
        
        if query.document_type:
            stmt = stmt.where(KnowledgeBase.document_type == query.document_type.value)
        
        if query.tags:
            stmt = stmt.where(KnowledgeBase.tags.contains(query.tags))
        
        # Order by relevance
        stmt = stmt.order_by(
            func.ts_rank(
                func.to_tsvector('english', 
                    KnowledgeBase.title + ' ' + KnowledgeBase.content
                ),
                func.plainto_tsquery('english', query.query)
            ).desc()
        )
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def _semantic_search(self, query: KBSearchQuery) -> List[KBDocument]:
        """Semantic search using vector embeddings"""
        
        # Generate embedding for query
        query_embedding = await self._generate_embedding(query.query)
        
        # Find similar documents using cosine similarity
        stmt = select(
            KnowledgeBase,
            (1 - KnowledgeBase.content_embedding.cosine_distance(query_embedding)).label('similarity')
        ).where(
            KnowledgeBase.status == 'active'
        ).order_by(
            KnowledgeBase.content_embedding.cosine_distance(query_embedding)
        ).limit(query.limit * 2)  # Get more for ranking
        
        result = await self.db.execute(stmt)
        return [row[0] for row in result.all()]
    
    async def _rank_results(
        self, 
        results: List[KBDocument], 
        query: KBSearchQuery,
        agent_id: Optional[str] = None
    ) -> List[KBDocument]:
        """Rank results by relevance, recency, and effectiveness"""
        
        scored_results = []
        
        for doc in results:
            score = 0.0
            
            # Effectiveness score (40% weight)
            score += doc.effectiveness_score * 0.4
            
            # Recency score (20% weight)
            days_old = (datetime.utcnow() - doc.created_at).days
            recency_score = max(0, 1 - (days_old / 365))
            score += recency_score * 0.2
            
            # Usage popularity (20% weight)
            usage_score = min(1.0, doc.use_count / 100)
            score += usage_score * 0.2
            
            # Validation bonus (10% weight)
            if doc.validated:
                score += 0.1
            
            # Agent-specific relevance (10% weight)
            if agent_id and agent_id in doc.metadata.get('successful_agents', []):
                score += 0.1
            
            scored_results.append((doc, score))
        
        # Sort by score descending
        scored_results.sort(key=lambda x: x[1], reverse=True)
        
        return [doc for doc, score in scored_results]
    
    async def _filter_by_access(
        self, 
        documents: List[KBDocument],
        agent_id: Optional[str] = None
    ) -> List[KBDocument]:
        """Filter documents based on access control"""
        
        if not agent_id:
            # Public access only
            return [doc for doc in documents if doc.access_level == 'public']
        
        # Get agent details
        agent = await self._get_agent(agent_id)
        
        filtered = []
        for doc in documents:
            if doc.access_level == 'public':
                filtered.append(doc)
            elif doc.access_level == 'department':
                if agent.department in doc.allowed_departments:
                    filtered.append(doc)
            elif doc.access_level == 'executive':
                if agent.department == 'executive':
                    filtered.append(doc)
            elif doc.access_level == 'confidential':
                if agent_id in doc.allowed_agents:
                    filtered.append(doc)
        
        return filtered
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate vector embedding for text"""
        response = await self.openai.embeddings.create(
            input=text[:8000],  # Limit to avoid token limits
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    
    async def _generate_summary(self, content: str) -> str:
        """Generate AI summary of content"""
        response = await self.openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a technical writer. Summarize the following content in 2-3 concise sentences."},
                {"role": "user", "content": content[:4000]}
            ],
            max_tokens=150
        )
        return response.choices[0].message.content
    
    async def _extract_keywords(self, content: str) -> List[str]:
        """Extract key terms from content"""
        response = await self.openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Extract 5-10 key technical terms/concepts from this content. Return as comma-separated list."},
                {"role": "user", "content": content[:4000]}
            ],
            max_tokens=100
        )
        keywords_str = response.choices[0].message.content
        return [k.strip() for k in keywords_str.split(',')]
    
    async def _discover_relationships(self, document_id: str):
        """Auto-discover related documents using embedding similarity"""
        
        # Get current document
        doc = await self._get_document(document_id)
        
        # Find similar documents
        similar_docs = await self.db.execute(
            select(KnowledgeBase).where(
                and_(
                    KnowledgeBase.document_id != document_id,
                    KnowledgeBase.status == 'active'
                )
            ).order_by(
                KnowledgeBase.content_embedding.cosine_distance(doc.content_embedding)
            ).limit(5)
        )
        
        # Create relationships for top similar documents
        for similar_doc in similar_docs.scalars().all():
            similarity = 1 - doc.content_embedding.cosine_distance(similar_doc.content_embedding)
            
            if similarity > 0.7:  # Threshold for auto-relationship
                relationship = KBRelationship(
                    source_document_id=document_id,
                    target_document_id=similar_doc.document_id,
                    relationship_type='related',
                    strength=similarity,
                    created_by='system'
                )
                self.db.add(relationship)
        
        await self.db.commit()
    
    async def log_usage(
        self,
        document_id: str,
        agent_id: str,
        task_id: Optional[str] = None,
        was_helpful: Optional[bool] = None,
        outcome: Optional[str] = None,
        feedback: Optional[str] = None
    ):
        """Log knowledge base document usage"""
        
        usage_log = KBUsageLog(
            document_id=document_id,
            used_by_agent_id=agent_id,
            used_in_task_id=task_id,
            was_helpful=was_helpful,
            outcome=outcome,
            feedback=feedback
        )
        
        self.db.add(usage_log)
        
        # Update document metrics
        await self.db.execute(
            update(KnowledgeBase)
            .where(KnowledgeBase.document_id == document_id)
            .values(
                use_count=KnowledgeBase.use_count + 1,
                view_count=KnowledgeBase.view_count + 1
            )
        )
        
        # Update effectiveness score if feedback provided
        if was_helpful is not None:
            await self._update_effectiveness_score(document_id, was_helpful)
        
        await self.db.commit()
```

**Testing Requirements:**
- ✅ Documents created with all metadata
- ✅ Embeddings generated correctly
- ✅ Keyword search returns relevant results
- ✅ Semantic search finds similar documents
- ✅ Hybrid search combines both approaches
- ✅ Access control filters correctly
- ✅ Usage logging tracks interactions
- ✅ Effectiveness scores update based on feedback

---

### 7.1.3: Agent Integration - Knowledge Retrieval

**User Story:**  
*As an agent, I need to automatically retrieve relevant knowledge when starting a task so that I can leverage past learnings.*

**Agent Knowledge Integration:**

```python
class AgentWithKnowledge(BaseAgent):
    """Extended agent class with knowledge base integration"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.kb_service = KnowledgeBaseService(db_session, openai_client)
    
    async def start_task_with_knowledge(self, task_id: str):
        """Start task with knowledge base context"""
        
        # 1. Get task details
        task = await self.get_task(task_id)
        
        # 2. Search knowledge base for relevant information
        relevant_knowledge = await self._retrieve_relevant_knowledge(task)
        
        # 3. Build enriched context
        context = await self._build_knowledge_context(task, relevant_knowledge)
        
        # 4. Execute task with enriched context
        result = await self._execute_with_context(task, context)
        
        # 5. Log knowledge usage
        await self._log_knowledge_usage(task_id, relevant_knowledge, result)
        
        # 6. Potentially create new knowledge
        if await self._is_novel_solution(result):
            await self._create_knowledge_entry(task, result)
        
        return result
    
    async def _retrieve_relevant_knowledge(self, task) -> List[KBDocument]:
        """Retrieve knowledge relevant to the task"""
        
        # Build search query from task
        search_query = KBSearchQuery(
            query=f"{task.title} {task.description}",
            category=self._infer_category(task),
            document_type=None,  # All types
            tags=self._extract_task_tags(task),
            limit=5,
            search_type="hybrid",
            agent_id=self.agent_id
        )
        
        # Search knowledge base
        results = await self.kb_service.search_documents(search_query)
        
        # Filter by relevance threshold
        relevant_results = [
            doc for doc in results 
            if await self._calculate_relevance(task, doc) > 0.6
        ]
        
        return relevant_results
    
    async def _build_knowledge_context(
        self, 
        task, 
        knowledge_docs: List[KBDocument]
    ) -> str:
        """Build context string from knowledge documents"""
        
        if not knowledge_docs:
            return f"Task: {task.description}\n\nNo directly relevant past knowledge found."
        
        context = f"Task: {task.description}\n\n"
        context += "=== Relevant Knowledge from Past Projects ===\n\n"
        
        for i, doc in enumerate(knowledge_docs, 1):
            context += f"## Knowledge Entry {i}: {doc.title}\n"
            context += f"Category: {doc.category}\n"
            context += f"Type: {doc.document_type}\n"
            context += f"Effectiveness: {doc.effectiveness_score:.0%}\n\n"
            
            if doc.summary:
                context += f"Summary: {doc.summary}\n\n"
            
            # Include relevant excerpt (not full content to save tokens)
            excerpt = doc.content[:1000] + "..." if len(doc.content) > 1000 else doc.content
            context += f"Content:\n{excerpt}\n\n"
            
            context += "---\n\n"
        
        return context
    
    async def _execute_with_context(self, task, context: str):
        """Execute task with knowledge-enriched context"""
        
        prompt = f"""
{context}

Based on the task description and the relevant knowledge above, complete the following:

Task: {task.title}
Description: {task.description}
Acceptance Criteria: {task.metadata.get('acceptance_criteria', 'Not specified')}

Instructions:
1. Review the relevant knowledge entries
2. Apply applicable patterns/solutions from past projects
3. Adapt approaches to the current task requirements
4. If the knowledge suggests a better approach, explain your reasoning
5. Provide your complete solution

Your solution:
"""
        
        # Call LLM with enriched context
        response = await self.call_llm(prompt, max_tokens=4000)
        
        return response
    
    async def _log_knowledge_usage(
        self, 
        task_id: str,
        knowledge_docs: List[KBDocument],
        result
    ):
        """Log which knowledge was used and how helpful it was"""
        
        for doc in knowledge_docs:
            await self.kb_service.log_usage(
                document_id=doc.document_id,
                agent_id=self.agent_id,
                task_id=task_id,
                was_helpful=None,  # Will be determined later based on task outcome
                outcome='pending',
                feedback=None
            )
    
    async def _is_novel_solution(self, result) -> bool:
        """Determine if this solution is novel enough to add to KB"""
        
        # Search for similar existing solutions
        similar = await self.kb_service.search_documents(
            KBSearchQuery(
                query=result[:500],  # Use first part of solution
                document_type=DocumentType.SOLUTION,
                limit=3,
                search_type="semantic",
                agent_id=self.agent_id
            )
        )
        
        # If no similar solutions found, or similarity is low, it's novel
        if not similar:
            return True
        
        # Check similarity threshold
        # (This would use embedding comparison in practice)
        return False  # Simplified for example
    
    async def _create_knowledge_entry(self, task, result):
        """Create new knowledge base entry from successful task"""
        
        document = KBDocument(
            title=f"Solution: {task.title}",
            content=f"""
## Problem
{task.description}

## Solution Approach
{result}

## Context
- Project: {task.project_id}
- Task: {task.task_id}
- Completed by: {self.agent_id}
- Date: {datetime.utcnow().isoformat()}

## Outcome
{task.metadata.get('outcome', 'Pending verification')}
""",
            category=self._infer_category(task),
            subcategory=self.department,
            document_type=DocumentType.SOLUTION,
            created_by_agent_id=self.agent_id,
            tags=self._extract_task_tags(task),
            related_tasks=[task.task_id],
            related_projects=[task.project_id],
            access_level=AccessLevel.PUBLIC
        )
        
        await self.kb_service.create_document(document)
        
        logger.info(f"Created knowledge entry from task {task.task_id}")
```

**Testing Requirements:**
- ✅ Agents retrieve relevant knowledge automatically
- ✅ Knowledge context improves task outcomes
- ✅ Usage is logged correctly
- ✅ Novel solutions create KB entries
- ✅ Similar solutions don't duplicate entries
- ✅ Knowledge effectiveness tracked

---

## Sub-Feature 7.2: Knowledge Base User Interface

### 7.2.1: Browse & Search Interface

**User Story:**  
*As a user, I want to browse and search the knowledge base so that I can learn from past projects and understand agent behavior.*

**Page Layout:**

**1. Knowledge Base Home Page (`/knowledge-base`):**

**Header Section:**
- Page title: "Knowledge Base"
- Subtitle: "Institutional memory of your AI agents"
- Stats bar:
  - Total documents: 234
  - Most popular category
  - Recently added count (last 7 days)
  - Your contributions (if applicable)

**Search Section:**
- **Prominent Search Bar:**
  - Placeholder: "Search knowledge base... (e.g., 'authentication best practices', 'API