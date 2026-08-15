# RAG Setup for Claude (Using Sentence Transformers)

**Optimized for:** Claude LLM + Local Embeddings
**Status:** ✅ Production Ready
**Cost:** Free (no API calls for embeddings)

---

## 🎯 Overview

You're using **Claude** for your LLM, which is excellent! However, Claude doesn't provide an embeddings API. This guide shows you how to set up RAG with **Sentence Transformers** - the perfect complement to Claude.

### Why Sentence Transformers?

| Aspect | Sentence Transformers | OpenAI | HuggingFace |
|--------|----------------------|--------|-------------|
| **Cost** | Free ✅ | $0.02 per 1M tokens | Free |
| **Speed** | Fast (local) ✅ | Slow (API call) | Medium |
| **Quality** | Good (384-768 dims) ✅ | Best (1536 dims) | Good |
| **Privacy** | Local, no API key ✅ | Sends to OpenAI | Local |
| **Setup** | Easy ✅ | Requires API key | Medium |
| **Recommended** | ✅ YES | No (but option) | Possible |

---

## 📦 Installation

### Step 1: Install Dependencies

```bash
cd backend

# Install Sentence Transformers (recommended for Claude)
pip install sentence-transformers torch

# Or install all RAG dependencies including ChromaDB
pip install -r requirements-rag.txt
```

### Step 2: Verify Installation

```bash
python -c "from sentence_transformers import SentenceTransformer; print('✅ Sentence Transformers installed')"
python -c "import torch; print(f'✅ PyTorch installed. GPU available: {torch.cuda.is_available()}')"
python -c "import chromadb; print('✅ ChromaDB installed')"
```

---

## 🔧 Configuration

### Default Settings (Already Configured!)

Your `backend/app/core/config.py` is already set up for Sentence Transformers:

```python
# Default embedding backend (local, free, good quality)
RAG_EMBEDDING_BACKEND: str = "sentence-transformers"

# Fast model, recommended for general use
RAG_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"  # 384 dimensions

# Other good options:
# "all-mpnet-base-v2"  # Better quality (768 dims)
# "distiluse-base-multilingual-cased-v1"  # Multi-language support
```

### Optional: Switch Embedding Models

If you want better quality (at the cost of slower embedding generation):

```python
# In backend/app/core/config.py

# High quality (768 dimensions, slower)
RAG_EMBEDDING_MODEL: str = "all-mpnet-base-v2"

# Or multi-language support (512 dimensions)
RAG_EMBEDDING_MODEL: str = "distiluse-base-multilingual-cased-v1"
```

### Optional: Use OpenAI Instead

If you want the highest quality embeddings and don't mind API costs:

```python
# In backend/app/core/config.py
RAG_EMBEDDING_BACKEND: str = "openai"
RAG_EMBEDDING_MODEL: str = "text-embedding-3-small"

# You'll also need to set OPENAI_API_KEY in .env
# OPENAI_API_KEY=sk-...
```

---

## 🚀 Quick Start (5 Minutes)

### 1. Create Test Data

```python
# test_rag_claude.py
import asyncio
from app.services.rag_service import get_rag_service

async def test_rag():
    rag = get_rag_service()

    # Index a task
    print("📝 Indexing task...")
    await rag.index_task(
        task_id="task_001",
        title="Build User Authentication API",
        description="Create REST API for user login and registration with JWT",
        output="FastAPI endpoints: POST /auth/login, POST /auth/register, GET /auth/me",
        agent_id="backend_001",
        project_id="proj_001"
    )

    # Retrieve similar content
    print("🔍 Retrieving similar tasks...")
    results = await rag.retrieve_context(
        query="How do I implement authentication endpoints?",
        agent_id="backend_001",
        collections=["tasks"]
    )

    # Show results
    print(f"✅ Found {len(results['tasks']['ids'])} similar task(s)")
    for i, (doc, score) in enumerate(zip(results['tasks']['documents'], results['tasks']['scores']), 1):
        print(f"  [{i}] Relevance: {score:.2%}")
        print(f"      {doc[:100]}...")

    # Check stats
    stats = await rag.get_stats()
    print(f"\n📊 RAG Stats: {stats}")

if __name__ == "__main__":
    asyncio.run(test_rag())
```

Run it:
```bash
python test_rag_claude.py
```

Expected output:
```
📝 Indexing task...
🔍 Retrieving similar tasks...
✅ Found 1 similar task(s)
  [1] Relevance: 87%
      Build User Authentication API
      Create REST API for user login...

📊 RAG Stats: {'tasks': 1, 'decisions': 0, 'messages': 0, ...}
```

---

## 💡 How It Works

### Embedding Pipeline

```
Your Text
   ↓
Sentence Transformers (local)
   ↓
384-dimensional vector (or your chosen size)
   ↓
ChromaDB (stores in ./data/chromadb)
   ↓
Ready for semantic search
```

### RAG + Claude Workflow

```
Agent receives task
   ↓
Agent calls: call_llm_with_rag()
   ↓
RAG Service:
  1. Convert query to embedding (Sentence Transformers)
  2. Search ChromaDB for similar tasks
  3. Format results
   ↓
Agent calls Claude with enriched context
   ↓
Claude generates informed response
```

---

## 📊 Performance Characteristics

### Sentence Transformers (Your Current Setup)

| Metric | Value | Notes |
|--------|-------|-------|
| **Embedding generation** | ~50-200ms per text | Local, no network |
| **Batch embedding** | ~10-30ms per text | Efficient batch processing |
| **Vector search** | <100ms | ChromaDB local search |
| **Total retrieval** | <500ms | Well under LLM call time |
| **Memory usage** | ~2GB for model | Loaded once on startup |
| **Storage per embedding** | ~1.5KB | 384 dimensions × 4 bytes |

### Cost Comparison

| Backend | Cost | Speed | Quality |
|---------|------|-------|---------|
| **Sentence Transformers** | **Free** | Fast | Good |
| OpenAI | $0.02 per 1M tokens | Slow | Best |
| HuggingFace | Free | Medium | Good |

**For 1000 tasks (3000 embeddings):**
- Sentence Transformers: **Free** + fast local processing
- OpenAI: **$0.06** + slow API calls
- HuggingFace: **Free** but slower than Sentence Transformers

---

## 🔍 Troubleshooting

### Problem: "sentence_transformers module not found"

```bash
# Solution: Install it
pip install sentence-transformers torch
```

### Problem: "torch not installed"

```bash
# Solution: Install PyTorch
# For CPU (faster install):
pip install torch --index-url https://download.pytorch.org/whl/cpu

# For GPU (CUDA 12.1):
pip install torch --index-url https://download.pytorch.org/whl/cu121

# For GPU (CUDA 11.8):
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

### Problem: "First embedding generation is very slow"

This is normal! The model is downloading from HuggingFace on first use (~100MB).

```
First embedding: 30-60 seconds (downloading model)
Subsequent embeddings: 50-200ms (model cached locally)
```

Solution: Run a test embedding after installation:
```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("all-MiniLM-L6-v2")
print("Model loaded!")  # Wait for download to complete
```

### Problem: "High memory usage"

Sentence Transformers models use ~2-4GB of memory:

```python
# If memory is tight, use smaller model
RAG_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"  # 384 dims, smaller

# Instead of
RAG_EMBEDDING_MODEL: str = "all-mpnet-base-v2"  # 768 dims, larger
```

### Problem: "Embeddings are not very relevant"

Try a better model:

```python
# Current (384 dims)
RAG_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

# Better quality (768 dims)
RAG_EMBEDDING_MODEL: str = "all-mpnet-base-v2"

# Or use OpenAI for best quality (1536 dims)
RAG_EMBEDDING_BACKEND: str = "openai"
```

---

## 🎓 Model Selection Guide

### Choose Model Based On Your Needs

| Use Case | Recommended Model | Dimensions | Size |
|----------|------------------|-----------|------|
| **Fast local (CPU)** | all-MiniLM-L6-v2 | 384 | ~30MB |
| **General use (balanced)** | all-mpnet-base-v2 | 768 | ~90MB |
| **Multi-language** | distiluse-base-multilingual-cased-v1 | 512 | ~60MB |
| **Maximum quality** | OpenAI's text-embedding-3-small | 1536 | - (API) |

### For Your Setup (Claude + Deviant)

**Recommended:**
```python
RAG_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"  # Fastest, good quality
```

**If you want better quality:**
```python
RAG_EMBEDDING_MODEL: str = "all-mpnet-base-v2"  # Better but slower
```

**If you have multi-language content:**
```python
RAG_EMBEDDING_MODEL: str = "distiluse-base-multilingual-cased-v1"
```

---

## 🚀 Production Checklist

- [ ] Install dependencies: `pip install -r requirements-rag.txt`
- [ ] Verify installation works
- [ ] Run test embedding to download model
- [ ] Configure `RAG_EMBEDDING_BACKEND` in config
- [ ] Test with sample task (see Quick Start)
- [ ] Verify ChromaDB creates `data/chromadb` directory
- [ ] Check retrieval results are relevant
- [ ] Integrate with agents (see RAG_PHASE2_INTEGRATION.md)

---

## 📚 Next Steps

1. **Test RAG:** Follow Quick Start section above
2. **Integrate Agents:** See [RAG_PHASE2_INTEGRATION.md](RAG_PHASE2_INTEGRATION.md)
3. **Index Data:** See [RAG_QUICKSTART.md](RAG_QUICKSTART.md)
4. **Monitor Performance:** See [RAG_PHASE1_IMPLEMENTATION.md](RAG_PHASE1_IMPLEMENTATION.md) - Monitoring section

---

## 💻 System Requirements

### Minimum (Sentence Transformers - Recommended)
- **RAM:** 4GB (for model + ChromaDB)
- **Storage:** ~5GB (for model + vector database)
- **CPU:** Any modern CPU
- **GPU:** Optional (faster embedding generation)

### Recommended (Sentence Transformers + Claude API)
- **RAM:** 8GB+ (comfortable)
- **Storage:** ~10GB
- **CPU:** Multi-core processor
- **GPU:** Optional (RTX 3050+ speeds up embeddings 10x)

### For OpenAI Embeddings Alternative
- Same as above, no local model storage needed
- Internet connection required
- API key and costs

---

## ⚡ Performance Tips

### Tip 1: GPU Acceleration

If you have GPU:
```python
# Install CUDA-enabled PyTorch
pip install torch --index-url https://download.pytorch.org/whl/cu121

# Sentence Transformers will automatically use GPU
# 5-10x faster embedding generation!
```

### Tip 2: Batch Embedding

Always use batch embedding for multiple texts:

```python
# Good - fast
embeddings = await embedding_service.embed_batch(texts, batch_size=32)

# Bad - slow
embeddings = [await embedding_service.embed_text(t) for t in texts]
```

### Tip 3: Increase Similarity Threshold

If getting too many irrelevant results:

```python
# In config.py
RAG_SIMILARITY_THRESHOLD: float = 0.75  # More strict (default 0.7)
```

### Tip 4: Cache Results

Phase 3 will add Redis caching, but for now:
- Results are cached by ChromaDB
- Repeated searches for same query are fast

---

## 🔗 Comparison: Claude + Sentence Transformers

**Your Setup:**
- LLM: Claude (via Anthropic API) - Excellent language understanding
- Embeddings: Sentence Transformers (local) - Free, fast, good quality
- Vector DB: ChromaDB (local) - Free, simple, effective

**Why this combination works:**
1. **Claude** excels at understanding complex context and generating high-quality text
2. **Sentence Transformers** provides good semantic search without API costs
3. **ChromaDB** keeps everything local and simple
4. **Combined** they create a cost-effective RAG system optimized for Claude

---

## 📖 Full Documentation

For more information, see:
- [RAG_QUICKSTART.md](RAG_QUICKSTART.md) - General setup and usage
- [RAG_PHASE1_IMPLEMENTATION.md](RAG_PHASE1_IMPLEMENTATION.md) - Complete reference
- [RAG_PHASE2_INTEGRATION.md](RAG_PHASE2_INTEGRATION.md) - Agent integration
- [RAG_DOCUMENTATION_MAP.md](RAG_DOCUMENTATION_MAP.md) - Find what you need

---

**Happy RAG building with Claude! 🚀**

*Sentence Transformers + Claude = Powerful, cost-effective RAG*
