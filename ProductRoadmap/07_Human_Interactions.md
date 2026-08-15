## Feature 6: Human Interactions

### Sub-Feature 6.1: Approval Requests

**Description:**  
Agents request human approval for critical decisions.

#### 6.1.1: Approval Request Flow

**User Story:**  
*As a user, I want to approve or reject agent decisions so that I maintain control over critical actions.*

**Approval Scenarios:**
1. **Budget Approval:**
   - Agent: CFO
   - Trigger: Expense >$1000
   - Requires: Human approval

2. **Strategic Decision:**
   - Agent: CEO
   - Trigger: Major direction change
   - Requires: Human approval

3. **Architecture Change:**
   - Agent: CTO
   - Trigger: Major tech stack change
   - Requires: Human approval

4. **Final Output:**
   - Agent: CEO
   - Trigger: Project completion
   - Requires: Human review & approval

**UI Flow:**

**1. Approval Notification:**
- **Desktop Notification:**
  - Title: "Approval Required"
  - Body: "[Agent] needs approval for [Action]"
  - Click to open approval modal

- **In-App Notification:**
  - Badge count on bell icon
  - Banner at top of page
  - "You have 2 pending approvals"

- **Email Notification:** (Optional)
  - Subject: "Approval Required: [Action]"
  - Link to approval page

**2. Approval Modal:**
- **Header:**
  - Title: "Approval Request from [Agent Name]"
  - Agent avatar
  - Priority indicator (if urgent)

- **Content:**
  - **What needs approval:**
    - Clear description
    - Why approval needed
    - Impact if approved/rejected
    - Related project/task links
  
  - **Agent's Rationale:**
    - Detailed explanation
    - Why this decision
    - Alternatives considered
    - Recommended action
  
  - **Context:**
    - Related documents/data
    - Previous decisions
    - Stakeholder impact

- **Actions:**
  - **Approve Button:**
    - Color: Green
    - Text: "Approve"
    - Confirmation: "Are you sure?"
  
  - **Reject Button:**
    - Color: Red
    - Text: "Reject"
    - Requires: Reason for rejection (textarea)
  
  - **Request More Info:**
    - Color: Gray
    - Opens message to agent
    - Agent responds with more details
  
  - **Defer Decision:**
    - Snooze for: 1 hour, 4 hours, 1 day
    - Reminder notification sent

**3. Response Handling:**
- **On Approve:**
  - Modal closes
  - Toast: "Approved successfully"
  - Agent notified immediately (WebSocket)
  - Agent continues work
  - Decision logged

- **On Reject:**
  - Modal shows rejection reason field
  - Submit rejection
  - Toast: "Rejected"
  - Agent notified with reason
  - Agent must re-plan or escalate
  - Decision logged

- **On Request More Info:**
  - Message sent to agent
  - Modal stays open or closes (user choice)
  - User notified when agent responds
  - Can then approve/reject

**Backend API:**
```
POST /api/v1/human-interactions/{interaction_id}/respond
Content-Type: application/json

{
  "response_type": "approved",
  "notes": "Approved with conditions: Keep budget under $5k",
  "conditions": {...}
}
```

**Database:**
```sql
UPDATE human_interactions
SET status = 'responded',
    human_response = 'Approved with conditions...',
    responded_at = NOW()
WHERE interaction_id = ?;
```

**Agent Handling:**
```python
# Agent checks for response
async def check_pending_approvals(agent_id):
    approvals = await get_pending_approvals(agent_id)
    
    for approval in approvals:
        if approval.status == 'responded':
            if approval.response_type == 'approved':
                await continue_work_approved(approval)
            elif approval.response_type == 'rejected':
                await handle_rejection(approval)
```

**Testing Requirements:**
- ✅ Approval request created correctly
- ✅ User notified
- ✅ Modal displays all info
- ✅ Approve flow works
- ✅ Reject flow works
- ✅ More info request works
- ✅ Agent receives response
- ✅ Agent acts on response

**Analytics:**
- `approval_request_created`
- `approval_viewed`
- `approval_# AgentForce - Complete Product Roadmap


### 7.2.2: Document Detail View

**User Story:**  
*As a user, I want to view complete details of a knowledge document so that I can learn from it and understand its context.*

**Page Layout (`/knowledge-base/{document_id}`):**

**1. Header Section:**
```
┌─────────────────────────────────────────────────────────┐
│ [← Back to Knowledge Base]              [⭐ Favorite]   │
│                                                           │
│ 💡 JWT Authentication Implementation                     │
│ Technical Standards > Security > Authentication          │
│                                                           │
│ ⭐⭐⭐⭐⭐ 95% Effective • 👁️ 234 views • ✅ Validated     │
│                                                           │
│ 🏷️ python  jwt  api  security  authentication           │
│                                                           │
│ Created by: Backend Agent • 15 days ago                  │
│ Last updated: 10 days ago • Version 2                    │
└─────────────────────────────────────────────────────────┘
```

**Action Buttons:**
- ⭐ Favorite/Unfavorite
- 📋 Copy to Clipboard
- 📥 Download as PDF
- 🔗 Share Link
- ✏️ Edit (if permitted)
- 🚩 Report Issue
- 📊 View Analytics

**2. Document Content (Main Area):**

**Summary Box (Highlighted):**
```
┌─────────────────────────────────────────────┐
│ 📝 Summary                                  │
│                                             │
│ This document provides a comprehensive      │
│ approach to implementing JWT authentication │
│ with refresh tokens in a REST API context. │
│ Includes security best practices and code   │
│ examples.                                   │
└─────────────────────────────────────────────┘
```

**Table of Contents (Collapsible):**
```
📑 Contents
1. Overview
2. Implementation Steps
3. Security Considerations
4. Code Examples
5. Testing Approach
6. Common Pitfalls
```

**Main Content:**
- Rendered markdown with syntax highlighting
- Code blocks with copy button
- Images/diagrams (if any)
- Interactive examples (if applicable)
- Collapsible sections
- Anchor links for headers

**Code Block Example:**
```python
# JWT Token Generation
def generate_token(user_id: str) -> str:
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

[📋 Copy Code]
```

**3. Metadata Sidebar (Right):**

**Quick Info:**
```
📊 Document Info
─────────────────
Document Type: Solution
Category: Technical Standards
Subcategory: Security

📈 Performance
─────────────────
Effectiveness: 95%
Success Rate: 42/45 uses
Avg. Time Saved: 2.3 hours

👥 Usage Stats
─────────────────
Total Views: 234
Total Uses: 45
Unique Users: 23
Last Used: 2 hours ago

🤖 Agent Info
─────────────────
Created By: Backend Agent
Validated By: CTO Agent
Contributing Agents: 3

🔒 Access
─────────────────
Access Level: Public
Anyone can view

📅 Timeline
─────────────────
Created: Oct 10, 2025
Last Updated: Oct 20, 2025
Version: 2
```

**4. Related Documents Section:**
```
🔗 Related Documents

┌─────────────────────────────────────┐
│ OAuth 2.0 Implementation Guide      │
│ Alternative authentication approach │
│ ⭐ 88% • 156 views                  │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ API Security Best Practices         │
│ Comprehensive security guide        │
│ ⭐ 92% • 189 views                  │
└─────────────────────────────────────┘

[View All Related →]
```

**5. Version History Section:**
```
📜 Version History

Version 2 • Oct 20, 2025 • Backend Agent
└─ Updated refresh token handling
   Added security considerations for token storage

Version 1 • Oct 10, 2025 • Backend Agent
└─ Initial implementation guide

[View Full History]
```

**6. Usage Examples Section:**
```
✅ Successfully Used In:

Project: E-commerce Platform (uuid-456)
├─ Task: Implement user authentication
└─ Outcome: ✅ Completed successfully in 2.5 hours

Project: Mobile App Backend (uuid-789)
├─ Task: Add JWT auth to API
└─ Outcome: ✅ Completed, user reported 30% faster

[View All Usage Examples →]
```

**7. Feedback Section:**
```
💭 Feedback & Comments

Was this document helpful?
[👍 Yes (42)]  [👎 No (3)]

Recent Feedback:
─────────────────

Backend Agent • 2 days ago
"Excellent guide, saved significant development time.
The refresh token implementation was particularly helpful."
└─ Used in: E-commerce Auth (Task #123)

Frontend Agent • 1 week ago
"Clear explanation of token lifecycle. Would benefit
from more frontend integration examples."
└─ Used in: Dashboard Login (Task #456)

[Load More Comments]

[💬 Add Your Feedback]
```

**8. Suggested Improvements Section:**
```
💡 Suggested Improvements

These improvements have been suggested by agents:

1. Add examples for mobile clients
   Suggested by: Mobile Engineer • 5 days ago
   Votes: 5 👍

2. Include rate limiting guidance
   Suggested by: Backend Agent • 1 week ago
   Votes: 3 👍

[➕ Suggest Improvement]
```

**Backend APIs:**
```
GET /api/v1/knowledge-base/{document_id}
GET /api/v1/knowledge-base/{document_id}/versions
GET /api/v1/knowledge-base/{document_id}/related
GET /api/v1/knowledge-base/{document_id}/usage
GET /api/v1/knowledge-base/{document_id}/feedback
POST /api/v1/knowledge-base/{document_id}/feedback
POST /api/v1/knowledge-base/{document_id}/favorite
```

**Real-time Features:**
- View count updates live
- New comments appear instantly
- Usage stats refresh automatically

**Testing Requirements:**
- ✅ All sections render correctly
- ✅ Markdown/code highlighting works
- ✅ Related documents relevant
- ✅ Version history accurate
- ✅ Feedback submits successfully
- ✅ Analytics track correctly
- ✅ Mobile responsive

---

### 7.2.3: Contribute Knowledge Interface

**User Story:**  
*As a user, I want to contribute knowledge so that I can share learnings with the AI agents.*

**Contribution Flow:**

**1. Create Document Modal/Page:**
- Triggered by: "➕ Add Knowledge" button
- Full-page form or modal (based on content length)

**Form Sections:**

**Basic Information:**
```
Title *
[________________________________________]
Min 10 characters, clear and descriptive

Category *
[Technical Standards ▼]

Subcategory
[Security ▼]

Document Type *
○ Solution
○ Standard
○ Template
○ Best Practice
○ Lesson Learned
○ Decision
```

**Content:**
```
Summary (Optional)
[________________________________________]
AI can generate this if left blank

Content *
┌─────────────────────────────────────┐
│ [B] [I] [Code] [Link] [Image]       │
│                                     │
│ [Markdown Editor]                   │
│                                     │
│ Supports markdown, code blocks,     │
│ and images. Drag & drop supported.  │
│                                     │
│ [Preview] tab available             │
└─────────────────────────────────────┘

Character count: 0 / 10,000
Minimum 50 characters required
```

**Classification:**
```
Tags
[________] [Add Tag]
Selected: python, authentication, security
Suggestions: jwt, api, backend

Keywords (Optional)
[________________________________________]
AI can extract these automatically

Access Level *
○ Public (Anyone can view)
○ Department (Engineering only)
○ Executive (Executive team only)
○ Confidential (Specific agents only)

If Confidential, select agents:
[☐ CEO Agent]
[☐ CTO Agent]
[☐ Backend Engineer]
```

**Context:**
```
Related To (Optional)

Projects:
[Search projects...] [➕]
• E-commerce Platform

Tasks:
[Search tasks...] [➕]
• Implement authentication

This helps agents understand when to use this knowledge
```

**Actions:**
```
[⚙️ AI Assist]  [👁️ Preview]  [💾 Save Draft]

[Cancel]          [Create Document]
```

**AI Assist Features:**
- Generate summary from content
- Extract keywords automatically
- Suggest categories
- Suggest related documents
- Improve writing clarity
- Check for duplicates

**2. Edit Document:**
- Same form as create
- Shows current version
- "What changed?" field (required)
- Creates new version on save
- Option to mark as "Major update"

**3. Validation Queue (For validated documents):**
```
📋 Pending Validation

You have 3 documents awaiting validation:

┌─────────────────────────────────────────────┐
│ React State Management Patterns             │
│ Submitted: 2 days ago                       │
│ Status: Awaiting CTO review                 │
│ [View] [Edit] [Withdraw]                    │
└─────────────────────────────────────────────┘
```

**Backend API:**
```
POST /api/v1/knowledge-base
PATCH /api/v1/knowledge-base/{document_id}
POST /api/v1/knowledge-base/{document_id}/validate
POST /api/v1/knowledge-base/check-duplicate
```

**Validation Rules:**
- Title: 10-500 characters, unique
- Content: Min 50 characters
- Category: Required, must exist
- Tags: Max 10 tags
- Check for near-duplicates using embeddings
- Warn if very similar document exists

**Testing Requirements:**
- ✅ Form validation works
- ✅ AI assist generates helpful content
- ✅ Duplicate detection works
- ✅ Draft saving works
- ✅ Access controls enforced
- ✅ Version created on edit
- ✅ Preview renders correctly

---

## Sub-Feature 7.3: Knowledge Base Analytics

### 7.3.1: Document Analytics Dashboard

**User Story:**  
*As an admin, I want to see analytics on knowledge base usage so that I can understand what's valuable and what needs improvement.*

**Analytics Dashboard (`/knowledge-base/analytics`):**

**1. Overview Stats:**
```
┌─────────────┬─────────────┬─────────────┬─────────────┐
│ Total Docs  │ Total Views │ Avg Effect. │ Active Users│
│    234      │   12,456    │     87%     │     45      │
│ ↑ 12 (5%)   │ ↑ 2,345     │ ↑ 3%        │ ↑ 8         │
└─────────────┴─────────────┴─────────────┴─────────────┘
```

**2. Effectiveness Trends:**
```
Effectiveness Score Over Time
┌────────────────────────────────────────┐
│ 100%                              ______|
│  90%                        _____/      │
│  80%                  _____/            │
│  70%            _____/                  │
│  60%     _____/                         │
│  50% ___/                               │
│     Jan  Feb  Mar  Apr  May  Jun  Jul  │
└────────────────────────────────────────┘
```

**3. Most Viewed Documents:**
```
Rank  Document                          Views  Effectiveness
1.    JWT Authentication Guide          1,234      95%
2.    React Component Patterns            856      88%
3.    Database Optimization Tips          745      92%
4.    API Error Handling                  678      85%
5.    Docker Best Practices               543      90%
```

**4. Most Effective Documents:**
```
Document                          Effectiveness  Uses  Success Rate
Database Index Optimization              98%     45      98%
Python Type Hints Guide                  97%     56      96%
JWT Auth Implementation                  95%     78      92%
```

**5. Category Distribution:**
```
Documents by Category

Technical Standards     ████████░░░░  45 (19%)
Solutions Library       ███████████░  78 (33%)
Decision History        ████████░░░░  56 (24%)
Best Practices          ████░░░░░░░░  41 (17%)
Templates              ███░░░░░░░░░  23 (10%)
```

**6. Agent Usage Patterns:**
```
Knowledge Usage by Agent

Backend Engineer    ████████████  245 uses
Frontend Engineer   ██████████    189 uses
CTO Agent          ████████      156 uses
Designer           █████         98 uses
PM Agent           ███           67 uses
```

**7. Search Analytics:**
```
Top Search Queries (Last 30 Days)

1. "authentication"         234 searches
2. "api design"            156 searches
3. "react patterns"        145 searches
4. "database performance"  123 searches
5. "error handling"        108 searches

No Results Searches (Need Content):
1. "websocket implementation"  23 searches
2. "mobile push notifications" 18 searches
3. "payment gateway"          15 searches
```

**8. Contribution Leaderboard:**
```
Top Contributors (Last 30 Days)

Agent/User              Documents  Total Views  Avg Effectiveness
Backend Agent                 12       3,456            92%
CTO Agent                      8       2,345            95%
John Doe (User)               5       1,234            88%
```

**9. Document Lifecycle:**
```
Document Age vs Effectiveness

New (0-30 days)       ████████░░   85%
Recent (31-90 days)   █████████░   90%
Mature (91-180 days)  ██████████   93%
Old (180+ days)       █████████░   88%

Note: Mature documents most effective
```

**10. Usage Heatmap:**
```
Knowledge Usage by Day & Hour

Hour    Mon  Tue  Wed  Thu  Fri  Sat  Sun
00-06   ░░   ░░   ░░   ░░   ░░   ░░   ░░
06-12   ██   ██   ███  ██   ██   ░░   ░░
12-18   ███  ███  ███  ███  ███  ██   ░░
18-24   ██   ██   ██   ██   ██   ██   ░░

Peak usage: Weekdays 12-18:00
```

**Backend APIs:**
```
GET /api/v1/knowledge-base/analytics/overview
GET /api/v1/knowledge-base/analytics/effectiveness-trend
GET /api/v1/knowledge-base/analytics/most-viewed
GET /api/v1/knowledge-base/analytics/search-queries
GET /api/v1/knowledge-base/analytics/contributors
```

**Export Options:**
- Export as CSV
- Export as PDF report
- Schedule weekly/monthly email reports

**Testing Requirements:**
- ✅ All metrics calculate correctly
- ✅ Charts render properly
- ✅ Date range filters work
- ✅ Export functions work
- ✅ Performance acceptable with large datasets

---

### 7.3.2: Document Health Monitoring

**User Story:**  
*As a knowledge curator, I want to identify outdated or ineffective documents so that I can improve the knowledge base quality.*

**Health Monitoring Dashboard:**

**1. Documents Needing Attention:**
```
🚨 Attention Required

Low Effectiveness (< 70%)
┌─────────────────────────────────────────┐
│ React Redux Setup Guide        65%      │
│ 12 uses, 5 negative feedback            │
│ [Review] [Update] [Deprecate]           │
└─────────────────────────────────────────┘

Outdated (Not updated in 6+ months)
┌─────────────────────────────────────────┐
│ Angular Component Guide                 │
│ Last updated: 8 months ago              │
│ [Update] [Mark as Current] [Archive]    │
└─────────────────────────────────────────┘

High Views, Low Use Rate
┌─────────────────────────────────────────┐
│ Docker Deployment Guide                 │
│ 234 views but only 12 uses              │
│ Possible Issues: Unclear or incomplete  │
│ [Review Content] [Add Examples]         │
└─────────────────────────────────────────┘
```

**2. Duplicate Detection:**
```
⚠️ Possible Duplicates

These documents may cover similar topics:

"JWT Authentication Guide" (95% effective)
    vs
"Token-Based Auth Implementation" (78% effective)

Similarity: 85%
Recommendation: Merge or clarify differences

[Compare] [Merge] [Mark as Different]
```

**3. Content Gaps:**
```
📊 Content Gap Analysis

Missing Topics (Based on Failed Searches):
1. WebSocket Implementation (23 searches, 0 docs)
2. Mobile Push Notifications (18 searches, 0 docs)
3. Payment Gateway Integration (15 searches, 0 docs)

[Create Document] [Request from Agent]
```

**4. Validation Status:**
```
✅ Validation Queue

Pending Validation: 5 documents
Recently Validated: 12 documents
Validation Rate: 89%

[View Queue] [Validation Settings]
```

---
