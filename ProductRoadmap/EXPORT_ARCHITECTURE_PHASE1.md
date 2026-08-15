# Phase 1 Export System Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Frontend (React/Next.js)                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────┐    ┌─────────────────┐   ┌──────────────────┐│
│  │  Export Dialog   │    │ Export Progress │   │  useExport Hook  ││
│  │  Component       │───→│  Component      │───│  (State Mgmt)    ││
│  │  (Export UI)     │    │  (Progress)     │   │  (API Calls)     ││
│  └──────────────────┘    └─────────────────┘   └──────────────────┘│
│           │                       │                       │          │
│           │  Export Type          │  Job Status Poll      │ Download │
│           │  Export Format        │  Cancel Request       │ Request  │
│           │  Options              │  Download Link        │          │
│           └───────────────────────┴───────────────────────┴──────────┘
│                                    │
│                                    ▼ (HTTP/Async)
├─────────────────────────────────────────────────────────────────────┤
│                         API Layer (FastAPI)                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │              Export API Routes (exports.py)                   │ │
│  │                                                                │ │
│  │  • POST /projects/{id}/export/pdf        [Create Job]        │ │
│  │  • POST /projects/{id}/export/markdown   [Create Job]        │ │
│  │  • GET  /exports/{id}/status             [Get Status]        │ │
│  │  • GET  /exports/{id}/download           [Download File]     │ │
│  │  • POST /exports/{id}/cancel             [Cancel Job]        │ │
│  │  • GET  /projects/{id}/exports           [List Exports]      │ │
│  │  • POST /exports/cleanup                 [Admin Only]        │ │
│  │                                                                │ │
│  │  Pydantic Models: ExportOptions, ExportJobResponse           │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                    │
│                    (Immediate Response + Background Task)
│                                    ▼
├─────────────────────────────────────────────────────────────────────┤
│                    Export Service Layer                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │         ExportService (Orchestrator)                        │   │
│  │                                                             │   │
│  │  • create_export_job()      [Job creation]                 │   │
│  │  • process_export_job()     [Main processing loop]         │   │
│  │  • _collect_export_data()   [Delegate to data service]    │   │
│  │  • _generate_export_file()  [Delegate to generators]      │   │
│  │  • _check_cache()           [Intelligent caching]          │   │
│  │  • _cache_export()          [Save to cache]                │   │
│  │  • cleanup_old_exports()    [Maintenance]                  │   │
│  │  • get_export_file_stream() [Download streaming]           │   │
│  │                                                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│           │                │                │                       │
│           ▼                ▼                ▼                       │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                │
│  │   Data       │ │   PDF        │ │   Markdown   │                │
│  │ Collection  │ │ Generation   │ │ Generation   │                │
│  │   Service   │ │   Service    │ │   Service    │                │
│  └──────────────┘ └──────────────┘ └──────────────┘                │
│           │                │                │                       │
├───────────┴────────────────┼────────────────┴───────────────────────┤
│                            ▼                                        │
│  ExportDataService        PDF Service        Markdown Service      │
│  ┌──────────────────┐  ┌─────────────────┐  ┌──────────────────┐  │
│  │ Data Collection  │  │ Playwright      │  │ YAML Frontmatter │  │
│  │                  │  │ HTML Templates  │  │ Table Formatting │  │
│  │ • collect_*()    │  │ Jinja2 Render   │  │ Code Blocks      │  │
│  │ • _get_*()       │  │ Pygments Syntax │  │ Clean Typography │  │
│  │ 40+ methods      │  │ Professional    │  │ GitHub Friendly  │  │
│  │                  │  │ Styling         │  │                  │  │
│  └──────────────────┘  └─────────────────┘  └──────────────────┘  │
│           │                │                │                      │
│           └────────────────┼────────────────┘                      │
│                            ▼                                       │
└────────────────────────────────────────────────────────────────────┘
                             │
                             ▼ (Database Query)
        ┌────────────────────────────────────────────┐
        │     PostgreSQL Database                   │
        │                                            │
        │  ┌──────────────────────────────────────┐ │
        │  │ Export Tables                        │ │
        │  │                                      │ │
        │  │  • export_jobs        [Main table]   │ │
        │  │  • export_templates   [Templates]    │ │
        │  │  • export_cache       [Caching]      │ │
        │  │  • deployments        [Phase 3]      │ │
        │  │  • platform_connections [Phase 3]    │ │
        │  │  • deployment_logs    [Phase 3]      │ │
        │  └──────────────────────────────────────┘ │
        │                                            │
        │  ┌──────────────────────────────────────┐ │
        │  │ Existing Retinue Tables              │ │
        │  │                                      │ │
        │  │  • projects, tasks, agents           │ │
        │  │  • messages, decisions               │ │
        │  │  • escalations, audit_logs           │ │
        │  │  • event tracking tables             │ │
        │  └──────────────────────────────────────┘ │
        │                                            │
        └────────────────────────────────────────────┘
```

## Data Flow Diagram

```
User initiates export:
  │
  ▼
Frontend: ExportDialog opens
  │
  ├─ User selects: Type (Summary/Full/Tasks/etc.)
  ├─ User selects: Format (PDF/Markdown)
  ├─ User selects: Options (code, images, conversations)
  │
  ▼
ExportDialog component calls: startExport()
  │
  ▼ (HTTP POST /api/v1/projects/{id}/export/{format})
  │
  ├─ Creates ExportJob in database
  ├─ Returns job_id immediately (non-blocking)
  │
  ▼
Frontend: Switches to ExportProgress component
  │
  ├─ Starts polling job status every 1 second
  │ (GET /api/v1/exports/{job_id}/status)
  │
  ▼
Backend: Async background processing
  │
  ├─ Status: PENDING → GATHERING_DATA (10%)
  │  ├─ Collects project, tasks, agents, etc.
  │  └─ Queries database with optimized queries
  │
  ├─ Status: RENDERING (30%)
  │  ├─ Renders Jinja2 template with data
  │  └─ Prepares output format
  │
  ├─ Status: GENERATING (50%)
  │  ├─ [If PDF]: HTML → PDF via Playwright
  │  ├─ [If Markdown]: Renders markdown with YAML frontmatter
  │  ├─ Syntax highlighting for code
  │  └─ Generates tables and formatting
  │
  ├─ Checks cache (content hash)
  │  ├─ If cached & valid: Return cached file
  │  └─ If not: Continue generation
  │
  ├─ Status: COMPLETED (100%)
  │  ├─ Saves file to temp directory
  │  ├─ Updates database with file info
  │  └─ Caches with 1-hour TTL
  │
  ▼
Frontend: Receives status update
  │
  ├─ Progress bar shows 100%
  ├─ Download button becomes active
  ├─ Shows file size and metadata
  │
  ▼
User clicks Download
  │
  ▼ (HTTP GET /api/v1/exports/{job_id}/download)
  │
  ├─ Backend verifies job status
  ├─ Streams file chunks (8KB each)
  ├─ Browser receives and saves file
  │
  ▼
File downloaded successfully ✅
```

## Component Interaction Diagram

```
┌──────────────────────────────────────────────────────────┐
│                    Project Page                          │
│                                                           │
│  ┌────────────────────────────────────────────────────┐ │
│  │ [Export Button] ◄────────────────────────────────┐ │ │
│  └────────────────────────────────────────────────────┘ │ │
│                    │                                      │ │
│                    ▼ onClick                              │ │
│  ┌────────────────────────────────────────────────────┐ │ │
│  │ ┌──────────────────────────────────────────────┐  │ │ │
│  │ │  ExportDialog                                │  │ │ │
│  │ │  • Select export type (radio buttons)        │  │ │ │
│  │ │  • Select format (PDF/Markdown)              │  │ │ │
│  │ │  • Toggle options (checkboxes)               │  │ │ │
│  │ │  [Export] button                             │  │ │ │
│  │ │                                              │  │ │ │
│  │ │  onExportStart(jobId) ──────────────────┐  │  │ │ │
│  │ └──────────────────────────────────────────────┘  │  │ │
│  └────────────────────────────────────────────────────┘  │ │
│                    │                                      │ │
│                    ▼ (Close & Show Progress)              │ │
│  ┌────────────────────────────────────────────────────┐ │ │
│  │ ┌──────────────────────────────────────────────┐  │ │ │
│  │ │  ExportProgress                              │  │ │ │
│  │ │  • Progress bar (%)                          │  │ │ │
│  │ │  • Current step display                      │  │ │ │
│  │ │  • Status icons (gathering, rendering, etc.) │  │ │ │
│  │ │  • [Download] button (when complete)         │  │ │ │
│  │ │                                              │  │ │ │
│  │ │  useExport hook provides:                    │  │ │ │
│  │ │  • getJobStatus() - polls every 1s          │  │ │ │
│  │ │  • downloadExport() - downloads file        │  │ │ │
│  │ │  • cancelExport() - cancels job             │  │ │ │
│  │ └──────────────────────────────────────────────┘  │  │ │
│  └────────────────────────────────────────────────────┘  │ │
│                                                           │ │
└──────────────────────────────────────────────────────────┘ │
                                                               │
        Uses: useExport hook for state management ────────────┘
```

## State Management Flow

```
Component:  ExportDialog          ExportProgress          useExport Hook
┌──────────────┐             ┌──────────────┐         ┌──────────────┐
│ Local State: │             │ Local State: │         │ Hook State:  │
│ • exportType │             │ • jobId      │         │ • job        │
│ • exportFmt  │             │ • isOpen     │         │ • loading    │
│ • options    │             │ • error      │         │ • error      │
│ • isExporting│             │              │         │              │
└──────────────┘             └──────────────┘         └──────────────┘
       │                            │                        │
       │ User selects              │                        │
       │ options & clicks          │                        │
       │ "Export"                  │                        │
       ▼                            │                        │
    Calls:                          │                        │
    startExport()                   │                        │
       │                            │                        │
       └────────────────────────────┼────────────────────────┤
                                    │                        │
                         API Call: POST /export/pdf
                                    │
                         Returns: { job_id: "..." }
                                    │
       ┌────────────────────────────┴────────────────────────┤
       │                                                      │
       ▼                                                      ▼
  onExportStart(jobId)                          setJob(jobData)
  setCurrentJobId(jobId)                        setLoading(false)
  setExportOpen(false)
  setProgressOpen(true)
       │                                                      │
       └────────────────────────┬─────────────────────────────┘
                                │
                    useEffect() triggered
                    (polls every 1s)
                    getJobStatus(jobId)
                                │
                    API Call: GET /exports/{id}/status
                                │
                    Returns: ExportJob with status & progress
                                │
                                ▼
                    setJob(jobData)
                                │
        ┌───────────┬───────────┼───────────┬───────────┐
        │           │           │           │           │
    PENDING   GATHERING   RENDERING    GENERATING   COMPLETED
        │           │           │           │           │
        └───────────┴───────────┴───────────┴───────────┘
                                │
                    When status === COMPLETED
                    Enable [Download] button
                                │
                    User clicks Download
                                │
                    Calls: downloadExport(jobId)
                                │
                    API Call: GET /exports/{id}/download
                                │
                    Returns: File blob
                                │
                    Triggers browser download ✅
```

## Service Dependencies

```
ExportService
├── Depends On:
│   ├── ExportDataService
│   │   └── Database Session
│   ├── PDFGenerationService
│   │   ├── Jinja2 Environment
│   │   ├── Playwright Browser
│   │   └── Pygments (syntax highlighting)
│   ├── MarkdownGenerationService
│   │   ├── PyYAML
│   │   └── Python built-ins
│   └── Database Session
│       └── AsyncSession

ExportDataService
├── Depends On:
│   ├── Database Models
│   │   ├── Project
│   │   ├── Task
│   │   ├── Agent
│   │   ├── Message
│   │   ├── Decision
│   │   ├── Escalation
│   │   └── ...
│   ├── Event Models
│   │   ├── AgentActivity
│   │   ├── AgentMetric
│   │   ├── LLMInteraction
│   │   └── ...
│   └── Escalation Models
│       ├── AdvancedEscalation
│       └── EscalationAnalytics

PDFGenerationService
├── Depends On:
│   ├── Jinja2 (templates)
│   ├── Playwright (chromium browser)
│   ├── Pygments (code highlighting)
│   └── File system (for output)

MarkdownGenerationService
├── Depends On:
│   ├── PyYAML (frontmatter)
│   └── File system (for output)
```

## Caching Strategy

```
┌─────────────────────────────────────────────────┐
│      User requests export (same config)         │
└──────────────────────────┬──────────────────────┘
                           │
                           ▼
            ExportService.check_cache()
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
    Cached &         Cached but        No cache
    Valid (TTL)      Expired           found
        │                  │                  │
        ▼                  ▼                  ▼
   Return             Delete            Process
   Cached File        from cache         & generate
   <500ms             & process          <40s
        │                  │                  │
        └──────────────────┴──────────────────┘
                           │
                           ▼
                Generate download link
                   & return to user
```

## Error Handling Flow

```
Export Processing
       │
       ├─ Validation Error
       │  └─ Response: 400 Bad Request
       │
       ├─ Database Error
       │  └─ Log + Response: 500 Internal Server Error
       │
       ├─ PDF Generation Timeout
       │  └─ Fail gracefully + Response: 500
       │
       ├─ File System Error
       │  └─ Cleanup + Response: 500
       │
       ├─ Playwright Browser Error
       │  └─ Retry logic + Response: 500
       │
       ├─ Memory Exceeded
       │  └─ Abort + Response: 500
       │
       ├─ Cache Writing Error
       │  └─ Continue without cache + Response: 200
       │
       └─ Success
          └─ Return: 200 with job_id

Frontend Error Handling
       │
       ├─ API Error (4xx/5xx)
       │  └─ Display error message
       │
       ├─ Network Error
       │  └─ Show retry option
       │
       ├─ Export Failed (status=failed)
       │  └─ Show error details + retry button
       │
       ├─ Download Failed
       │  └─ Show error + retry button
       │
       └─ Success
          └─ Show file size + metadata
```

## Performance Optimization Points

```
Frontend Optimization:
├─ Polling strategy (vs WebSocket) - simpler, more reliable
├─ 1-second poll interval - balances UX and server load
├─ Component memoization - prevents unnecessary re-renders
└─ Async/await - non-blocking API calls

Backend Optimization:
├─ Database indexes on common query columns
├─ Optimized SQLAlchemy queries with projections
├─ Content-based caching (SHA256 hashing)
├─ 1-hour cache TTL - balances freshness and speed
├─ Async background processing - non-blocking HTTP
├─ Streaming file downloads - memory efficient
├─ Lazy loading for large datasets
├─ Batch processing for file operations
└─ Connection pooling - efficient database access

File Storage Optimization:
├─ Temporary directory (/tmp) for local files
├─ Automatic 24-hour cleanup of old files
├─ Optional S3 integration for production
├─ Signed URLs for secure downloads
└─ File size limits (500MB default)
```

## Security Considerations

```
Authentication & Authorization:
├─ API endpoints require authentication (FastAPI dependency)
├─ User can only access their project exports
├─ Signed download URLs with 15-minute expiration
└─ No sensitive data in exports (secrets replaced with placeholders)

Data Protection:
├─ OAuth tokens encrypted at rest (Phase 3)
├─ HTTPS required for all API calls
├─ Rate limiting on export endpoints
├─ File size validation before processing
└─ Content validation and sanitization

Infrastructure:
├─ Temporary files auto-deleted after 24 hours
├─ No sensitive data in logs
├─ Audit trail for all exports
└─ Error details not exposed to frontend
```

---

This architecture provides:
- ✅ Clear separation of concerns
- ✅ Scalable to Phase 2 & 3
- ✅ Real-time user feedback
- ✅ Intelligent caching
- ✅ Comprehensive error handling
- ✅ Production-ready performance
