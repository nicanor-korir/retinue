# Retinue - Complete Setup Guide

**Get your AI Agent Company running in 15 minutes!**

This guide covers both backend and frontend setup for the complete Retinue platform.

---

## Prerequisites

Before starting, ensure you have:

✅ **Docker Desktop** - For PostgreSQL and Redis
- Download: https://www.docker.com/products/docker-desktop
- Verify: `docker --version`

✅ **Python 3.11+** - For backend
- Download: https://www.python.org/downloads/
- Verify: `python --version`

✅ **Node.js 18+** - For frontend dashboard
- Download: https://nodejs.org/
- Verify: `node --version`

✅ **Anthropic API Key** - For AI agents
- Get from: https://console.anthropic.com/

---

> **Cost warning.** Agents make real Claude API calls, and a small project typically costs a few dollars. Start small and watch your usage the first time through.

> **Don't run `docker-compose up` on its own.** The compose file declares `backend` and `frontend` services, but `frontend/Dockerfile` doesn't exist yet and the containers skip database setup. Start only `postgres` and `redis` from Docker, as this guide does, and run the applications natively.

---

## Quick Setup (Recommended)

### Option A: Automated Setup (Windows only)

From the repository root:

```powershell
.\quick-setup.ps1
```

This sets up the backend only. Continue with the frontend setup below afterward.

### Option B: Manual Setup

Follow the step-by-step instructions below. This works on every platform and is worth doing once even on Windows, so you know what the script did.

---

## Part 1: Backend Setup

All commands assume you start from the repository root.

### Step 1: Configure Environment

```bash
# macOS / Linux
cp .env.example .env

# Windows PowerShell
Copy-Item .env.example .env
```

Then open `.env` in any editor.

Add your Anthropic API key:
```env
ANTHROPIC_API_KEY=sk-ant-xxxxx
DB_PASSWORD=your_secure_password
```

### Step 2: Start Docker Services

```bash
# Start PostgreSQL and Redis (not the other services — see the note above)
docker-compose up -d postgres redis

# Wait ~30 seconds for health checks, then verify
docker-compose ps
```

You should see both services as "healthy". If they aren't, give them another 30 seconds — Postgres initializes its data directory on first run.

### Step 3: Setup Python Environment

```bash
cd backend
python -m venv venv
```

Activate it:

```bash
# macOS / Linux
source venv/bin/activate

# Windows PowerShell
.\venv\Scripts\Activate.ps1
```

Your prompt should now show `(venv)`. Then install dependencies:

```bash
pip install -r requirements.txt
```

### Step 4: Initialize Database

```powershell
# Create database tables (includes Knowledge Base and Multi-Agent Chat tables)
alembic upgrade head

# Initialize the 7 AI agents
python -m app.scripts.init_agents

# Seed agent expertise tags (for multi-agent discovery)
python -m app.scripts.seed_agent_expertise

# (Optional) Initialize knowledge system with default categories
python -m app.scripts.init_knowledge_system
```

You should see confirmation that all 7 agents were created and expertise tags seeded.

### Step 5: Start Backend Server

```powershell
# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Backend is now running!**

- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

Keep this terminal open.

---

## Part 2: Frontend Setup

Open a **new terminal window**.

### Step 6: Navigate to Frontend

```powershell
cd "Domains\02-shoman-saas-domain\apps\Retinue\frontend"
```

### Step 7: Install Dependencies

```powershell
npm install
```

This will install all required packages (~1-2 minutes).

### Step 8: Configure Environment

The `.env.local` file should already exist with:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

If not, create it with the above content.

### Step 9: Start Frontend Development Server

```powershell
npm run dev
```

**Dashboard is now running!**

- Dashboard: http://localhost:3000

---

## Verification

### Test Backend

Open http://localhost:8000/health

You should see:
```json
{
  "status": "healthy",
  "agents_count": 7,
  "agents": {
    "ceo": "running",
    "cto": "running",
    "pm": "running",
    "hr": "running",
    "backend": "running",
    "frontend": "running",
    "designer": "running"
  }
}
```

### Test Frontend

Open http://localhost:3000

You should see:
- Beautiful dashboard with dark mode toggle
- Agent status cards
- System health indicator
- Navigation sidebar

---

## Create Your First Project

### Via Dashboard (Recommended)

1. Go to http://localhost:3000
2. Click "Projects" in sidebar
3. Click "New Project" button
4. Fill in the form:
   - Name: "Simple Todo App"
   - Description: "Build a todo list with user auth, CRUD operations, and clean UI"
   - Priority: High
5. Click "Create Project"
6. Watch the progress!

### Via API

```powershell
$project = @{
    name = "Todo App"
    description = "Build a todo list with authentication and CRUD operations"
    priority = "high"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/projects" `
    -Method Post `
    -ContentType "application/json" `
    -Body $project
```

---

## What Happens Next?

Once you create a project:

| Time | Agent | Action |
|------|-------|--------|
| 0 min | You | Create project |
| ~15 min | CEO | Evaluates and approves |
| ~30 min | CTO | Provides technical guidance |
| ~45 min | PM | Breaks down into tasks |
| ~60 min | Designer | Creates UI/UX specs |
| ~90 min | Backend Eng | Writes Python/FastAPI code |
| ~120 min | Frontend Eng | Writes React/Next.js code |
| ~150 min | CTO | Reviews all code |
| ~180 min | System | **Project complete!** |

**Total**: ~3 hours for autonomous development

---

## Monitoring Progress

### Dashboard (Recommended)

Visit http://localhost:3000 and navigate to:

- **Dashboard** - Overview with key metrics
- **Projects** - See your project and its status
- **Agents** - Monitor agent availability
- **Tasks** - Track individual tasks
- **Messages** - View agent communications

Everything updates automatically!

### API Endpoints

```powershell
# Dashboard metrics
Invoke-RestMethod http://localhost:8000/api/v1/dashboard

# All projects
Invoke-RestMethod http://localhost:8000/api/v1/projects

# Specific project
Invoke-RestMethod "http://localhost:8000/api/v1/projects/{project-id}"

# Agent status
Invoke-RestMethod http://localhost:8000/api/v1/agents/status

# All tasks
Invoke-RestMethod http://localhost:8000/api/v1/tasks

# Recent messages
Invoke-RestMethod "http://localhost:8000/api/v1/messages?limit=20"
```

---

## Stopping the System

### Gracefully

```powershell
# In backend terminal
Press Ctrl+C

# In frontend terminal
Press Ctrl+C

# Stop Docker services
docker-compose stop
```

### Complete Shutdown

```powershell
# Stop and remove containers
docker-compose down

# If you want to clear data (start fresh)
docker-compose down -v
```

---

## Restarting

### Backend

```bash
cd backend
source venv/bin/activate        # Windows: .\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```powershell
cd frontend
npm run dev
```

### Docker Services (if stopped)

```powershell
docker-compose up -d postgres redis
```

---

## Troubleshooting

### "Backend not connecting"

1. Check backend is running: http://localhost:8000/health
2. Verify `.env` has `ANTHROPIC_API_KEY`
3. Restart backend server

### "Frontend showing errors"

1. Ensure backend is running on port 8000
2. Check `.env.local` has `NEXT_PUBLIC_API_URL=http://localhost:8000`
3. Restart frontend: `npm run dev`

### "Agents not working"

1. Check API key is valid
2. Verify agents initialized:
```powershell
docker-compose exec postgres psql -U agent -d ai_company -c "SELECT agent_id, name FROM agents;"
```
3. Re-initialize if needed:
```bash
cd backend
source venv/bin/activate        # Windows: .\venv\Scripts\Activate.ps1
python -m app.scripts.init_agents
```

### "Docker services won't start"

1. Ensure Docker Desktop is running
2. Restart Docker Desktop
3. Try:
```powershell
docker-compose down -v
docker-compose up -d postgres redis
```

### "Port already in use"

```powershell
# Check what's using ports
netstat -ano | findstr :8000  # Backend
netstat -ano | findstr :3000  # Frontend
netstat -ano | findstr :5432  # PostgreSQL
```

Change ports in configuration if needed.

---

## Production Build

### Backend

```powershell
cd backend

# Install production dependencies
pip install -r requirements.txt

# Use production server (Gunicorn)
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Frontend

```powershell
cd frontend

# Build for production
npm run build

# Start production server
npm start
```

---

## Next Steps

### Learn More

- [Root README](../README.md) — what Retinue is, core concepts, project structure
- [docs/README.md](README.md) — the documentation map, with three onboarding paths
- [ARCHITECTURE.md](ARCHITECTURE.md) — full system architecture
- [PROJECT_STATUS.md](PROJECT_STATUS.md) — what's built and what's in progress
- [../frontend/README.md](../frontend/README.md) — frontend-specific docs
- **http://localhost:8000/docs** — interactive API reference, generated from the code

### Explore Features

1. **Create Multiple Projects** - Test different types of applications
2. **Monitor Agents** - Watch them collaborate in real-time
3. **Review Generated Code** - Check task outputs
4. **Test Dark Mode** - Toggle theme in dashboard
5. **Use Mobile** - Dashboard is fully responsive
6. **Multi-Agent Chat** - Start a conversation and invite multiple agents
7. **Knowledge Base** - See how agents learn from conversations
8. **Agent Discovery** - Watch the system suggest relevant agents

### Deploy

Ready to deploy? See **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)**, which covers Vercel (frontend), Heroku (backend), and full-stack deployment to AWS, Azure, and Google Cloud.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                    User/Browser                      │
│  ┌──────────────────────────────────────────────┐   │
│  │ Chat Widget + Agent Suggestions + Presence   │   │
│  └──────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
    ┌────▼─────┐          ┌─────▼─────┐
    │ Frontend │          │  Backend  │
    │ Next.js  │◄────────►│  FastAPI  │
    │ :3000    │   API    │  :8000    │
    └──────────┘          └─────┬─────┘
                                │
         ┌──────────────────────┼──────────────────────┐
         │                      │                      │
   ┌─────▼──┐  ┌────────┐  ┌───▼────┐  ┌───────────┐
   │Postgres│  │ChromaDB│  │ Redis  │  │ Anthropic │
   │ :5432  │  │(Vector)│  │ :6379  │  │  Claude   │
   └────────┘  └────────┘  └────────┘  └───────────┘
         │
  ┌──────┴──────────────────────────────────────────┐
  │                7 AI Agents                        │
  │  CEO, CTO, PM, HR, Backend, Frontend, Designer  │
  ├──────────────────────────────────────────────────┤
  │ Knowledge Base │ Multi-Agent Chat │ Discovery    │
  └──────────────────────────────────────────────────┘
```

---

## Quick Reference

### Ports

| Service | Port | URL |
|---------|------|-----|
| Frontend | 3000 | http://localhost:3000 |
| Backend API | 8000 | http://localhost:8000 |
| PostgreSQL | 5432 | Internal |
| Redis | 6379 | Internal |

### Key Files

| File | Purpose |
|------|---------|
| `.env` | Backend environment variables |
| `frontend/.env.local` | Frontend environment variables |
| `docker-compose.yml` | Docker service configuration |
| `backend/requirements.txt` | Python dependencies |
| `frontend/package.json` | Node.js dependencies |

### Useful Commands

```powershell
# Check system status
Invoke-RestMethod http://localhost:8000/health

# View Docker logs
docker-compose logs -f

# Access database
docker-compose exec postgres psql -U agent -d ai_company

# Clear and restart
docker-compose down -v && docker-compose up -d postgres redis
```

---

## Support

For issues, questions, or enhancements:

1. Check troubleshooting section above
2. Review documentation in project root
3. Check API docs: http://localhost:8000/docs
4. Review agent logs in backend terminal

---

**🎉 Congratulations! Your AI Agent Company is ready to build software!**

Start by creating a project and watch your agents collaborate autonomously.

**Recommended First Project**: "Build a simple todo list app with user authentication, CRUD operations for tasks, and a modern UI using React and PostgreSQL"

Have fun building with AI agents! 🚀
