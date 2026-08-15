## Feature 4: Messages & Communication

### Sub-Feature 4.1: Message Center

**Description:**  
Centralized hub for all messages between user and agents.

#### 4.1.1: Message Inbox

**User Story:**  
*As a user, I want to see all my messages with agents so that I can track conversations and responses.*

**Page Layout:**

**1. Inbox View:**
- **Layout:** Similar to email client
- **Left Sidebar:**
  - All Messages (count badge)
  - Unread (count badge)
  - Sent by Me
  - By Agent (expandable list)
  - By Project (expandable list)
  - Starred/Important
  - Archive

**2. Message List (Center):**
- **Message Preview Cards:**
  - Agent avatar + name
  - Subject line (bold if unread)
  - Message preview (first 100 chars)
  - Timestamp (relative)
  - Unread indicator (blue dot)
  - Star/Favorite icon
  - Priority indicator (if high)
  - Related project/task badge
  
- **Sorting:**
  - Newest first (default)
  - Oldest first
  - By priority
  - By agent
  
- **Bulk Actions:**
  - Select multiple messages
  - Mark as read/unread
  - Star/Unstar
  - Archive
  - Delete

**3. Message Detail (Right Panel):**
- **When message selected:**
  - Full message content
  - Sender info (agent profile link)
  - Timestamp
  - Related project/task links
  - Thread history (if conversation)
  
- **Actions:**
  - Reply button (opens reply box)
  - Forward (future feature)
  - Star/Unstar
  - Archive
  - Delete
  
- **Reply Box:**
  - Textarea at bottom
  - Send button
  - Attach context (checkbox)
  - Cancel (closes reply box)

**4. Filters & Search:**
- **Filter Panel:**
  - Unread only (toggle)
  - By agent (multi-select)
  - By priority
  - By date range
  - Has attachments (future)
  
- **Search:**
  - Search bar at top
  - Searches subject and content
  - Full-text search
  - Highlight results

**Backend API:**
```
GET /api/v1/messages?
  unread=true&
  from_agent=ceo_001&
  page=1&
  page_size=50&
  sort_by=timestamp&
  sort_order=desc
```

**Response:**
```json
{
  "messages": [
    {
      "message_id": "uuid-123",
      "from_agent_id": "ceo_001",
      "from_agent_name": "CEO Agent",
      "to_agent_id": "human",
      "subject": "Project Approved",
      "content": "Your project has been approved...",
      "priority": "high",
      "read_status": false,
      "timestamp": "2025-10-25T10:30:00Z",
      "related_task_id": "uuid-456",
      "related_project_id": "uuid-789"
    }
  ],
  "pagination": {...},
  "unread_count": 5
}
```

**Real-time Updates:**
- WebSocket for new messages
- Desktop notification
- Sound alert (optional)
- Badge count updates

**Mark as Read:**
- Automatic: After 3 seconds of viewing
- Manual: Click "Mark as read" button
- Bulk: Select multiple, mark as read

**Testing Requirements:**
- ✅ Messages display correctly
- ✅ Filters work
- ✅ Search works
- ✅ Real-time updates work
- ✅ Reply sends successfully
- ✅ Unread count accurate

**Accessibility:**
- Keyboard navigation (arrow keys, enter)
- Screen reader support
- Focus management
- ARIA labels

**Analytics:**
- `message_inbox_viewed`
- `message_opened`
- `message_replied`
- `message_searched`

---

### Sub-Feature 4.2: Message Threading

**Description:**  
Group related messages into conversation threads.

#### 4.2.1: Threaded Conversations

**User Story:**  
*As a user, I want to see messages grouped by conversation so that I can follow the context.*

**Threading Logic:**
1. **Thread Creation:**
   - First message creates thread
   - Thread ID = first message_id
   
2. **Thread Association:**
   - Reply includes `thread_id` field
   - All replies linked to same thread
   
3. **Thread Display:**
   - Messages shown chronologically
   - Visual indentation for replies
   - Thread starter highlighted
   - Collapse/expand thread

**UI Design:**
- **Thread Indicator:**
  - Show count: "3 messages in thread"
  - Expand/collapse icon
  
- **Expanded Thread:**
  - All messages visible
  - Alternating background colors
  - Reply box at bottom
  
- **Collapsed Thread:**
  - Show latest message only
  - "Show previous messages" link

**Backend Structure:**
```json
{
  "message_id": "uuid-123",
  "thread_id": "uuid-100",
  "in_reply_to": "uuid-122",
  "thread_position": 3,
  "is_thread_starter": false
}
```

**Testing Requirements:**
- ✅ Threads group correctly
- ✅ Replies associate with thread
- ✅ Thread display works
- ✅ Collapse/expand works

---


