# Retinue Documentation

Everything written about Retinue lives here. This page is the map — it tells you which document answers which question, so you don't have to open six files to find one answer.

**New to the project?** Read the [root README](../README.md) first for what Retinue is and how to get it running. Come back here when you want depth.

---

## Start here: three onboarding paths

Pick the one that matches why you're here.

### Path A — "I want to run it and see it work" (~30 min)

1. [Root README → Quick start](../README.md#quick-start) — get it running
2. [GETTING-STARTED.md](GETTING-STARTED.md) — the same setup with more detail and verification at each step
3. [Root README → Your first project](../README.md#your-first-project) — create something and watch agents work
4. http://localhost:8000/docs — poke at the API while it's running

### Path B — "I'm going to work on the code" (~2 hours)

1. Finish Path A. Nothing below makes sense until you've watched a project run.
2. [Root README → Core concepts](../README.md#core-concepts) — agent, project, task, escalation, knowledge base
3. [ARCHITECTURE.md](ARCHITECTURE.md) — the full system design
4. Read code in this order:
   `backend/app/main.py` → `backend/app/api/projects.py` → `backend/app/agents/base_agent.py` → `backend/app/agents/ceo_agent.py`
5. [articles/2-architecture/](articles/2-architecture/) — the reasoning behind the design choices you just read
6. [ProductRoadmap/](../ProductRoadmap/) — the spec for whichever feature you're touching

### Path C — "I need to understand the product, not the code" (~1 hour)

1. [articles/1-urgent-introduction/01-what-is-retinue.md](articles/1-urgent-introduction/01-what-is-retinue.md) — the pitch
2. [BUSINESS_PLAN.md](BUSINESS_PLAN.md) — vision, market, strategy
3. [articles/3-use-cases/](articles/3-use-cases/) — ten industry-specific walkthroughs
4. [PROJECT_STATUS.md](PROJECT_STATUS.md) — what actually works today

---

## The full map

### Setup and operations

| Document | What it answers |
|---|---|
| [GETTING-STARTED.md](GETTING-STARTED.md) | How do I set up backend and frontend, step by step? |
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | How do I deploy to production? |
| [PROJECT_STATUS.md](PROJECT_STATUS.md) | What's built, what's in progress, what's planned? |

### Architecture and design

| Document | What it answers |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | How is the whole system put together? |
| [architecture/mermaid_chart/general.md](architecture/mermaid_chart/general.md) | Can I see it as diagrams? |
| [architecture/mermaid_chart/phase_1_MVP.md](architecture/mermaid_chart/phase_1_MVP.md) | What did the MVP scope look like? |
| [AGENT_INTELLIGENCE_IMPLEMENTATION_PLAN.md](AGENT_INTELLIGENCE_IMPLEMENTATION_PLAN.md) | How are agents being made smarter over time? |
| [CONSOLIDATION_ANALYSIS.md](CONSOLIDATION_ANALYSIS.md) | Why is the codebase organized the way it is? |

### The knowledge base and RAG layer

| Document | What it answers |
|---|---|
| [v2/RAG_QUICKSTART.md](v2/RAG_QUICKSTART.md) | Fastest path to a working RAG setup |
| [v2/README_RAG.md](v2/README_RAG.md) | How does retrieval work in depth? |
| [v2/RAG_CLAUDE_SETUP.md](v2/RAG_CLAUDE_SETUP.md) | How do I wire RAG to Claude? |
| [v2/CLAUDE_SETUP_SUMMARY.md](v2/CLAUDE_SETUP_SUMMARY.md) | Condensed version of the above |
| [v2/TASKS_REDESIGN_V2.md](v2/TASKS_REDESIGN_V2.md) | How was the task system redesigned? |

### Product and business

| Document | What it answers |
|---|---|
| [BUSINESS_PLAN.md](BUSINESS_PLAN.md) | Vision, market, competition, strategy |
| [../ProductRoadmap/](../ProductRoadmap/) | Detailed spec for each feature |
| [articles/](articles/) | 33 long-form pieces — see below |

### Original specifications

Historical records. Useful for understanding *why* a decision was made; not always current on *what* the code does now.

| Document | What it answers |
|---|---|
| [reference/IMPLEMENTATION.md](reference/IMPLEMENTATION.md) | The original technical specification |
| [reference/PROMPT.md](reference/PROMPT.md) | The original requirements |
| [reference/MESSAGES_REDESIGN.md](reference/MESSAGES_REDESIGN.md) | How the messaging system was redesigned |

---

## The articles

Thirty-three long-form pieces in [articles/](articles/), organized into six sets. These explain *thinking*, not mechanics — read them when you want to know why something is built a particular way.

| Set | Contents | Read it when |
|---|---|---|
| [1 — Introduction](articles/1-urgent-introduction/) | 5 articles: what Retinue is, why it exists, the market gap | You're new, or explaining the project to someone |
| [2 — Architecture](articles/2-architecture/) | 4 articles: event-driven design, the agent org, real-time coordination, knowledge | You're about to change the architecture |
| [3 — Use cases](articles/3-use-cases/) | 10 articles: founders, agencies, startups, enterprise, marketing, finance, manufacturing, ecommerce, education, healthcare | You're evaluating fit for a specific industry |
| [4 — Design patterns](articles/4-design-patterns/) | 3 articles: orchestration, hybrid polling/events, goal-aware execution | You're implementing something similar |
| [5 — Challenges](articles/5-challenges/) | 3 articles: stuck agents, cost of intelligence, trust and oversight | You've hit one of these problems |
| [6 — Future plans](articles/6-future-plans/) | 4 articles: consultant model, user control, marketplace, the vision | You're planning roadmap work |

See [articles/README.md](articles/README.md) for a per-article index.

---

## Quick answers

**How do I run this?** → [Root README → Quick start](../README.md#quick-start)

**Something's broken.** → [Root README → Troubleshooting](../README.md#troubleshooting), then [GETTING-STARTED.md](GETTING-STARTED.md#troubleshooting)

**What endpoints exist?** → Run the backend and open http://localhost:8000/docs. That's generated from the code, so it's never stale.

**How do I add a new agent?** → Register it in `backend/app/agents/agent_registry.py`, then implement its class alongside the existing agents. [ARCHITECTURE.md](ARCHITECTURE.md) covers the contract.

**How do I change the database schema?** → Edit the models in `backend/app/db/`, then `alembic revision --autogenerate -m "..."` and `alembic upgrade head`.

**What's actually finished?** → [PROJECT_STATUS.md](PROJECT_STATUS.md)

---

## While the system is running

| Resource | URL |
|---|---|
| Dashboard | http://localhost:3000 |
| Interactive API docs | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |

---

## A note on accuracy

Some documents here were written at different stages of the project and describe intentions as much as current behavior. When a document and the code disagree, **the code is right**. The most reliable sources are the interactive API docs at `/docs` (generated from code), the Alembic migrations in `backend/alembic/versions/` (the real schema history), and [PROJECT_STATUS.md](PROJECT_STATUS.md).
