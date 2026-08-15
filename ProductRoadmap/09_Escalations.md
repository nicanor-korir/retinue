### 8.2.2: Escalation Detail View

**User Story:**  
*As an agent or user, I want to see complete details of an escalation so that I can understand and resolve it.*

**Modal/Page Layout:**

**1. Header:**
```
┌─────────────────────────────────────────────────────────┐
│ [← Back]                                    [⭐ Follow]  │
│                                                          │
│ 🔴 CRITICAL                                             │
│ Agent backend_001 unresponsive for 120 minutes          │
│                                                          │
│ Status: [Open ▼]  •  Priority: 100  •  Type: agent_unresponsive │
│                                                          │
│ Created: 2 hours ago by System                          │
│ Assigned to: HR Agent • Escalation Level: 1             │
└─────────────────────────────────────────────────────────┘
```

**2. Main Content:**

**Impact Summary (Highlighted Box):**
```
┌─────────────────────────────────────────────┐
│ 📊 Impact Analysis                          │
│                                             │
│ 5 tasks waiting, may cause project delays  │
│                                             │
│ Affected Projects: 2                        │
│ Affected Tasks: 5                           │
│ Estimated Delay: 2-4 hours                  │
└─────────────────────────────────────────────┘
```

**Description:**
```
📝 Description

Agent backend_001 has not checked in for 120 minutes.

Status:
- Last Active: 2:45 PM (120 minutes ago)
- Current Status: busy
- Pending Tasks: 5
- Current Task: uuid-123

This may indicate:
- Agent process crashed
- Network connectivity issues
- Infinite loop or deadlock
- System resource exhaustion

Immediate attention required to restore agent functionality.
```

**Suggested Actions (Checklist):**
```
✅ Suggested Actions

☐ Check agent health status
☐ Review agent logs for errors
☐ Restart agent if necessary
☐ Reassign pending tasks if agent cannot recover

[Mark Action Complete]
```

**Context Information:**
```
🔗 Related Items

Agent: backend_001 [View Agent →]

Tasks Affected:
├─ Build API endpoints (uuid-123) [View →]
├─ Implement authentication (uuid-456) [View →]
├─ Database schema migration (uuid-789) [View →]
└─ + 2 more

Projects Affected:
├─ E-commerce Platform [View →]
└─ Mobile App Backend [View →]
```

**3. Activity Timeline:**
```
📜 Activity History

[HR Agent]  2 min ago
Added comment: "Checking agent logs now. Found timeout errors..."

[System]  5 min ago
Sent notification to HR Agent

[System]  2 hours ago
Escalation created - Agent unresponsive threshold exceeded

──────────────────

💬 Add Comment or Action
┌─────────────────────────────────────────────┐
│ [Comment text area]                         │
│                                             │
│ [Attach logs]  [Mention agent]             │
└─────────────────────────────────────────────┘

[Add Comment]
```

**4. Action Buttons:**
```
Primary Actions:
[✅ Mark Resolved]  [⏸️ Acknowledge]  [⬆️ Escalate Further]

Secondary Actions:
[↔️ Reassign]  [🔄 Restart Agent]  [📋 View Logs]  [⚙️ Run Diagnostic]

Destructive:
[🗑️ Dismiss]  [❌ Close without Resolution]
```

**5. Resolution Form (When Resolving):**
```
✅ Resolve Escalation

Resolution Type:
○ Fixed - Issue resolved permanently
○ Workaround - Temporary solution applied
○ Not an Issue - False positive
○ Duplicate - Already tracked elsewhere

Resolution Description: *
┌─────────────────────────────────────────────┐
│ Describe what was done to resolve...       │
│                                             │
│ Min 20 characters                           │
└─────────────────────────────────────────────┘

Root Cause (Optional):
[Agent timeout due to LLM API rate limiting]

Prevention Steps (Optional):
[Implemented retry logic and circuit breakers]

☐ Apply same resolution to similar escalations

[Cancel]  [Resolve Escalation]
```

**6. Escalation Path Visualization:**
```
📈 Escalation Path

Level 1: System → HR Agent
         2 hours ago

⬆️ Not yet escalated to next level
   Will auto-escalate to CTO Agent in 1 hour if unresolved
```

**7. Similar Escalations:**
```
🔍 Similar Escalations

backend_001 unresponsive (Resolved)
└─ 3 days ago • Resolved by HR Agent • 45 min resolution time
   Solution: Restarted agent, added monitoring

frontend_001 unresponsive (Resolved)
└─ 1 week ago • Resolved by HR Agent • 30 min resolution time
   Solution: Fixed memory leak in code generation

[View All Similar →]
```

**Backend APIs:**
```
GET /api/v1/escalations/{escalation_id}
GET /api/v1/escalations/{escalation_id}/activity
GET /api/v1/escalations/{escalation_id}/similar
POST /api/v1/escalations/{escalation_id}/resolve
POST /api/v1/escalations/{escalation_id}/comment
POST /api/v1/escalations/{escalation_id}/acknowledge
POST /api/v1/escalations/{escalation_id}/escalate
POST /api/v1/escalations/{escalation_id}/reassign
```

**Testing Requirements:**
- ✅ All details display correctly
- ✅ Activity timeline updates in real-time
- ✅ Actions work with proper permissions
- ✅ Resolution form validates
- ✅ Similar escalations relevant
- ✅ Can navigate to related items

---

## Sub-Feature 8.3: Escalation Analytics

### 8.3.1: Escalation Metrics Dashboard

**User Story:**  
*As an admin, I want to see escalation trends and patterns so that I can improve system reliability.*

**Analytics Dashboard (`/escalations/analytics`):**

**1. Key Metrics:**
```
┌──────────────────────────────────────────────────────────┐
│ Last 30 Days                                             │
│                                                          │
│ Total: 234  |  Resolved: 218  |  Avg Time: 2.3 hrs     │
│ Resolution Rate: 93%  |  Recurring: 15%                 │
└──────────────────────────────────────────────────────────┘
```

**2. Escalation Trend:**
```
Escalations Over Time
┌────────────────────────────────────────────┐
│ 30│                                  ___   │
│ 25│                            _____/   \  │
│ 20│                      _____/          \_│
│ 15│                _____/                  │
│ 10│          _____/                        │
│  5│    _____/                              │
│   ├────────────────────────────────────────│
│    W1   W2   W3   W4   W5   W6   (weeks)  │
└────────────────────────────────────────────┘

Trend: ↑ 12% increase (Action needed)
```

**3. By Type:**
```
Escalations by Type (Last 30 Days)

Blocked Tasks         ████████████  78 (33%)
Agent Issues          ████████      52 (22%)
Deadline Risk         ██████        38 (16%)
Dependencies          ████          24 (10%)
Budget               ███           18 (8%)
Other                ████          24 (10%)
```

**4. By Severity:**
```
Critical    🔴 23 (10%)  Avg: 1.2 hrs
High        🟠 67 (29%)  Avg: 2.5 hrs
Medium      🟡 98 (42%)  Avg: 4.1 hrs
Low         ⚪ 46 (20%)  Avg: 8.3 hrs
```

**5. Resolution Time Distribution:**
```
< 1 hour     ████████  45%
1-4 hours    ███████   35%
4-12 hours   ███       15%
> 12 hours   █         5%

Target: 90% resolved within 4 hours
Current: 80% (Below target)
```

**6. Top Issues:**
```
Most Common Escalations

1. Backend agent timeout         23 occurrences
   └─ Avg resolution: 45 min
   └─ Root cause: LLM API rate limiting

2. Task dependencies blocking    18 occurrences
   └─ Avg resolution: 3.2 hrs
   └─ Root cause: Unclear requirements

3. Frontend build errors         15 occurrences
   └─ Avg resolution: 1.5 hrs
   └─ Root cause: Package version conflicts

[View Full Report →]
```

**7. Agent Performance:**
```
Escalation Resolution by Agent

HR Agent       Resolution Rate: 95%  Avg Time: 1.2 hrs
PM Agent       Resolution Rate: 88%  Avg Time: 3.5 hrs
CTO Agent      Resolution Rate: 92%  Avg Time: 2.8 hrs
CEO Agent      Resolution Rate: 85%  Avg Time: 6.2 hrs

Best Performer: HR Agent ⭐
```

**8. Recurring Issues:**
```
⚠️ Recurring Issues (Need Attention)

Backend agent timeout
├─ Occurrences: 23 times in 30 days
├─ Always resolved the same way: Restart agent
└─ Recommendation: Fix root cause (API rate limits)

Task dependency conflicts
├─ Occurrences: 18 times in 30 days
├─ Pattern: Unclear task breakdowns
└─ Recommendation: Improve PM task planning

[Create Action Plan]
```

**9. Impact Analysis:**
```
Business Impact

Total Delay Caused: 156 hours
Projects Affected: 45
Tasks Delayed: 234
Estimated Cost: $3,900 (agent time wasted)

Top Impact Categories:
1. Agent downtime: 89 hours
2. Blocked tasks: 45 hours
3. Deadline pressure: 22 hours
```

**10. Predictive Insights:**
```
🔮 Predictions & Recommendations

Based on current trends:
- Expect 65 escalations next week (↑15%)
- Backend agent timeout likely to recur (85% confidence)
- Project "Mobile App" at risk of escalation (deadline in 3 days)

Recommended Actions:
1. Implement API rate limit monitoring
2. Add redundancy for backend agent
3. Review PM task breakdown process
4. Schedule preventive maintenance for agents
```

**Export Options:**
- Export as PDF Report
- Export raw data as CSV
- Schedule weekly email reports
- Create custom dashboards

**Testing Requirements:**
- ✅ All metrics calculate correctly
- ✅ Charts render accurately
- ✅ Trends identified correctly
- ✅ Predictions reasonable
- ✅ Export functions work

---

### 8.1.2: Escalation Routing & Assignment

**User Story:**  
*As a system, I need to route escalations to the right agent or human based on issue type and severity.*

**Routing Logic:**

```python
class EscalationRoutingService:
    """Service for routing escalations to appropriate handlers"""
    
    # Escalation routing table
    ROUTING_TABLE = {
        'blocked_task': {
            'primary': 'pm_001',
            'secondary': 'cto_001',
            'escalate_after_hours': 4
        },
        'agent_unresponsive': {
            'primary': 'hr_001',
            'secondary': 'cto_001',
            'escalate_after_hours': 1
        },
        'circular_dependency': {
            'primary': 'pm_001',
            'secondary': 'cto_001',
            'escalate_after_hours': 2
        },
        'deadline_risk': {
            'primary': 'ceo_001',
            'secondary': 'pm_001',
            'escalate_after_hours': 8,
            'notify_human': True
        },
        'budget_exceeded': {
            'primary': 'cfo_001',
            'secondary': 'cto_001',
            'escalate_after_hours': 2,
            'notify_human': True
        },
        'agent_error_rate': {
            'primary': 'hr_001',
            'secondary': 'cto_001',
            'escalate_after_hours': 1
        },
        'resource_conflict': {
            'primary': 'pm_001',
            'secondary': 'coo_001',
            'escalate_after_hours': 2
        },
        'approval_timeout': {
            'primary': 'ceo_001',
            'escalate_after_hours': 24,
            'notify_human': True
        }
    }
    
    async def route_escalation(self, escalation_id: str):
        """Route escalation to appropriate handler"""
        
        escalation = await self._get_escalation(escalation_id)
        routing_config = self.ROUTING_TABLE.get(escalation.issue_type)
        
        if not routing_config:
            # Default routing
            escalation.escalated_to_agent_id = 'ceo_001'
        else:
            escalation.escalated_to_agent_id = routing_config['primary']
        
        await self.db.commit()
        
        # Send notification
        await self._notify_assigned_agent(escalation)
        
        # Set up auto-escalation if not resolved
        if routing_config and 'escalate_after_hours' in routing_config:
            await self._schedule_auto_escalation(
                escalation_id,
                hours=routing_config['escalate_after_hours'],
                escalate_to=routing_config.get('secondary')
            )
        
        # Notify human if required
        if routing_config and routing_config.get('notify_human'):
            await self._notify_human(escalation)
    
    async def escalate_further(self, escalation_id: str, reason: str):
        """Escalate to next level in hierarchy"""
        
        escalation = await self._get_escalation(escalation_id)
        routing_config = self.ROUTING_TABLE.get(escalation.issue_type)
        
        # Get next in escalation chain
        if escalation.escalation_level == 1:
            # Escalate to secondary
            new_handler = routing_config.get('secondary', 'ceo_001')
        else:
            # Escalate to CEO or human
            new_handler = 'ceo_001'
            if escalation.escalated_to_agent_id == 'ceo_001':
                # Already at CEO, escalate to human
                await self._notify_human(escalation, urgent=True)
                return
        
        # Update escalation
        escalation.escalation_level += 1
        escalation.escalation_path.append({
            'from': escalation.escalated_to_agent_id,
            'to': new_handler,
            'timestamp': datetime.utcnow().isoformat(),
            'reason': reason
        })
        escalation.escalated_to_agent_id = new_handler
        
        await self.db.commit()
        
        # Log escalation action
        await self._log_escalation_action(
            escalation_id,
            'escalate_further',
            f"Escalated to {new_handler}: {reason}"
        )
        
        # Notify new handler
        await self._notify_assigned_agent(escalation, escalated_from=True)
```

**Testing Requirements:**
- ✅ Escalations  - Placeholder: "Search knowledge base... (e.g., 'authentication best practices', 'API error handling')"
  - Auto-complete suggestions
  - Recent searches dropdown
  - Search button
  - Advanced search toggle

**Advanced Search Panel (Collapsible):**
```
┌─────────────────────────────────────────────┐
│ Category:        [Dropdown ▼]              │
│ Document Type:   [All Types ▼]             │
│ Tags:            [Multi-select]            │
│ Date Range:      [From] - [To]             │
│ Effectiveness:   [●────────○] 50%+         │
│ Created By:      [Agent/User dropdown]     │
│                                             │
│ [Clear Filters]        [Search]            │
└─────────────────────────────────────────────┘
```

**2. Category Browser (Left Sidebar):**

```
📁 Categories
├─ 💻 Technical Standards (45)
│  ├─ Code Style (12)
│  ├─ Architecture (15)
│  └─ Technology Stack (18)
├─ 🔄 Process Documentation (32)
├─ ⚖️ Decision History (56)
├─ 💡 Solutions Library (78)
├─ 📋 Project Templates (23)
├─ 📚 Lessons Learned (34)
└─ ⭐ Best Practices (41)

🏷️ Popular Tags
• python (89)
• authentication (45)
• api-design (38)
• frontend (52)
• database (41)
[View all tags →]

📊 Quick Stats
• Most Viewed This Week
• Newly Added
• Most Effective
• Awaiting Validation
```

**3. Main Content Area - Document List:**

**View Options:**
- Grid view (cards)
- List view (table)
- Timeline view

**Grid View - Document Cards:**
```
┌─────────────────────────────────────────────┐
│ 💡 Solution: JWT Authentication Implementation │
│                                               │
│ Implementing secure JWT-based authentication  │
│ with refresh tokens for REST APIs...         │
│                                               │
│ 🏷️ python  api  security  jwt               │
│                                               │
│ ⭐ 95% effective • 👁️ 234 views • ✅ Validated │
│ 📅 Created by Backend Agent • 15 days ago    │
│                                               │
│ [View Details]              [Use Template]   │
└─────────────────────────────────────────────┘
```

**List View - Table Format:**
| Title | Category | Type | Effectiveness | Views | Created | Actions |
|-------|----------|------|---------------|-------|---------|---------|
| JWT Auth Implementation | Technical | Solution | ⭐⭐⭐⭐⭐ 95% | 👁️ 234 | Backend Agent, 15d ago | 👁️ 📋 ⭐ |
| React Component Patterns | Technical | Standard | ⭐⭐⭐⭐ 88% | 👁️ 156 | Frontend Agent, 1mo ago | 👁️ 📋 ⭐ |

**4. Sorting & Filtering Bar:**
```
Sort by: [Most Relevant ▼]  |  Filter: [All ▼]  |  Show: [20 per page ▼]
```

**Sort Options:**
- Most Relevant (default for search)
- Most Recent
- Most Viewed
- Most Effective
- Most Used
- Alphabetical

**Backend API:**
```
GET /api/v1/knowledge-base?
  q=authentication&
  category=technical_standards&
  document_type=solution&
  tags=python,api&
  min_effectiveness=0.7&
  sort_by=effectiveness&
  sort_order=desc&
  page=1&
  page_size=20
```

**Response:**
```json
{
  "documents": [
    {
      "document_id": "uuid-123",
      "title": "JWT Authentication Implementation",
      "summary": "Secure JWT-based auth with refresh tokens...",
      "category": "Technical Standards",
      "subcategory": "Security",
      "document_type": "solution",
      "tags": ["python", "jwt", "api", "security"],
      "effectiveness_score": 0.95,
      "view_count": 234,
      "use_count": 45,
      "created_by_agent_id": "backend_001",
      "created_by_agent_name": "Backend Engineer",
      "created_at": "2025-10-10T10:30:00Z",
      "validated": true,
      "is_favorite": false
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 156,
    "total_pages": 8
  },
  "facets": {
    "categories": {
      "Technical Standards": 45,
      "Solutions Library": 78,
      "Best Practices": 33
    },
    "document_types": {
      "solution": 56,
      "standard": 34,
      "template": 23
    }
  }
}
```

**UI Interactions:**

**1. Search Behavior:**
- Debounced search (300ms delay)
- Highlight matching terms in results
- Show result count
- Suggest corrections for typos
- "Did you mean...?" suggestions
- Save search to recent searches

**2. Filter Behavior:**
- Multiple filters can be combined (AND logic)
- Show active filter count badge
- Clear individual filters
- Clear all filters button
- Filters persist in URL (shareable links)

**3. Empty States:**
```
No Results Found

We couldn't find any documents matching your search.

Try:
• Using different keywords
• Removing some filters
• Browsing by category instead

[Browse Categories]  [Clear Filters]
```

**Testing Requirements:**
- ✅ Search returns relevant results
- ✅ Filters work correctly in combination
- ✅ Sorting changes order correctly
- ✅ Pagination works
- ✅ URL reflects search state (shareable)
- ✅ Performance acceptable with 1000+ documents
- ✅ Mobile responsive

**Accessibility:**
- Keyboard navigation for all elements
- Screen reader announces result count
- Filter changes announced
- Focus management on navigation
- ARIA labels for all interactive elements

**Analytics:**
- `kb_searched`
- `kb_filter_applied`
- `kb_category_browsed`
- `kb_document_clicked`
- `kb_sort_changed`

---

# Feature 8: Escalations

## Overview
The Escalation system automatically detects issues, bottlenecks, and problems in the agent workflow, then routes them to the appropriate agent or human for resolution. It ensures no task gets stuck indefinitely and provides a safety net for the autonomous system.

---
