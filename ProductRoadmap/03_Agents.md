## Feature 3: Agents

### Sub-Feature 3.1: Agent Status Monitoring

**Description:**  
Real-time monitoring of all AI agents in the system, their current state, and health.

#### 3.1.1: Agent Dashboard

**User Story:**  
*As a user, I want to see the status of all AI agents so that I know if the system is working properly.*

**Page Layout:**

**1. Agent Grid View:**
- **Agent Cards (7 cards for Phase 1):**
  
  **Card Design:**
  - Agent avatar/icon (unique per role)
  - Agent name (e.g., "CEO Agent")
  - Agent ID (small, bottom)
  - Role subtitle (e.g., "Chief Executive Officer")
  - Department badge
  
  **Status Indicator:**
  - Large circular badge (top-right)
  - Colors:
    - 🟢 Green: Available
    - 🔵 Blue: Busy
    - 🟡 Yellow: Blocked
    - 🔴 Red: Error
    - ⚪ Gray: Offline
  - Pulse animation when active
  
  **Current Activity:**
  - If busy: "Working on: [Task Title]"
  - If available: "Ready for new tasks"
  - If blocked: "Waiting on: [Blocker]"
  - Progress bar (if applicable)
  
  **Metrics:**
  - Tasks completed today: 3
  - Average completion time: 2.5 hours
  - Success rate: 95%
  - Last active: 2 minutes ago
  
  **Quick Actions:**
  - View Agent Details
  - View Current Task
  - Send Message
  - View History

**2. System Health Overview:**
- **Aggregate Metrics:**
  - Total Agents: 7
  - Active: 4
  - Idle: 2
  - Error: 1
  - System Uptime: 99.8%
  
- **Health Status:**
  - Overall health indicator (green/yellow/red)
  - Critical issues count
  - Warnings count

**3. Activity Feed:**
- Real-time stream of agent actions
- Last 20 activities
- Auto-scroll to new items
- Format:
  ```
  [2 min ago] Backend Engineer Agent completed "API Endpoints"
  [5 min ago] CEO Agent approved new project
  [8 min ago] PM Agent created 5 tasks
  ```

**4. Performance Charts:**
- **Tasks Completed Over Time:**
  - Line chart
  - Last 24 hours
  - Per agent breakdown
  
- **Agent Utilization:**
  - Bar chart
  - % of time busy vs idle
  - Per agent

**Real-time Updates:**
- WebSocket connection
- Updates every 15 seconds (or on agent check cycle)
- Visual feedback on update
- Connection status indicator

**Backend API:**
```
GET /api/v1/agents/status
GET /api/v1/agents/{agent_id}/status
GET /api/v1/agents/activity-feed
GET /api/v1/agents/metrics
```

**Response Example:**
```json
{
  "agents": [
    {
      "agent_id": "ceo_001",
      "name": "CEO Agent",
      "role": "Chief Executive Officer",
      "department": "executive",
      "status": {
        "availability": "busy",
        "health_status": "healthy",
        "current_task_id": "uuid-123",
        "current_task_title": "Process new project",
        "last_active": "2025-10-25T10:30:00Z",
        "last_check_time": "2025-10-25T10:30:00Z"
      },
      "metrics": {
        "tasks_completed_today": 3,
        "tasks_completed_total": 45,
        "average_completion_time_hours": 2.5,
        "success_rate": 0.95
      }
    }
  ],
  "system_health": {
    "overall": "healthy",
    "critical_issues": 0,
    "warnings": 1,
    "uptime_percentage": 99.8
  }
}
```

**Testing Requirements:**
- ✅ All agents display correctly
- ✅ Status updates in real-time
- ✅ Metrics calculate accurately
- ✅ Activity feed updates
- ✅ Charts render correctly
- ✅ WebSocket reconnects on disconnect

**Accessibility:**
- Status changes announced to screen readers
- Color-blind friendly status indicators
- Keyboard navigation support

**Analytics:**
- `agents_dashboard_viewed`
- `agent_card_clicked`
- `agent_message_sent`

---

#### 3.1.2: Agent Detail View

**User Story:**  
*As a user, I want to see detailed information about a specific agent so that I can understand its behavior and performance.*

**URL:** `/agents/{agent_id}`

**Page Layout:**

**1. Agent Profile Header:**
- Large avatar/icon
- Agent name and ID
- Role and department
- Current status (prominent badge)
- Reports to: Link to manager agent
- Team members: Links to direct reports (if any)

**2. Current State:**
- **If Busy:**
  - Current task (title + link)
  - Project context (link)
  - Started: Timestamp
  - Estimated completion: Based on task estimate
  - Progress: Visual progress bar
  - Output preview (if available)

- **If Available:**
  - "Ready for new tasks"
  - Next task in queue (if any)
  - Waiting for: Dependencies, approvals, etc.

- **If Blocked:**
  - Blocking reason
  - Blocked since: Timestamp
  - Escalation status
  - Responsible for resolution: Which agent/human

**3. Capabilities & Permissions:**
- **Decision Authority:**
  - List what agent can decide autonomously
  - What needs approval
  - Example decisions made

- **Permissions (RBAC):**
  - Read access: [list of resources]
  - Write access: [list of resources]
  - Approve access: [list of approval types]

- **System Prompt (Collapsible):**
  - Shows agent's instructions
  - Read-only
  - Helps understand agent behavior

**4. Performance Metrics:**
- **Statistics Cards:**
  - Total Tasks Completed: 125
  - Success Rate: 97%
  - Average Task Duration: 3.2 hours
  - Tasks Today: 5
  - On-time Completion: 92%
  
- **Performance Trends:**
  - Line chart: Tasks per day (last 30 days)
  - Bar chart: Task duration distribution
  - Pie chart: Task types handled

**5. Task History:**
- **Recent Tasks Table:**
  - Last 20 tasks
  - Columns: Title, Project, Status, Duration, Completed Date
  - Click to view task details
  - Filter by status, date range
  - Export to CSV

**6. Communication History:**
- **Messages Sent/Received:**
  - Last 50 messages
  - Thread view
  - Filter by recipient/sender
  - Search within messages

**7. Decision Log:**
- All decisions made by this agent
- Approval status
- Rationale provided
- Timeline visualization

**8. Health & Diagnostics:**
- **Health Metrics:**
  - Last check time: 1 minute ago
  - Response time: 3.2 seconds average
  - Error rate: 0.5%
  - LLM call success rate: 99.2%

- **Recent Errors (if any):**
  - Error message
  - Timestamp
  - Context (what agent was doing)
  - Resolution status

- **Diagnostic Actions:**
  - Restart Agent (Admin only)
  - Clear Context (Admin only)
  - View Logs
  - Test Health Check

**Backend APIs:**
```
GET /api/v1/agents/{agent_id}
GET /api/v1/agents/{agent_id}/tasks?page=1&page_size=20
GET /api/v1/agents/{agent_id}/messages
GET /api/v1/agents/{agent_id}/decisions
GET /api/v1/agents/{agent_id}/metrics
GET /api/v1/agents/{agent_id}/health
```

**Real-time Updates:**
- WebSocket: `ws://api/v1/agents/{agent_id}/subscribe`
- Status changes update immediately
- Task progress updates

**Testing Requirements:**
- ✅ All sections load correctly
- ✅ Metrics calculate accurately
- ✅ Charts render properly
- ✅ Real-time updates work
- ✅ History loads with pagination
- ✅ Diagnostic actions work (Admin)

**Analytics:**
- `agent_detail_viewed`
- `agent_task_history_viewed`
- `agent_diagnostic_run`

---

### Sub-Feature 3.2: Agent Communication

**Description:**  
Enable users to send messages to specific agents and receive responses.

#### 3.2.1: Send Message to Agent

**User Story:**  
*As a user, I want to send a message to an agent so that I can provide additional context or ask questions.*

**UI Components:**

**1. Message Modal/Panel:**
- **Trigger:** "Send Message" button on agent card/detail page
- **Modal Contents:**
  
  **Header:**
  - "Message to [Agent Name]"
  - Agent avatar
  - Close button
  
  **Form:**
  - **Subject (Optional):**
    - Text input
    - Max 100 characters
    - Placeholder: "Brief subject..."
  
  - **Message (Required):**
    - Textarea
    - Min 10 characters, max 2000
    - Character counter
    - Placeholder: "Type your message to [Agent Name]..."
  
  - **Priority:**
    - Select: Low, Medium, High
    - Default: Medium
    - High priority messages interrupt agent
  
  - **Attach Context:**
    - Checkbox: "Related to current task"
    - If checked, dropdown to select task
    - Auto-fills context for agent
  
  **Actions:**
  - Send button (primary)
  - Cancel button (secondary)

**2. Message Sending Flow:**
1. User fills form and clicks "Send"
2. Validation checks
3. Show loading spinner
4. API call to send message
5. Success:
   - Close modal
   - Show toast: "Message sent to [Agent]"
   - Add to message history
6. Error:
   - Show error message
   - Keep modal open
   - Retry option

**Backend API:**
```
POST /api/v1/messages
Content-Type: application/json

{
  "from_agent_id": "human",
  "to_agent_id": "ceo_001",
  "subject": "Question about project",
  "content": "Can you provide status update?",
  "priority": "high",
  "related_task_id": "uuid-123"
}
```

**Response:**
```json
{
  "message_id": "uuid-456",
  "status": "sent",
  "created_at": "2025-10-25T10:30:00Z",
  "expected_response_time": "Within 15 minutes",
  "agent_will_respond": true
}
```

**Agent Processing:**
1. Message added to agent's unread messages
2. On next check cycle (within 15 min):
   - Agent reads message
   - Processes with LLM
   - Generates response
   - Sends response message back
3. User notified of response

**Message Priority Handling:**
- **High Priority:**
  - Interrupts agent immediately (WebSocket push)
  - Agent pauses current work (if safe)
  - Processes message urgently
  - Responds within 5 minutes

- **Medium Priority:**
  - Added to message queue
  - Processed in next check cycle
  - Responds within 15 minutes

- **Low Priority:**
  - Processed when agent available
  - Responds within 1 hour

**Notification System:**
- User notified when agent responds
- Browser notification (if enabled)
- Email notification (configurable)
- In-app badge count

**Testing Requirements:**
- ✅ Message sends successfully
- ✅ Validation works
- ✅ Agent receives message
- ✅ Agent responds appropriately
- ✅ User notified of response
- ✅ Priority handling works correctly

**Analytics:**
- `message_to_agent_sent`
- `message_priority_used`
- `agent_response_received`

---
