# Reference Documentation

This directory contains original design specifications and reference documents that provide deeper context about Retinue's architecture and design decisions.

## Purpose

These documents serve as:
- **Historical record** of original requirements and specifications
- **Design reference** for understanding architectural decisions
- **Deep dive material** for developers wanting to understand system internals

---

## Reference Documents

### Technical Specifications

#### IMPLEMENTATION.md
**Original Phase 1 Technical Specification (11,200 lines)**

This comprehensive document contains:
- Complete system architecture design
- Detailed database schema (10 tables)
- All 7 agent specifications with full system prompts
- Communication protocols and patterns
- Implementation phases and timeline
- Testing strategy
- Deployment architecture
- Security and permissions model

**Use this for:**
- Understanding original design decisions
- Database schema reference
- Agent role and permission definitions
- System architecture deep dive

**Current equivalent:** See `../ARCHITECTURE.md` for current architecture documentation

---

#### PROMPT.md  
**Original Project Requirements and Prompt (62,000 lines)**

The complete original prompt that defined Retinue, including:
- Vision and goals
- Detailed agent specifications
- Time compression concept
- Decision-making frameworks
- Escalation hierarchies
- Complete workflow examples

**Use this for:**
- Understanding project vision
- Original requirements
- Detailed agent behavior specifications
- Decision-making authority rules

**Current equivalent:** See `../PROJECT_STATUS.md` and `../BUSINESS_PLAN.md` for current vision

---

### Design Documents

#### MESSAGES_REDESIGN.md
**Messages System Redesign Specification**

Details the redesign of the agent-to-agent messaging system:
- Message types and priorities
- Channel architecture
- Real-time delivery mechanisms
- Read/unread status tracking

**Use this for:**
- Understanding messaging system design
- Message schema reference
- Communication patterns

**Current equivalent:** See `../FEATURES.md` section on Messaging System

---

## When to Use Reference Docs

### ✅ Use reference docs when:
- Researching why specific design decisions were made
- Need complete historical context
- Building on or extending existing features
- Troubleshooting complex system behaviors
- Understanding agent decision-making logic
- Learning the complete system architecture

### ❌ Don't use reference docs for:
- Getting started (use `../GETTING-STARTED.md`)
- Current setup instructions (use the [root README](../../README.md))
- Deployment procedures (use `../DEPLOYMENT_GUIDE.md`)
- Current architecture (use `../ARCHITECTURE.md`)
- What's built today (use `../PROJECT_STATUS.md`)

---

## Relationship to Current Documentation

```
Reference (Original Design)          Current Documentation
├── IMPLEMENTATION.md        ────────> ARCHITECTURE.md (current arch)
├── PROMPT.md               ────────> BUSINESS_PLAN.md (vision)
│                                     PROJECT_STATUS.md (status)
└── MESSAGES_REDESIGN.md    ────────> ARCHITECTURE.md (messaging section)
```

---

## Current Documentation Structure

For actively maintained documentation:

### Getting Started
- **[../../README.md](../../README.md)** - Main entry point
- **[../README.md](../README.md)** - Documentation map
- **[../GETTING-STARTED.md](../GETTING-STARTED.md)** - Setup guide

### Technical Docs
- **[../ARCHITECTURE.md](../ARCHITECTURE.md)** - Current architecture
- **[../DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md)** - Deployment guide

### Status & Planning
- **[../PROJECT_STATUS.md](../PROJECT_STATUS.md)** - Current status
- **[../BUSINESS_PLAN.md](../BUSINESS_PLAN.md)** - Business strategy

---

## Document Versions

| Document | Version | Date | Status |
|----------|---------|------|--------|
| IMPLEMENTATION.md | 1.0 | October 2025 | Original spec |
| PROMPT.md | 1.0 | October 2025 | Original requirements |
| MESSAGES_REDESIGN.md | 1.0 | October 2025 | Design doc |

---

**Note:** These documents are preserved for reference but are not actively updated. For current information, always refer to the main documentation in the parent directory.
