## Feature 2: Tasks

### Sub-Feature 2.1: View Tasks

**Description:**  
Display all tasks with their current status, assigned agents, and progress.

#### 2.1.1: Task List View

**User Story:**  
*As a user, I want to see all tasks across all projects so that I understand what work is happening.*

**Page Layout:**

**1. Task Board (Kanban):**
- **Columns:**
  - Pending (Yellow)
  - In Progress (Blue)
  - Blocked (Red)
  - Review (Purple)
  - Completed (Green)

- **Task Cards:**
  - Task ID (small, top right)
  - Task title
  - Project name (link)
  - Agent avatar + name
  - Priority indicator (small dot)
  - Estimated hours badge
  - Last updated (relative time)
  - Dependency indicator (if any)
  - Hover: Shows preview tooltip

- **Drag & Drop:**
  - Can reorder within column
  - Cannot drag between columns (auto-managed)
  - Visual feedback on drag
  - Smooth animations

**2. Task Table (List):**
- **Columns:**
  - Status (badge)
  - Title (clickable)
  - Project (link)
  - Agent (avatar + name)
  - Priority
  - Created
  - Updated
  - Estimated Hours
  - Actions (...)

- **Row Actions:**
  - View details
  - View in project context
  - Copy task ID
  - Escalate (if blocked >2 hours)

**3. Filters:**
- Status (multi-select)
- Agent (multi-select)
- Project (multi-select with search)
- Priority
- Date range
- Has dependencies (yes/no)
- Blocked (yes/no)

**4. Search:**
- Search by task title, description, output
- Real-time results
- Highlight matches

**Backend API:**
```
GET /api/v1/tasks?
  status=in_progress&
  assigned_to=backend_001&
  project_id=uuid&
  page=1&
  page_size=20
```

**Real-time Updates:**
- Tasks auto-update every 15 seconds
- WebSocket for instant updates
- Visual pulse on change
- Sound notification (optional, user setting)

**Testing Requirements:**
- ✅ Board view displays correctly
- ✅ Table view displays correctly
- ✅ Filters work
- ✅ Real-time updates work
- ✅ Can switch views seamlessly

---

#### 2.1.2: Task Detail View

**User Story:**  
*As a user, I want to see complete information about a specific task so that I understand what an agent is doing.*

**Modal/Page Layout:**

**1. Task Header:**
- Task title (large)
- Status badge (prominent)
- Agent working on it (avatar + name, clickable)
- Project breadcrumb (Home > Projects > ProjectName > Task)

**2. Task Information:**
- **Description:**
  - Full task description
  - Acceptance criteria (bullet points)
  - Technical requirements

- **Metadata:**
  - Created: Timestamp + agent who created
  - Assigned: Timestamp + assigning agent
  - Last Updated: Timestamp + what changed
  - Estimated Hours: e.g., 4 hours
  - Actual Hours: e.g., 3.5 hours (if completed)
  - Status: Current status with history

**3. Dependencies:**
- **Depends On:**
  - List of tasks that must complete first
  - Visual: Green checkmark if done, yellow if pending
  - Click to view dependent task

- **Blocking:**
  - List of tasks waiting for this one
  - Shows impact

- **Dependency Graph:**
  - Visual tree diagram
  - Interactive (click nodes)

**4. Activity Timeline:**
- Chronological log of all actions:
  - Task created
  - Status changed
  - Agent started work
  - Output added
  - Review requested
  - Approved
- Each entry:
  - Icon
  - Description
  - Agent/user who did it
  - Timestamp

**5. Output/Deliverables:**
- **If Code:**
  - Syntax highlighted code editor (read-only)
  - Language detection
  - Copy button
  - Download button
  - Line numbers

- **If Design:**
  - Image preview
  - Zoom functionality
  - Download original

- **If Document:**
  - Rendered markdown/HTML
  - Download as PDF

**6. Reviews/Approvals:**
- If task status = "review":
  - Shows who needs to approve
  - "Approve" button (if user is approver)
  - "Request Changes" button
  - Comment box

**7. Messages:**
- Task-specific message thread
- Send message to assigned agent
- @mention other agents

**8. Actions:**
- Copy Task ID
- Copy Link to Task
- Escalate (if blocked)
- Reassign (PM/CTO only)
- Edit Task (PM only)
- Delete Task (PM only, with confirmation)

**Loading States:**
- Skeleton for all sections
- Progressive loading

**Error States:**
- Task not found
- Access denied
- Output unavailable

**Backend API:**
```
GET /api/v1/tasks/{task_id}
GET /api/v1/tasks/{task_id}/activity
GET /api/v1/tasks/{task_id}/dependencies
GET /api/v1/tasks/{task_id}/output
```

**Real-time:**
- WebSocket: `ws://api/v1/tasks/{task_id}/subscribe`
- Live updates to status, output, comments

**Testing Requirements:**
- ✅ All sections load correctly
- ✅ Dependencies display accurately
- ✅ Output renders correctly for all types
- ✅ Real-time updates work
- ✅ Actions work with proper permissions

**Analytics:**
- `task_detail_viewed`
- `task_output_downloaded`
- `task_escalated`
- `task_approved`

---

### Sub-Feature 2.2: Task Dependencies

**Description:**  
Manage relationships between tasks to ensure proper execution order.

#### 2.2.1: Automatic Dependency Management

**How It Works:**
1. **PM Agent Creates Dependencies:**
   - When PM breaks down project
   - Analyzes task relationships
   - Creates dependency links automatically

2. **Dependency Types:**
   - **Finish-to-Start (FS):**
     - Task B cannot start until Task A finishes
     - Most common type
     - Example: Design must finish before Frontend starts

   - **Start-to-Start (SS):**
     - Task B can start when Task A starts
     - Parallel work
     - Example: Backend and Frontend can start together

3. **Dependency Storage:**
```json
{
  "task_id": "uuid-123",
  "dependencies": [
    {
      "depends_on_task_id": "uuid-456",
      "type": "finish-to-start",
      "blocking": true
    }
  ]
}
```

4. **Automatic Blocking:**
   - If dependency not met, task status cannot change to "in_progress"
   - Agent attempts to start → System blocks
   - Task shows "Waiting on dependencies" status

5. **Dependency Resolution:**
   - When dependency task completes
   - System checks all tasks waiting on it
   - Changes status from "pending" to "ready"
   - Notifies assigned agent
   - Notifies assigned agent

**UI Visualization:**
- **Dependency Graph:**
  - Interactive flow diagram
  - Nodes = Tasks
  - Edges = Dependencies
  - Color coding:
    - Green: Completed
    - Blue: In progress
    - Yellow: Ready to start
    - Gray: Blocked
  - Click node to view task
  - Zoom/pan controls

- **Task Card Indicators:**
  - "🔒 Blocked by 2 tasks" badge
  - "⏳ Waiting on: Design task"
  - "✅ Dependencies met" checkmark

**Backend Logic:**
```python
async def can_start_task(task_id: str) -> bool:
    """Check if all dependencies are met"""
    task = await get_task(task_id)
    dependencies = task.dependencies
    
    for dep in dependencies:
        dep_task = await get_task(dep['depends_on_task_id'])
        if dep_task.status != 'completed':
            return False
    
    return True

async def on_task_completed(task_id: str):
    """When task completes, unblock dependent tasks"""
    blocked_tasks = await get_tasks_blocked_by(task_id)
    
    for blocked_task in blocked_tasks:
        if await can_start_task(blocked_task.task_id):
            await notify_agent(blocked_task.assigned_to_agent_id)
            await update_task_status(blocked_task.task_id, 'ready')
```

**Circular Dependency Prevention:**
- Detect cycles in dependency graph
- Prevent creation of circular dependencies
- Alert PM agent if detected
- Suggest resolution

**Testing Requirements:**
- ✅ Dependencies prevent premature task start
- ✅ Task unblocks when dependencies met
- ✅ Circular dependencies detected
- ✅ Dependency graph visualizes correctly
- ✅ Notifications sent on unblock

---
