# Retinue/Retinue Evolution: Software → Full Business Operations
## Comprehensive Change Analysis & Implementation Plan

**Date**: November 22, 2025  
**Purpose**: Transform Retinue from a 7-agent software development platform to a full multi-agent business operations system

---

## Executive Summary

### Current System (v1.0 - Software Focus)
- **Fixed Configuration**: 7 agents (CEO, CTO, PM, HR, Backend, Frontend, Designer)
- **Single Use Case**: Autonomous software development
- **Output**: Code files (Python, React, TypeScript)
- **Workflow**: Linear software development lifecycle

### Target System (v2.0 - Business Operations)
- **Flexible Configuration**: User selects agents based on business need
- **Multiple Use Cases**: Any business function (Marketing, Finance, Sales, HR, Operations, Legal)
- **Diverse Outputs**: Reports, presentations, code, research, proposals, strategies, analysis
- **Workflow**: Dynamic business problem-solving with appropriate agent teams

---

## 1. CORE ARCHITECTURAL CHANGES

### 1.1 Database Schema Updates

#### New Tables Required

```sql
-- Agent Categories/Departments
CREATE TABLE departments (
    department_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    color VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE
);

-- Department categories
INSERT INTO departments VALUES
    ('executive', 'Executive Leadership', 'C-suite strategic decision making', 'briefcase', '#8B4513', TRUE),
    ('engineering', 'Engineering', 'Software development and technical solutions', 'code', '#2563EB', TRUE),
    ('marketing', 'Marketing & Growth', 'Marketing campaigns and growth strategies', 'megaphone', '#DC2626', TRUE),
    ('sales', 'Sales & Business Development', 'Revenue generation and client acquisition', 'dollar-sign', '#059669', TRUE),
    ('finance', 'Finance & Accounting', 'Financial analysis and planning', 'chart-line', '#7C3AED', TRUE),
    ('hr', 'Human Resources', 'People operations and talent management', 'users', '#EA580C', TRUE),
    ('operations', 'Operations', 'Business operations and efficiency', 'settings', '#64748B', TRUE),
    ('legal', 'Legal & Compliance', 'Legal advice and compliance', 'scale', '#6B7280', TRUE),
    ('research', 'Research & Analytics', 'Data analysis and market research', 'search', '#14B8A6', TRUE);

-- Expanded Agents Table
ALTER TABLE agents ADD COLUMN IF NOT EXISTS output_types JSONB DEFAULT '["text"]';
ALTER TABLE agents ADD COLUMN IF NOT EXISTS specializations JSONB DEFAULT '[]';
ALTER TABLE agents ADD COLUMN IF NOT EXISTS required_for_types JSONB DEFAULT '[]';
ALTER TABLE agents ADD COLUMN IF NOT EXISTS cost_per_hour DECIMAL(10,2) DEFAULT 0;

-- Project Configuration (User Agent Selection)
CREATE TABLE project_agent_assignments (
    assignment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(project_id),
    agent_id VARCHAR(100) NOT NULL REFERENCES agents(agent_id),
    role_in_project VARCHAR(100),
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(project_id, agent_id)
);

-- Deliverable Types
CREATE TABLE deliverable_types (
    type_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    typical_agents JSONB, -- List of agent_ids typically used
    output_format VARCHAR(50), -- 'pdf', 'code', 'pptx', 'docx', 'xlsx', 'json'
    template_path VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE
);

INSERT INTO deliverable_types VALUES
    ('software_mvp', 'Software MVP', 'Full stack application with code', 
     '["ceo_001", "cto_001", "pm_001", "backend_001", "frontend_001", "designer_001"]', 
     'code', '/templates/software/', TRUE),
    ('marketing_campaign', 'Marketing Campaign', 'Complete marketing campaign with assets',
     '["ceo_001", "cmo_001", "content_001", "designer_001", "social_media_001"]',
     'pdf', '/templates/marketing/', TRUE),
    ('financial_analysis', 'Financial Analysis Report', 'Financial projections and analysis',
     '["cfo_001", "financial_analyst_001"]',
     'xlsx', '/templates/finance/', TRUE),
    ('business_proposal', 'Business Proposal', 'Professional business proposal',
     '["ceo_001", "sales_001", "designer_001"]',
     'pdf', '/templates/proposals/', TRUE),
    ('hr_policy', 'HR Policy Document', 'Company policy documentation',
     '["chro_001", "hr_specialist_001", "legal_001"]',
     'docx', '/templates/hr/', TRUE),
    ('market_research', 'Market Research Report', 'Comprehensive market analysis',
     '["research_001", "data_analyst_001"]',
     'pdf', '/templates/research/', TRUE);

-- Project Types (replaces implicit "software project" assumption)
ALTER TABLE projects ADD COLUMN IF NOT EXISTS project_type VARCHAR(50) DEFAULT 'custom';
ALTER TABLE projects ADD COLUMN IF NOT EXISTS deliverable_type VARCHAR(50) REFERENCES deliverable_types(type_id);
ALTER TABLE projects ADD COLUMN IF NOT EXISTS selected_agents JSONB DEFAULT '[]';

-- Task Output Formats (beyond just code)
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS output_format VARCHAR(50) DEFAULT 'text';
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS output_metadata JSONB DEFAULT '{}';
```

---

### 1.2 Agent System Redesign

#### Current Agent Structure
```python
# OLD: Fixed 7 agents with hardcoded roles
AGENTS = {
    'ceo_001': CEOAgent,
    'cto_001': CTOAgent,
    'pm_001': PMAgent,
    'hr_001': HRAgent,
    'backend_001': BackendEngineerAgent,
    'frontend_001': FrontendEngineerAgent,
    'designer_001': DesignerAgent
}
```

#### New Agent Structure
```python
# NEW: Dynamic agent registry by department
class AgentRegistry:
    """Central registry for all available agents"""
    
    AGENT_CATALOG = {
        # Executive
        'ceo_001': {
            'class': CEOAgent,
            'name': 'CEO Agent',
            'department': 'executive',
            'role': 'Chief Executive Officer',
            'output_types': ['decision', 'strategy', 'approval'],
            'specializations': ['strategic_planning', 'decision_making', 'leadership'],
            'cost_per_hour': 0,
            'always_active': True  # CEO monitors all projects
        },
        
        # Engineering
        'cto_001': {
            'class': CTOAgent,
            'name': 'CTO Agent',
            'department': 'engineering',
            'role': 'Chief Technology Officer',
            'output_types': ['technical_guidance', 'code_review', 'architecture'],
            'specializations': ['system_architecture', 'tech_leadership', 'code_review'],
            'required_for_types': ['software_mvp', 'api_development'],
            'cost_per_hour': 0
        },
        'backend_001': {
            'class': BackendEngineerAgent,
            'name': 'Backend Engineer',
            'department': 'engineering',
            'role': 'Senior Backend Engineer',
            'output_types': ['code', 'api', 'database'],
            'specializations': ['python', 'fastapi', 'postgresql', 'rest_api'],
            'required_for_types': ['software_mvp', 'api_development'],
            'cost_per_hour': 0
        },
        'frontend_001': {
            'class': FrontendEngineerAgent,
            'name': 'Frontend Engineer',
            'department': 'engineering',
            'role': 'Senior Frontend Engineer',
            'output_types': ['code', 'ui', 'components'],
            'specializations': ['react', 'nextjs', 'typescript', 'tailwindcss'],
            'required_for_types': ['software_mvp', 'web_application'],
            'cost_per_hour': 0
        },
        'designer_001': {
            'class': DesignerAgent,
            'name': 'Product Designer',
            'department': 'engineering',
            'role': 'Senior Product Designer',
            'output_types': ['design_specs', 'mockups', 'style_guide'],
            'specializations': ['ui_ux', 'visual_design', 'user_research'],
            'required_for_types': ['software_mvp', 'marketing_campaign'],
            'cost_per_hour': 0
        },
        
        # Marketing
        'cmo_001': {
            'class': CMOAgent,
            'name': 'CMO Agent',
            'department': 'marketing',
            'role': 'Chief Marketing Officer',
            'output_types': ['strategy', 'campaign_plan', 'brand_guidelines'],
            'specializations': ['marketing_strategy', 'brand_management', 'growth'],
            'required_for_types': ['marketing_campaign', 'brand_strategy'],
            'cost_per_hour': 0
        },
        'content_001': {
            'class': ContentMarketingAgent,
            'name': 'Content Marketing Specialist',
            'department': 'marketing',
            'role': 'Content Marketing Manager',
            'output_types': ['content', 'copy', 'blog_posts'],
            'specializations': ['copywriting', 'seo', 'content_strategy'],
            'required_for_types': ['marketing_campaign', 'content_strategy'],
            'cost_per_hour': 0
        },
        'social_media_001': {
            'class': SocialMediaAgent,
            'name': 'Social Media Manager',
            'department': 'marketing',
            'role': 'Social Media Specialist',
            'output_types': ['social_posts', 'campaign', 'analytics'],
            'specializations': ['social_media', 'community_management', 'paid_ads'],
            'required_for_types': ['marketing_campaign'],
            'cost_per_hour': 0
        },
        
        # Finance
        'cfo_001': {
            'class': CFOAgent,
            'name': 'CFO Agent',
            'department': 'finance',
            'role': 'Chief Financial Officer',
            'output_types': ['financial_report', 'budget', 'forecast'],
            'specializations': ['financial_planning', 'budgeting', 'forecasting'],
            'required_for_types': ['financial_analysis', 'budget_planning'],
            'cost_per_hour': 0
        },
        'financial_analyst_001': {
            'class': FinancialAnalystAgent,
            'name': 'Financial Analyst',
            'department': 'finance',
            'role': 'Senior Financial Analyst',
            'output_types': ['analysis', 'models', 'reports'],
            'specializations': ['financial_modeling', 'data_analysis', 'excel'],
            'required_for_types': ['financial_analysis', 'investment_analysis'],
            'cost_per_hour': 0
        },
        
        # Sales
        'sales_manager_001': {
            'class': SalesManagerAgent,
            'name': 'Sales Manager',
            'department': 'sales',
            'role': 'Sales Team Lead',
            'output_types': ['sales_strategy', 'pitch_deck', 'proposal'],
            'specializations': ['b2b_sales', 'enterprise_sales', 'negotiation'],
            'required_for_types': ['business_proposal', 'sales_strategy'],
            'cost_per_hour': 0
        },
        
        # HR
        'chro_001': {
            'class': CHROAgent,
            'name': 'CHRO Agent',
            'department': 'hr',
            'role': 'Chief Human Resources Officer',
            'output_types': ['hr_policy', 'strategy', 'guidelines'],
            'specializations': ['hr_strategy', 'talent_management', 'culture'],
            'required_for_types': ['hr_policy', 'talent_strategy'],
            'cost_per_hour': 0
        },
        'hr_specialist_001': {
            'class': HRSpecialistAgent,
            'name': 'HR Specialist',
            'department': 'hr',
            'role': 'HR Operations Specialist',
            'output_types': ['documentation', 'processes', 'templates'],
            'specializations': ['hr_operations', 'compliance', 'employee_relations'],
            'required_for_types': ['hr_policy'],
            'cost_per_hour': 0
        },
        'hr_monitor_001': {  # Formerly just "HR Agent"
            'class': HRMonitorAgent,
            'name': 'HR Monitor',
            'department': 'hr',
            'role': 'Agent Health Monitor',
            'output_types': ['health_report', 'intervention', 'escalation'],
            'specializations': ['agent_monitoring', 'system_health', 'escalation'],
            'always_active': True,  # Always monitors all agents
            'cost_per_hour': 0
        },
        
        # Operations
        'coo_001': {
            'class': COOAgent,
            'name': 'COO Agent',
            'department': 'operations',
            'role': 'Chief Operating Officer',
            'output_types': ['operations_plan', 'process', 'optimization'],
            'specializations': ['operations', 'process_improvement', 'efficiency'],
            'required_for_types': ['operations_optimization'],
            'cost_per_hour': 0
        },
        
        # Legal
        'legal_001': {
            'class': LegalAgent,
            'name': 'Legal Counsel',
            'department': 'legal',
            'role': 'Corporate Legal Advisor',
            'output_types': ['legal_review', 'contracts', 'compliance'],
            'specializations': ['corporate_law', 'contracts', 'compliance'],
            'required_for_types': ['hr_policy', 'contracts'],
            'cost_per_hour': 0
        },
        
        # Research & Analytics
        'research_001': {
            'class': ResearchAgent,
            'name': 'Research Analyst',
            'department': 'research',
            'role': 'Market Research Specialist',
            'output_types': ['research_report', 'analysis', 'insights'],
            'specializations': ['market_research', 'competitive_analysis', 'user_research'],
            'required_for_types': ['market_research'],
            'cost_per_hour': 0
        },
        'data_analyst_001': {
            'class': DataAnalystAgent,
            'name': 'Data Analyst',
            'department': 'research',
            'role': 'Senior Data Analyst',
            'output_types': ['data_analysis', 'visualizations', 'dashboards'],
            'specializations': ['data_analysis', 'python', 'sql', 'visualization'],
            'required_for_types': ['market_research', 'financial_analysis'],
            'cost_per_hour': 0
        },
        
        # Project Management (cross-functional)
        'pm_001': {
            'class': PMAgent,
            'name': 'Project Manager',
            'department': 'operations',
            'role': 'Senior Project Manager',
            'output_types': ['project_plan', 'tasks', 'timeline'],
            'specializations': ['project_management', 'agile', 'coordination'],
            'always_active': True,  # PM needed for all projects
            'cost_per_hour': 0
        }
    }
    
    @classmethod
    def get_agents_by_department(cls, department: str) -> List[Dict]:
        """Get all agents in a department"""
        return [
            {'agent_id': agent_id, **config}
            for agent_id, config in cls.AGENT_CATALOG.items()
            if config['department'] == department
        ]
    
    @classmethod
    def get_required_agents(cls, deliverable_type: str) -> List[str]:
        """Get agents required for a deliverable type"""
        required = ['ceo_001', 'pm_001', 'hr_monitor_001']  # Always active
        
        for agent_id, config in cls.AGENT_CATALOG.items():
            if deliverable_type in config.get('required_for_types', []):
                required.append(agent_id)
        
        return list(set(required))
    
    @classmethod
    def get_suggested_agents(cls, deliverable_type: str) -> List[str]:
        """Get suggested additional agents for a deliverable type"""
        # Get typical agents from deliverable_types table
        # This would query the database
        pass
```

---

## 2. USER INTERFACE CHANGES

### 2.1 Project Creation Flow Update

#### OLD: Simple Project Form
```
Project Name: [_____________]
Description: [_____________]
Priority: [Medium ▼]
[Create Project]
```

#### NEW: Multi-Step Project Configuration

**Step 1: Project Type Selection**
```
┌────────────────────────────────────────────────────────┐
│ What do you want to create?                            │
├────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │   💻 Code   │  │ 📄 Document │  │ 📊 Analysis │   │
│  │             │  │             │  │             │   │
│  │  Software   │  │   Report    │  │  Research   │   │
│  │     MVP     │  │  Proposal   │  │   & Data    │   │
│  └─────────────┘  └─────────────┘  └─────────────┘   │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │ 📣 Campaign │  │ 💰 Financial│  │ 👥 HR Doc   │   │
│  │             │  │             │  │             │   │
│  │  Marketing  │  │   Analysis  │  │   Policy    │   │
│  │   Assets    │  │   & Model   │  │  Handbook   │   │
│  └─────────────┘  └─────────────┘  └─────────────┘   │
│                                                         │
│  ┌─────────────┐                                       │
│  │ ⚙️ Custom   │                                       │
│  │             │  [Select specific agents yourself]    │
│  │   Mixed     │                                       │
│  │  Deliverable│                                       │
│  └─────────────┘                                       │
└────────────────────────────────────────────────────────┘
```

**Step 2: Agent Team Selection**
```
┌────────────────────────────────────────────────────────┐
│ Select Your Agent Team                                  │
│ Project Type: Marketing Campaign                        │
├────────────────────────────────────────────────────────┤
│                                                         │
│ ✅ Required Agents (Auto-selected)                     │
│  ☑ CEO Agent          - Strategic oversight            │
│  ☑ Project Manager    - Coordination & planning        │
│  ☑ HR Monitor         - System health monitoring       │
│  ☑ CMO Agent          - Marketing strategy             │
│  ☑ Designer           - Visual assets                  │
│                                                         │
│ 💡 Recommended Agents                                   │
│  ☐ Content Marketer   - Campaign copy & content        │
│  ☐ Social Media       - Social channel strategy        │
│  ☐ Data Analyst       - Campaign analytics             │
│                                                         │
│ ➕ Add More Agents (Optional)                          │
│  [Browse All Departments ▼]                            │
│                                                         │
│  Executive  Engineering  Marketing  Sales  Finance     │
│  HR  Operations  Legal  Research                       │
│                                                         │
│ ───────────────────────────────────────────────────    │
│ Total Agents: 8 agents selected                        │
│ Estimated Cost: $0/hour (free tier)                    │
│                                                         │
│               [Back]           [Next: Configure]       │
└────────────────────────────────────────────────────────┘
```

**Step 3: Project Configuration**
```
┌────────────────────────────────────────────────────────┐
│ Project Configuration                                   │
├────────────────────────────────────────────────────────┤
│                                                         │
│ Project Name: *                                         │
│ [Launch Q1 Marketing Campaign________________]          │
│                                                         │
│ Description: *                                          │
│ ┌─────────────────────────────────────────────────┐   │
│ │ Create a comprehensive marketing campaign for   │   │
│ │ our new SaaS product launch in Q1. Include:     │   │
│ │ - Brand messaging and positioning               │   │
│ │ - Social media content calendar                 │   │
│ │ - Email marketing sequence                      │   │
│ │ - Landing page copy                             │   │
│ │ - Ad creative concepts                          │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
│ Priority: [High ▼]                                      │
│ Deadline: [2025-12-31] (Optional)                      │
│                                                         │
│ Output Format:                                          │
│  ○ PDF Report (Recommended)                            │
│  ○ Presentation (PPTX)                                 │
│  ○ Multiple formats (PDF + Assets)                     │
│                                                         │
│ Advanced Options:                                       │
│  ☑ Include visual mockups                              │
│  ☑ Provide competitor analysis                         │
│  ☐ Generate sample content                             │
│                                                         │
│               [Back]           [Create Project]        │
└────────────────────────────────────────────────────────┘
```

---

### 2.2 Dashboard Updates

#### Agent Selection Widget
```
┌────────────────────────────────────────────────────────┐
│ 🏢 Your Agent Company                                  │
├────────────────────────────────────────────────────────┤
│                                                         │
│ Active Departments: 5/9                                │
│                                                         │
│ ✅ Executive (2 agents)                                │
│    • CEO Agent                                         │
│    • Project Manager                                   │
│                                                         │
│ ✅ Engineering (4 agents)                              │
│    • CTO Agent                                         │
│    • Backend Engineer                                  │
│    • Frontend Engineer                                 │
│    • Designer                                          │
│                                                         │
│ ✅ Marketing (3 agents)                                │
│    • CMO Agent                                         │
│    • Content Marketer                                  │
│    • Social Media Manager                              │
│                                                         │
│ ⭕ Finance (0 agents)     [+ Add Agents]               │
│ ⭕ Sales (0 agents)       [+ Add Agents]               │
│                                                         │
│                    [Manage All Agents]                 │
└────────────────────────────────────────────────────────┘
```

---

## 3. BACKEND LOGIC CHANGES

### 3.1 Project Orchestration Update

#### OLD: Fixed Software Development Flow
```python
async def process_project(project_id: str):
    """Fixed flow for software projects"""
    # 1. CEO evaluates
    await ceo_agent.evaluate_project(project_id)
    
    # 2. CTO provides guidance
    await cto_agent.provide_technical_guidance(project_id)
    
    # 3. PM breaks down tasks
    await pm_agent.create_tasks(project_id)
    
    # 4. Engineers work
    # ... fixed sequence
```

#### NEW: Dynamic Business Operations Flow
```python
async def process_project(project_id: str):
    """Dynamic flow based on selected agents and deliverable type"""
    
    # 1. Load project configuration
    project = await db.get_project(project_id)
    selected_agents = project.selected_agents
    deliverable_type = project.deliverable_type
    
    # 2. CEO always evaluates (strategic oversight)
    await orchestrator.execute_agent_task(
        agent_id='ceo_001',
        project_id=project_id,
        task_type='evaluate_project'
    )
    
    if not await project.is_approved():
        return  # Stop if CEO rejects
    
    # 3. PM creates execution plan based on selected agents
    execution_plan = await orchestrator.execute_agent_task(
        agent_id='pm_001',
        project_id=project_id,
        task_type='create_execution_plan',
        context={
            'selected_agents': selected_agents,
            'deliverable_type': deliverable_type,
            'project_requirements': project.description
        }
    )
    
    # 4. Execute tasks based on plan (parallel where possible)
    task_graph = execution_plan['task_graph']
    await orchestrator.execute_task_graph(task_graph, project_id)
    
    # 5. Department heads review (if selected)
    await orchestrator.conduct_department_reviews(project_id, selected_agents)
    
    # 6. Compile final deliverable
    await orchestrator.compile_deliverable(
        project_id=project_id,
        output_format=project.output_format,
        deliverable_type=deliverable_type
    )
    
    # 7. CEO final approval
    await orchestrator.execute_agent_task(
        agent_id='ceo_001',
        project_id=project_id,
        task_type='final_approval'
    )
```

---

### 3.2 Task Assignment Logic

#### OLD: Hardcoded Assignment
```python
# Backend tasks → backend_001
# Frontend tasks → frontend_001
# Design tasks → designer_001
```

#### NEW: Dynamic Assignment Based on Capabilities
```python
class TaskAssignmentService:
    """Intelligently assign tasks to available agents"""
    
    async def assign_task(self, task: Task, project_id: str) -> str:
        """Assign task to best available agent"""
        
        # 1. Get agents assigned to this project
        project_agents = await self.get_project_agents(project_id)
        
        # 2. Analyze task requirements
        task_type = task.metadata.get('task_type')
        required_skills = task.metadata.get('required_skills', [])
        
        # 3. Find agents with matching skills
        capable_agents = [
            agent for agent in project_agents
            if self.agent_can_handle_task(agent, task_type, required_skills)
        ]
        
        if not capable_agents:
            # Escalate: no capable agent assigned
            await self.escalate_missing_capability(project_id, task, required_skills)
            return None
        
        # 4. Select best agent (based on load, expertise, etc.)
        best_agent = await self.select_best_agent(capable_agents, task)
        
        # 5. Assign
        task.assigned_to_agent_id = best_agent.agent_id
        await self.db.commit()
        
        return best_agent.agent_id
    
    def agent_can_handle_task(
        self, 
        agent: Agent, 
        task_type: str, 
        required_skills: List[str]
    ) -> bool:
        """Check if agent has required capabilities"""
        
        agent_config = AgentRegistry.AGENT_CATALOG[agent.agent_id]
        
        # Check specializations
        agent_skills = agent_config.get('specializations', [])
        has_required_skills = all(
            skill in agent_skills for skill in required_skills
        )
        
        # Check output types
        can_produce_output = task_type in agent_config.get('output_types', [])
        
        return has_required_skills or can_produce_output
```

---

### 3.3 Output Generation Service

#### OLD: Code Output Only
```python
class OutputService:
    async def save_task_output(self, task_id: str, code: str):
        """Save code to database"""
        task.output = code
        task.output_type = 'code'
        await self.db.commit()
```

#### NEW: Multi-Format Output
```python
class OutputService:
    """Handle diverse output formats"""
    
    SUPPORTED_FORMATS = {
        'code': CodeOutputHandler,
        'pdf': PDFOutputHandler,
        'docx': DocumentOutputHandler,
        'pptx': PresentationOutputHandler,
        'xlsx': SpreadsheetOutputHandler,
        'json': JSONOutputHandler,
        'text': TextOutputHandler,
        'markdown': MarkdownOutputHandler
    }
    
    async def save_task_output(
        self,
        task_id: str,
        content: Any,
        output_format: str,
        metadata: Dict = None
    ):
        """Save output in specified format"""
        
        handler_class = self.SUPPORTED_FORMATS.get(output_format)
        if not handler_class:
            raise ValueError(f"Unsupported format: {output_format}")
        
        handler = handler_class()
        
        # 1. Validate content
        handler.validate(content)
        
        # 2. Process/format content
        processed_content = await handler.process(content, metadata)
        
        # 3. Save to database
        task = await self.db.get_task(task_id)
        task.output = processed_content
        task.output_format = output_format
        task.output_metadata = metadata or {}
        await self.db.commit()
        
        # 4. If file-based output, save file
        if handler.is_file_based():
            file_path = await handler.save_file(
                task_id=task_id,
                content=processed_content,
                metadata=metadata
            )
            task.output_metadata['file_path'] = file_path
            await self.db.commit()
        
        return task

class PDFOutputHandler:
    """Handle PDF report generation"""
    
    def is_file_based(self) -> bool:
        return True
    
    async def process(self, content: str, metadata: Dict) -> str:
        """Process markdown/HTML to PDF"""
        # Use existing PDF generation service
        from app.services.pdf_generation import PDFGenerationService
        
        pdf_service = PDFGenerationService()
        pdf_bytes = await pdf_service.generate_from_markdown(
            content=content,
            template=metadata.get('template', 'default'),
            metadata=metadata
        )
        
        return pdf_bytes
    
    async def save_file(self, task_id: str, content: bytes, metadata: Dict) -> str:
        """Save PDF to file system"""
        filename = f"task_{task_id}_output.pdf"
        file_path = f"/outputs/tasks/{filename}"
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        return file_path

class CodeOutputHandler:
    """Handle code file generation"""
    
    def is_file_based(self) -> bool:
        return True
    
    async def process(self, content: Dict, metadata: Dict) -> Dict:
        """Process code files (multiple files possible)"""
        # Content is dict: { 'backend/main.py': '...', 'frontend/app.tsx': '...' }
        return content
    
    async def save_file(self, task_id: str, content: Dict, metadata: Dict) -> str:
        """Save code files to file system"""
        base_path = f"/outputs/tasks/{task_id}/code"
        os.makedirs(base_path, exist_ok=True)
        
        for file_path, file_content in content.items():
            full_path = os.path.join(base_path, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            async with aiofiles.open(full_path, 'w') as f:
                await f.write(file_content)
        
        return base_path
```

---

## 4. NEW AGENT IMPLEMENTATIONS

### 4.1 Marketing Agents

```python
class CMOAgent(BaseAgent):
    """Chief Marketing Officer Agent"""
    
    def __init__(self):
        super().__init__(
            agent_id='cmo_001',
            name='CMO Agent',
            role='Chief Marketing Officer',
            department='marketing'
        )
    
    async def process_task(self, task: Task) -> Dict:
        """Process marketing strategy tasks"""
        
        if task.title.startswith('Create marketing strategy'):
            return await self.create_marketing_strategy(task)
        elif task.title.startswith('Review campaign'):
            return await self.review_campaign(task)
        else:
            return await self.default_marketing_task(task)
    
    async def create_marketing_strategy(self, task: Task) -> Dict:
        """Create comprehensive marketing strategy"""
        
        project = await self.get_project(task.project_id)
        
        prompt = f"""
You are the Chief Marketing Officer of a company. You need to create a comprehensive 
marketing strategy for the following project:

Project: {project.name}
Description: {project.description}

Create a marketing strategy that includes:
1. Target Audience Analysis
   - Demographics
   - Psychographics
   - Pain points
   - Buying behavior

2. Positioning & Messaging
   - Unique value proposition
   - Key messages
   - Brand voice

3. Channel Strategy
   - Primary channels
   - Secondary channels
   - Channel-specific tactics

4. Campaign Ideas
   - 3-5 campaign concepts
   - Creative direction for each
   - Expected outcomes

5. Success Metrics
   - KPIs to track
   - Target numbers
   - Measurement approach

6. Budget Allocation
   - Channel budget breakdown
   - Resource requirements
   - Timeline

Output as structured markdown suitable for PDF generation.
"""
        
        strategy = await self.call_llm(prompt, max_tokens=3000)
        
        return {
            'output': strategy,
            'output_format': 'markdown',
            'output_metadata': {
                'document_type': 'marketing_strategy',
                'sections': ['audience', 'positioning', 'channels', 'campaigns', 'metrics', 'budget']
            }
        }

class ContentMarketingAgent(BaseAgent):
    """Content Marketing Specialist Agent"""
    
    async def process_task(self, task: Task) -> Dict:
        """Generate marketing content"""
        
        if 'blog post' in task.title.lower():
            return await self.write_blog_post(task)
        elif 'email sequence' in task.title.lower():
            return await self.create_email_sequence(task)
        elif 'landing page copy' in task.title.lower():
            return await self.write_landing_page(task)
        else:
            return await self.default_content_task(task)
    
    async def write_blog_post(self, task: Task) -> Dict:
        """Write SEO-optimized blog post"""
        
        prompt = f"""
You are a content marketing expert. Write a blog post based on:

{task.description}

Requirements:
- 1500-2000 words
- SEO optimized with target keywords
- Engaging introduction
- Clear structure with H2/H3 subheadings
- Actionable takeaways
- Call-to-action at end

Output as markdown.
"""
        
        blog_post = await self.call_llm(prompt, max_tokens=2500)
        
        return {
            'output': blog_post,
            'output_format': 'markdown',
            'output_metadata': {
                'content_type': 'blog_post',
                'word_count': len(blog_post.split()),
                'seo_optimized': True
            }
        }
```

### 4.2 Finance Agents

```python
class CFOAgent(BaseAgent):
    """Chief Financial Officer Agent"""
    
    async def process_task(self, task: Task) -> Dict:
        """Process financial analysis tasks"""
        
        if 'financial model' in task.title.lower():
            return await self.create_financial_model(task)
        elif 'budget' in task.title.lower():
            return await self.create_budget(task)
        elif 'forecast' in task.title.lower():
            return await self.create_forecast(task)
        else:
            return await self.default_financial_task(task)
    
    async def create_financial_model(self, task: Task) -> Dict:
        """Create financial model with projections"""
        
        prompt = f"""
You are a Chief Financial Officer. Create a financial model for:

{task.description}

Include:
1. Revenue Projections (3-year)
   - Revenue streams
   - Growth assumptions
   - Monthly breakdown

2. Cost Structure
   - Fixed costs
   - Variable costs
   - One-time costs

3. Cash Flow Analysis
   - Operating cash flow
   - Investment requirements
   - Financing needs

4. Key Metrics
   - Gross margin
   - EBITDA margin
   - Break-even analysis
   - Runway calculation

5. Scenarios
   - Base case
   - Best case
   - Worst case

6. Recommendations
   - Key insights
   - Risk factors
   - Mitigation strategies

Output as structured data suitable for Excel/CSV generation.
Include formulas where applicable.
"""
        
        model_data = await self.call_llm(prompt, max_tokens=3000)
        
        # Parse model data and convert to structured format
        # This would include logic to extract tables, formulas, etc.
        
        return {
            'output': model_data,
            'output_format': 'xlsx',
            'output_metadata': {
                'document_type': 'financial_model',
                'projection_years': 3,
                'includes_scenarios': True
            }
        }

class FinancialAnalystAgent(BaseAgent):
    """Financial Analyst Agent"""
    
    async def process_task(self, task: Task) -> Dict:
        """Perform detailed financial analysis"""
        
        # Implementation similar to CFO but more detailed
        pass
```

### 4.3 HR Agents

```python
class CHROAgent(BaseAgent):
    """Chief Human Resources Officer Agent"""
    
    async def process_task(self, task: Task) -> Dict:
        """Process HR strategy and policy tasks"""
        
        if 'policy' in task.title.lower():
            return await self.create_hr_policy(task)
        elif 'handbook' in task.title.lower():
            return await self.create_employee_handbook(task)
        else:
            return await self.default_hr_task(task)
    
    async def create_hr_policy(self, task: Task) -> Dict:
        """Create HR policy document"""
        
        prompt = f"""
You are the Chief Human Resources Officer. Create a comprehensive HR policy for:

{task.description}

Include:
1. Policy Overview
   - Purpose
   - Scope
   - Effective date

2. Policy Details
   - Detailed procedures
   - Responsibilities
   - Compliance requirements

3. Implementation
   - Rollout plan
   - Training needs
   - Communication strategy

4. Review & Updates
   - Review schedule
   - Amendment process

Output as professional document suitable for DOCX generation.
Use clear, legal-friendly language.
"""
        
        policy = await self.call_llm(prompt, max_tokens=2500)
        
        return {
            'output': policy,
            'output_format': 'docx',
            'output_metadata': {
                'document_type': 'hr_policy',
                'requires_legal_review': True
            }
        }

class HRMonitorAgent(BaseAgent):
    """Agent Health Monitoring (formerly HR Agent)"""
    # This remains largely the same as current HR agent
    # But renamed for clarity about its monitoring role
    pass
```

---

## 5. DELIVERABLE COMPILATION SYSTEM

### 5.1 Multi-Format Export

```python
class DeliverableCompilationService:
    """Compile project deliverables in various formats"""
    
    async def compile_project_deliverable(
        self,
        project_id: str,
        output_format: str = 'pdf'
    ) -> str:
        """Compile all project outputs into final deliverable"""
        
        project = await self.db.get_project(project_id)
        tasks = await self.db.get_project_tasks(project_id)
        
        # 1. Collect all task outputs
        outputs = await self.collect_task_outputs(tasks)
        
        # 2. Organize by section
        sections = await self.organize_outputs(outputs, project.deliverable_type)
        
        # 3. Generate deliverable based on format
        if output_format == 'pdf':
            return await self.compile_pdf_report(project, sections)
        elif output_format == 'zip':
            return await self.compile_code_package(project, sections)
        elif output_format == 'pptx':
            return await self.compile_presentation(project, sections)
        else:
            raise ValueError(f"Unsupported format: {output_format}")
    
    async def compile_pdf_report(
        self,
        project: Project,
        sections: Dict[str, List[TaskOutput]]
    ) -> str:
        """Compile PDF report from all outputs"""
        
        # Build markdown document
        markdown = f"""---
title: {project.name}
project_id: {project.project_id}
deliverable_type: {project.deliverable_type}
generated: {datetime.now().isoformat()}
agents_involved: {len(project.selected_agents)}
---

# {project.name}

## Executive Summary

{await self.generate_executive_summary(project, sections)}

## Project Overview

**Description:** {project.description}

**Status:** {project.status}

**Priority:** {project.priority}

**Agents Assigned:** {', '.join([a['name'] for a in project.selected_agents])}

---

"""
        
        # Add sections
        for section_name, outputs in sections.items():
            markdown += f"\n## {section_name}\n\n"
            
            for output in outputs:
                markdown += f"\n### {output.task_title}\n\n"
                markdown += f"{output.content}\n\n"
                markdown += "---\n\n"
        
        # Generate PDF
        from app.services.pdf_generation import PDFGenerationService
        pdf_service = PDFGenerationService()
        
        pdf_path = await pdf_service.generate_from_markdown(
            content=markdown,
            template='professional_report',
            metadata={
                'project_id': project.project_id,
                'project_name': project.name
            }
        )
        
        return pdf_path
    
    async def compile_code_package(
        self,
        project: Project,
        sections: Dict[str, List[TaskOutput]]
    ) -> str:
        """Compile code outputs into ZIP package"""
        
        import zipfile
        
        zip_path = f"/outputs/projects/{project.project_id}/code_package.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            # Add README
            readme = await self.generate_code_readme(project, sections)
            zipf.writestr('README.md', readme)
            
            # Add code files
            code_outputs = [
                out for outs in sections.values() 
                for out in outs 
                if out.output_format == 'code'
            ]
            
            for output in code_outputs:
                for file_path, content in output.content.items():
                    zipf.writestr(file_path, content)
        
        return zip_path
```

---

## 6. MIGRATION STRATEGY

### 6.1 Database Migration

```sql
-- Migration Script: v1_to_v2_business_operations.sql

-- 1. Add new tables
-- (See section 1.1 for full SQL)

-- 2. Update existing projects
UPDATE projects 
SET 
    project_type = 'software_mvp',
    deliverable_type = 'software_mvp',
    selected_agents = '["ceo_001", "cto_001", "pm_001", "hr_001", "backend_001", "frontend_001", "designer_001"]'::jsonb
WHERE project_type IS NULL;

-- 3. Migrate existing tasks
UPDATE tasks
SET 
    output_format = CASE 
        WHEN assigned_to_agent_id IN ('backend_001', 'frontend_001') THEN 'code'
        WHEN assigned_to_agent_id = 'designer_001' THEN 'design_specs'
        ELSE 'text'
    END,
    output_metadata = '{}'::jsonb
WHERE output_format IS NULL;

-- 4. Create project-agent assignments for existing projects
INSERT INTO project_agent_assignments (project_id, agent_id, role_in_project)
SELECT 
    p.project_id,
    unnest(ARRAY['ceo_001', 'cto_001', 'pm_001', 'hr_001', 'backend_001', 'frontend_001', 'designer_001']),
    'core_team'
FROM projects p
WHERE NOT EXISTS (
    SELECT 1 FROM project_agent_assignments paa 
    WHERE paa.project_id = p.project_id
);
```

### 6.2 Code Migration Plan

**Phase 1: Add New Agents (Non-Breaking)**
- Add new agent classes (CMO, CFO, etc.)
- Register in AgentRegistry
- No impact on existing functionality

**Phase 2: Update Database Schema (Non-Breaking)**
- Add new columns with defaults
- Add new tables
- Existing code continues to work

**Phase 3: Update UI (Feature Flag)**
- Add new project creation flow behind feature flag
- Keep old flow as default initially
- Gradual rollout

**Phase 4: Update Backend Logic (Backward Compatible)**
- Check if `selected_agents` exists, use if present
- Fall back to legacy 7-agent flow if not
- Both flows work simultaneously

**Phase 5: Full Migration**
- Make new flow default
- Migrate all existing projects
- Remove legacy code

---

## 7. TESTING STRATEGY

### 7.1 Test Scenarios

**Scenario 1: Marketing Campaign Project**
```yaml
test_name: "Complete Marketing Campaign"
project_type: "marketing_campaign"
selected_agents:
  - ceo_001
  - pm_001
  - hr_monitor_001
  - cmo_001
  - content_001
  - social_media_001
  - designer_001

expected_deliverables:
  - marketing_strategy.pdf
  - content_calendar.xlsx
  - sample_blog_posts.md
  - social_media_plan.pdf
  - creative_assets/ (folder)

success_criteria:
  - All agents complete tasks
  - PDF report generated successfully
  - Content is relevant and actionable
  - No agent errors or blockers
  - Deliverable quality > 85%
```

**Scenario 2: Financial Analysis Project**
```yaml
test_name: "Q1 Financial Analysis"
project_type: "financial_analysis"
selected_agents:
  - ceo_001
  - pm_001
  - cfo_001
  - financial_analyst_001

expected_deliverables:
  - financial_model.xlsx
  - analysis_report.pdf
  - forecast_charts/ (folder)

success_criteria:
  - Financial model with formulas
  - All calculations accurate
  - Charts and visualizations included
  - Executive summary present
```

**Scenario 3: Custom Mixed Project**
```yaml
test_name: "Product Launch Plan"
project_type: "custom"
selected_agents:
  - ceo_001
  - pm_001
  - cto_001
  - cmo_001
  - sales_manager_001
  - financial_analyst_001
  - designer_001

expected_deliverables:
  - launch_strategy.pdf
  - technical_architecture.md
  - marketing_plan.pdf
  - sales_playbook.pdf
  - financial_projections.xlsx

success_criteria:
  - Cross-functional coordination works
  - All departments contribute
  - Outputs are cohesive
  - Timeline is realistic
```

---

## 8. PRIORITY IMPLEMENTATION ORDER

### Phase 1: Foundation (Week 1-2)
1. **Database schema updates**
   - Add new tables
   - Update existing tables
   - Migration scripts

2. **Agent Registry system**
   - Dynamic agent catalog
   - Department organization
   - Capability mapping

3. **Basic UI updates**
   - Project type selection
   - Agent selection interface

### Phase 2: Core Agents (Week 3-4)
1. **Implement new agent classes**
   - CMO Agent
   - CFO Agent
   - CHRO Agent
   - Research Agent

2. **Output handling**
   - Multi-format support
   - PDF generation
   - Document generation

3. **Task assignment logic**
   - Dynamic assignment
   - Capability matching

### Phase 3: Orchestration (Week 5-6)
1. **Dynamic workflow engine**
   - Flexible execution plans
   - Parallel task execution
   - Department coordination

2. **Deliverable compilation**
   - PDF reports
   - Code packages
   - Multi-format export

### Phase 4: Testing & Polish (Week 7-8)
1. **End-to-end testing**
   - All project types
   - All agent combinations

2. **UI/UX refinement**
   - Better agent selection
   - Progress visualization
   - Output preview

3. **Documentation**
   - User guides
   - API documentation
   - Agent capabilities reference

---

## 9. SUCCESS METRICS

### Technical Metrics
- ✅ Support 5+ project types
- ✅ 15+ agent types available
- ✅ 4+ output formats (PDF, DOCX, XLSX, Code)
- ✅ Dynamic agent assignment working
- ✅ <5% error rate in multi-agent coordination

### Business Metrics
- ✅ Users create non-software projects
- ✅ 80%+ satisfaction with deliverable quality
- ✅ Average project completion time acceptable
- ✅ Agent utilization balanced across departments

### User Experience Metrics
- ✅ Agent selection intuitive (measured via user testing)
- ✅ <3 clicks to create project
- ✅ Progress visibility clear
- ✅ Output preview available before download

---

## 10. DOCUMENTATION UPDATES NEEDED

1. **BUSINESS_PLAN.md**
   - Update target market to include non-technical users
   - Add new use cases (marketing, finance, HR)
   - Update pricing tiers to reflect agent combinations

2. **README.md**
   - Update product description
   - Show diverse project examples
   - Update agent list

3. **GETTING-STARTED.md**
   - New project creation flow
   - Agent selection guide
   - Output format options

4. **Feature Documentation (02_Projects.md, etc.)**
   - Update all UI mockups
   - Add new agent sections
   - Document deliverable types

5. **API Documentation**
   - New endpoints for agent selection
   - Deliverable type management
   - Output format handling

---

## CONCLUSION

This evolution transforms Retinue from a specialized software development tool into a comprehensive **autonomous business operations platform**. The changes enable:

1. **Flexibility**: Users select the right agents for their specific needs
2. **Versatility**: Support for any business function, not just engineering
3. **Scalability**: Easy to add new agents and departments
4. **Professional Output**: High-quality deliverables in appropriate formats
5. **True Autonomy**: Agents collaborate across functions like a real company

The implementation plan ensures backward compatibility while enabling this significant evolution. Existing software projects continue to work while new capabilities are gradually introduced.

**Next Steps**:
1. Review and approve this evolution plan
2. Prioritize features based on user demand
3. Begin Phase 1 implementation
4. Conduct user testing at each phase
5. Iterate based on feedback

---

**End of Document**
