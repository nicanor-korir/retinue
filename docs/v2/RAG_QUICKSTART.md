# RAG Phase 1 Quick Start Guide

**TL;DR:** RAG system now allows agents to learn from past work and make informed decisions.

---

## ⚡ Quick Start (5 minutes)

### 1. Setup
```bash
# Install dependencies (if not already installed)
pip install chromadb openai

# Set environment variables in .env
OPENAI_API_KEY=sk-...
RAG_ENABLED=true

# Create ChromaDB directory
mkdir -p data/chromadb
```

### 2. Index Your First Task
### 3. Retrieve Similar Context
### 4. Use in Agent LLM Call

## 📊 RAG System Overview

```
┌─────────────────────────────────────────────┐
│          YOUR TASK PROMPT                   │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│     RAG Service (retrieve_context)          │
│  1. Generate embedding of your query        │
│  2. Search vector DB for similar work       │
│  3. Return top matches + metadata           │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│  Format Context for LLM Prompt              │
│  - Add retrieved documents                  │
│  - Add relevance scores                     │
│  - Stay within token budget                 │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│  Call Claude with Enhanced Prompt           │
│  Claude knows about past implementations    │
│  Can reuse patterns and learn from history  │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│          INFORMED RESPONSE                  │
│  - Uses past patterns                       │
│  - Consistent with past decisions           │
│  - Reduces code duplication                 │
└─────────────────────────────────────────────┘
```

---

## 🔧 Core APIs
### RAG Service Methods
#### Indexing
#### Retrieval
#### Agent Integration

---

## ✅ Common Use Cases
### Use Case 1: Code Pattern Reuse
### Use Case 2: Decision Consistency
### Use Case 3: Problem Resolution

---

## 📈 Monitoring
### Check RAG Status
### Check Indexing Queue
### Monitor Retrieval Quality

## 🎯 Best Practices

### 1. **Quality Data In**
### 2. **Query Specificity**
### 3. **Agent-Specific Learning**
### 4. **Regular Indexing**

---

## 💡 Pro Tips

1. **Use project context:** Filter by project_id for project-specific learning
2. **Combine with decisions:** Retrieve both tasks AND decisions for context
3. **Leverage agent specialization:** Each agent learns their own patterns
4. **Monitor vector DB size:** Keep CHROMADB_PATH on fast storage
5. **Version your retrieval:** Different queries may need different TOP_K values
6. **Validate relevance:** Sample retrieved results for quality assurance

---

## ❓ FAQ

**Q: Will RAG slow down my agents?**
A: No - RAG adds ~50-100ms per query, which is negligible compared to LLM call time (~10+ seconds).

**Q: How much storage does RAG use?**
A: ~1MB per 100 indexed tasks. 1000 tasks ≈ 10MB.

**Q: Can I delete old data?**
A: Yes - use `await rag.vector_store.delete()` to remove documents.

**Q: Does RAG improve agent quality?**
A: Yes - agents make more consistent decisions and reuse proven patterns.

**Q: When does indexing happen?**
A: Currently manual via `index_task()`. Auto-indexing added in Phase 2.

**Q: Can RAG access real-time data?**
A: Only data that's been indexed. New work won't appear until indexed.

---

**Happy learning! 🎯**
