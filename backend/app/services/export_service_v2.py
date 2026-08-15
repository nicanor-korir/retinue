"""
Export Service v2 - Clean, simple export functionality.

Design principles:
1. One export method, multiple formats
2. Auto-detect project type and generate appropriate content
3. Simple progress tracking without over-engineering
4. Proper error handling with retries
"""
import asyncio
import hashlib
import json
import logging
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Agent, Message, Project, Task, TaskStatus
from app.schemas.export_schemas import ExportFormat, ExportRequest, ExportStatus

logger = logging.getLogger(__name__)


class ExportServiceV2:
    """
    Simplified export service.

    Instead of 6 different export types and complex options,
    we have one export flow that adapts to project type.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.export_dir = Path(tempfile.gettempdir()) / "retinue_exports"
        self.export_dir.mkdir(parents=True, exist_ok=True)

    async def get_project_export_info(self, project_id: UUID) -> Dict[str, Any]:
        """
        Get info about what can be exported from a project.

        This replaces the complex "content availability" analysis.
        """
        project = await self.session.get(Project, project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        # Count tasks
        task_result = await self.session.execute(
            select(func.count(Task.task_id)).where(Task.project_id == project_id)
        )
        task_count = task_result.scalar() or 0

        # Count content (tasks with output files)
        content_result = await self.session.execute(
            select(func.count(Task.task_id)).where(
                Task.project_id == project_id,
                Task.output.isnot(None)
            )
        )
        content_count = content_result.scalar() or 0

        # Count messages
        message_result = await self.session.execute(
            select(func.count(Message.message_id)).where(
                Message.related_project_id == project_id
            )
        )
        message_count = message_result.scalar() or 0

        # Detect project type from metadata or task patterns
        project_type = self._detect_project_type(project, task_count)

        # Recommend format based on project type
        recommended_format = self._get_recommended_format(project_type)

        return {
            "project_id": str(project_id),
            "project_name": project.name,
            "project_type": project_type,
            "has_tasks": task_count > 0,
            "has_content": content_count > 0,
            "has_conversations": message_count > 0,
            "has_metrics": task_count > 0,  # Metrics available if tasks exist
            "task_count": task_count,
            "content_count": content_count,
            "message_count": message_count,
            "recommended_format": recommended_format,
        }

    def _detect_project_type(self, project: Project, task_count: int) -> str:
        """
        Detect project type from metadata and patterns.

        Categories:
        - software: Code, APIs, technical documentation
        - content: Articles, blog posts, marketing copy
        - marketing: Campaigns, social media, ads
        - legal: Contracts, policies, compliance
        - general: Everything else
        """
        meta = project.meta_data or {}

        # Check explicit type in metadata
        if "project_type" in meta:
            return meta["project_type"]

        # Check for technology indicators
        if meta.get("technologies") or meta.get("framework"):
            return "software"

        # Check description for keywords
        desc = (project.description or "").lower()
        name = project.name.lower()

        software_keywords = ["api", "app", "code", "develop", "build", "software", "website", "backend", "frontend"]
        content_keywords = ["article", "blog", "content", "write", "copy", "seo"]
        marketing_keywords = ["campaign", "marketing", "social", "ad", "promotion", "brand"]
        legal_keywords = ["contract", "legal", "policy", "compliance", "agreement", "terms"]

        combined = f"{name} {desc}"

        if any(kw in combined for kw in software_keywords):
            return "software"
        if any(kw in combined for kw in content_keywords):
            return "content"
        if any(kw in combined for kw in marketing_keywords):
            return "marketing"
        if any(kw in combined for kw in legal_keywords):
            return "legal"

        return "general"

    def _get_recommended_format(self, project_type: str) -> str:
        """Get recommended export format based on project type."""
        recommendations = {
            "software": "zip",       # Developers want files
            "content": "markdown",   # Writers want editable text
            "marketing": "pdf",      # Marketers want polished docs
            "legal": "pdf",          # Legal needs formal documents
            "general": "pdf",        # Default to PDF
        }
        return recommendations.get(project_type, "pdf")

    async def create_export(
        self,
        project_id: UUID,
        request: ExportRequest,
    ) -> Tuple[str, str]:
        """
        Create an export synchronously.

        For most projects, exports complete in under 5 seconds.
        No need for complex job queues and SSE for simple exports.

        Returns: (file_path, file_name)
        """
        project = await self.session.get(Project, project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        # Collect data based on options
        data = await self._collect_data(project_id, request)

        # Generate export based on format
        if request.format == ExportFormat.PDF:
            return await self._generate_pdf(project, data)
        elif request.format == ExportFormat.MARKDOWN:
            return await self._generate_markdown(project, data)
        elif request.format == ExportFormat.ZIP:
            return await self._generate_zip(project, data)
        else:
            raise ValueError(f"Unsupported format: {request.format}")

    async def _collect_data(self, project_id: UUID, request: ExportRequest) -> Dict[str, Any]:
        """Collect all data needed for export based on options."""
        project = await self.session.get(Project, project_id)
        data = {
            "project": {
                "id": str(project_id),
                "name": project.name,
                "description": project.description,
                "status": project.status.value,
                "created_at": project.created_at.isoformat() if project.created_at else None,
                "updated_at": project.updated_at.isoformat() if project.updated_at else None,
            },
            "exported_at": datetime.now().isoformat(),
        }

        if request.include_tasks:
            data["tasks"] = await self._get_tasks(project_id)

        if request.include_content:
            data["content"] = await self._get_content(project_id)

        if request.include_conversations:
            data["conversations"] = await self._get_conversations(project_id)

        if request.include_metrics:
            data["metrics"] = await self._get_metrics(project_id)

        return data

    async def _get_tasks(self, project_id: UUID) -> list:
        """Get all tasks for export."""
        result = await self.session.execute(
            select(Task)
            .where(Task.project_id == project_id)
            .order_by(Task.created_at)
        )
        tasks = result.scalars().all()

        return [
            {
                "id": str(t.task_id),
                "title": t.title,
                "description": t.description,
                "status": t.status.value,
                "assigned_to": t.assigned_to_agent_id,
                "estimated_hours": t.estimated_hours,
                "actual_hours": t.actual_hours,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "updated_at": t.updated_at.isoformat() if t.updated_at else None,
                "output": t.output,
            }
            for t in tasks
        ]

    async def _get_content(self, project_id: UUID) -> list:
        """Get generated content/files from tasks."""
        result = await self.session.execute(
            select(Task)
            .where(Task.project_id == project_id, Task.output.isnot(None))
        )
        tasks = result.scalars().all()

        content = []
        for task in tasks:
            if task.output:
                output = task.output if isinstance(task.output, dict) else {}
                if "files_created" in output:
                    for file_info in output["files_created"]:
                        content.append({
                            "task_title": task.title,
                            "file_path": file_info.get("path", ""),
                            "file_type": file_info.get("type", "unknown"),
                            "content": file_info.get("content", ""),
                        })
                elif "result" in output:
                    content.append({
                        "task_title": task.title,
                        "content": str(output["result"])[:5000],  # Limit size
                    })
        return content

    async def _get_conversations(self, project_id: UUID) -> list:
        """Get agent conversations."""
        result = await self.session.execute(
            select(Message)
            .where(Message.related_project_id == project_id)
            .order_by(Message.timestamp)
            .limit(500)  # Reasonable limit
        )
        messages = result.scalars().all()

        return [
            {
                "from": m.from_agent_id,
                "to": m.to_agent_id,
                "content": m.content[:2000] if m.content else "",  # Limit size
                "timestamp": m.timestamp.isoformat() if m.timestamp else None,
            }
            for m in messages
        ]

    async def _get_metrics(self, project_id: UUID) -> Dict[str, Any]:
        """Get project metrics."""
        # Task status counts
        result = await self.session.execute(
            select(Task.status, func.count(Task.task_id))
            .where(Task.project_id == project_id)
            .group_by(Task.status)
        )
        status_counts = {str(status.value): count for status, count in result.all()}

        # Calculate completion
        total = sum(status_counts.values())
        completed = status_counts.get("completed", 0)

        return {
            "total_tasks": total,
            "completed_tasks": completed,
            "completion_rate": (completed / total * 100) if total > 0 else 0,
            "task_by_status": status_counts,
        }

    def _sanitize_text(self, text: str) -> str:
        """Remove or replace Unicode characters not supported by Helvetica."""
        # Replace common Unicode characters with ASCII equivalents
        replacements = {
            '\u2022': '-',   # Bullet
            '\u2023': '>',   # Triangular bullet
            '\u2043': '-',   # Hyphen bullet
            '\u2219': '-',   # Bullet operator
            '\u25aa': '-',   # Small black square
            '\u25cf': '-',   # Black circle
            '\u2013': '-',   # En dash
            '\u2014': '--',  # Em dash
            '\u2018': "'",   # Left single quote
            '\u2019': "'",   # Right single quote
            '\u201c': '"',   # Left double quote
            '\u201d': '"',   # Right double quote
            '\u2026': '...', # Ellipsis
            '\u00a0': ' ',   # Non-breaking space
            '\u00b7': '-',   # Middle dot
            '\u2192': '->',  # Right arrow
            '\u2190': '<-',  # Left arrow
            '\u2713': '[x]', # Check mark
            '\u2717': '[ ]', # Ballot X
            '\u00ae': '(R)', # Registered
            '\u2122': '(TM)',# Trademark
            '\u00a9': '(C)', # Copyright
        }
        for unicode_char, ascii_char in replacements.items():
            text = text.replace(unicode_char, ascii_char)

        # Remove any remaining non-latin-1 characters
        try:
            text.encode('latin-1')
        except UnicodeEncodeError:
            text = text.encode('latin-1', errors='replace').decode('latin-1')

        return text

    def _parse_markdown_to_pdf(self, pdf, text: str):
        """Parse markdown text and render it properly in PDF."""
        import re

        # Sanitize text first
        text = self._sanitize_text(text)

        lines = text.split('\n')

        for line in lines:
            try:
                # Reset to left margin before each line
                pdf.set_x(pdf.l_margin)

                # Skip empty lines
                if not line.strip():
                    pdf.ln(3)
                    continue

                # H1: # Header
                if line.startswith('# '):
                    pdf.ln(5)
                    pdf.set_font("Helvetica", "B", 16)
                    pdf.multi_cell(0, 8, line[2:].strip())
                    pdf.ln(2)
                # H2: ## Header
                elif line.startswith('## '):
                    pdf.ln(4)
                    pdf.set_font("Helvetica", "B", 14)
                    pdf.multi_cell(0, 7, line[3:].strip())
                    pdf.ln(2)
                # H3: ### Header
                elif line.startswith('### '):
                    pdf.ln(3)
                    pdf.set_font("Helvetica", "B", 12)
                    pdf.multi_cell(0, 6, line[4:].strip())
                    pdf.ln(1)
                # H4: #### Header
                elif line.startswith('#### '):
                    pdf.ln(2)
                    pdf.set_font("Helvetica", "B", 11)
                    pdf.multi_cell(0, 6, line[5:].strip())
                # Bullet points
                elif line.strip().startswith('- ') or line.strip().startswith('* '):
                    pdf.set_font("Helvetica", "", 10)
                    bullet_text = line.strip()[2:].strip()
                    # Remove markdown bold/italic
                    bullet_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', bullet_text)
                    bullet_text = re.sub(r'\*([^*]+)\*', r'\1', bullet_text)
                    pdf.multi_cell(0, 5, f"  - {bullet_text}")
                # Numbered list
                elif re.match(r'^\d+\.\s', line.strip()):
                    pdf.set_font("Helvetica", "", 10)
                    pdf.multi_cell(0, 5, f"  {line.strip()}")
                # Bold text line (starts with **)
                elif line.strip().startswith('**') and line.strip().endswith('**'):
                    pdf.set_font("Helvetica", "B", 10)
                    clean_text = line.strip()[2:-2]
                    pdf.multi_cell(0, 5, clean_text)
                # Regular paragraph - handle inline markdown
                else:
                    pdf.set_font("Helvetica", "", 10)
                    # Clean up markdown formatting for plain text
                    clean_line = line
                    clean_line = re.sub(r'\*\*([^*]+)\*\*', r'\1', clean_line)  # Bold
                    clean_line = re.sub(r'\*([^*]+)\*', r'\1', clean_line)      # Italic
                    clean_line = re.sub(r'`([^`]+)`', r'\1', clean_line)        # Code
                    clean_line = clean_line.replace('\\n', '\n')
                    pdf.multi_cell(0, 5, clean_line)
            except Exception as e:
                # If any line fails, just skip it and continue
                logger.warning(f"Failed to render PDF line: {e}")
                pdf.set_x(pdf.l_margin)
                pdf.ln(5)
                continue

    async def _generate_pdf(self, project: Project, data: Dict[str, Any]) -> Tuple[str, str]:
        """Generate PDF export using fpdf2 (pure Python, no system deps)."""
        from fpdf import FPDF

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = project.name.replace(" ", "_").lower()[:30]
        file_name = f"{safe_name}_export_{timestamp}.pdf"
        file_path = self.export_dir / file_name

        # Create PDF
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # Title
        pdf.set_font("Helvetica", "B", 24)
        pdf.multi_cell(0, 12, project.name)

        # Export date
        pdf.ln(3)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(128, 128, 128)
        pdf.cell(0, 6, f"Exported on {data['exported_at'][:10]}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)

        # Description
        if project.description:
            pdf.ln(5)
            pdf.set_font("Helvetica", "", 11)
            pdf.multi_cell(0, 6, project.description)

        # Status - on its own line with proper formatting
        pdf.ln(5)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(20, 8, "Status: ", new_x="RIGHT")
        pdf.set_font("Helvetica", "", 11)
        status_colors = {
            "COMPLETED": (34, 197, 94),
            "IN_PROGRESS": (59, 130, 246),
            "BLOCKED": (239, 68, 68),
            "PENDING": (156, 163, 175),
            "PLANNING": (168, 85, 247),
            "CANCELLED": (107, 114, 128),
            "FAILED": (239, 68, 68),
        }
        r, g, b = status_colors.get(project.status.value, (0, 0, 0))
        pdf.set_text_color(r, g, b)
        pdf.cell(0, 8, project.status.value, new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)

        # Metrics
        if "metrics" in data:
            m = data["metrics"]
            pdf.ln(10)
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(0, 10, "Metrics", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 11)
            pdf.cell(0, 7, f"Total Tasks: {m['total_tasks']}", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 7, f"Completed: {m['completed_tasks']}", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 7, f"Completion Rate: {m['completion_rate']:.1f}%", new_x="LMARGIN", new_y="NEXT")

        # Tasks - Full detail view
        if "tasks" in data and data["tasks"]:
            pdf.ln(10)
            pdf.set_font("Helvetica", "B", 18)
            pdf.cell(0, 12, "Tasks", new_x="LMARGIN", new_y="NEXT")

            for i, task in enumerate(data["tasks"], 1):
                pdf.ln(8)

                # Task title with number
                pdf.set_font("Helvetica", "B", 14)
                pdf.set_text_color(30, 64, 175)  # Blue
                pdf.multi_cell(0, 8, f"{i}. {task['title']}")
                pdf.set_text_color(0, 0, 0)

                # Status - on its own line
                pdf.ln(2)
                pdf.set_font("Helvetica", "B", 10)
                pdf.cell(18, 6, "Status: ", new_x="RIGHT")
                status = task["status"]
                r, g, b = status_colors.get(status, (0, 0, 0))
                pdf.set_text_color(r, g, b)
                pdf.set_font("Helvetica", "", 10)
                pdf.cell(0, 6, status, new_x="LMARGIN", new_y="NEXT")
                pdf.set_text_color(0, 0, 0)

                # Assigned to - on its own line
                if task.get("assigned_to"):
                    pdf.set_font("Helvetica", "B", 10)
                    pdf.cell(28, 6, "Assigned to: ", new_x="RIGHT")
                    pdf.set_font("Helvetica", "", 10)
                    pdf.cell(0, 6, task['assigned_to'], new_x="LMARGIN", new_y="NEXT")

                # Description
                if task.get("description"):
                    pdf.ln(3)
                    pdf.set_font("Helvetica", "B", 10)
                    pdf.cell(0, 6, "Description:", new_x="LMARGIN", new_y="NEXT")
                    pdf.set_font("Helvetica", "", 10)
                    pdf.multi_cell(0, 5, task["description"])

                # Output - Full content with markdown rendering
                if task.get("output"):
                    pdf.ln(5)
                    pdf.set_font("Helvetica", "B", 12)
                    pdf.set_fill_color(245, 245, 245)
                    pdf.cell(0, 8, "Output", new_x="LMARGIN", new_y="NEXT", fill=True)
                    pdf.ln(3)

                    output = task["output"]
                    if isinstance(output, dict):
                        # Handle answer field (common in CEO responses)
                        if "answer" in output:
                            self._parse_markdown_to_pdf(pdf, str(output["answer"]))
                        # Handle result field
                        elif "result" in output:
                            self._parse_markdown_to_pdf(pdf, str(output["result"]))
                        # Handle content field
                        elif "content" in output:
                            self._parse_markdown_to_pdf(pdf, str(output["content"]))
                        # Handle analysis field
                        elif "analysis" in output:
                            self._parse_markdown_to_pdf(pdf, str(output["analysis"]))
                        # Handle files_created
                        elif "files_created" in output:
                            for file_info in output["files_created"]:
                                pdf.set_font("Helvetica", "B", 10)
                                file_path_str = file_info.get("path", "Unknown file")
                                pdf.cell(0, 6, f"File: {file_path_str}", new_x="LMARGIN", new_y="NEXT")
                                if file_info.get("content"):
                                    pdf.set_font("Courier", "", 8)
                                    content = str(file_info["content"])[:10000]
                                    pdf.multi_cell(0, 4, content)
                                pdf.ln(3)
                        else:
                            # Show other fields nicely
                            for key, value in output.items():
                                if key not in ["query_type", "answered_by", "can_continue"] and value:
                                    pdf.set_font("Helvetica", "B", 10)
                                    pdf.cell(0, 6, f"{key.replace('_', ' ').title()}:", new_x="LMARGIN", new_y="NEXT")
                                    pdf.set_font("Helvetica", "", 10)
                                    if isinstance(value, str) and len(value) > 100:
                                        self._parse_markdown_to_pdf(pdf, value)
                                    else:
                                        pdf.multi_cell(0, 5, str(value))
                                    pdf.ln(2)
                    else:
                        self._parse_markdown_to_pdf(pdf, str(output)[:15000])

                # Separator line
                pdf.ln(8)
                pdf.set_draw_color(200, 200, 200)
                pdf.line(10, pdf.get_y(), 200, pdf.get_y())

        # Content section (if included separately)
        if "content" in data and data["content"]:
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 18)
            pdf.cell(0, 12, "Generated Content", new_x="LMARGIN", new_y="NEXT")

            for content in data["content"]:
                pdf.ln(5)
                pdf.set_font("Helvetica", "B", 12)
                pdf.multi_cell(0, 7, content.get("task_title", "Content"))

                if content.get("file_path"):
                    pdf.set_font("Helvetica", "I", 9)
                    pdf.set_text_color(100, 100, 100)
                    pdf.cell(0, 5, f"File: {content['file_path']}", new_x="LMARGIN", new_y="NEXT")
                    pdf.set_text_color(0, 0, 0)

                if content.get("content"):
                    pdf.ln(2)
                    self._parse_markdown_to_pdf(pdf, str(content["content"])[:20000])

                pdf.ln(5)

        # Conversations (if included)
        if "conversations" in data and data["conversations"]:
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 18)
            pdf.cell(0, 12, "Conversations", new_x="LMARGIN", new_y="NEXT")

            for conv in data["conversations"]:
                pdf.ln(3)
                pdf.set_font("Helvetica", "B", 10)
                from_agent = conv.get("from", "Unknown")
                to_agent = conv.get("to", "Unknown")
                timestamp_str = conv.get("timestamp", "")[:16] if conv.get("timestamp") else ""
                pdf.cell(0, 6, f"{from_agent} -> {to_agent}  ({timestamp_str})", new_x="LMARGIN", new_y="NEXT")

                pdf.set_font("Helvetica", "", 9)
                if conv.get("content"):
                    pdf.multi_cell(0, 5, conv["content"])
                pdf.ln(2)

        # Footer
        pdf.ln(15)
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(128, 128, 128)
        pdf.cell(0, 8, "Generated by RetinueAI", new_x="LMARGIN", new_y="NEXT")

        # Save
        pdf.output(str(file_path))
        logger.info(f"Generated PDF using fpdf2: {file_path}")
        return str(file_path), file_name

    async def _generate_markdown(self, project: Project, data: Dict[str, Any]) -> Tuple[str, str]:
        """Generate Markdown export."""
        md = self._generate_markdown_content(project, data)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = project.name.replace(" ", "_").lower()[:30]
        file_name = f"{safe_name}_export_{timestamp}.md"
        file_path = self.export_dir / file_name

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(md)

        return str(file_path), file_name

    async def _generate_zip(self, project: Project, data: Dict[str, Any]) -> Tuple[str, str]:
        """Generate ZIP archive with project files."""
        import zipfile
        from io import BytesIO

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = project.name.replace(" ", "_").lower()[:30]
        file_name = f"{safe_name}_project_{timestamp}.zip"
        file_path = self.export_dir / file_name

        with zipfile.ZipFile(file_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # Add README
            readme = self._generate_readme(project, data)
            zf.writestr("README.md", readme)

            # Add project.json with metadata
            zf.writestr("project.json", json.dumps(data["project"], indent=2))

            # Add tasks
            if "tasks" in data:
                tasks_md = self._generate_tasks_markdown(data["tasks"])
                zf.writestr("TASKS.md", tasks_md)

            # Add content files
            if "content" in data:
                for i, content in enumerate(data["content"]):
                    if "file_path" in content and content.get("content"):
                        # Use original path or create one
                        path = content["file_path"] or f"content/file_{i}.txt"
                        # Ensure path is relative
                        path = path.lstrip("/")
                        zf.writestr(f"src/{path}", content["content"])

            # Add conversations if included
            if "conversations" in data and data["conversations"]:
                conv_md = self._generate_conversations_markdown(data["conversations"])
                zf.writestr("CONVERSATIONS.md", conv_md)

        return str(file_path), file_name

    def _generate_html(self, project: Project, data: Dict[str, Any]) -> str:
        """Generate HTML for PDF conversion."""
        tasks_html = ""
        if "tasks" in data:
            tasks_html = "<h2>Tasks</h2><table><thead><tr><th>Title</th><th>Status</th><th>Assigned To</th></tr></thead><tbody>"
            for task in data["tasks"]:
                status_color = {"COMPLETED": "green", "IN_PROGRESS": "blue", "BLOCKED": "red"}.get(task["status"], "gray")
                tasks_html += f"""
                <tr>
                    <td>{task['title']}</td>
                    <td style="color: {status_color}">{task['status']}</td>
                    <td>{task['assigned_to'] or '-'}</td>
                </tr>
                """
            tasks_html += "</tbody></table>"

        metrics_html = ""
        if "metrics" in data:
            m = data["metrics"]
            metrics_html = f"""
            <h2>Metrics</h2>
            <ul>
                <li>Total Tasks: {m['total_tasks']}</li>
                <li>Completed: {m['completed_tasks']}</li>
                <li>Completion Rate: {m['completion_rate']:.1f}%</li>
            </ul>
            """

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{project.name} - Export</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 40px; max-width: 800px; margin: 0 auto; }}
                h1 {{ color: #1a1a1a; border-bottom: 2px solid #4f46e5; padding-bottom: 10px; }}
                h2 {{ color: #374151; margin-top: 30px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #e5e7eb; padding: 12px; text-align: left; }}
                th {{ background: #f9fafb; font-weight: 600; }}
                .meta {{ color: #6b7280; font-size: 0.9em; }}
                ul {{ list-style: none; padding: 0; }}
                li {{ padding: 8px 0; border-bottom: 1px solid #f3f4f6; }}
            </style>
        </head>
        <body>
            <h1>{project.name}</h1>
            <p class="meta">Exported on {data['exported_at'][:10]}</p>
            <p>{project.description or 'No description'}</p>
            <p><strong>Status:</strong> {project.status.value}</p>
            {metrics_html}
            {tasks_html}
        </body>
        </html>
        """

    def _generate_markdown_content(self, project: Project, data: Dict[str, Any]) -> str:
        """Generate Markdown content with full task details."""
        lines = [
            f"# {project.name}",
            "",
            f"> Exported on {data['exported_at'][:10]}",
            "",
            project.description or "_No description_",
            "",
            f"**Status:** {project.status.value}",
            "",
        ]

        # Metrics
        if "metrics" in data:
            m = data["metrics"]
            lines.extend([
                "---",
                "",
                "## Metrics",
                "",
                f"- **Total Tasks:** {m['total_tasks']}",
                f"- **Completed:** {m['completed_tasks']}",
                f"- **Completion Rate:** {m['completion_rate']:.1f}%",
                "",
            ])

        # Tasks - Full detail view
        if "tasks" in data and data["tasks"]:
            lines.extend([
                "---",
                "",
                "## Tasks",
                "",
            ])

            for i, task in enumerate(data["tasks"], 1):
                status_emoji = {
                    "COMPLETED": "✅",
                    "IN_PROGRESS": "🔄",
                    "BLOCKED": "❌",
                    "PENDING": "⏳",
                    "REVIEW": "👀",
                    "CANCELLED": "🚫",
                    "FAILED": "💥",
                }.get(task["status"], "❓")

                lines.extend([
                    f"### {i}. {task['title']}",
                    "",
                    f"**Status:** {status_emoji} {task['status']}",
                    "",
                ])

                if task.get("assigned_to"):
                    lines.append(f"**Assigned to:** {task['assigned_to']}")
                    lines.append("")

                if task.get("description"):
                    lines.extend([
                        "**Description:**",
                        "",
                        task["description"],
                        "",
                    ])

                # Output - Full content
                if task.get("output"):
                    lines.extend([
                        "#### Output",
                        "",
                    ])

                    output = task["output"]
                    if isinstance(output, dict):
                        # Handle answer field (common in CEO responses)
                        if "answer" in output:
                            lines.append(str(output["answer"]))
                            lines.append("")
                        # Handle result field
                        elif "result" in output:
                            lines.append(str(output["result"]))
                            lines.append("")
                        # Handle content field
                        elif "content" in output:
                            lines.append(str(output["content"]))
                            lines.append("")
                        # Handle analysis field
                        elif "analysis" in output:
                            lines.append(str(output["analysis"]))
                            lines.append("")
                        # Handle files_created
                        elif "files_created" in output:
                            for file_info in output["files_created"]:
                                file_path_str = file_info.get("path", "Unknown file")
                                lines.append(f"**File:** `{file_path_str}`")
                                lines.append("")
                                if file_info.get("content"):
                                    lines.append("```")
                                    lines.append(str(file_info["content"]))
                                    lines.append("```")
                                    lines.append("")
                        else:
                            # Show other fields nicely (skip metadata fields)
                            for key, value in output.items():
                                if key not in ["query_type", "answered_by", "can_continue"] and value:
                                    lines.append(f"**{key.replace('_', ' ').title()}:**")
                                    lines.append("")
                                    if isinstance(value, str):
                                        lines.append(value)
                                    else:
                                        lines.append(f"```json")
                                        lines.append(json.dumps(value, indent=2, default=str))
                                        lines.append("```")
                                    lines.append("")
                    else:
                        lines.append(str(output))
                        lines.append("")

                lines.extend([
                    "---",
                    "",
                ])

        # Content section (if included separately)
        if "content" in data and data["content"]:
            lines.extend([
                "## Generated Content",
                "",
            ])
            for content in data["content"]:
                lines.append(f"### {content.get('task_title', 'Generated Content')}")
                if content.get("file_path"):
                    lines.append(f"*File: `{content['file_path']}`*")
                lines.append("")
                if content.get("content"):
                    lines.append(str(content["content"]))
                lines.append("")

        # Conversations (if included)
        if "conversations" in data and data["conversations"]:
            lines.extend([
                "## Conversations",
                "",
            ])
            for conv in data["conversations"]:
                from_agent = conv.get("from", "Unknown")
                to_agent = conv.get("to", "Unknown")
                timestamp_str = conv.get("timestamp", "")[:16] if conv.get("timestamp") else ""
                lines.append(f"**{from_agent}** → **{to_agent}** ({timestamp_str})")
                lines.append("")
                if conv.get("content"):
                    lines.append(f"> {conv['content']}")
                lines.append("")

        # Footer
        lines.extend([
            "---",
            "",
            "*Generated by [Retinue](http://retinue.team/)*",
        ])

        return "\n".join(lines)

    def _generate_readme(self, project: Project, data: Dict[str, Any]) -> str:
        """Generate README.md for ZIP export."""
        return f"""# {project.name}

{project.description or '_No description_'}

## Project Info

- **Status:** {project.status.value}
- **Created:** {data['project'].get('created_at', 'Unknown')[:10] if data['project'].get('created_at') else 'Unknown'}
- **Exported:** {data['exported_at'][:10]}

## Contents

- `README.md` - This file
- `project.json` - Project metadata
- `TASKS.md` - Task list and details
- `src/` - Generated content and files

## Generated by Retinue

This project was managed and exported using [Retinue](http://retinue.team/).
"""

    def _generate_tasks_markdown(self, tasks: list) -> str:
        """Generate tasks markdown."""
        lines = ["# Tasks", ""]

        for task in tasks:
            status_emoji = {"COMPLETED": "✅", "IN_PROGRESS": "🔄", "BLOCKED": "❌", "PENDING": "⏳"}.get(task["status"], "❓")
            lines.extend([
                f"## {status_emoji} {task['title']}",
                "",
                f"**Status:** {task['status']} | **Assigned to:** {task.get('assigned_to', '-')}",
                "",
                task.get("description") or "_No description_",
                "",
            ])
            if task.get("actual_hours"):
                lines.append(f"**Time spent:** {task['actual_hours']} hours")
            lines.append("")

        return "\n".join(lines)

    def _generate_conversations_markdown(self, conversations: list) -> str:
        """Generate conversations markdown."""
        lines = ["# Conversations", ""]

        for conv in conversations:
            timestamp = conv.get("timestamp", "")[:16] if conv.get("timestamp") else ""
            lines.extend([
                f"**{conv.get('from', 'Unknown')}** → **{conv.get('to', 'Unknown')}** ({timestamp})",
                "",
                f"> {conv.get('content', '')}",
                "",
                "---",
                "",
            ])

        return "\n".join(lines)

    def cleanup_old_exports(self, hours: int = 24) -> int:
        """Clean up exports older than specified hours."""
        from datetime import timedelta
        import os

        cutoff = datetime.now() - timedelta(hours=hours)
        count = 0

        for file_path in self.export_dir.glob("*"):
            if file_path.is_file():
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mtime < cutoff:
                    try:
                        file_path.unlink()
                        count += 1
                    except OSError:
                        pass

        return count
