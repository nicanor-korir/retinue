# Deviant Documentation

**Complete documentation for the AI Agent Company Platform**

---

## 🚀 Quick Start

**New to Deviant?** Start here:

1. **[GETTING-STARTED.md](GETTING-STARTED.md)** - Complete setup guide (15 minutes)
2. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Commands and quick tips
3. **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - What's built and working

---

## 📚 Documentation Structure

### Getting Started
- **[GETTING-STARTED.md](GETTING-STARTED.md)** - Step-by-step setup for backend and frontend
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - One-page command reference

### Core Documentation
- **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Current project status and capabilities
- **[BUSINESS_PLAN.md](BUSINESS_PLAN.md)** - Vision, strategy, and roadmap
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Production deployment to various platforms

### Technical Documentation
- **[REAL_TIME_EVENTS_README.md](REAL_TIME_EVENTS_README.md)** - Real-time event system
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Event-driven implementation
- **[REAL_TIME_EXECUTION_IMPLEMENTATION.md](REAL_TIME_EXECUTION_IMPLEMENTATION.md)** - Execution architecture
- **[MIGRATION_GUIDE_EVENT_DRIVEN.md](MIGRATION_GUIDE_EVENT_DRIVEN.md)** - Migration to event-driven mode
- **[AGENT_EVENT_INTEGRATION_GUIDE.md](AGENT_EVENT_INTEGRATION_GUIDE.md)** - Agent integration guide

### Reference Materials
- **[reference/](reference/)** - Original specifications and design documents
  - [IMPLEMENTATION.md](reference/IMPLEMENTATION.md) - Original technical specification
  - [PROMPT.md](reference/PROMPT.md) - Original requirements
  - [MESSAGES_REDESIGN.md](reference/MESSAGES_REDESIGN.md) - Messages system design

### Historical Archive
- **[archive/](archive/)** - Historical development snapshots
  - Stage completion summaries (STAGE_1, STAGE_2, STAGE_3)
  - Individual feature documentation
  - Outdated setup guides

---

## 🎯 Common Tasks

### I want to...

**Get started quickly**
→ See [GETTING-STARTED.md](GETTING-STARTED.md)

**Find a specific command**
→ See [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

**Deploy to production**
→ See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

**Understand the architecture**
→ See [REAL_TIME_EVENTS_README.md](REAL_TIME_EVENTS_README.md) and [reference/IMPLEMENTATION.md](reference/IMPLEMENTATION.md)

**Migrate to event-driven mode**
→ See [MIGRATION_GUIDE_EVENT_DRIVEN.md](MIGRATION_GUIDE_EVENT_DRIVEN.md)

**Check current project status**
→ See [PROJECT_STATUS.md](PROJECT_STATUS.md)

**Understand the business strategy**
→ See [BUSINESS_PLAN.md](BUSINESS_PLAN.md)

---

## 📖 What is Deviant?

Deviant is an **autonomous multi-agent AI system** that operates like a real company, with:

- **7 AI Agents**: CEO, CTO, PM, HR, Backend Engineer, Frontend Engineer, Designer
- **Event-Driven Architecture**: <100ms response times (10-30x faster than polling)
- **Autonomous Collaboration**: Agents work together to build software projects
- **Human Oversight**: Strategic decisions require human approval
- **Complete Audit Trail**: Every action and decision is logged
- **Intelligent Knowledge Base**: AI-powered knowledge extraction and retrieval
- **Multi-Agent Chat**: Dynamic agent collaboration in conversations

### The 7 Agents

| Agent | Role | Responsibilities |
|-------|------|------------------|
| **CEO** | Chief Executive Officer | Evaluates projects, makes strategic decisions |
| **CTO** | Chief Technology Officer | Technical guidance, code review, architecture |
| **PM** | Project Manager | Breaks down projects, assigns tasks, tracks progress |
| **HR** | Human Resources | Monitors agent health, intervenes when stuck |
| **Backend** | Senior Backend Engineer | Generates Python/FastAPI code |
| **Frontend** | Senior Frontend Engineer | Generates React/Next.js code |
| **Designer** | Product Designer | Creates UI/UX specifications |

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                    User Interface                     │
│              (Web Dashboard / API Calls)              │
└────────────────────┬────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
    ┌────▼─────┐          ┌─────▼─────┐
    │ Frontend │          │  Backend  │
    │ Next.js  │◄────────►│  FastAPI  │
    │          │   API    │           │
    └──────────┘          └─────┬─────┘
                                │
                    ┌───────────┼───────────┐
                    │           │           │
              ┌─────▼──┐  ┌────▼────┐ ┌───▼──────┐
              │Postgres│  │  Redis  │ │ Anthropic│
              │        │  │         │ │  Claude  │
              └────────┘  └─────────┘ └──────────┘
                    │
         ┌──────────┴──────────┐
         │    7 AI Agents       │
         │  Autonomous Work     │
         │  Event-Driven        │
         └─────────────────────┘
```

### Key Technologies

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.0
- **Frontend**: Next.js 14, React 18, TailwindCSS
- **Database**: PostgreSQL 15, Redis 7
- **AI**: Anthropic Claude 3.5 Sonnet
- **Infrastructure**: Docker, Docker Compose

---

## ⚡ Performance

### Event-Driven Mode (Current)
- **Agent Response**: <100ms (vs 0-15 minutes with polling)
- **Simple Project**: 10-15 minutes (vs ~4.5 hours)
- **Medium Project**: 30-45 minutes (vs ~8.5 hours)

**10-30x faster than polling mode!**

---

## 📦 What's Included

### Backend
- 7 fully implemented AI agents
- Complete REST API (30+ endpoints)
- Event-driven execution system
- Real-time agent communication
- Database schema (30+ tables)
- Migration system
- Health monitoring
- **Intelligent Knowledge Base** with hybrid search (vector + full-text)
- **Multi-Agent Chat** with dynamic agent invitations
- **Agent Discovery** with expertise-based matching

### Frontend (Optional)
- Modern Next.js dashboard
- Real-time status updates
- Agent monitoring
- Task tracking
- Dark mode support
- Fully responsive
- **Chat Widget** with markdown rendering
- **Agent Suggestions Panel** with AI-powered recommendations
- **Participant List** with real-time presence indicators

---

## 🎓 Learning Path

### Beginner
1. Read [GETTING-STARTED.md](GETTING-STARTED.md)
2. Follow setup instructions
3. Create your first project
4. Watch agents collaborate

### Intermediate
1. Read [PROJECT_STATUS.md](PROJECT_STATUS.md)
2. Explore [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
3. Review [REAL_TIME_EVENTS_README.md](REAL_TIME_EVENTS_README.md)
4. Experiment with different project types

### Advanced
1. Study [reference/IMPLEMENTATION.md](reference/IMPLEMENTATION.md)
2. Review [MIGRATION_GUIDE_EVENT_DRIVEN.md](MIGRATION_GUIDE_EVENT_DRIVEN.md)
3. Read [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
4. Deploy to production

---

## 🚀 Status: Production Ready

✅ **Phase 1 MVP Complete**
- All 7 agents operational
- Complete REST API
- Event-driven execution
- Real-time monitoring
- Production deployment ready

✅ **Intelligent Knowledge Base**
- Automatic knowledge extraction from conversations
- Hybrid search (vector + full-text + exact matching)
- User profiles and preferences
- Predictive agent involvement

✅ **Multi-Agent Chat**
- Dynamic agent invitations in conversations
- Auto-join for highly relevant agents (>90%)
- Real-time presence indicators
- Context briefings for joining agents

For current status, see [PROJECT_STATUS.md](PROJECT_STATUS.md)

---

## 🤝 Support & Resources

### Documentation
- **Setup Help**: [GETTING-STARTED.md](GETTING-STARTED.md)
- **Quick Commands**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- **Technical Details**: [REAL_TIME_EVENTS_README.md](REAL_TIME_EVENTS_README.md)
- **Deployment**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

### While Running
- **API Docs**: http://localhost:8000/docs (interactive)
- **Health Check**: http://localhost:8000/health
- **Dashboard**: http://localhost:3000 (if frontend running)

### Troubleshooting
See [QUICK_REFERENCE.md](QUICK_REFERENCE.md#troubleshooting-quick-fixes) for common issues and solutions.

---

## 📝 Recent Updates

**November 28, 2025** - Knowledge Base & Multi-Agent Chat
- Added Intelligent Knowledge Base with AI-powered extraction
- Implemented Multi-Agent Chat with dynamic collaboration
- Added agent discovery and expertise matching
- Enhanced chat with markdown rendering
- Added real-time presence indicators

**October 30, 2025** - Documentation consolidation
- Reorganized documentation structure
- Created clear entry points
- Archived historical documents
- Consolidated redundant content
- Improved navigation

---

## 🔗 Quick Links

| Resource | Link |
|----------|------|
| **Quick Start** | [GETTING-STARTED.md](GETTING-STARTED.md) |
| **Commands** | [QUICK_REFERENCE.md](QUICK_REFERENCE.md) |
| **Status** | [PROJECT_STATUS.md](PROJECT_STATUS.md) |
| **Deploy** | [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) |
| **Business** | [BUSINESS_PLAN.md](BUSINESS_PLAN.md) |
| **Technical** | [REAL_TIME_EVENTS_README.md](REAL_TIME_EVENTS_README.md) |
| **Reference** | [reference/](reference/) |
| **Archive** | [archive/](archive/) |

---

**Ready to get started?** → [GETTING-STARTED.md](GETTING-STARTED.md)

**🎉 Your AI agent company is ready to build software for you!**
