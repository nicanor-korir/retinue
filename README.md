# Deviant - AI Agent Company Platform

## ✅ Phase 0 COMPLETE - Foundation Ready!

**Status**: Expanded foundation complete with AgentRegistry system supporting 25+ agents across 9 departments.

## ✅ Phase 1 COMPLETE - API Implementation Ready!

**Status**: REST API fully enhanced with 32 new endpoints supporting flexible teams, capability matching, and multiple output formats.

## ✅ Phase 1 MVP COMPLETE - Ready for Testing!

**Status**: Fully functional with 7 autonomous AI agents working together to build software projects.

---

## 🚀 Quick Start (5 Minutes)

**New here?** See [QUICK_START.md](QUICK_START.md) for the fastest way to get running.

**Want details?** See [PROJECT_STATUS.md](PROJECT_STATUS.md) for complete implementation status.

**Ready to test?** See [TESTING_GUIDE.md](TESTING_GUIDE.md) for comprehensive test scenarios.

---

## Phase 1: REST API Implementation

The REST API has been fully enhanced with 32 new endpoints supporting Phase 0's capabilities.

### Phase 1 Highlights

**New API Endpoints:**
- **12 Agent Endpoints**: Discovery, filtering, capability matching, team validation
- **6 Project Endpoints**: Creation with custom teams, team management, deliverable support
- **10 Task Endpoints**: Capability-based assignment, output format support
- **4 Support Endpoints**: Validation, suggestions, status tracking

**Key Features:**
- Flexible project team selection (not fixed 7 agents)
- Skill-based agent recommendations
- Automatic task assignment by capability match
- Multiple output format support (PDF, DOCX, XLSX, code, etc.)
- Team validation with cost estimation
- Complete API documentation (Swagger/OpenAPI)

**Usage Example**:
```bash
# Create project with custom team
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Q1 Marketing Campaign",
    "deliverable_type": "marketing_campaign",
    "selected_agents": ["ceo_001", "cmo_001", "designer_001"]
  }'

# Find capable agents
curl http://localhost:8000/api/v1/agents/by-capability/python

# Validate team
curl -X POST http://localhost:8000/api/v1/agents/validate-team \
  -H "Content-Type: application/json" \
  -d '{
    "agent_ids": ["ceo_001", "cto_001", "backend_001"],
    "deliverable_type": "software_mvp"
  }'
```

**See [PHASE_1_COMPLETE.md](PHASE_1_COMPLETE.md) for full details.**

---

## Phase 0: Flexible Multi-Agent Foundation

Deviant evolved from a specialized 7-agent software development platform into a flexible multi-agent business operations system.

### Phase 0 Highlights

**Expanded Agent System:**
- **25 Agents** across 9 departments (Executive, Engineering, Marketing, Finance, Sales, HR, Operations, Legal, Research)
- **Dynamic Agent Registry** - Centralized catalog with metadata-driven agent management
- **Flexible Project Teams** - Custom agent selection per project instead of fixed 7-agent teams
- **Multiple Output Formats** - PDF, DOCX, XLSX, code, and more
- **10 Deliverable Types** - Software MVP, marketing campaigns, financial analysis, proposals, and more
- **Backward Compatible** - All existing projects continue to work unchanged

**Key Features:**
- AgentRegistry system with 25 configurable agents
- Capability-based agent matching for task assignment
- Team composition validation
- Department-based organization
- Specialization tracking and skill matching
- 66 comprehensive tests (52 unit + 14 integration)
- Non-breaking database migration with full downgrade support

## Phase 1 MVP: 7-Agent System

A multi-agent AI system that operates like a real company, with 7 AI agents working together to build software projects autonomously.

### Phase 1 Agents

**7 Core Agents:**
- **CEO Agent** - Strategic orchestrator
- **CTO Agent** - Technical oversight
- **Project Manager Agent** - Task coordination
- **HR Agent** - Agent monitoring and health
- **Senior Backend Engineer Agent** - Server-side development
- **Senior Frontend Engineer Agent** - Client-side development
- **Product Designer Agent** - UI/UX design

**Plus 18 Additional Agents (Phase 0):**
- **Marketing**: CMO, Content Specialist, Social Media Manager
- **Finance**: CFO, Financial Analyst
- **Sales**: Sales Manager
- **HR**: CHRO, HR Specialist
- **Legal**: Legal Counsel
- **Research**: Research Analyst, Data Analyst
- **Operations**: COO

**Tech Stack:**
- Backend: Python 3.11+, FastAPI, SQLAlchemy, Alembic
- Database: PostgreSQL 15+, Redis 7+
- AI: Anthropic Claude 3.5 Sonnet
- Frontend: Next.js 14+ (coming soon)
- Infrastructure: Docker, Docker Compose

---

## Quick Start (Windows PowerShell)

### Prerequisites

1. **Install Docker Desktop for Windows**
   - Download from: https://www.docker.com/products/docker-desktop
   - Make sure it's running before proceeding

2. **Install Python 3.11+**
   - Download from: https://www.python.org/downloads/
   - Make sure to check "Add Python to PATH" during installation

3. **Get Anthropic API Key**
   - Sign up at: https://console.anthropic.com/
   - Create an API key
   - You'll need this for the `.env` file

### Step 1: Clone and Setup

```powershell
# Navigate to the project directory
cd Domains\02-shoman-saas-domain\apps\Deviant

# Create environment file from example
Copy-Item .env.example .env

# Edit .env file with your API keys
notepad .env
# Add your ANTHROPIC_API_KEY and set a secure DB_PASSWORD
```

### Step 2: Start Infrastructure (PostgreSQL & Redis)

```powershell
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Wait for services to be healthy (about 30 seconds)
docker-compose ps
```

### Step 3: Setup Python Environment

```powershell
# Create virtual environment
cd backend
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Initialize Database

```powershell
# Create database tables (while in backend directory with venv activated)
alembic upgrade head

# Initialize database with departments, deliverable types, and agent metadata
python -m app.scripts.init_database

# Initialize the 7 core agents
python -m app.scripts.init_agents
```

### Step 5: Start Backend Server

```powershell
# Start FastAPI backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: http://localhost:8000

API Documentation (Swagger): http://localhost:8000/docs

---

## Testing the System

### Option 1: Using the API (Swagger UI)

1. Open http://localhost:8000/docs in your browser
2. Use the `POST /api/v1/projects` endpoint
3. Submit a project request:

```json
{
  "name": "Simple Todo App",
  "description": "Build a todo list app with user authentication, CRUD operations, and a clean UI",
  "priority": "high"
}
```

4. Monitor progress using `GET /api/v1/projects/{project_id}`
5. Check agent status with `GET /api/v1/agents/status`

### Option 2: Using curl (PowerShell)

```powershell
# Create a new project
$body = @{
    name = "Todo App Test"
    description = "Build a simple todo app with auth and database"
    priority = "high"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/projects" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

# Save the project ID
$projectId = $response.project_id

# Check project status
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/projects/$projectId"

# View all agent statuses
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/agents/status"

# View dashboard data
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/dashboard"
```

## Architecture
- [System Architecture](https://claude.ai/public/artifacts/e4fd68ed-4c03-481a-9bf7-4308a923f31d)
- [Event Driven Workflow](https://claude.ai/public/artifacts/4ea9a4c2-7794-4a4e-99b8-a5b267262ffa)

## Project Structure

```
Deviant/
├── backend/
│   ├── alembic/              # Database migrations
│   │   └── versions/         # Migration files (including Phase 0 additions)
│   ├── app/
│   │   ├── agents/
│   │   │   ├── agent_registry.py     # NEW: Centralized 25-agent catalog (Phase 0)
│   │   │   ├── base_agent.py
│   │   │   ├── ceo_agent.py
│   │   │   ├── cto_agent.py
│   │   │   ├── pm_agent.py
│   │   │   ├── hr_agent.py
│   │   │   ├── backend_engineer_agent.py
│   │   │   ├── frontend_engineer_agent.py
│   │   │   └── designer_agent.py
│   │   ├── api/              # FastAPI routes
│   │   ├── core/             # Core utilities
│   │   ├── db/               # Database models and connection
│   │   │   └── models.py     # UPDATED: Phase 0 models (departments, deliverables)
│   │   ├── scripts/
│   │   │   ├── init_database.py      # NEW: Initialize Phase 0 data (Phase 0)
│   │   │   └── init_agents.py        # Initialize agents
│   │   ├── utils/
│   │   │   └── agent_capabilities.py # NEW: Agent capability utilities (Phase 0)
│   │   └── tests/
│   │       ├── test_agent_registry.py        # NEW: 52 tests (Phase 0)
│   │       └── test_database_integration.py  # NEW: 14 tests (Phase 0)
│   ├── output/               # Generated code output
│   ├── requirements.txt
│   ├── Dockerfile
│   └── alembic.ini
├── frontend/                 # Next.js dashboard
├── docs/                     # Documentation
├── PHASE_0_COMPLETE.md       # Phase 0 completion summary
├── PHASE_0_PROGRESS.md       # Phase 0 detailed progress
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Development Workflow

### Running Migrations

```powershell
# Create a new migration after model changes
cd backend
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1
```

### Viewing Logs

```powershell
# View all container logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f postgres
docker-compose logs -f redis
docker-compose logs -f backend

# View Python application logs
# (When running backend directly, logs appear in console)
```

### Database Access

```powershell
# Connect to PostgreSQL
docker-compose exec postgres psql -U agent -d ai_company

# Common SQL commands:
\dt                 # List tables
\d+ agents          # Describe agents table
SELECT * FROM agents;
SELECT * FROM agent_status;
SELECT * FROM projects;
SELECT * FROM tasks ORDER BY created_at DESC;
\q                  # Quit
```

### Redis Access

```powershell
# Connect to Redis
docker-compose exec redis redis-cli

# Common Redis commands:
KEYS *              # List all keys
GET agent_status:ceo_001
HGETALL agent_status:ceo_001
QUIT                # Quit
```

---

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Your Anthropic API key for Claude |
| `DB_PASSWORD` | Yes | PostgreSQL password |
| `OPENAI_API_KEY` | No | Optional fallback LLM |
| `ENVIRONMENT` | No | `development` or `production` |
| `LOG_LEVEL` | No | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `JWT_SECRET` | No | Secret for JWT tokens (future use) |

### Agent Configuration

Agents are initialized with predefined roles and prompts. See:
- `backend/app/agents/` for individual agent implementations
- `backend/app/scripts/init_agents.py` for initialization

---

## Using the AgentRegistry System (Phase 0)

### Quick Reference

```python
from app.agents import AgentRegistry, Specialization, Department

# Get agent configuration
config = AgentRegistry.get_agent_config('cmo_001')

# Get agents by department
marketing_agents = AgentRegistry.get_agents_by_department(Department.MARKETING)

# Get required agents for a deliverable type
required = AgentRegistry.get_required_agents('marketing_campaign')

# Find agents by capability
python_devs = AgentRegistry.get_agents_by_capability(Specialization.PYTHON)

# Check if agent can handle a task
can_handle, missing = AgentRegistry.validate_agent_selection(['ceo_001', 'cmo_001'])

# Get detailed agent information
summary = AgentRegistry.get_agent_capability_summary('backend_001')
```

### Key Concepts

**Departments**: Organize agents by business function
- Executive, Engineering, Marketing, Sales, Finance, HR, Operations, Legal, Research

**Specializations**: Represent agent skills and capabilities
- PYTHON, FASTAPI, REACT, UI_DESIGN, STRATEGY, ANALYTICS, FINANCIAL_ANALYSIS, etc.

**Output Types**: What agents can produce
- CODE, DOCUMENT, PRESENTATION, ANALYSIS, REPORT, etc.

**Deliverable Types**: Project types with predefined team composition
- software_mvp, marketing_campaign, financial_analysis, business_proposal, etc.

### Agent Capability Utilities

Use `agent_capabilities.py` utilities for task assignment:

```python
from app.utils.agent_capabilities import (
    can_agent_handle_task,
    find_capable_agents,
    validate_team_composition,
    calculate_skill_match,
    suggest_agents_for_task
)

# Check if agent has required skills
can_handle, missing = can_agent_handle_task(
    'backend_001',
    required_skills=['python', 'fastapi'],
    required_output_type='code'
)

# Find agents for a task
agents = find_capable_agents(
    required_skills=['marketing_strategy', 'content_writing'],
    required_output_type='document'
)

# Validate team composition
is_valid, issues = validate_team_composition(['ceo_001', 'cto_001', 'backend_001'])

# Calculate match score (0.0-1.0)
score = calculate_skill_match('backend_001', ['python', 'fastapi'])

# Get agent recommendations
suggestions = suggest_agents_for_task('design', ['ui_design', 'ux_strategy'])
```

### Creating Projects with AgentRegistry

```python
from app.db.models import Project, ProjectStatus, Priority
from app.agents import AgentRegistry

# Get agents for a specific deliverable type
selected_agents = AgentRegistry.get_required_agents('marketing_campaign')

# Create project with custom team
project = Project(
    name='Q1 Marketing Campaign',
    project_type='marketing_campaign',
    deliverable_type='marketing_campaign',
    selected_agents=selected_agents,
    status=ProjectStatus.PLANNING,
    priority=Priority.HIGH,
    owner_agent_id='ceo_001'
)

# Database will validate team composition automatically
```

### Available Agents (25 Total)

See `PHASE_0_COMPLETE.md` for full agent list with details, or run:

```python
from app.agents import AgentRegistry

# List all agents
for agent_id, config in AgentRegistry.AGENT_CATALOG.items():
    print(f"{agent_id}: {config['name']} ({config['department']})")
```

---

## Troubleshooting

### Issue: Docker containers won't start

```powershell
# Check Docker is running
docker --version
docker-compose --version

# Restart Docker Desktop
# Check container status
docker-compose ps

# View container logs for errors
docker-compose logs postgres
docker-compose logs redis
```

### Issue: Database connection errors

```powershell
# Ensure PostgreSQL is healthy
docker-compose ps

# Check the DATABASE_URL in .env matches docker-compose.yml
# Default: postgresql+asyncpg://agent:your_password@localhost:5432/ai_company

# Recreate database
docker-compose down -v
docker-compose up -d postgres redis
# Wait 30 seconds
cd backend
alembic upgrade head
```

### Issue: "ANTHROPIC_API_KEY not set" error

```powershell
# Make sure .env file exists and contains your API key
cat .env | Select-String "ANTHROPIC"

# Verify the key is valid at https://console.anthropic.com/

# Restart the backend after updating .env
```

### Issue: Port already in use

```powershell
# Check what's using the port
netstat -ano | findstr :8000    # For backend
netstat -ano | findstr :5432    # For PostgreSQL
netstat -ano | findstr :6379    # For Redis

# Change ports in docker-compose.yml or stop conflicting services
```

### Issue: Agents not processing tasks

```powershell
# Check agent statuses
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/agents/status"

# Check for errors in agent logs
docker-compose logs -f backend

# Verify agents were initialized
docker-compose exec postgres psql -U agent -d ai_company -c "SELECT agent_id, name, role FROM agents;"
```

---

## Testing

### Run Unit Tests

```powershell
cd backend
pytest app/tests/ -v
```

### Run Integration Tests

```powershell
cd backend
pytest app/tests/integration/ -v
```

### End-to-End Test

```powershell
# This will test the full workflow
cd backend
pytest app/tests/test_e2e.py -v -s
```

---

## Current Implementation Status

### ✅ Phase 0: Flexible Foundation (COMPLETE)

- [x] AgentRegistry system with 25 agents
- [x] 9 departments across organization
- [x] 30+ specializations and capabilities
- [x] 10 deliverable types
- [x] Database migration with new tables and columns
- [x] Agent capability utilities
- [x] Backward compatible schema updates
- [x] 66 comprehensive tests (52 unit + 14 integration)
- [x] Non-breaking changes to existing data

### ✅ Stage 1: All 7 Agents (COMPLETE)

- [x] Project structure
- [x] Docker Compose configuration
- [x] PostgreSQL database schema (10 tables)
- [x] SQLAlchemy models with async support
- [x] Alembic migrations
- [x] Base agent class with LLM integration
- [x] CEO Agent - Strategic decisions and project evaluation
- [x] CTO Agent - Technical guidance and code review
- [x] PM Agent - Task breakdown and coordination
- [x] HR Agent - Agent health monitoring
- [x] Backend Engineer Agent - Python/FastAPI code generation
- [x] Frontend Engineer Agent - React/Next.js code generation
- [x] Designer Agent - UI/UX specifications
- [x] Database connection and session management
- [x] Environment configuration

### ✅ Stage 2: API & Orchestration (COMPLETE)

- [x] FastAPI routes with 15+ endpoints
- [x] Main orchestrator (app.main) with agent lifecycle
- [x] Agent initialization script
- [x] Complete REST API with Swagger docs
- [x] Dashboard endpoint with metrics
- [x] Health monitoring endpoints
- [x] Message and task filtering
- [x] Audit logging system

### ✅ Stage 3: Frontend Dashboard (COMPLETE)

- [x] Next.js 14 dashboard with App Router
- [x] Real-time project monitoring UI with auto-refresh
- [x] Agent status visualization with health indicators
- [x] Interactive task board with filtering
- [x] Message feed viewer with real-time updates
- [x] Dark mode support
- [x] Fully responsive design (mobile/tablet/desktop)
- [x] TypeScript throughout
- [x] React Query for state management
- [x] Beautiful UI with TailwindCSS

### 📋 Future Enhancements (Phase 2+)

- [ ] Code execution environment
- [ ] File generation system
- [ ] Multi-project parallel processing
- [ ] Additional specialist agents
- [ ] Production deployment configuration
- [ ] Monitoring and alerting (Prometheus/Grafana)

---

## What You Can Do Now

### ✅ Available Features

All Phase 1 MVP features are **fully operational**:

- **Create Projects**: Submit project requests via REST API or beautiful UI
- **Autonomous Agents**: 7 AI agents work together without human intervention
- **Complete Workflow**: From project request to code generation
- **Code Generation**: Backend (Python/FastAPI) and Frontend (React/Next.js) code
- **Design Specs**: Detailed UI/UX specifications
- **Monitoring**: Real-time agent status and task tracking via dashboard
- **Communication**: View inter-agent messages and decisions
- **Audit Trail**: Complete history of all agent actions
- **Modern Dashboard**: Next.js 14 frontend with real-time updates and dark mode

### 🎯 Next Steps

1. **Test the System** - Follow [TESTING_GUIDE.md](TESTING_GUIDE.md) or use the dashboard at http://localhost:3000
2. **Deploy** - Production deployment guide available
3. **Expand** - Phase 2 features (more agents, file generation, code execution, etc.)

---

## Resources

### Documentation

**Phase 1 Documentation:**
- **[PHASE_1_COMPLETE.md](PHASE_1_COMPLETE.md)** - Complete Phase 1 API implementation summary
- **[PHASE_1_SUMMARY.md](PHASE_1_SUMMARY.md)** - Quick executive summary
- **[PHASE_1_PLAN.md](PHASE_1_PLAN.md)** - Detailed implementation plan

**Phase 0 Documentation:**
- **[PHASE_0_COMPLETE.md](PHASE_0_COMPLETE.md)** - Complete Phase 0 implementation summary
- **[PHASE_0_PROGRESS.md](PHASE_0_PROGRESS.md)** - Detailed Phase 0 progress tracking

**Phase 1 & Setup Documentation:**
- **[QUICK_START.md](QUICK_START.md)** - Get running locally in 5 minutes
- **[COMPLETE_SETUP_GUIDE.md](COMPLETE_SETUP_GUIDE.md)** - Full local setup guide
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Comprehensive test scenarios
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete deployment documentation
- **[DEPLOYMENT_QUICK_START.md](DEPLOYMENT_QUICK_START.md)** - Deploy to production in 30 minutes
- **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Current implementation status
- **[STAGE_1_COMPLETE.md](STAGE_1_COMPLETE.md)** - Agent implementation details
- **[STAGE_2_COMPLETE.md](STAGE_2_COMPLETE.md)** - API documentation
- **[STAGE_3_COMPLETE.md](STAGE_3_COMPLETE.md)** - Frontend dashboard details
- **`docs/` folder** - Detailed architecture and business plan

### Live Resources
- **API Docs**: http://localhost:8000/docs (when running)
- **Anthropic Claude**: https://console.anthropic.com/docs
- **FastAPI**: https://fastapi.tiangolo.com/
- **SQLAlchemy**: https://docs.sqlalchemy.org/
- **Next.js**: https://nextjs.org/docs

---

## Support & Contributing

For issues, questions, or contributions, please refer to the project documentation in the `docs/` folder.

## License

[Add your license here]

---

## Phase 1 MVP - Success! ✅

**Goal**: Build a working 7-agent system that can complete projects autonomously.

**Success Criteria** (All Met):
- ✅ All 7 agents operational with 15-minute check cycles
- ✅ Complete end-to-end workflow (human request → code output)
- ✅ Autonomous operation with zero human intervention required
- ✅ High-quality code generation (Backend, Frontend, Design)
- ✅ Real-time monitoring and status tracking
- ✅ Complete audit trail and message history

**Timeline**: Simple projects complete in ~3 hours with time-compressed agent work (1 hour = 1 agent day)

**Ready to Use**: Follow [QUICK_START.md](QUICK_START.md) to get started in 5 minutes!
