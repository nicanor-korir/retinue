# The Cost of Intelligence: LLM API Economics

*The uncomfortable truth about what AI agents actually cost to run—and how to make the math work.*

---

## The Hidden Bill

Here's something the AI hype doesn't mention: every time an agent "thinks," it costs money.

Not theoretical compute costs. Actual dollars charged to your Anthropic account.

I learned this the hard way. My first complex project with Deviant ran up $47 in API costs. The project was worth it, but I hadn't budgeted for that number.

Let's talk about the real economics of running AI agents.

---

## The Cost Breakdown

### Claude API Pricing (as of 2024)

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|------------------------|
| Claude 3.5 Sonnet | $3.00 | $15.00 |
| Claude 3 Opus | $15.00 | $75.00 |
| Claude 3 Haiku | $0.25 | $1.25 |

Deviant uses Claude 3.5 Sonnet by default—the best balance of capability and cost.

### What a Single Task Costs

A typical coding task involves:

```
System prompt:     ~2,000 tokens
Task context:      ~1,500 tokens
Project context:   ~3,000 tokens
Previous output:   ~2,000 tokens
─────────────────────────────────
Input:             ~8,500 tokens

Agent output:      ~3,000 tokens
─────────────────────────────────
Output:            ~3,000 tokens
```

**Cost per task:**
- Input: 8,500 tokens × $3 / 1M = $0.0255
- Output: 3,000 tokens × $15 / 1M = $0.045

**Total: ~$0.07 per task**

But wait—there's more. A task might require:
- Initial generation
- CTO review (another LLM call)
- Revision based on review
- Second review
- Final approval

**Realistic cost per completed task: $0.20 - $0.50**

### What a Project Costs

A medium-sized project might have:
- 15-25 tasks
- CEO evaluation (2-3 calls)
- PM task breakdown (2-3 calls)
- CTO reviews (15+ calls)
- Inter-agent communication (10+ messages)

**Total LLM calls: 50-80**
**Total cost: $10-25**

Complex projects can exceed $50.

---

## The Cost Drivers

### 1. Context Window Bloat

The biggest cost driver is cramming too much context into prompts:

```python
# BAD: Include everything
context = {
    "system_prompt": full_agent_prompt,          # 2,000 tokens
    "entire_project_history": all_messages,       # 10,000 tokens
    "all_tasks": project_tasks,                   # 5,000 tokens
    "previous_code": all_generated_code,          # 20,000 tokens
    "knowledge_base": full_kb_dump                # 15,000 tokens
}
# Total: 52,000 tokens input = $0.16 per call

# GOOD: Include only relevant context
context = {
    "system_prompt": optimized_prompt,            # 1,000 tokens
    "current_task": task_details,                 # 500 tokens
    "relevant_dependencies": deps,                # 1,000 tokens
    "key_decisions": recent_decisions,            # 500 tokens
    "relevant_knowledge": top_5_entries           # 1,500 tokens
}
# Total: 4,500 tokens input = $0.014 per call
```

**10x cost reduction** just by being selective about context.

### 2. Review Loops

Endless revision cycles multiply costs:

```
Attempt 1: Generate → Review → Revise
Attempt 2: Generate → Review → Revise
Attempt 3: Generate → Review → Revise
Attempt 4: Generate → Review → Approve
```

That's 8 LLM calls for one task. At $0.10/call = $0.80.

With better prompts that generate approval-ready output the first time:

```
Attempt 1: Generate → Review → Approve
```

2 LLM calls. $0.20.

### 3. Agent Verbosity

Some agents generate unnecessarily long outputs:

```python
# Verbose agent
"I will now implement the user authentication system.
First, let me consider the requirements:
- Users need to log in
- Users need to log out
[500 more tokens of preamble]
...actual code...
[500 tokens of summary]"

# Efficient agent
"[actual code]"
```

Output tokens cost 5x more than input. Every unnecessary word adds up.

---

## Cost Optimization Strategies

### 1. Smart Caching

Cache expensive operations:

```python
class LLMCache:
    def __init__(self):
        self.cache = TTLCache(maxsize=1000, ttl=3600)  # 1 hour

    async def call_cached(
        self,
        prompt_hash: str,
        generator: Callable
    ) -> str:
        if prompt_hash in self.cache:
            return self.cache[prompt_hash]

        result = await generator()
        self.cache[prompt_hash] = result
        return result

# Usage
async def get_task_breakdown(project: Project) -> List[Task]:
    prompt_hash = hash(f"breakdown:{project.description}")

    return await cache.call_cached(
        prompt_hash,
        lambda: llm.generate(breakdown_prompt, project)
    )
```

### 2. Tiered Model Selection

Use cheaper models for simple tasks:

```python
class ModelSelector:
    def select_model(self, task_type: str) -> str:
        # High complexity - use best model
        if task_type in ["architecture_decision", "complex_code"]:
            return "claude-3-5-sonnet"

        # Medium complexity - use standard model
        if task_type in ["code_review", "task_breakdown"]:
            return "claude-3-5-sonnet"

        # Low complexity - use cheap model
        if task_type in ["formatting", "simple_message", "summary"]:
            return "claude-3-haiku"  # 12x cheaper

        return "claude-3-5-sonnet"  # Default
```

Haiku can handle:
- Message formatting
- Simple summaries
- Status updates
- Basic validation

That's 30-40% of calls at 1/12th the cost.

### 3. Prompt Optimization

Shorter prompts = lower costs:

```python
# Before: 2,500 tokens
"""
You are a senior backend engineer at a software company called Deviant.
You have extensive experience with Python, FastAPI, PostgreSQL, and
modern software development practices. Your role is to generate
high-quality, production-ready code that follows best practices.

When given a task, you should:
1. Analyze the requirements carefully
2. Consider the existing architecture
3. Generate clean, well-documented code
... [500 more tokens of instructions]
"""

# After: 800 tokens
"""
You are a backend engineer. Generate production Python/FastAPI code.
Requirements: Type hints, error handling, docstrings.
Output format: Code only, no explanations.
"""
```

**68% cost reduction** on system prompt alone.

### 4. Batching Operations

Combine multiple small tasks:

```python
# Before: 5 separate calls
for message in messages:
    await llm.summarize(message)  # $0.05 × 5 = $0.25

# After: 1 batched call
combined = "\n---\n".join(messages)
await llm.summarize_batch(combined)  # $0.08
```

### 5. Output Limits

Constrain output length:

```python
# Let model decide length - often verbose
result = await llm.generate(prompt)  # 3,000 tokens = $0.045

# Constrain to needed length
result = await llm.generate(prompt, max_tokens=500)  # 500 tokens = $0.0075
```

---

## Real Cost Data

Here's actual cost data from running Deviant:

### Simple Project (Todo App MVP)

| Component | LLM Calls | Tokens | Cost |
|-----------|-----------|--------|------|
| CEO evaluation | 2 | 15K | $0.45 |
| PM breakdown | 3 | 20K | $0.60 |
| Designer specs | 4 | 30K | $0.90 |
| Backend code | 6 | 45K | $1.35 |
| Frontend code | 8 | 60K | $1.80 |
| CTO reviews | 10 | 50K | $1.50 |
| **Total** | **33** | **220K** | **$6.60** |

### Medium Project (Dashboard with Auth)

| Component | LLM Calls | Tokens | Cost |
|-----------|-----------|--------|------|
| CEO evaluation | 3 | 25K | $0.75 |
| PM breakdown | 5 | 40K | $1.20 |
| Designer specs | 6 | 50K | $1.50 |
| Backend code | 12 | 100K | $3.00 |
| Frontend code | 15 | 120K | $3.60 |
| CTO reviews | 18 | 90K | $2.70 |
| Revisions | 8 | 60K | $1.80 |
| **Total** | **67** | **485K** | **$14.55** |

### Complex Project (SaaS MVP)

| Component | LLM Calls | Tokens | Cost |
|-----------|-----------|--------|------|
| CEO evaluation | 5 | 40K | $1.20 |
| PM breakdown | 8 | 70K | $2.10 |
| Designer specs | 10 | 80K | $2.40 |
| Backend code | 25 | 250K | $7.50 |
| Frontend code | 30 | 280K | $8.40 |
| CTO reviews | 35 | 175K | $5.25 |
| Revisions | 20 | 150K | $4.50 |
| **Total** | **133** | **1.05M** | **$31.35** |

---

## Making the Math Work

### ROI Calculation

| Metric | Traditional Dev | With Deviant |
|--------|-----------------|--------------|
| Developer cost/hour | $75-150 | - |
| Hours for MVP | 40-80 | - |
| Developer cost | $3,000-12,000 | - |
| Deviant API cost | - | $10-50 |
| Your review time | - | 3-5 hours |
| Your cost (@$100/hr) | - | $300-500 |
| **Total cost** | **$3,000-12,000** | **$310-550** |

**ROI: 5-20x cost savings**

Even if you factor in infrastructure and your time, the economics are compelling.

### When It Doesn't Work

The economics break down when:

1. **Excessive iteration**: 10+ revision cycles per task
2. **Massive context**: Projects requiring 100K+ token context
3. **Rejection rate**: >50% of output rejected
4. **Simple tasks**: Human could do it faster

For these cases, either:
- Improve prompts to reduce iterations
- Break projects into smaller pieces
- Use humans for simple/clear tasks
- Accept higher costs for complex work

---

## Monitoring Costs

Track spending in real-time:

```python
class CostTracker:
    async def track_call(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        project_id: str
    ):
        cost = self.calculate_cost(model, input_tokens, output_tokens)

        await self.db.insert("llm_costs", {
            "timestamp": datetime.now(),
            "project_id": project_id,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": cost
        })

        # Check budget
        project_total = await self.get_project_total(project_id)
        if project_total > PROJECT_BUDGET:
            await self.pause_project(project_id)
            await self.alert_budget_exceeded(project_id)
```

---

## The Takeaway

AI agents aren't free. Every decision, review, and generation costs real money.

But compared to human developers, the economics are favorable:
- $10-50 per project vs $3,000-12,000
- Hours vs weeks
- Scalable vs limited by hiring

The key is optimization:
1. Minimize context window size
2. Use cheaper models for simple tasks
3. Reduce revision cycles with better prompts
4. Cache where possible
5. Monitor and budget

Intelligence has a cost. Make sure you're getting value for it.

---

**Next**: [Building Trust in Autonomous Systems: The Human Oversight Balance →](./03-trust-and-oversight.md)

---

*Nicanor Korir has watched his API bills with a mix of horror and fascination. These strategies are hard-won.*
