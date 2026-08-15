# Retinue

**An AI company you can staff.** Retinue gives you a hand-picked team of AI agents — a CEO, a CTO, engineers, designers, marketers, analysts — that plan, delegate, and execute real project work together, while you stay in control of the decisions that matter.

You describe what you want built. A team of agents organizes itself around the goal, breaks it into tasks, assigns them by skill, does the work, escalates to you when it needs a decision, and hands you finished deliverables.

```
You ──► "Build me a customer feedback portal"
         │
         ▼
    ┌──────────────────────────────────────────┐
    │  CEO plans  →  CTO designs the approach   │
    │       ↓                                   │
    │  PM breaks it into tasks                  │
    │       ↓                                   │
    │  Engineers + Designer execute in parallel │
    │       ↓                                   │
    │  HR agent monitors health, escalates      │
    └──────────────────────────────────────────┘
         │
         ▼
You ◄── Working code, docs, and a deployable project
```

---

## Table of contents

- [What makes this different](#what-makes-this-different)
- [Core concepts](#core-concepts) — read this before the code
- [Quick start](#quick-start) — running in about 15 minutes
- [Your first project](#your-first-project)
- [How the system works](#how-the-system-works)
- [Project structure](#project-structure)
- [Common tasks](#common-tasks)
- [Troubleshooting](#troubleshooting)
- [Where to go next](#where-to-go-next)

---

## What makes this different

Most AI agent tools give you one assistant, or a flat swarm of identical workers. Retinue models a **company**: roles, hierarchy, departments, and escalation paths.

| | Single assistant (ChatGPT) | Agent swarms (AutoGPT) | Retinue |
|---|---|---|---|
| Structure | One generalist | Flat, unstructured | Org chart with roles |
| Delegation | You do it manually | Emergent, often chaotic | PM agent assigns by skill |
| When stuck | Tells you | Loops or drifts | Escalates to a human |
| Output | Text in a chat | Scattered files | Packaged deliverables |

The bet is that **structure is what makes autonomy safe**. A CTO agent reviewing a backend agent's plan catches things neither would catch alone, and an explicit escalation path means the system asks instead of guessing.

---

## Core concepts

Five ideas explain almost everything. Learn these and the codebase will make sense.

### 1. Agent

A specialist with a role, a department, and a set of capabilities. Each agent is a Python class that knows how to plan and execute a certain kind of work.

There are **25 agents across 9 departments** (Executive, Engineering, Marketing, Finance, Sales, HR, Operations, Legal, Research). **7 are fully implemented** and do real work today:

| Agent | Department | Responsibility |
|---|---|---|
| CEO | Executive | Sets direction, approves plans, resolves conflicts |
| CTO | Engineering | Technical decisions, architecture review |
| Project Manager | Operations | Breaks goals into tasks, assigns, tracks |
| HR | HR | Monitors agent health, detects stuck agents |
| Backend Engineer | Engineering | Server-side implementation |
| Frontend Engineer | Engineering | Client-side implementation |
| Product Designer | Engineering | UI/UX and design assets |

The other 18 are registered in the **AgentRegistry** with metadata and capabilities — they can be selected onto teams and assigned tasks, but their specialized execution logic is still being built out.

> **Registry vs. implementation.** `AgentRegistry` (`backend/app/agents/agent_registry.py`) is the catalog of *who exists and what they're good at*. The agent classes next to it are *how they actually work*. The registry is why you can add an agent's metadata without writing its executor first.

### 2. Project

A goal plus the team assigned to it. You pick a **deliverable type** (software MVP, marketing campaign, financial analysis, proposal, and others) and either accept the recommended team or hand-pick agents.

### 3. Task

A unit of work owned by exactly one agent. The PM agent creates tasks, and the system assigns them by **capability matching** — comparing a task's required skills against each agent's declared capabilities and scoring the fit.

### 4. Escalation

When an agent is blocked, uncertain, or hits a decision above its authority, it escalates instead of guessing. Escalations surface in the dashboard and wait for you. This is the human-in-the-loop control that keeps autonomy from becoming unpredictability.

### 5. Knowledge base

A RAG-backed store of project context, company knowledge, and past learnings that agents query before acting, so they build on what the system already knows rather than starting cold each time.

---

## Quick start

This gets you a running system with agents doing real work. Budget **~15 minutes**, most of it waiting on installs.

### Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Docker Desktop | Any recent | Runs PostgreSQL + Redis |
| Python | 3.11+ | Backend |
| Node.js | 18+ | Frontend |
| Anthropic API key | — | Get one at [console.anthropic.com](https://console.anthropic.com/) |

> **Cost warning.** Agents make real Claude API calls. A small project typically costs a few dollars. Start with something small and watch your usage the first time.

> **Don't run `docker-compose up` bare.** The compose file declares `backend` and `frontend` services, but `frontend/Dockerfile` doesn't exist yet and the containers skip database setup. Start only the data services, as below, and run the app natively — that's the supported path and it's better for development anyway.

### Step 1 — Configure your environment

```bash
cp .env.example .env
```

Open `.env` and set two values:

```bash
ANTHROPIC_API_KEY=sk-ant-...      # required — nothing works without this
DB_PASSWORD=pick_something_secure # required — used by Postgres and the backend
```

### Step 2 — Start PostgreSQL and Redis

```bash
docker-compose up -d postgres redis
docker-compose ps        # both should read "healthy" after ~30s
```

### Step 3 — Set up the backend

```bash
cd backend
python -m venv venv

# macOS / Linux
source venv/bin/activate
# Windows PowerShell
venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### Step 4 — Create and seed the database

Run these in order. Each one is safe to re-run.

```bash
alembic upgrade head                        # create all tables
python -m app.scripts.init_agents           # register the 7 core agents
python -m app.scripts.seed_agent_expertise  # tag agents for skill matching
python -m app.scripts.init_knowledge_system # optional: knowledge base categories
```

Verify it worked:

```bash
python -m app.scripts.verify_database
```

### Step 5 — Start the backend

```bash
uvicorn app.main:app --reload --port 8000
```

Confirm it's alive: open **http://localhost:8000/docs** for interactive API documentation.

### Step 6 — Start the frontend

In a **second terminal**:

```bash
cd frontend
npm install
cp .env.example .env.local   # defaults point at localhost:8000
npm run dev
```

Open **http://localhost:3000**.

### You should now have

| Service | URL | What it is |
|---|---|---|
| Dashboard | http://localhost:3000 | The UI you'll work in |
| API docs | http://localhost:8000/docs | Swagger, fully interactive |
| Health check | http://localhost:8000/health | Should return a healthy status |
| PostgreSQL | localhost:5432 | Database `ai_company`, user `agent` |
| Redis | localhost:6379 | Cache and event bus |

Stuck? Jump to [Troubleshooting](#troubleshooting).

---

## Your first project

### From the dashboard

1. Open http://localhost:3000 and create a new project.
2. Give it a goal — be specific. *"A task tracker with user login, projects, and due dates"* works far better than *"a productivity app."*
3. Pick a deliverable type (start with **Software MVP**).
4. Accept the recommended team, or hand-pick agents.
5. Create it, then watch the **Tasks** and **Messages** views as agents plan and execute.

### From the API

```bash
# Create a project with a custom team
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Customer Feedback Portal",
    "description": "A web app where customers submit and vote on feature requests",
    "deliverable_type": "software_mvp",
    "selected_agents": ["ceo_001", "cto_001", "backend_001", "frontend_001"]
  }'

# Watch it progress
curl http://localhost:8000/api/v1/projects/{project_id}
curl http://localhost:8000/api/v1/agents/status
```

Useful helper endpoints while you're picking a team:

```bash
# Which agents can do Python?
curl http://localhost:8000/api/v1/agents/by-capability/python

# Is this team viable for this deliverable? (returns gaps + cost estimate)
curl -X POST http://localhost:8000/api/v1/agents/validate-team \
  -H "Content-Type: application/json" \
  -d '{"agent_ids": ["ceo_001","cto_001"], "deliverable_type": "software_mvp"}'
```

Browse the full endpoint list at http://localhost:8000/docs.

### What to expect

The first minutes are mostly planning — the CEO and CTO agents think before anyone writes code. Tasks appear, get assigned, and move through states. If an agent gets blocked you'll see an **escalation** waiting for your decision. That's the system working as designed, not an error.

---

## How the system works

### Request flow

```
Browser (Next.js)
   │  REST for actions, WebSocket for live updates
   ▼
FastAPI  (backend/app/main.py)
   │
   ├── API layer      backend/app/api/       route handlers, validation
   ├── Service layer  backend/app/services/  business logic, orchestration
   ├── Agent layer    backend/app/agents/    planning + execution, calls Claude
   └── Data layer     backend/app/db/        SQLAlchemy models
         │
         ├── PostgreSQL   projects, tasks, agents, messages, escalations
         └── Redis        caching + event bus between agents
```

### How agents coordinate

Agents communicate through an **event bus** rather than calling each other directly. When a task completes, an event fires and interested agents react. This keeps agents decoupled — a new agent subscribes to events without any existing agent needing to know it exists.

A **hybrid model** runs alongside it: events drive immediate reactions, while periodic polling catches anything missed, so a dropped event degrades throughput instead of stalling the project.

The **HR agent** independently monitors the others, watching for agents stuck on a task or looping, and escalates when it finds one.

### Tech stack

**Backend** — Python 3.11, FastAPI, SQLAlchemy 2.0 (async), Alembic, asyncpg, Redis, WebSockets, Anthropic Claude SDK

**Frontend** — Next.js 14 (App Router), React 18, TypeScript, TanStack Query, Axios

**Infrastructure** — PostgreSQL 15, Redis 7, Docker Compose

---

## Project structure

```
.
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI entry point — start reading here
│   │   ├── agents/          # agent implementations + AgentRegistry
│   │   ├── api/             # HTTP route handlers, one module per resource
│   │   ├── services/        # business logic and orchestration
│   │   ├── db/              # SQLAlchemy models
│   │   ├── schemas/         # Pydantic request/response models
│   │   ├── core/            # config, settings
│   │   ├── scripts/         # setup, seeding, verification
│   │   ├── templates/       # PDF/export templates
│   │   └── workers/         # background jobs
│   ├── alembic/versions/    # database migrations
│   ├── tests/
│   └── requirements.txt
│
├── frontend/                # Next.js dashboard (the product UI)
│   └── src/
│       ├── app/             # App Router pages
│       ├── components/      # UI components by feature
│       └── hooks/           # data fetching (TanStack Query)
│
├── website/                 # Marketing site — separate from the product
├── docs/                    # Documentation (start at docs/README.md)
├── ProductRoadmap/          # Per-feature specifications
└── docker-compose.yml       # PostgreSQL + Redis for local dev
```

**Where to start reading code:** `backend/app/main.py` → `backend/app/api/projects.py` → `backend/app/agents/base_agent.py` → `backend/app/agents/ceo_agent.py`. That path takes you from an HTTP request to an agent thinking.

---

## Common tasks

### Database migrations

```bash
cd backend
alembic revision --autogenerate -m "describe your change"   # after editing models
alembic upgrade head                                        # apply
alembic downgrade -1                                        # roll back one
```

### Running tests

```bash
cd backend
pytest tests/                              # everything
pytest tests/test_agent_registry.py -v     # one file
```

### Inspecting data

```bash
# PostgreSQL
docker-compose exec postgres psql -U agent -d ai_company
#   \dt                        list tables
#   SELECT * FROM agents;      see registered agents

# Redis
docker-compose exec redis redis-cli
#   KEYS *
```

### Logs

```bash
docker-compose logs -f postgres redis   # data services
# Backend and frontend log to their own terminals when run natively
```

### Stopping

```bash
docker-compose down       # stop, keep data
docker-compose down -v    # stop and DELETE all data
```

---

## Troubleshooting

### `ANTHROPIC_API_KEY not set`

`.env` must exist in the **repository root** and contain a valid key. The backend reads it at startup, so restart the backend after editing. Verify the key at [console.anthropic.com](https://console.anthropic.com/).

### Database connection errors

Check Postgres is healthy with `docker-compose ps`. The defaults are user `agent`, database `ai_company`, and the password comes from `DB_PASSWORD` in `.env`. If you set `DATABASE_URL` by hand, make sure it matches `docker-compose.yml`.

To start completely fresh (**this deletes all data**):

```bash
docker-compose down -v
docker-compose up -d postgres redis
# wait ~30s for health checks
cd backend && alembic upgrade head && python -m app.scripts.init_agents
```

### `docker-compose up` fails on the frontend service

Expected — `frontend/Dockerfile` doesn't exist yet. Use `docker-compose up -d postgres redis` and run the apps natively.

### Port already in use

```bash
# macOS / Linux
lsof -i :8000
# Windows PowerShell
netstat -ano | findstr :8000
```

Kill the process, or change the port (`uvicorn --port 8001`, `npm run dev -- -p 3001`).

### Agents aren't picking up tasks

1. Confirm they were registered: `curl http://localhost:8000/api/v1/agents/status`
2. If that's empty, run `python -m app.scripts.init_agents`
3. Check the backend terminal for Claude API errors (rate limits, invalid key, insufficient credits)

### Frontend loads but shows no data

The API base URL is wrong or the backend is down. Confirm `curl http://localhost:8000/health` responds, then check `NEXT_PUBLIC_API_URL` in `frontend/.env.local`.

---

## Where to go next

### Getting productive

- **[docs/GETTING-STARTED.md](docs/GETTING-STARTED.md)** — the setup guide in more depth, with verification at every step
- **[docs/README.md](docs/README.md)** — the full documentation map
- **http://localhost:8000/docs** — interactive API reference, the fastest way to explore endpoints

### Understanding the design

- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** — system architecture in detail
- **[docs/articles/](docs/articles/)** — long-form writing on why the system is built this way
- **[ProductRoadmap/](ProductRoadmap/)** — per-feature specifications (projects, tasks, escalations, knowledge base, auth)

### Operating it

- **[docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)** — deploying to production
- **[docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md)** — what's built and what's in progress

---

## Project status

Retinue is in **active development**. The 7 core agents, the REST API, the dashboard, real-time updates, escalations, and the knowledge base all work end to end. The remaining 18 agents are registered and selectable but still gaining their specialized execution logic.

See **[docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md)** for a detailed breakdown.
