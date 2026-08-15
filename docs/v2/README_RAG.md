# RAG System - Retinue Knowledge Persistence

**Welcome to RAG Phase 1! 🚀**

This directory contains the implementation of RAG (Retrieval-Augmented Generation) for Retinue - enabling agents to learn from past work and make informed decisions.

---

## 📁 Documentation Structure

### Getting Started (Start Here!)
- **[RAG_QUICKSTART.md](RAG_QUICKSTART.md)** ← Start here (5-minute setup)
  - Installation instructions
  - Basic usage examples
  - Common use cases
  - Troubleshooting FAQ

### Wiring RAG to Claude
- **[RAG_CLAUDE_SETUP.md](RAG_CLAUDE_SETUP.md)** (Setup)
  - Connecting retrieval to the Claude API
  - Configuration and keys
  - Verification steps
- **[CLAUDE_SETUP_SUMMARY.md](CLAUDE_SETUP_SUMMARY.md)** (Condensed)
  - The same setup, abridged

### Project-wide status
- **[../PROJECT_STATUS.md](../PROJECT_STATUS.md)** (Executive summary)
  - What's delivered across the whole platform
  - Where RAG sits in it

### This file
- **README_RAG.md** (you are here)
  - Complete RAG architecture and all four phases
  - What Phase 1 implemented
  - Testing guide and common tasks

> **A note on links.** Several companion documents referenced in earlier drafts (`RAG_PHASE1_IMPLEMENTATION.md`, `RAG_PHASE2_INTEGRATION.md`, `RAG_IMPLEMENTATION_PLAN.md`, `RAG_DOCUMENTATION_MAP.md`) were consolidated into this file. References to them now point here.

---

## 🚀 Quick Start (5 Minutes)

### 1. Install RAG Dependencies
```bash
cd backend
pip install -r requirements-rag.txt
# Installs: chromadb, openai
```

### 2. Configure Environment
```bash
# Add to your .env file:
OPENAI_API_KEY=sk-your-key-here
RAG_ENABLED=true

# Create ChromaDB directory
mkdir -p data/chromadb
```

### 3. Test RAG Service
```python
from app.services.rag_service import get_rag_service

rag = get_rag_service()

# Index a task
await rag.index_task(
    task_id="test_001",
    title="Build User API",
    description="Create REST API for user management",
    output="FastAPI endpoints for CRUD operations...",
    agent_id="backend_001"
)

# Retrieve context
results = await rag.retrieve_context(
    query="How do I build a REST API?",
    agent_id="backend_001"
)

# Check stats
stats = await rag.get_stats()
print(f"Tasks indexed: {stats['tasks']}")
```

### 4. Use RAG in Your Agent
```python
# Instead of:
response = await agent.call_llm(prompt, context)

# Use:
response = await agent.call_llm_with_rag(
    prompt=prompt,
    context=context,
    project_id=project_id
)
```

---

## 🎯 What RAG Does

### Before RAG
```
Agent receives task
    ↓
Agent calls Claude
    ↓
Claude generates response (no historical context)
    ↓
Same solution generated multiple times
```

### After RAG
```
Agent receives task
    ↓
RAG retrieves relevant past work
    ↓
Agent calls Claude with context
    ↓
Claude generates informed response
    ↓
Consistent patterns + reuses proven approaches
```

---

## 📊 Architecture Overview

```
┌─────────────────────────────────────┐
│   Agent LLM Call with RAG           │
├─────────────────────────────────────┤
│                                     │
│  1. call_llm_with_rag(prompt)      │
│     ↓                               │
│  2. retrieve_context(query)         │
│     ↓ (async)                       │
│  3. Generate embedding              │
│     ↓                               │
│  4. Search vector DB (ChromaDB)    │
│     ↓                               │
│  5. Format results for prompt       │
│     ↓                               │
│  6. call_llm(prompt + context)     │
│     ↓                               │
│  7. Claude returns informed answer  │
│                                     │
└─────────────────────────────────────┘
```

---

## 🔧 Core Services

### EmbeddingService (`rag_embedding_service.py`)
Generates embeddings using OpenAI API
```python
from app.services.rag_embedding_service import get_embedding_service

embedding = get_embedding_service()
vec = await embedding.embed_text("Your text here")
# Returns: [0.123, -0.456, ...] (1536 dimensions)
```

### VectorStore (`rag_vector_store.py`)
Persistent embedding storage (ChromaDB)
```python
from app.services.rag_vector_store import get_vector_store

store = get_vector_store()
await store.add_documents(
    collection_name="tasks",
    documents=["text1", "text2"],
    embeddings=[vec1, vec2],
    metadatas=[{...}, {...}],
    ids=["id1", "id2"]
)
```

### RAGService (`rag_service.py`)
Main orchestrator for indexing & retrieval
```python
from app.services.rag_service import get_rag_service

rag = get_rag_service()

# Index
await rag.index_task(task_id="...", title="...", ...)

# Retrieve
results = await rag.retrieve_context(query="...", top_k=5)

# Format
context_text = await rag.format_context_for_prompt(results)

# Stats
stats = await rag.get_stats()
```

### IndexingService (`rag_indexing_service.py`)
Async background indexing
```python
from app.services.rag_indexing_service import get_indexing_service

indexing = get_indexing_service()

# Start background worker
await indexing.start()

# Queue indexing jobs
await indexing.queue_index_task(task_id="...", ...)
```

---

## 📝 Configuration

Edit `backend/app/core/config.py`:

```python
# Enable/disable RAG
RAG_ENABLED = True

# Embedding model
RAG_EMBEDDING_MODEL = "text-embedding-3-small"

# Retrieval settings
RAG_TOP_K = 5  # Results to return
RAG_SIMILARITY_THRESHOLD = 0.7  # Min relevance (0-1)

# Chunking
RAG_CHUNK_SIZE = 512  # Characters
RAG_CHUNK_OVERLAP = 50  # Overlap

# Vector DB
CHROMADB_PATH = "./data/chromadb"
CHROMADB_PERSIST = True  # Save to disk

# Context window
RAG_MAX_CONTEXT_LENGTH = 50000  # Tokens

# OpenAI API
OPENAI_API_KEY = "sk-..."  # Required
```

---

## 💡 Common Tasks

### Task 1: Index a Completed Task
```python
from app.services.rag_service import get_rag_service

rag = get_rag_service()

await rag.index_task(
    task_id="task_001",
    title="Implement JWT Authentication",
    description="Build JWT-based auth system",
    output="""
    # Implementation
    - FastAPI dependency for token validation
    - Pydantic models for token schemas
    - Database for token blacklist
    """,
    agent_id="backend_001",
    project_id="project_001",
    status="completed"
)
```

### Task 2: Search Knowledge Base
```python
results = await rag.retrieve_context(
    query="How do I implement authentication?",
    agent_id="backend_001",
    collections=["tasks"],
    top_k=5
)

# results contains:
# - results['tasks']['ids']
# - results['tasks']['documents']
# - results['tasks']['scores']
# - results['tasks']['metadatas']
```

### Task 3: Format Context for Prompt
```python
# After retrieval, format for LLM
context_text = await rag.format_context_for_prompt(
    results,
    max_tokens=4000
)

# Use in prompt
prompt = f"""
{context_text}

Now implement: {task_description}
"""
```

### Task 4: Use in Agent
```python
# In any agent class
response = await self.call_llm_with_rag(
    prompt="Build user API",
    context={"project": "e-commerce"},
    max_tokens=4000,
    project_id="proj_123",
    agent_specific_filter=True
)
```

### Task 5: Monitor Progress
```python
stats = await rag.get_stats()
print(f"""
Tasks indexed: {stats['tasks']}
Decisions indexed: {stats['decisions']}
Messages indexed: {stats['messages']}
Total knowledge base size: {sum(stats.values())}
""")
```

---

## 🐛 Troubleshooting

### "OPENAI_API_KEY is required"
```bash
# Add to .env
OPENAI_API_KEY=sk-your-key-here

# Or set environment variable
export OPENAI_API_KEY=sk-your-key-here
```

### "ChromaDB not found"
```bash
# Create directory
mkdir -p data/chromadb

# Or check config
CHROMADB_PATH = "./data/chromadb"  # in config.py
```

### "No results returned"
- ✓ Check RAG_ENABLED=true
- ✓ Verify tasks are indexed (check stats)
- ✓ Try a different query (less specific)
- ✓ Reduce SIMILARITY_THRESHOLD
- ✓ Increase TOP_K

### "Retrieval is slow"
- Reduce TOP_K (e.g., 3 instead of 5)
- Increase SIMILARITY_THRESHOLD (e.g., 0.8)
- Reduce CHUNK_SIZE (affects search)
- Use metadata filters

---

## 📚 Learn More

### Quick Overview
→ Start with [RAG_QUICKSTART.md](RAG_QUICKSTART.md)

### Implementation Details
→ Keep reading this document — see [What's Implemented](#-whats-implemented-phase-1) below

### Wiring it to Claude
→ See [RAG_CLAUDE_SETUP.md](RAG_CLAUDE_SETUP.md)

### Executive Summary
→ Check [../PROJECT_STATUS.md](../PROJECT_STATUS.md)

---

## ✅ What's Implemented (Phase 1)

| Component | Status | File |
|-----------|--------|------|
| Embedding Service | ✅ | `rag_embedding_service.py` |
| Vector Store | ✅ | `rag_vector_store.py` |
| RAG Service | ✅ | `rag_service.py` |
| Indexing Pipeline | ✅ | `rag_indexing_service.py` |
| Config Settings | ✅ | `config.py` |
| Base Agent Integration | ✅ | `base_agent.py` |
| Backend Engineer Integration | ✅ | `backend_engineer_agent.py` |
| Documentation | ✅ | This directory |

## ⏳ Planned (Phase 2-4)

| Feature | Phase | Status |
|---------|-------|--------|
| Event-Driven Auto-Indexing | Phase 2 | 📋 Planned |
| All 7 Agents Integrated | Phase 2 | 📋 Planned |
| Decision Indexing | Phase 2 | 📋 Planned |
| Message Indexing | Phase 2 | 📋 Planned |
| Redis Caching | Phase 3 | 📋 Planned |
| Feedback Loop | Phase 3 | 📋 Planned |
| Monitoring Dashboard | Phase 4 | 📋 Planned |
| Qdrant Migration | Phase 4 | 📋 Planned |

---

## 🎯 Success Indicators

You'll know RAG is working when:

1. ✅ Backend Engineer agent retrieves past implementations
2. ✅ Code patterns repeat consistently across projects
3. ✅ Agent responses reference relevant past work
4. ✅ Code duplication decreases
5. ✅ Retrieval time is <500ms
6. ✅ Indexing queue is < 10 items

---

## 💬 Questions?

### "How do I enable RAG?"
Just set `RAG_ENABLED=true` in config. It's on by default.

### "Will RAG slow down my agents?"
No - adds ~100ms, which is negligible vs. 10+ second LLM call.

### "How much does RAG cost?"
Phase 1: ~$0.002/month. Phase 2+: ~$70/month with Pinecone.

### "Can I delete old data?"
Yes - use `await store.delete(collection, ids)` to remove documents.

### "Will my data be sent to OpenAI?"
Only text for embedding. Stored vectors are kept in your ChromaDB.

### "Can RAG fail gracefully?"
Yes - if RAG unavailable, agents work without context (no impact).

### "When does automatic indexing start?"
Phase 2. Currently index manually or via `queue_index_task()`.

---

## 🚀 Next Steps

1. **Read Quick Start** (5 min) → RAG_QUICKSTART.md
2. **Index Test Data** (10 min) → Follow examples above
3. **Verify Retrieval** (5 min) → Call retrieve_context()
4. **Watch Agent Use RAG** (10 min) → Run Backend Engineer task
5. **Review Metrics** (5 min) → Check get_stats()

---

## 📞 Support

- **How-to questions:** See the FAQ in [RAG_QUICKSTART.md](RAG_QUICKSTART.md)
- **Technical and architecture details:** This document
- **Claude wiring:** [RAG_CLAUDE_SETUP.md](RAG_CLAUDE_SETUP.md)
- **Bugs or issues:** Check the troubleshooting section above

---

## 📄 File Guide

```
docs/v2/
├── README_RAG.md                        ← You are here (architecture + all 4 phases)
├── RAG_QUICKSTART.md                    ← Start here (5 min)
├── RAG_CLAUDE_SETUP.md                  ← Wiring retrieval to Claude
├── CLAUDE_SETUP_SUMMARY.md              ← Condensed version of the above
└── TASKS_REDESIGN_V2.md                 ← Task system redesign

backend/app/services/
├── rag_embedding_service.py             ← OpenAI embeddings
├── rag_vector_store.py                  ← ChromaDB interface
├── rag_service.py                       ← Main RAG orchestrator
└── rag_indexing_service.py              ← Async indexing

backend/app/agents/
├── base_agent.py                        ← call_llm_with_rag() method
└── backend_engineer_agent.py            ← RAG integration example

backend/
├── app/core/config.py                   ← RAG configuration
└── requirements-rag.txt                 ← RAG dependencies
```

---

**Happy Knowledge Building! 🧠**

Start with RAG_QUICKSTART.md →
