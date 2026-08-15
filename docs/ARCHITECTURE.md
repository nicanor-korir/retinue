# Retinue - Complete Architecture & Design Document

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Project Overview](#project-overview)
3. [System Architecture](#system-architecture)
4. [Core Components](#core-components)
5. [Database Design](#database-design)
6. [API Design](#api-design)
7. [Frontend Architecture](#frontend-architecture)
8. [Event-Driven System](#event-driven-system)
9. [Agent System](#agent-system)
10. [Key Workflows](#key-workflows)
11. [Deployment](#deployment)
12. [Technology Stack](#technology-stack)

---

## Executive Summary

**Retinue** is an innovative event-driven multi-agent AI platform that simulates a fully functional software company. Seven autonomous AI agents collaborate in real-time to analyze project requests, break them down into tasks, execute development work, and deliver complete software solutions.

### Key Characteristics
- **7 Autonomous Agents**: CEO, CTO, PM, HR, Backend Engineer, Frontend Engineer, Designer
- **Event-Driven Architecture**: <100ms response latency between agent actions
- **Real-Time Monitoring**: Glass-box AI with complete visibility into agent reasoning
- **Advanced Escalation Management**: Automatic issue tracking and resolution
- **Production-Grade Infrastructure**: Docker, PostgreSQL, Redis, FastAPI, Next.js
- **AI-Powered**: Anthropic Claude 3.5 Sonnet integration with streaming support

### Execution Timeline
- **Event-Driven Mode**: Projects complete in seconds to minutes (real-time agent coordination)
- **Polling Mode**: Projects complete in ~3 hours (15-minute agent check cycles)
- **Hybrid Mode**: Combination of event-driven and periodic checks

---

## Project Overview

### Mission
Create a functional AI-powered software company that can autonomously receive project requests from humans, break them down, execute tasks through specialized agents, and deliver complete software solutions without human intervention.

### Architecture Overview
```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                        │
│  Dashboard │ Projects │ Agents │ Tasks │ Messages │ Escalations  │
└────────────────────────────┬──────────────────────────────────────┘
                             │ REST API + WebSocket
┌────────────────────────────▼──────────────────────────────────────┐
│                      FastAPI Backend Layer                         │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │        Event-Driven System (Event Bus + Redis)              │ │
│  │  • Real-time event delivery (<100ms latency)               │ │
│  │  • Guaranteed delivery with retry logic                     │ │
│  │  • 30+ event types for system coordination                  │ │
│  └──────────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │              Multi-Agent System (7 Agents)                   │ │
│  │  ┌─────────┐  ┌─────────┐  ┌──────────┐                    │ │
│  │  │   CEO   │─▶│  CTO    │◀─┤   PM     │                    │ │
│  │  └─────────┘  └─────────┘  └──────────┘                    │ │
│  │       △           △              △                           │ │
│  │       │           │              │                           │ │
│  │       └───────────┼──────────────┘                           │ │
│  │                   │                                           │ │
│  │  ┌──────────────────────────────────────────────────────┐   │ │
│  │  │  Backend Engineer   Frontend Engineer    Designer     │   │ │
│  │  └──────────────────────────────────────────────────────┘   │ │
│  │                                                              │ │
│  │  ┌──────────────────────────────────────────────────────┐   │ │
│  │  │     HR Agent (Continuous Monitoring & Health)        │   │ │
│  │  └──────────────────────────────────────────────────────┘   │ │
│  └──────────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                  Services Layer                               │ │
│  │  • Escalation Management • Feedback System                   │ │
│  │  • Task Dependency Resolution • Health Monitoring            │ │
│  │  • WebSocket Broadcasting • Export Services                  │ │
│  └──────────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                    API Layer (REST)                           │ │
│  │  • Projects • Agents • Tasks • Messages                       │ │
│  │  • Escalations • Feedback • Dashboard Metrics                │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬──────────────────────────────────────┘
                             │ SQLAlchemy ORM
┌────────────────────────────▼──────────────────────────────────────┐
│               Database Layer (PostgreSQL + Redis)                   │
│  ┌─────────────┬────────────┬────────────┬──────────────┐         │
│  │   Agents    │  Projects  │   Tasks    │  Messages    │         │
│  │   Decisions │Escalations │  Feedback  │  Audit Log   │         │
│  │ Agent Status│ Knowledge  │   Events   │  Settings    │         │
│  └─────────────┴────────────┴────────────┴──────────────┘         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## System Architecture

### 1. High-Level Architecture Pattern

Retinue follows a **Layered Architecture** with **Event-Driven** communication:

```
┌─────────────────────────────────────────────┐
│       Presentation Layer (Next.js)          │
│       Dashboard & Real-time Monitoring      │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│         API Layer (REST + WebSocket)        │
│     Routes, Request Validation, Response    │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│        Business Logic Layer (Services)      │
│  Event Bus, Escalations, Monitoring, etc    │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│      Multi-Agent Orchestration Layer        │
│     7 Specialized Autonomous Agents         │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│  Data Access Layer (SQLAlchemy ORM)         │
│     Database Models & Query Layer           │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│    Persistence Layer (PostgreSQL + Redis)   │
│  Structured Data, Real-time Events, Cache   │
└──────────────────────────────────────────────┘
```

### 2. Core Architectural Principles

| Principle | Implementation |
|-----------|-----------------|
| **Event-Driven** | Real-time event bus with <100ms latency |
| **Asynchronous** | FastAPI async/await throughout |
| **Scalable** | Event-driven avoids polling bottlenecks |
| **Resilient** | Retry logic, graceful degradation, monitoring |
| **Observable** | Complete audit trail, real-time activity tracking |
| **Modular** | Clear separation of concerns (agents, services, APIs) |
| **Type-Safe** | Full TypeScript frontend, Python type hints |

### 3. Data Flow

#### Synchronous Request-Response
```
Frontend Request
     ↓
API Route Handler (validates, authorizes)
     ↓
Service Layer (business logic)
     ↓
Database Query (SQLAlchemy ORM)
     ↓
PostgreSQL (execute)
     ↓
Response Builder
     ↓
Frontend Response
```

#### Asynchronous Event-Driven
```
Database Change (task created, approved, etc)
     ↓
Event Publisher (automatic via trigger/ORM hook)
     ↓
Event Bus (Redis Pub/Sub or in-memory)
     ↓
Agent Subscribers (listening to relevant events)
     ↓
Agent Processing (immediate action)
     ↓
Event Created (new task, message sent, etc)
     ↓
WebSocket Broadcaster (real-time dashboard update)
     ↓
Frontend Update (live activity)
```

---

## Core Components

### 1. Multi-Agent System

#### A. Agent Roles and Hierarchy

**Organizational Chart:**
```
                     HUMAN FOUNDER
                           ▲
                           │
                        CEO AGENT
                      /    │    \
                   CTO  HR  PM    Human Input Handler
                  /  \    \      /
        Backend  Frontend  Designer
        Engineer Engineer
```

#### B. The 7 Agents

##### 1. CEO Agent (`ceo_agent.py`)
**Role**: Strategic decision maker and project approver
**Responsibilities**:
- Receives and evaluates project proposals from humans
- Analyzes feasibility, scope, and resource requirements
- Consults with CTO on technical aspects
- Makes final approval/rejection decisions
- Convenes executive meetings
- Escalates critical issues
- Delivers final project results to humans

**Authority**: Full project approval/rejection
**Reports To**: Human founder
**Key Methods**:
- `evaluate_project()`: Initial analysis
- `make_decision()`: Approval/rejection
- `consult_with_cto()`: Technical discussion
- `handle_escalation()`: Issue resolution

**LLM Prompt Focus**: Strategic analysis, business viability, risk assessment

##### 2. CTO Agent (`cto_agent.py`)
**Role**: Technical architecture and quality assurance
**Responsibilities**:
- Technical feasibility review
- Architecture design oversight
- Code quality review and approval
- Provides technical guidance to engineers
- Database schema review
- API design review
- Performance and scalability assessment

**Authority**: Technical approval of all implementations
**Reports To**: CEO
**Key Methods**:
- `technical_review()`: Architecture assessment
- `code_review()`: Quality check
- `provide_guidance()`: Technical mentoring

**LLM Prompt Focus**: Software architecture, technical best practices, code quality

##### 3. Project Manager Agent (`pm_agent.py`)
**Role**: Work coordination and task management
**Responsibilities**:
- Breaking down projects into manageable tasks
- Assigning tasks to specialist agents (Backend, Frontend, Designer)
- Creating task dependencies
- Monitoring progress
- Tracking project timeline
- Handling blockers
- Detecting project completion

**Authority**: Task creation, assignment, dependency management
**Reports To**: CEO
**Key Methods**:
- `break_down_project()`: Create task list
- `assign_tasks()`: Distribute work
- `monitor_progress()`: Status tracking
- `detect_completion()`: Final project status

**LLM Prompt Focus**: Project management, task breakdown, planning, coordination

##### 4. HR Agent (`hr_agent.py`)
**Role**: Agent health monitoring and issue resolution
**Responsibilities**:
- Continuous agent health monitoring (30-second intervals)
- Detecting inactive agents (30min warning, 1hr critical)
- Identifying stuck tasks (2+ hours in-progress)
- Monitoring review timeouts (4+ hours in approval)
- Creating escalations for persistent issues
- Providing intervention instructions
- Tracking agent performance metrics

**Authority**: Escalation creation, agent intervention
**Reports To**: CEO
**Special Feature**: Only agent with continuous monitoring cycle (not on demand)

**Key Methods**:
- `monitor_agents()`: Health check loop
- `detect_issues()`: Problem identification
- `create_escalation()`: Issue escalation
- `provide_intervention()`: Guidance

**LLM Prompt Focus**: Problem identification, agent motivation, issue escalation

##### 5. Backend Engineer Agent (`backend_engineer_agent.py`)
**Role**: Python/FastAPI implementation
**Responsibilities**:
- Writing Python code (API endpoints, services, utilities)
- Database schema design and migrations
- API endpoint implementation
- Error handling implementation
- Testing code generation
- Documentation writing

**Authority**: Backend implementation decisions
**Reports To**: CTO
**Key Methods**:
- `write_code()`: Generate Python code
- `design_schema()`: Database design
- `create_endpoints()`: API creation
- `write_tests()`: Test generation

**LLM Prompt Focus**: Python, FastAPI, SQLAlchemy, async/await, best practices

##### 6. Frontend Engineer Agent (`frontend_engineer_agent.py`)
**Role**: React/Next.js implementation
**Responsibilities**:
- Writing TypeScript/React code
- Component development
- UI implementation
- State management
- Testing code generation
- Documentation

**Authority**: Frontend implementation decisions
**Reports To**: CTO
**Key Methods**:
- `write_component()`: React component generation
- `implement_feature()`: Full feature implementation
- `write_tests()`: Frontend test generation

**LLM Prompt Focus**: React, Next.js, TypeScript, TailwindCSS, best practices

##### 7. Designer Agent (`designer_agent.py`)
**Role**: UI/UX and design specifications
**Responsibilities**:
- Creating UI/UX specifications
- Component design and wireframes
- Design system documentation
- Visual guidelines
- Accessibility specifications
- Design review and feedback

**Authority**: Design specifications and guidelines
**Reports To**: PM
**Key Methods**:
- `create_design()`: Design specifications
- `create_wireframes()`: Component layouts
- `define_design_system()`: Design tokens

**LLM Prompt Focus**: UI/UX design, accessibility, design systems

#### C. Agent Communication Patterns

**Message Types:**
1. **INFO**: Informational updates ("Task completed")
2. **REQUEST**: Work requests ("Please review this code")
3. **APPROVAL**: Approval requests ("Do you approve this approach?")
4. **ALERT**: Critical notifications ("Task timeout approaching")

**Communication Channels:**
1. **Messages Table**: Persistent, queryable, timestamped
2. **Event Bus**: Real-time, guaranteed delivery
3. **WebSocket**: Broadcasting to dashboard

#### D. Agent Execution Model

**Three Modes:**

| Mode | Trigger | Latency | Use Case |
|------|---------|---------|----------|
| **Event-Driven** | Event arrival | <100ms | Production, fast coordination |
| **Hybrid** | Events + 15min check | <100ms for events | Balanced approach |
| **Polling** | 15-minute check interval | ~15min | Legacy, resource-constrained |

**Agent Lifecycle:**
```
[Available] ←──────────────────────────────────────┐
    ↓                                               │
[Process Event/Task]                               │
    ↓                                               │
[Call LLM] (streaming support)                     │
    ↓                                               │
[Create Output/Message/Task]                       │
    ↓                                               │
[Trigger Events]                                   │
    ↓                                               │
[Update Status] ─────────────────────────────────→ [Available]
```

---

## Database Design

### 1. Database Overview

**Database**: PostgreSQL 15+
**ORM**: SQLAlchemy 2.0 with async support
**Async Driver**: asyncpg
**Migrations**: Alembic

### 2. Core Tables

#### Table 1: `agents`
Defines all available agents in the system.

```sql
CREATE TABLE agents (
  agent_id UUID PRIMARY KEY,
  name VARCHAR(100) NOT NULL UNIQUE,
  role VARCHAR(50) NOT NULL,
  department VARCHAR(100),
  permissions JSONB,
  system_prompt TEXT NOT NULL,
  llm_model VARCHAR(100) DEFAULT 'claude-3.5-sonnet',
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Data**:
- CEO, CTO, PM, HR, Backend Engineer, Frontend Engineer, Designer
- Each with specialized system prompts
- Configurable LLM model per agent
- Permission matrix for authorization

#### Table 2: `agent_status`
Real-time status of each agent.

```sql
CREATE TABLE agent_status (
  status_id UUID PRIMARY KEY,
  agent_id UUID NOT NULL REFERENCES agents(agent_id),
  availability VARCHAR(50), -- AVAILABLE, BUSY, BLOCKED, OFFLINE
  current_task_id UUID REFERENCES tasks(task_id),
  health_status VARCHAR(50), -- healthy, warning, critical
  last_active TIMESTAMP,
  last_check_time TIMESTAMP,
  is_stuck BOOLEAN DEFAULT false,
  stuck_duration_seconds INTEGER,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Purpose**: Real-time tracking for dashboard and HR monitoring

#### Table 3: `projects`
Main project records.

```sql
CREATE TABLE projects (
  project_id UUID PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  status VARCHAR(50), -- PLANNING, IN_PROGRESS, REVIEW, COMPLETED, CANCELLED, ON_HOLD, FAILED
  priority VARCHAR(20), -- LOW, MEDIUM, HIGH, URGENT
  owner_agent_id UUID NOT NULL REFERENCES agents(agent_id),
  human_request TEXT,
  result_output TEXT,
  agent_days_elapsed DECIMAL(10, 2),
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  cancelled_at TIMESTAMP,
  failure_reason TEXT,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  deleted_at TIMESTAMP  -- soft delete
);
```

**Status Workflow**: PLANNING → IN_PROGRESS → REVIEW → COMPLETED

#### Table 4: `tasks`
Work items assigned to agents.

```sql
CREATE TABLE tasks (
  task_id UUID PRIMARY KEY,
  project_id UUID NOT NULL REFERENCES projects(project_id),
  title VARCHAR(255) NOT NULL,
  description TEXT,
  status VARCHAR(50), -- PENDING, IN_PROGRESS, BLOCKED, REVIEW, COMPLETED, CANCELLED, FAILED
  priority VARCHAR(20),
  assigned_to_agent_id UUID NOT NULL REFERENCES agents(agent_id),
  created_by_agent_id UUID REFERENCES agents(agent_id),
  depends_on_task_ids UUID[] DEFAULT '{}',
  approval_required_from UUID REFERENCES agents(agent_id),
  output TEXT,  -- generated code, design, etc
  blocked_reason TEXT,
  review_started_at TIMESTAMP,
  completed_at TIMESTAMP,
  estimated_completion_time TIMESTAMP,
  actual_completion_time TIMESTAMP,
  retries_count INTEGER DEFAULT 0,
  last_error_message TEXT,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Workflow**: PENDING → IN_PROGRESS → REVIEW → COMPLETED

#### Table 5: `messages`
Inter-agent communication.

```sql
CREATE TABLE messages (
  message_id UUID PRIMARY KEY,
  from_agent_id UUID NOT NULL REFERENCES agents(agent_id),
  to_agent_id UUID NOT NULL REFERENCES agents(agent_id),
  content TEXT NOT NULL,
  message_type VARCHAR(50), -- INFO, REQUEST, APPROVAL, ALERT
  priority VARCHAR(20),
  related_project_id UUID REFERENCES projects(project_id),
  related_task_id UUID REFERENCES tasks(task_id),
  read_status BOOLEAN DEFAULT false,
  read_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Purpose**: Persistent message history for agent coordination

#### Table 6: `decisions`
Decision tracking and audit trail.

```sql
CREATE TABLE decisions (
  decision_id UUID PRIMARY KEY,
  decision_type VARCHAR(100),
  question TEXT,
  rationale TEXT,
  decision VARCHAR(255),
  approved BOOLEAN,
  made_by_agent_id UUID NOT NULL REFERENCES agents(agent_id),
  approved_by_agent_id UUID REFERENCES agents(agent_id),
  related_project_id UUID REFERENCES projects(project_id),
  related_task_id UUID REFERENCES tasks(task_id),
  metadata JSONB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Table 7: `knowledge_base`
Shared documentation and guidelines.

```sql
CREATE TABLE knowledge_base (
  kb_id UUID PRIMARY KEY,
  category VARCHAR(100),
  title VARCHAR(255),
  content TEXT,
  access_level VARCHAR(50), -- PUBLIC, INTERNAL, RESTRICTED
  tags TEXT[],
  version INTEGER DEFAULT 1,
  created_by_agent_id UUID REFERENCES agents(agent_id),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Table 8: `audit_log`
Complete action history for compliance and debugging.

```sql
CREATE TABLE audit_log (
  log_id UUID PRIMARY KEY,
  agent_id UUID REFERENCES agents(agent_id),
  action VARCHAR(100),
  entity_type VARCHAR(100),
  entity_id UUID,
  old_value JSONB,
  new_value JSONB,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  ip_address VARCHAR(45),
  user_id UUID,
  request_id VARCHAR(100)
);
```

#### Table 9: `human_interactions`
Human approval and feedback.

```sql
CREATE TABLE human_interactions (
  interaction_id UUID PRIMARY KEY,
  interaction_type VARCHAR(50), -- APPROVAL_REQUEST, FEEDBACK, ESCALATION
  request TEXT,
  human_response TEXT,
  status VARCHAR(50), -- PENDING, APPROVED, REJECTED, RESOLVED
  related_project_id UUID REFERENCES projects(project_id),
  related_task_id UUID REFERENCES tasks(task_id),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  responded_at TIMESTAMP,
  resolved_at TIMESTAMP
);
```

### 3. Extended Tables for Advanced Features

#### Event Tracking Tables

**agent_activity**
```sql
Real-time activity feed for dashboard
- activity_id, agent_id, activity_type, description, timestamp
- Types: task_started, decision_made, message_sent, etc
```

**agent_thoughts**
```sql
Reasoning visibility (Glass-box AI feature)
- thought_id, agent_id, content, reasoning, timestamp
- Shows what agents are thinking in real-time
```

**llm_interactions**
```sql
LLM call tracking for performance monitoring
- interaction_id, agent_id, prompt, response, latency_ms, token_count, timestamp
```

**agent_handoff**
```sql
Work transfer tracking
- handoff_id, from_agent_id, to_agent_id, related_task_id, reason, timestamp
```

#### Escalation Management

**advanced_escalations**
```sql
CREATE TABLE advanced_escalations (
  escalation_id UUID PRIMARY KEY,
  title VARCHAR(255),
  description TEXT,
  escalation_type VARCHAR(50),
  -- TECHNICAL_DECISION, BUDGET_THRESHOLD, AGENT_MALFUNCTION,
  -- RESOURCE_ALLOCATION, DEADLINE_RISK, SCOPE_CHANGE, BLOCKED_TASK

  severity VARCHAR(50),
  priority VARCHAR(50), -- LOW, MEDIUM, HIGH, CRITICAL, URGENT
  status VARCHAR(50), -- OPEN, IN_PROGRESS, RESOLVED, CLOSED

  created_by_agent_id UUID REFERENCES agents(agent_id),
  assigned_to_agent_id UUID REFERENCES agents(agent_id),

  related_project_id UUID REFERENCES projects(project_id),
  related_task_id UUID REFERENCES tasks(task_id),

  sla_deadline TIMESTAMP,
  resolved_at TIMESTAMP,
  resolution_notes TEXT,

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**escalation_timeline**
```sql
Timeline of escalation events
- timeline_id, escalation_id, event_type (assigned, status_changed, commented)
- timestamp, agent_id, details
```

**escalation_comments**
```sql
Discussion threads on escalations
- comment_id, escalation_id, agent_id, content, timestamp
```

#### Feedback System

**project_feedback**
```sql
- feedback_id, project_id, feedback_type (GENERAL, QUALITY, etc)
- rating (1-5), comments, status (PENDING, IMPLEMENTED)
```

**task_feedback**
```sql
- feedback_id, task_id, feedback_type, rating, comments, status
```

**agent_feedback**
```sql
- feedback_id, agent_id, feedback_type, rating, comments
```

### 4. Database Relationships

```
Agent (1) ──→ (N) Tasks (assigned_to_agent_id)
Agent (1) ──→ (N) Messages (from_agent_id, to_agent_id)
Agent (1) ──→ (N) Decisions (made_by_agent_id)
Agent (1) ──→ (1) AgentStatus

Project (1) ──→ (N) Tasks
Project (1) ──→ (N) Messages (related_project_id)
Project (1) ──→ (N) Decisions
Project (1) ──→ (N) Escalations

Task (1) ──→ (N) Messages (related_task_id)
Task (1) ──→ (N) Escalations
Task (1) ──→ (N) Feedback

Escalation (1) ──→ (N) Comments
Escalation (1) ──→ (N) Timeline events
```

### 5. Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **UUID Primary Keys** | Distributed system support, security (no sequential guessing) |
| **JSONB Columns** | Flexible metadata storage without schema changes |
| **Timestamps on All Tables** | Audit trail, debugging, performance analysis |
| **Soft Deletes** | Data preservation, compliance, recovery capability |
| **Async ORM** | Non-blocking database operations, high concurrency |
| **Enums as VARCHAR** | Database portability, easier queries than ENUM type |
| **Array Columns (deps)** | Simple dependency representation, PostgreSQL native support |

---

## API Design

### 1. API Overview

**Base URL**: `http://localhost:8000/api/v1`
**Authentication**: JWT (prepared, configurable)
**Response Format**: JSON
**Error Handling**: Consistent error response format with HTTP status codes

### 2. API Endpoints

#### Projects API

**Create Project**
```http
POST /api/v1/projects
Content-Type: application/json

{
  "name": "Build User Dashboard",
  "description": "Create a responsive user dashboard with analytics",
  "priority": "HIGH"
}

Response 201:
{
  "project_id": "uuid",
  "name": "Build User Dashboard",
  "status": "PLANNING",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**List Projects**
```http
GET /api/v1/projects?status=IN_PROGRESS&priority=HIGH&limit=20&offset=0

Response 200:
{
  "projects": [
    {
      "project_id": "uuid",
      "name": "Build User Dashboard",
      "status": "IN_PROGRESS",
      "priority": "HIGH",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 45,
  "limit": 20,
  "offset": 0
}
```

**Get Project Details**
```http
GET /api/v1/projects/{project_id}

Response 200:
{
  "project_id": "uuid",
  "name": "Build User Dashboard",
  "description": "...",
  "status": "IN_PROGRESS",
  "owner_agent_id": "uuid",
  "tasks": [
    {
      "task_id": "uuid",
      "title": "Design UI Mockups",
      "status": "COMPLETED",
      "assigned_to": "Designer Agent"
    }
  ],
  "messages": [...],
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T12:45:00Z"
}
```

**Update Project**
```http
PUT /api/v1/projects/{project_id}
{
  "status": "REVIEW",
  "priority": "URGENT"
}
```

**Cancel Project**
```http
POST /api/v1/projects/{project_id}/cancel
{
  "reason": "Client requirements changed"
}
```

**Restart Project**
```http
POST /api/v1/projects/{project_id}/restart
{
  "reason": "Critical bug fixed"
}
```

**Get Project Activity**
```http
GET /api/v1/projects/{project_id}/activity?limit=50

Response:
{
  "activities": [
    {
      "activity_id": "uuid",
      "agent_id": "uuid",
      "agent_name": "CEO Agent",
      "activity_type": "project_approved",
      "description": "Approved project for development",
      "timestamp": "2024-01-15T11:00:00Z"
    }
  ]
}
```

#### Agents API

**List All Agents**
```http
GET /api/v1/agents

Response 200:
{
  "agents": [
    {
      "agent_id": "uuid",
      "name": "CEO Agent",
      "role": "Strategic Decision Maker",
      "department": "Executive",
      "llm_model": "claude-3.5-sonnet",
      "is_active": true
    }
  ]
}
```

**Get Agent Status**
```http
GET /api/v1/agents/status

Response 200:
{
  "agents": [
    {
      "agent_id": "uuid",
      "name": "Backend Engineer",
      "availability": "BUSY",
      "current_task_id": "uuid",
      "current_task_title": "Implement user authentication",
      "health_status": "healthy",
      "last_active": "2024-01-15T14:25:00Z"
    }
  ]
}
```

**Get Agent Details**
```http
GET /api/v1/agents/{agent_id}

Response 200:
{
  "agent_id": "uuid",
  "name": "Backend Engineer",
  "role": "Backend Development",
  "department": "Engineering",
  "system_prompt": "You are a backend engineer...",
  "llm_model": "claude-3.5-sonnet",
  "permissions": {
    "can_create_tasks": true,
    "can_approve_tasks": false
  }
}
```

**Get Agent Activity**
```http
GET /api/v1/agents/{agent_id}/activity?days=7&limit=100

Response 200:
{
  "activities": [
    {
      "timestamp": "2024-01-15T14:25:00Z",
      "activity_type": "task_completed",
      "description": "Completed database migration"
    }
  ]
}
```

**Send Human Input to Agent**
```http
POST /api/v1/agents/{agent_id}/human-input
{
  "message": "Please focus on performance optimization",
  "related_project_id": "uuid"
}
```

#### Tasks API

**List Tasks**
```http
GET /api/v1/tasks?project_id=uuid&status=IN_PROGRESS&limit=50

Response 200:
{
  "tasks": [
    {
      "task_id": "uuid",
      "project_id": "uuid",
      "title": "Implement user authentication",
      "description": "Add JWT-based auth to API",
      "status": "IN_PROGRESS",
      "assigned_to_agent_id": "uuid",
      "assigned_to_agent_name": "Backend Engineer",
      "priority": "HIGH",
      "dependencies": ["uuid1", "uuid2"],
      "approval_required_from": "uuid",
      "created_at": "2024-01-15T10:30:00Z",
      "started_at": "2024-01-15T11:00:00Z"
    }
  ]
}
```

**Get Task Details**
```http
GET /api/v1/tasks/{task_id}

Response 200:
{
  "task_id": "uuid",
  "title": "Implement user authentication",
  "description": "Add JWT-based auth to API",
  "status": "REVIEW",
  "assigned_to": "Backend Engineer",
  "output": "# User Authentication Implementation\n...",
  "approval_required_from": "CTO Agent",
  "review_started_at": "2024-01-15T14:00:00Z",
  "dependencies": [...],
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Update Task**
```http
PUT /api/v1/tasks/{task_id}
{
  "status": "COMPLETED",
  "output": "Final implementation"
}
```

**Cancel Task**
```http
POST /api/v1/tasks/{task_id}/cancel
{
  "reason": "Blocked by dependency"
}
```

**Resolve Review Timeout**
```http
POST /api/v1/tasks/{task_id}/resolve-review
{
  "action": "ESCALATE", // or "REMIND", "REASSIGN"
  "notes": "Task is critical, needs immediate review"
}
```

#### Messages API

**List Messages**
```http
GET /api/v1/messages?from_agent_id=uuid&to_agent_id=uuid&limit=50

Response 200:
{
  "messages": [
    {
      "message_id": "uuid",
      "from_agent_name": "PM Agent",
      "to_agent_name": "Backend Engineer",
      "content": "Please start on the authentication task",
      "message_type": "REQUEST",
      "priority": "HIGH",
      "read_status": true,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

**Send Message**
```http
POST /api/v1/messages
{
  "to_agent_id": "uuid",
  "content": "Please review the frontend implementation",
  "message_type": "REQUEST",
  "priority": "HIGH",
  "related_project_id": "uuid",
  "related_task_id": "uuid"
}
```

**Mark Message as Read**
```http
PUT /api/v1/messages/{message_id}/read
```

#### Escalations API

**List Escalations**
```http
GET /api/v1/escalations?status=OPEN&priority=CRITICAL&limit=50

Response 200:
{
  "escalations": [
    {
      "escalation_id": "uuid",
      "title": "Blocked task: Database migration",
      "escalation_type": "BLOCKED_TASK",
      "severity": "HIGH",
      "priority": "URGENT",
      "status": "OPEN",
      "created_by_agent": "HR Agent",
      "assigned_to_agent": "CTO Agent",
      "sla_deadline": "2024-01-15T18:00:00Z",
      "created_at": "2024-01-15T14:00:00Z"
    }
  ]
}
```

**Create Escalation**
```http
POST /api/v1/escalations
{
  "title": "Task review timeout",
  "description": "Backend engineer task stuck in review for 5 hours",
  "escalation_type": "BLOCKED_TASK",
  "priority": "CRITICAL",
  "related_task_id": "uuid"
}
```

**Get Escalation Details**
```http
GET /api/v1/escalations/{escalation_id}

Response 200:
{
  "escalation_id": "uuid",
  "title": "Task review timeout",
  "description": "...",
  "status": "IN_PROGRESS",
  "timeline": [
    {
      "event_type": "CREATED",
      "timestamp": "2024-01-15T14:00:00Z",
      "details": "Escalation created by HR Agent"
    },
    {
      "event_type": "ASSIGNED",
      "timestamp": "2024-01-15T14:05:00Z",
      "assigned_to": "CTO Agent"
    }
  ],
  "comments": [
    {
      "comment_id": "uuid",
      "agent_name": "CTO Agent",
      "content": "I'll review this immediately",
      "timestamp": "2024-01-15T14:06:00Z"
    }
  ]
}
```

**Resolve Escalation**
```http
POST /api/v1/escalations/{escalation_id}/resolve
{
  "status": "RESOLVED",
  "resolution_notes": "Task approved, no changes needed",
  "action_taken": "APPROVED_TASK"
}
```

#### Feedback API

**Submit Project Feedback**
```http
POST /api/v1/projects/{project_id}/feedback
{
  "feedback_type": "QUALITY",
  "rating": 4,
  "comments": "Great work, minor improvements needed"
}
```

**Submit Task Feedback**
```http
POST /api/v1/tasks/{task_id}/feedback
{
  "feedback_type": "CORRECTNESS",
  "rating": 5,
  "comments": "Implementation is perfect"
}
```

**Submit Agent Feedback**
```http
POST /api/v1/agents/{agent_id}/feedback
{
  "feedback_type": "PERFORMANCE",
  "rating": 4,
  "comments": "Good decision making, could be faster"
}
```

#### Dashboard API

**Get Dashboard Metrics**
```http
GET /api/v1/dashboard/metrics?time_period=week

Response 200:
{
  "projects": {
    "total": 42,
    "completed": 38,
    "in_progress": 3,
    "failed": 1,
    "completion_rate": 0.90
  },
  "tasks": {
    "total": 156,
    "completed": 145,
    "blocked": 3,
    "stuck": 2,
    "average_completion_time_minutes": 45
  },
  "agents": {
    "total": 7,
    "healthy": 7,
    "warning": 0,
    "critical": 0,
    "avg_utilization": 0.87
  },
  "escalations": {
    "total_this_period": 5,
    "resolved": 4,
    "pending": 1,
    "avg_resolution_time_minutes": 32
  },
  "timeline": {
    "projects_completed_today": 2,
    "tasks_completed_today": 8,
    "escalations_created_today": 1
  }
}
```

#### Settings API

**Get System Settings**
```http
GET /api/v1/system-settings

Response 200:
{
  "agent_execution_mode": "event_driven",
  "agent_check_interval": 900,
  "task_stuck_threshold": 7200,
  "approval_timeout_threshold": 14400,
  "hr_monitoring_interval": 30,
  "default_llm_model": "claude-3.5-sonnet",
  "max_retries": 3,
  "cors_origins": ["http://localhost:3000"]
}
```

**Update System Settings** (Admin only)
```http
PUT /api/v1/system-settings
{
  "agent_execution_mode": "hybrid",
  "task_stuck_threshold": 10800,
  "max_retries": 5
}
```

### 3. Error Response Format

All errors follow this format:

```json
{
  "error": {
    "code": "TASK_NOT_FOUND",
    "message": "The task with ID 'uuid' was not found",
    "details": {
      "task_id": "uuid",
      "timestamp": "2024-01-15T15:30:00Z"
    },
    "request_id": "req_abc123xyz789"
  },
  "status": 404
}
```

**Common HTTP Status Codes**:
- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Authorization failed
- `404 Not Found`: Resource not found
- `409 Conflict`: State conflict (e.g., can't approve completed task)
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Temporary outage

---

## Frontend Architecture

### 1. Overall Structure

**Framework**: Next.js 14 with App Router
**Language**: TypeScript 5.6+
**Styling**: TailwindCSS + custom design system
**State**: React Query (TanStack Query) + local React state

```
frontend/src/
├── app/                    # Next.js App Router pages
├── components/             # Reusable React components
├── lib/                    # Utilities and API clients
├── hooks/                  # Custom React hooks
├── types/                  # TypeScript type definitions
├── styles/                 # Global styles
├── config/                 # Configuration files
└── public/                 # Static assets
```

### 2. Page Structure

**Dashboard Pages** (`src/app`):

| Page | Purpose |
|------|---------|
| `/` | Dashboard homepage with metrics and recent activity |
| `/projects` | Project list with filters and creation |
| `/projects/[id]` | Project details with tasks and messages |
| `/agents` | Agent status and performance |
| `/agents/[id]` | Individual agent details and activity |
| `/tasks` | Task board with kanban/list views |
| `/tasks/[id]` | Task details with output and feedback |
| `/messages` | Message inbox/feed |
| `/escalations` | Escalation management |
| `/escalations/[id]` | Escalation details with timeline |
| `/audit` | Audit log viewer |
| `/settings` | System settings (admin) |
| `/profile` | User profile management |

### 3. Component Architecture

**Layout Components** (`src/components/layout`):
- Dashboard wrapper with sidebar
- Header with navigation
- Sidebar with menu
- Footer with status

**UI Components** (`src/components/ui`):
- Cards, buttons, badges
- Forms and inputs
- Dialogs and modals
- Tabs and accordion
- Dropdowns and menus
- Progress bars and spinners

**Feature Components**:
- **Project Components** (`src/components/project`):
  - ProjectCard, ProjectList, ProjectDetails
  - ProjectForm, ProjectTimeline
  - ProjectMetrics

- **Task Components** (`src/components/tasks`):
  - TaskBoard (kanban view)
  - TaskCard, TaskList
  - TaskDetails, TaskForm
  - DependencyGraph

- **Message Components** (`src/components/messages`):
  - MessageFeed, MessageCard
  - MessageForm, MessageThread

- **Escalation Components** (`src/components/escalations`):
  - EscalationList, EscalationCard
  - EscalationDetails, EscalationTimeline
  - EscalationComments

- **Agent Components** (`src/components/agents`):
  - AgentCard, AgentStatus
  - AgentActivity, AgentThoughts
  - AgentPerformance

### 4. State Management Strategy

**React Query (TanStack Query v5)**:
- Server state management for all API data
- Automatic caching and refetching
- Background synchronization
- Optimistic updates
- Pagination support

**Custom Hooks** (`src/hooks/useApi.ts`):
```typescript
// Auto-generated React Query hooks for all API endpoints
useProjects(filters)           // List projects
useProject(id)                 // Get single project
useCreateProject()             // Create mutation
useUpdateProject()             // Update mutation
useAgents()                    // List agents
useAgentStatus()               // Real-time agent status
useTasks(filters)              // List tasks
useTaskDetails(id)             // Task details
useMessages(filters)           // List messages
useEscalations(filters)        // List escalations
useDashboardMetrics()          // Dashboard data
// ... etc
```

**Local State**:
- UI state (modals, dropdowns, filters)
- Form state (React Hook Form with Zod validation)
- Real-time subscriptions (WebSocket)
- User preferences

### 5. Real-time Features

**WebSocket Integration**:
```typescript
// Auto-connect to project-specific updates
useProjectSubscription(projectId)
// Returns: { activities, messages, taskUpdates, events }

// Global event subscription
useGlobalSubscription()
// Returns: { systemEvents, agentStatusUpdates }

// Task-specific updates
useTaskUpdates(taskId)
// Returns: { statusChanges, outputUpdates, approvalChanges }
```

**Live Activity Feed**:
- Real-time agent activities
- Message notifications
- Status updates
- Escalation alerts

### 6. Type Safety

**API Response Types** (`src/types`):
```typescript
interface Project {
  project_id: string
  name: string
  description: string
  status: ProjectStatus
  priority: Priority
  owner_agent_id: string
  tasks: Task[]
  created_at: string
  updated_at: string
}

interface Task {
  task_id: string
  project_id: string
  title: string
  status: TaskStatus
  assigned_to_agent_id: string
  dependencies: string[]
  approval_required_from?: string
  output?: string
  created_at: string
}

interface Agent {
  agent_id: string
  name: string
  role: string
  department: string
  llm_model: string
  is_active: boolean
}

// Enum types for select dropdowns
type ProjectStatus = 'PLANNING' | 'IN_PROGRESS' | 'REVIEW' | 'COMPLETED' | 'CANCELLED'
type TaskStatus = 'PENDING' | 'IN_PROGRESS' | 'BLOCKED' | 'REVIEW' | 'COMPLETED'
type Priority = 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT'
```

### 7. Styling System

**TailwindCSS Configuration**:
- Custom color palette (brand colors)
- Custom spacing scale
- Custom typography
- Dark mode support
- Responsive breakpoints

**Component Styling Pattern**:
```typescript
// Button component with variants
<Button variant="primary" size="lg" disabled={isLoading}>
  {isLoading ? "Loading..." : "Create Project"}
</Button>

// Card with consistent styling
<Card className="p-6 rounded-lg border shadow-sm">
  <h2 className="text-lg font-semibold mb-2">{title}</h2>
  <p className="text-gray-600">{description}</p>
</Card>
```

### 8. Forms and Validation

**React Hook Form + Zod**:
```typescript
// Type-safe form with client-side validation
const form = useForm<CreateProjectInput>({
  resolver: zodResolver(createProjectSchema),
  defaultValues: {
    name: '',
    description: '',
    priority: 'MEDIUM'
  }
})

// Automatic validation feedback
<input {...form.register('name')} />
{form.formState.errors.name && (
  <span className="text-red-600">{form.formState.errors.name.message}</span>
)}
```

---

## Event-Driven System

### 1. Event Architecture

The event-driven system enables real-time coordination between agents with <100ms latency.

**Components**:
- **Event Bus**: Central pub/sub system (Redis or in-memory)
- **Event Publisher**: Automatically publishes database changes
- **Event Subscribers**: Agents listen for relevant events
- **Event Persistence**: All events logged to `agent_activity` table

### 2. Event Types (30+)

**Project Events**:
- `PROJECT_CREATED`: New project submitted
- `PROJECT_APPROVED`: CEO approved project
- `PROJECT_REJECTED`: CEO rejected project
- `PROJECT_STARTED`: Work begins
- `PROJECT_COMPLETED`: All tasks done
- `PROJECT_FAILED`: Unrecoverable error
- `PROJECT_CANCELLED`: Cancelled by user/agent

**Task Events**:
- `TASK_CREATED`: New task created
- `TASK_ASSIGNED`: Task assigned to agent
- `TASK_STARTED`: Agent begins work
- `TASK_DEPENDENCY_RESOLVED`: Blocking task completed
- `TASK_BLOCKED`: Task can't proceed
- `TASK_OUTPUT_READY`: Task complete, awaiting approval
- `TASK_APPROVED`: Task approved
- `TASK_REJECTED`: Task needs rework
- `TASK_COMPLETED`: Task done
- `TASK_FAILED`: Task error

**Agent Events**:
- `AGENT_ONLINE`: Agent started
- `AGENT_OFFLINE`: Agent stopped
- `AGENT_BUSY`: Agent processing
- `AGENT_AVAILABLE`: Agent free
- `AGENT_STUCK`: Agent not responding

**Message Events**:
- `MESSAGE_CREATED`: New message
- `MESSAGE_READ`: Message seen
- `MESSAGE_ACKNOWLEDGED`: Message acted upon

**Decision Events**:
- `DECISION_MADE`: Agent made decision
- `DECISION_APPROVED`: Decision approved
- `DECISION_REJECTED`: Decision rejected

**Escalation Events**:
- `ESCALATION_CREATED`: New escalation
- `ESCALATION_ASSIGNED`: Escalation assigned
- `ESCALATION_RESOLVED`: Escalation resolved
- `ESCALATION_COMMENTED`: Comment added

### 3. Event Flow Example: Project Approval

**Timeline:**
```
T+0ms    Human creates project
         POST /api/v1/projects → 201

T+10ms   Event bus publishes PROJECT_CREATED
         Database: projects table insert
         Event: PROJECT_CREATED emitted

T+20ms   CEO Agent receives event
         Event subscriber triggers
         LLM call starts (analyzing project)

T+500ms  CEO Agent completes analysis
         Database: message to CTO (for consultation)
         Message event published
         Event: MESSAGE_CREATED

T+510ms  CTO Agent receives message
         LLM call starts (technical review)

T+1000ms CTO Agent responds
         Event: MESSAGE_CREATED
         CEO Agent receives response

T+1100ms CEO Agent makes final decision
         Database: project status = IN_PROGRESS
         Event: PROJECT_APPROVED

T+1110ms PM Agent receives PROJECT_APPROVED
         Breaks down project into tasks
         Creates 5 tasks in database
         Event: TASK_CREATED (5x)

T+1200ms Designer receives first task
         Frontend Engineer receives task
         Backend Engineer receives task
         All start working in parallel
         Event: TASK_STARTED (3x)

        WebSocket broadcasts real-time updates to frontend
        User sees live project status updates
```

### 4. Event Bus Implementation

**In-Memory Backend** (Development):
```python
# Simple Python dict with event listeners
event_subscribers: Dict[str, List[Callable]] = {
    'PROJECT_CREATED': [ceo_agent.on_project_created],
    'TASK_COMPLETED': [pm_agent.on_task_completed, ...]
}

async def publish(event_type: str, data: dict):
    for subscriber in event_subscribers.get(event_type, []):
        await subscriber(data)  # <100ms delivery
```

**Redis Backend** (Production):
```python
# Redis Pub/Sub for distributed system
redis_pubsub = redis.pubsub()
await redis_pubsub.psubscribe('agent.*', 'task.*', 'project.*')

async def publish(event_type: str, data: dict):
    await redis.publish(event_type, json.dumps(data))
    # Guaranteed delivery, persisted to Redis streams

async def subscribe(event_pattern: str):
    async for message in redis_pubsub.listen():
        await handle_event(message)
```

### 5. Dependency Resolution

**Automatic Task Dependency Handling:**
```
When TASK_COMPLETED event fires for Task A:
├─ Check all tasks where Task A is in depends_on_task_ids
├─ For each blocked task:
│  ├─ Check if all other dependencies complete
│  └─ If yes: emit TASK_DEPENDENCY_RESOLVED event
├─ Assigned agent receives event immediately
└─ Agent starts work without waiting for next check cycle
```

**30-Second Dependency Check**:
Backup mechanism (in case events lost):
- Every 30 seconds, scan database for unresolved dependencies
- Compare with event log to find missed events
- Re-emit TASK_DEPENDENCY_RESOLVED for missed tasks

### 6. Event Persistence

**Event Activity Table**:
All events logged for audit, analytics, and debugging:

```sql
SELECT * FROM agent_activity WHERE agent_id = 'backend-engineer'
ORDER BY created_at DESC LIMIT 100;

event_type        | timestamp           | description
------------------+---------------------+-----------------------------
TASK_STARTED      | 2024-01-15 14:25:10 | Started: Implement auth
TASK_OUTPUT_READY | 2024-01-15 14:42:30 | Completed: Implement auth
MESSAGE_CREATED   | 2024-01-15 14:43:00 | CTO reviewed, requested fixes
TASK_STARTED      | 2024-01-15 14:44:00 | Restarted: Implement auth
TASK_APPROVED     | 2024-01-15 15:02:45 | CTO approved implementation
TASK_COMPLETED    | 2024-01-15 15:03:00 | Task marked complete
```

---

## Agent System

### 1. Agent Execution Model

**Base Agent Class** (`backend/app/agents/base_agent.py`):

```python
class BaseAgent:
    agent_id: UUID
    name: str
    role: str
    system_prompt: str
    llm_model: str = "claude-3.5-sonnet"

    async def process_event(self, event: Event):
        """Handle incoming event - no waiting"""
        if self.is_relevant(event):
            await self.execute()

    async def check_for_work(self):
        """Legacy polling - check every 15 minutes"""
        pending_items = await self.find_pending_work()
        for item in pending_items:
            await self.execute_item(item)

    async def execute(self):
        """Main execution logic"""
        context = await self.build_context()

        # Stream LLM response in real-time
        async for chunk in self.llm_stream(self.system_prompt, context):
            # Broadcast to WebSocket
            await websocket_manager.broadcast(
                f'agent_{self.agent_id}_thought',
                {'chunk': chunk, 'timestamp': now()}
            )

        output = await self.process_llm_output(response)
        await self.create_artifacts(output)  # tasks, messages, decisions
        await self.emit_events()  # trigger dependent work
```

### 2. Agent Initialization

All agents created at startup with specialized prompts:

```python
agents = [
    Agent(
        name="CEO Agent",
        role="Chief Executive Officer",
        system_prompt="""You are the CEO of an AI software company...

        Your responsibilities:
        1. Evaluate project proposals
        2. Make strategic decisions
        3. Approve/reject projects
        4. Escalate critical issues
        5. Report to the human founder

        Always think strategically. Ask CTO about technical feasibility.
        Document all decisions with clear reasoning.
        """,
        llm_model="claude-3.5-sonnet",
        permissions={
            "can_create_projects": False,
            "can_approve_projects": True,
            "can_escalate": True,
            "can_create_messages": True
        }
    ),
    # 6 more agents...
]
```

### 3. Agent Message Format

**System Context Passed to LLM**:
```json
{
  "current_time": "2024-01-15T14:30:00Z",
  "agent_info": {
    "agent_id": "backend-engineer-id",
    "name": "Backend Engineer",
    "role": "Backend Development",
    "current_tasks": [
      {
        "task_id": "task-123",
        "title": "Implement user authentication",
        "description": "Add JWT-based auth to API endpoints",
        "status": "IN_PROGRESS",
        "started_at": "2024-01-15T14:25:00Z",
        "progress": "40% - Auth service created, testing routes"
      }
    ]
  },
  "recent_messages": [
    {
      "from_agent": "CTO Agent",
      "timestamp": "2024-01-15T14:20:00Z",
      "content": "Any blockers on the auth task?",
      "message_type": "REQUEST"
    }
  ],
  "system_events": [
    {
      "event_type": "TASK_DEPENDENCY_RESOLVED",
      "task_id": "task-121",
      "content": "Database schema is ready for use"
    }
  ],
  "knowledge_base": [
    "Security best practices for JWT implementation",
    "Our approved tech stack"
  ]
}
```

### 4. Agent LLM Interaction

**Streaming Response Processing**:
```python
async def llm_stream(self, system_prompt: str, context: dict):
    """Stream LLM response in real-time"""
    async with client.messages.stream(
        model="claude-3.5-sonnet",
        max_tokens=4096,
        system=system_prompt,
        messages=[
            {"role": "user", "content": json.dumps(context)}
        ]
    ) as stream:
        full_response = ""
        async for text in stream:
            full_response += text
            # Broadcast thought/reasoning
            await broadcast_agent_thought(text)
            yield text

        # Log interaction
        await log_llm_interaction({
            "agent_id": self.agent_id,
            "input_tokens": stream.usage.input_tokens,
            "output_tokens": stream.usage.output_tokens,
            "latency_ms": (time.time() - start) * 1000,
            "timestamp": now()
        })

        return full_response
```

### 5. Agent Decision Making

**Decision Logging**:
```python
async def make_decision(self, question: str, options: List[str]):
    """Make tracked decision"""
    llm_response = await self.llm_query(
        f"""Based on the current context, which option is best?
        Question: {question}
        Options: {options}

        Provide: DECISION, RATIONALE, CONFIDENCE (0-100)
        """
    )

    # Parse response
    decision = parse_decision(llm_response)

    # Log decision
    await db.decisions.create({
        "decision_id": uuid4(),
        "decision_type": "PROJECT_APPROVAL",
        "question": question,
        "rationale": decision.rationale,
        "decision": decision.choice,
        "made_by_agent_id": self.agent_id,
        "created_at": now()
    })

    # Broadcast decision event
    await event_bus.publish("DECISION_MADE", {
        "decision_id": str(uuid4()),
        "agent_id": str(self.agent_id),
        "decision": decision.choice,
        "confidence": decision.confidence
    })

    return decision
```

### 6. Agent Health and Monitoring

**HR Agent Monitoring Loop** (Continuous):
```python
async def hr_monitoring_loop():
    """Runs every 30 seconds"""
    while True:
        await asyncio.sleep(30)  # 30-second intervals

        for agent in await get_all_agents():
            # Check last activity
            last_active = agent.status.last_active
            inactive_duration = now() - last_active

            if inactive_duration > 30 * 60:  # 30 minutes
                # Warning status
                await create_escalation(
                    title=f"{agent.name} Inactive (30+ min)",
                    severity="MEDIUM",
                    escalation_type="AGENT_MALFUNCTION"
                )

            if inactive_duration > 60 * 60:  # 1 hour
                # Critical status
                await create_escalation(
                    title=f"{agent.name} Offline (1+ hour)",
                    severity="CRITICAL",
                    escalation_type="AGENT_MALFUNCTION"
                )

            # Check for stuck tasks
            stuck_task = await find_stuck_task(agent_id=agent.agent_id)
            if stuck_task and stuck_task.duration > 2 * 60 * 60:  # 2+ hours
                await create_escalation(
                    title=f"Task stuck: {stuck_task.title}",
                    description=f"Agent working on task for {stuck_task.duration}s",
                    escalation_type="BLOCKED_TASK"
                )

            # Check for review timeouts
            timeout_task = await find_review_timeout_task(agent_id=agent.agent_id)
            if timeout_task and timeout_task.review_duration > 4 * 60 * 60:  # 4+ hours
                await resolve_review_timeout(task_id=timeout_task.task_id)
```

---

## Key Workflows

### 1. Complete Project Workflow

**Overview**: End-to-end journey from human request to completed deliverable

**Timeline: Event-Driven Mode (~3-5 minutes)**

```
┌─────────────────────────────────────────────────────────────────┐
│                    PROJECT LIFECYCLE                             │
└─────────────────────────────────────────────────────────────────┘

[T+0s] HUMAN SUBMITS PROJECT REQUEST
      └─→ POST /api/v1/projects
         {
           "name": "Build User Dashboard",
           "description": "Responsive dashboard with analytics",
           "priority": "HIGH"
         }
      └─→ Response: Project created with status=PLANNING
      └─→ Event: PROJECT_CREATED published

[T+0.1s] CEO AGENT RECEIVES PROJECT_CREATED EVENT
        └─→ Subscriber triggered immediately (<100ms)
        └─→ CEO analyzes project request
        └─→ Calls LLM: "Is this project feasible? Resource requirements?"
        └─→ Response streams in real-time
        └─→ Event: THOUGHT_RECORDED (broadcasts to WebSocket)

[T+0.5s] CEO DECIDES TO CONSULT CTO
        └─→ Creates message to CTO Agent
        └─→ Event: MESSAGE_CREATED
        └─→ Content: "Can we build a dashboard with React + FastAPI?"

[T+0.6s] CTO AGENT RECEIVES MESSAGE
        └─→ Analyzes technical feasibility
        └─→ Calls LLM: "Architecture for user dashboard?"
        └─→ Responds with tech stack recommendation
        └─→ Event: MESSAGE_CREATED (CTO response)

[T+1.2s] CEO RECEIVES CTO FEEDBACK
        └─→ Makes final decision: APPROVE
        └─→ Updates database: project.status = IN_PROGRESS
        └─→ Event: PROJECT_APPROVED

[T+1.3s] PM AGENT RECEIVES PROJECT_APPROVED
        └─→ Breaks down project into tasks:
            • Task 1: Design UI mockups (→ Designer)
            • Task 2: Backend API structure (→ Backend Engineer)
            • Task 3: Frontend components (→ Frontend Engineer)
            • Task 4: Database schema (→ Backend Engineer)
            • Task 5: Integration testing (→ Backend Engineer)
        └─→ Creates dependencies:
            • Task 2 & 4 before Task 5
            • Task 1 before Task 3
        └─→ Event: TASK_CREATED (5x)

[T+1.5s] DESIGNER RECEIVES TASK
        └─→ Event: TASK_ASSIGNED (Designer)
        └─→ Starts work immediately
        └─→ Calls LLM: "Create UI/UX for user dashboard"
        └─→ Generates: Wireframes, design tokens, color palette
        └─→ Event: TASK_STARTED

[T+1.5s] BACKEND ENGINEER RECEIVES 2 TASKS
        └─→ Checks dependencies: Can start database schema first
        └─→ Event: TASK_STARTED (database task)
        └─→ Works on database schema design
        └─→ Output: SQL migration file

[T+2.0s] DESIGNER COMPLETES WORK
        └─→ Task output: UI specifications (Figma-ready)
        └─→ Event: TASK_OUTPUT_READY
        └─→ Requires approval from: PM Agent

[T+2.1s] PM APPROVES DESIGNER TASK
        └─→ Event: TASK_APPROVED
        └─→ Triggers: TASK_DEPENDENCY_RESOLVED for Frontend task

[T+2.2s] FRONTEND ENGINEER UNBLOCKED
        └─→ Event: TASK_DEPENDENCY_RESOLVED received
        └─→ Starts frontend work immediately (didn't have to wait for next check cycle!)
        └─→ Calls LLM: "Build React components from design specs"
        └─→ Generates: React components, TypeScript types

[T+2.5s] BACKEND ENGINEER COMPLETES DATABASE
        └─→ Task output: SQL migration file
        └─→ Event: TASK_OUTPUT_READY
        └─→ Requires approval from: CTO Agent

[T+2.6s] CTO REVIEWS DATABASE SCHEMA
        └─→ Approves technical implementation
        └─→ Event: TASK_APPROVED
        └─→ Triggers: TASK_DEPENDENCY_RESOLVED for API task

[T+2.7s] BACKEND ENGINEER STARTS API DEVELOPMENT
        └─→ Calls LLM: "Implement FastAPI endpoints for dashboard"
        └─→ Generates: API routes, database queries, error handling

[T+3.5s] BACKEND ENGINEER COMPLETES API
        └─→ Task output: API implementation code
        └─→ Event: TASK_OUTPUT_READY
        └─→ Requires approval from: CTO Agent

[T+3.6s] CTO REVIEWS API CODE
        └─→ Checks: Code quality, error handling, performance
        └─→ Approves
        └─→ Event: TASK_APPROVED
        └─→ Triggers: TASK_DEPENDENCY_RESOLVED for integration testing

[T+3.7s] BACKEND ENGINEER STARTS INTEGRATION TEST
        └─→ Calls LLM: "Write integration tests for dashboard API"
        └─→ Generates: Test suite

[T+4.0s] BACKEND ENGINEER COMPLETES TESTS
        └─→ Event: TASK_APPROVED (CTO reviews)

[T+4.1s] FRONTEND ENGINEER COMPLETES COMPONENTS
        └─→ Event: TASK_OUTPUT_READY

[T+4.2s] CTO REVIEWS FRONTEND
        └─→ Approves
        └─→ Event: TASK_APPROVED

[T+4.3s] PM AGENT DETECTS ALL TASKS COMPLETE
        └─→ Automatic detection: All project tasks have status=COMPLETED
        └─→ Event: PROJECT_COMPLETED

[T+4.4s] CEO AGENT RECEIVES PROJECT_COMPLETED
        └─→ Prepares final deliverable summary
        └─→ Notifies human founder
        └─→ Status updated: project.status = COMPLETED
        └─→ Human receives notification: "Dashboard project completed!"

[T+5.0s] HUMAN VIEWS COMPLETED PROJECT
        └─→ GET /api/v1/projects/{project_id}
        └─→ Sees: All tasks completed, code generated, ready to use
        └─→ Optional: Submit feedback for project

┌─────────────────────────────────────────────────────────────────┐
│                    TOTAL TIME: ~5 MINUTES                        │
│              (Seconds to minutes with streaming LLM)              │
│           (Hours with polling mode, days with manual work)        │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Escalation Workflow

**When issues arise:**

```
[TRIGGER] HR Agent detects issue
         └─→ Stuck task (2+ hours in-progress)
         └─→ Review timeout (4+ hours awaiting approval)
         └─→ Inactive agent (1+ hour no activity)
         └─→ Review stuck (multiple rejections)

[ACTION] Create Escalation
        └─→ POST /api/v1/escalations
        └─→ Details: Issue type, affected task/agent, severity
        └─→ Priority calculated from impact + urgency
        └─→ SLA deadline: 30min for CRITICAL, 2hr for HIGH
        └─→ Auto-assigned based on severity

[NOTIFICATION] Escalation appears in dashboard
              └─→ WebSocket broadcast: ESCALATION_CREATED
              └─→ System notification created
              └─→ Assigned agent receives alert

[INVESTIGATION] Assigned agent examines escalation
               └─→ GET /api/v1/escalations/{escalation_id}
               └─→ Views timeline of events
               └─→ Reads related task/agent context

[ACTION] Agent resolves escalation
        └─→ Approves task despite issues
        └─→ OR: Provides clear next steps
        └─→ OR: Reassigns task to different agent
        └─→ OR: Escalates to human for override

[RESOLUTION] POST /api/v1/escalations/{escalation_id}/resolve
            └─→ Status: RESOLVED
            └─→ Resolution notes: What was done
            └─→ Time to resolution tracked
            └─→ Feedback recorded

[FOLLOWUP] System monitors for related issues
          └─→ If same task times out again → new escalation
          └─→ Pattern detection: Recurring issues
          └─→ Recommendations: Adjust thresholds or improve processes
```

### 3. Feedback Loop

**How the system learns:**

```
[HUMAN INPUT] Submit feedback on completed project
             └─→ POST /api/v1/projects/{project_id}/feedback
             └─→ Type: QUALITY, CORRECTNESS, COMPLETENESS
             └─→ Rating: 1-5 stars
             └─→ Comments: "Missing feature X", "Great work!"

[PROCESSING] Feedback routed to relevant agents
            └─→ Quality feedback → Designer Agent
            └─→ Code correctness → Backend Engineer + CTO
            └─→ UI feedback → Frontend Engineer
            └─→ Process feedback → PM Agent

[AGENT ANALYSIS] Relevant agent reviews feedback
                └─→ LLM: "How can I improve based on this feedback?"
                └─→ Updates system prompt (learning)
                └─→ OR: Creates task to implement improvements
                └─→ Status: PENDING → IMPLEMENTED

[METRICS] System tracks feedback metrics
         └─→ Average rating by agent
         └─→ Common feedback themes
         └─→ Improvement tracking
         └─→ Dashboard shows quality trends
```

---

## Deployment

### 1. Development Setup

**Docker Compose** (`docker-compose.yml`):
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: ai_company
      POSTGRES_USER: agent
      POSTGRES_PASSWORD: changeme
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U agent"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://agent:changeme@postgres:5432/ai_company
      REDIS_URL: redis://redis:6379
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      ENVIRONMENT: development
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app
      - /app/__pycache__

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000/api/v1
      NEXT_PUBLIC_WS_URL: ws://localhost:8000/ws
    depends_on:
      - backend
    volumes:
      - ./frontend:/app
      - /app/.next

volumes:
  postgres_data:
  redis_data:
```

**Start Development**:
```bash
# Set API key
export ANTHROPIC_API_KEY=sk-ant-xxxxx

# Start all services
docker-compose up -d

# Run migrations
docker-compose exec backend alembic upgrade head

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### 2. Production Deployment

**Fly.io** (`fly.backend.toml`):
```toml
app = "Retinue-backend"
primary_region = "ord"  # Chicago

[build]
  image = "Retinue-backend:latest"

[[services]]
  protocol = "tcp"
  internal_port = 8000
  processes = ["app"]

  [services.concurrency]
    hard_limit = 25
    soft_limit = 20

  [[services.ports]]
    handlers = ["http"]
    port = 80

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443

[env]
  ENVIRONMENT = "production"
  LOG_LEVEL = "INFO"

[[env.ANTHROPIC_API_KEY]]
  inherit = true
[[env.DATABASE_URL]]
  inherit = true
```

**Environment Variables (Production)**:
```bash
# Security
ENVIRONMENT=production
DEBUG=false
JWT_SECRET=very-secure-random-secret-change-this

# Database
DATABASE_URL=postgresql+asyncpg://user:password@postgres-prod.example.com:5432/Retinue
DB_POOL_SIZE=20
DB_POOL_TIMEOUT=30

# LLM APIs
ANTHROPIC_API_KEY=sk-ant-xxxxx
OPENAI_API_KEY=sk-xxxxx (optional)

# Event Bus
EVENT_BUS_BACKEND=redis
REDIS_URL=redis://redis-prod.example.com:6379/0

# Agent Configuration
AGENT_EXECUTION_MODE=event_driven
AGENT_CHECK_INTERVAL=900
TASK_STUCK_THRESHOLD=7200
APPROVAL_TIMEOUT_THRESHOLD=14400

# HR Monitoring
HR_MONITORING_ENABLED=true
HR_MONITORING_INTERVAL=30

# CORS
CORS_ORIGINS=["https://app.Retinue.com", "https://Retinue.com"]

# Logging
LOG_LEVEL=INFO
SENTRY_DSN=https://xxxxx@sentry.io/xxxxx (optional)
```

### 3. Scaling Considerations

**Horizontal Scaling**:
- Multiple FastAPI instances behind load balancer
- Redis pub/sub ensures all instances see events
- Database connection pooling (20-50 connections)
- WebSocket sticky sessions for real-time updates

**Performance Bottlenecks**:
- LLM API calls (slower than local processing)
- Database queries (use indexes on common filters)
- WebSocket broadcasting (Redis pub/sub efficient)
- Event bus latency (<100ms achievable with Redis)

**Monitoring**:
- Application metrics (Prometheus)
- Database performance (query logs, slow queries)
- LLM API usage and costs
- Agent health status
- Escalation response times

---

## Technology Stack

### Backend
| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Framework | FastAPI | 0.104+ | REST API, WebSocket |
| Language | Python | 3.11+ | Backend implementation |
| Database | PostgreSQL | 15+ | Primary datastore |
| Driver | asyncpg | 0.29+ | Async database driver |
| ORM | SQLAlchemy | 2.0+ | Object relational mapping |
| Migrations | Alembic | 1.13+ | Schema versioning |
| Cache/Events | Redis | 7.0+ | Pub/Sub, caching |
| LLM | Anthropic Claude | 3.5 Sonnet | AI reasoning |
| Async | asyncio | Built-in | Concurrency |
| Validation | Pydantic | 2.0+ | Data validation |
| HTTP Client | httpx | 0.25+ | Async HTTP requests |
| Admin Panel | SQLAdmin | 0.1.3+ | Database UI |
| CORS | fastapi-cors | Built-in | Cross-origin requests |

### Frontend
| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Framework | Next.js | 14.0+ | React meta-framework |
| Language | TypeScript | 5.6+ | Type-safe JavaScript |
| Runtime | Node.js | 18+ | Runtime environment |
| Styling | TailwindCSS | 3.4+ | Utility CSS |
| UI Components | Radix UI | 1.0+ | Accessible components |
| UI Presets | shadcn/ui | Latest | Copy-paste components |
| State | React Query | 5.0+ | Server state management |
| HTTP | Axios | 1.6+ | HTTP requests |
| Forms | React Hook Form | 7.48+ | Form state management |
| Validation | Zod | 3.22+ | Schema validation |
| Icons | Lucide React | 0.292+ | Icon library |
| Charts | Recharts | 2.10+ | Data visualization |
| Dates | date-fns | 2.30+ | Date manipulation |
| Notifications | Sonner | 1.2+ | Toast notifications |
| Development | Vite | 5.0+ | Build tool (optional) |

### DevOps
| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Containerization | Docker | 24+ | Container platform |
| Orchestration | Docker Compose | 2.0+ | Local development |
| Deployment | Fly.io | - | Backend deployment |
| Deployment | Vercel | - | Frontend deployment (optional) |
| Version Control | Git | 2.40+ | Code management |
| CI/CD | GitHub Actions | - | Continuous integration |

### Development Tools
- **linting**: ruff, ESLint
- **formatting**: black, prettier
- **testing**: pytest, Jest
- **type-checking**: mypy, TypeScript
- **environment**: python-dotenv, direnv

---

## Intelligent Knowledge Base System

The Knowledge Base System enables agents to learn from conversations and projects, providing intelligent context enrichment.

### Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Knowledge System                          │
├─────────────────────────────────────────────────────────────┤
│  ┌────────────────┐    ┌────────────────┐                   │
│  │   Extraction   │───▶│   Processing   │                   │
│  │     Engine     │    │    Pipeline    │                   │
│  └────────────────┘    └────────────────┘                   │
│           │                      │                           │
│           ▼                      ▼                           │
│  ┌────────────────┐    ┌────────────────┐                   │
│  │  Vector Store  │    │   Knowledge    │                   │
│  │   (ChromaDB)   │    │    Entries     │                   │
│  └────────────────┘    └────────────────┘                   │
│                                 │                            │
│                                 ▼                            │
│                        ┌────────────────┐                    │
│                        │  Application   │                    │
│                        │     Layer      │                    │
│                        └────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

### Key Features

- **Automatic Knowledge Extraction**: LLM-powered extraction from conversations and completed work
- **Hybrid Search**: Full-text + vector + exact matching for optimal retrieval
- **User Profiles**: Personalized knowledge delivery based on user preferences
- **Predictive Agent Involvement**: AI-powered predictions for which agents should join conversations
- **Knowledge Graph**: Relationships between knowledge entries for context enrichment
- **Quality Tracking**: Usage metrics and feedback loops for continuous improvement

### Database Tables (14 tables)

1. `knowledge_entries` - Core knowledge storage with vector embeddings
2. `knowledge_categories` - Hierarchical categorization
3. `knowledge_relationships` - Knowledge graph connections
4. `knowledge_versions` - Version history
5. `user_knowledge_profiles` - User preferences and patterns
6. `extraction_candidates` - Pending knowledge for review
7. `knowledge_usage_log` - Usage tracking
8. `knowledge_feedback` - User/agent feedback
9. `agent_involvement_predictions` - AI predictions for agent involvement

### API Endpoints

- `POST /api/v1/knowledge/search` - Hybrid knowledge search
- `GET /api/v1/knowledge/entries/{id}` - Get knowledge entry
- `POST /api/v1/knowledge/entries` - Create knowledge entry
- `GET /api/v1/knowledge/extractions/pending` - Get pending extractions
- `POST /api/v1/knowledge/feedback` - Submit feedback
- `POST /api/v1/knowledge/predict-agents` - Predict agent involvement

---

## Multi-Agent Chat System

The Multi-Agent Chat System enables dynamic collaboration between users and multiple AI agents within conversations.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ ChatWidget   │  │ AgentSuggestions│ │ ParticipantList│    │
│  │ (Enhanced)   │  │ Panel        │  │ (With Presence)│    │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                           │                                  │
│                      WebSocket + REST API                    │
└───────────────────────────┼──────────────────────────────────┘
                            │
┌───────────────────────────┼──────────────────────────────────┐
│                      Backend Services                        │
│  ┌────────────────────────┴─────────────────────────┐       │
│  │         Multi-Agent Orchestrator                 │       │
│  │  ┌──────────────┐  ┌──────────────┐             │       │
│  │  │ Agent        │  │ Context      │             │       │
│  │  │ Discovery    │  │ Briefing     │             │       │
│  │  └──────────────┘  └──────────────┘             │       │
│  │  ┌──────────────────────────────────┐           │       │
│  │  │   Turn Management &               │           │       │
│  │  │   Response Coordination           │           │       │
│  │  └──────────────────────────────────┘           │       │
│  └──────────────────────────────────────────────────┘       │
└──────────────────────────────────────────────────────────────┘
```

### Key Features

- **Agent Discovery**: Context-aware agent recommendations based on conversation content
- **Agent Invitation System**: Invite agents with specific reasons/context
- **Auto-Join**: Agents with relevance score >0.9 join automatically
- **Context Briefings**: New agents receive LLM-summarized conversation context
- **Agent Presence**: Real-time status indicators (active, thinking, typing)
- **Turn Management**: Coordinate multi-agent responses to prevent conflicts

### Database Tables (6 new tables)

1. `agent_invitations` - Track agent invitation requests and status
2. `agent_presence` - Real-time presence tracking
3. `conversation_turns` - Turn-based coordination
4. `agent_collaboration_sessions` - Collaboration analytics
5. `agent_expertise_tags` - Expertise mapping with proficiency levels
6. `conversation_agent_suggestions` - AI suggestion tracking

### Backend Services

- **AgentDiscoveryService**: Discovers and recommends relevant agents
- **MultiAgentOrchestrator**: Coordinates invitations, presence, and turns
- **ContextBriefingService**: Generates summaries for joining agents
- **MessageAnalyzer**: Detects agent requests in user messages

### API Endpoints

- `GET /api/v1/conversations/{id}/suggested-agents` - Get AI-suggested agents
- `POST /api/v1/conversations/{id}/invite-agent` - Invite agent to conversation
- `GET /api/v1/conversations/{id}/participants` - Get participants with presence
- `POST /api/v1/conversations/{id}/presence` - Update agent presence
- `GET /api/v1/conversations/{id}/invitations` - Get invitation history
- `GET /api/v1/conversations/{id}/briefing/{agent_id}` - Get agent briefing

### Frontend Components

- **ChatWidget**: Enhanced with participant list and presence indicators
- **AgentSuggestionsPanel**: Shows AI-recommended agents with invite buttons
- **ParticipantList**: Displays all participants with real-time presence
- **AgentPresenceIndicator**: Shows agent status (active, thinking, typing)

### WebSocket Events

- `agent_invited` - Agent invitation sent
- `agent_joined` - Agent joined conversation (auto-join or accepted)
- `agent_left` - Agent left conversation
- `agent_presence_updated` - Presence status changed

---

## Summary

Retinue represents a **cutting-edge event-driven multi-agent AI platform** that achieves several remarkable things:

### Key Achievements
1. **Real-time Agent Coordination**: <100ms event latency enables natural, flowing collaboration
2. **Complete Autonomy**: 7 specialized agents can execute entire projects without human intervention
3. **Full Transparency**: Glass-box AI shows exactly what agents are thinking in real-time
4. **Production-Grade**: Enterprise-quality infrastructure with PostgreSQL, Redis, async/await
5. **Type-Safe**: Full TypeScript frontend + Python type hints throughout
6. **Scalable Architecture**: Event-driven design avoids polling bottlenecks
7. **Comprehensive Monitoring**: Audit logs, escalation management, health monitoring
8. **Learning Capability**: Feedback system enables continuous improvement
9. **Intelligent Knowledge Base**: AI-powered knowledge extraction and retrieval
10. **Multi-Agent Chat**: Dynamic agent collaboration in conversations

### Unique Aspects
- **Simulates Real Company**: CEO, CTO, PM, HR, and specialist engineers working like real humans
- **Agent Hierarchy**: Clear reporting structure enables meaningful decision-making
- **Task Dependencies**: Automatic resolution enables parallel work without manual coordination
- **Escalation System**: Intelligent escalation prevents deadlocks
- **Real-time Dashboard**: WebSocket integration shows live agent activity
- **Multiple Execution Modes**: Event-driven (real-time) or polling (robust) based on needs
- **Knowledge-Aware Agents**: Agents learn from past work and apply knowledge
- **Dynamic Agent Collaboration**: Agents can invite specialists to conversations

### Business Value
- **Speed**: Projects complete in minutes (event-driven) vs hours/days (manual)
- **Cost**: Reduced need for human developers for routine work
- **Quality**: AI consistently follows best practices
- **Insights**: Complete audit trail for every decision and action
- **Flexibility**: Easily adjust agent prompts and behaviors
- **Learning**: System improves over time through knowledge extraction

This architecture provides a solid foundation for building sophisticated multi-agent AI systems with production-grade infrastructure.

---

**Document Generated**: January 2024
**Version**: 2.0 (Updated November 2025)
**Status**: Complete Architecture Review
