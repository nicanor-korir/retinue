"""Service for generating Markdown exports."""
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import yaml
import logging

logger = logging.getLogger(__name__)


class MarkdownGenerationService:
    """Generate professional Markdown documents from export data."""

    def __init__(self, templates_dir: Optional[Path] = None):
        """Initialize Markdown generation service.

        Args:
            templates_dir: Path to templates directory (for future use)
        """
        self.templates_dir = templates_dir

    async def generate_project_summary_markdown(
        self,
        data: Dict[str, Any],
        output_path: Path
    ) -> Path:
        """Generate project summary in Markdown."""
        content = self._build_project_summary(data)
        return await self._write_markdown_file(content, output_path)

    async def generate_full_documentation_markdown(
        self,
        data: Dict[str, Any],
        output_path: Path
    ) -> Path:
        """Generate full documentation in Markdown."""
        content = self._build_full_documentation(data)
        return await self._write_markdown_file(content, output_path)

    async def generate_task_report_markdown(
        self,
        data: Dict[str, Any],
        output_path: Path
    ) -> Path:
        """Generate task report in Markdown."""
        content = self._build_task_report(data)
        return await self._write_markdown_file(content, output_path)

    async def generate_agent_activity_report_markdown(
        self,
        data: Dict[str, Any],
        output_path: Path
    ) -> Path:
        """Generate agent activity report in Markdown."""
        content = self._build_agent_activity_report(data)
        return await self._write_markdown_file(content, output_path)

    async def generate_code_documentation_markdown(
        self,
        data: Dict[str, Any],
        output_path: Path
    ) -> Path:
        """Generate code documentation in Markdown."""
        content = self._build_code_documentation(data)
        return await self._write_markdown_file(content, output_path)

    async def generate_analytics_metrics_markdown(
        self,
        data: Dict[str, Any],
        output_path: Path
    ) -> Path:
        """Generate analytics and metrics in Markdown."""
        content = self._build_analytics_metrics(data)
        return await self._write_markdown_file(content, output_path)

    # ==================== Document Builders ====================

    def _build_project_summary(self, data: Dict[str, Any]) -> str:
        """Build project summary document."""
        parts = [
            self._create_frontmatter(data.get("project", {})),
            self._create_heading("Project Summary", 1),
            self._create_heading("Overview", 2),
            self._format_project_overview(data.get("overview", {})),
            self._create_heading("Agent Involvement", 2),
            self._format_agent_involvement(data.get("agent_involvement", [])),
            self._create_heading("Timeline", 2),
            self._format_timeline(data.get("timeline", [])),
            self._create_heading("Key Metrics", 2),
            self._format_metrics(data.get("key_metrics", {})),
            self._create_heading("Status Summary", 2),
            f"{data.get('status_summary', '')}\n",
            self._create_heading("Next Steps", 2),
            self._format_list(data.get("next_steps", [])),
        ]
        return "\n".join(parts)

    def _build_full_documentation(self, data: Dict[str, Any]) -> str:
        """Build full documentation document."""
        parts = [
            self._create_frontmatter(data.get("project", {})),
            self._create_heading("Full Project Documentation", 1),
            self._create_heading("Executive Summary", 2),
            self._format_project_overview(data.get("overview", {})),
            self._create_heading("Project Overview", 2),
            self._format_dict_as_list(data.get("overview", {})),
        ]

        # Add sections based on available data
        if data.get("agent_involvement"):
            parts.extend([
                self._create_heading("Agent Involvement", 2),
                self._format_agent_involvement(data.get("agent_involvement", [])),
            ])

        if data.get("tasks"):
            parts.extend([
                self._create_heading("Tasks", 2),
                self._format_tasks(data.get("tasks", [])),
            ])

        if data.get("agent_conversations"):
            parts.extend([
                self._create_heading("Agent Conversations", 2),
                self._format_conversations(data.get("agent_conversations", [])),
            ])

        if data.get("decisions"):
            parts.extend([
                self._create_heading("Decisions", 2),
                self._format_decisions(data.get("decisions", [])),
            ])

        if data.get("code_documentation"):
            parts.extend([
                self._create_heading("Code Documentation", 2),
                self._format_code_files(data.get("code_documentation", [])),
            ])

        if data.get("technical_specs"):
            parts.extend([
                self._create_heading("Technical Specifications", 2),
                self._format_dict_as_list(data.get("technical_specs", {})),
            ])

        if data.get("escalations"):
            parts.extend([
                self._create_heading("Escalations", 2),
                self._format_escalations(data.get("escalations", [])),
            ])

        # Add footer
        parts.append(self._create_footer())

        return "\n".join(parts)

    def _build_task_report(self, data: Dict[str, Any]) -> str:
        """Build task report document."""
        parts = [
            self._create_frontmatter(data.get("project", {})),
            self._create_heading("Task Report", 1),
            self._create_heading("Summary", 2),
            self._format_metrics(data.get("completion_metrics", {})),
            self._create_heading("All Tasks", 2),
            self._format_tasks(data.get("tasks", [])),
            self._create_heading("Task Timeline", 2),
            self._format_timeline(data.get("task_timeline", [])),
            self._create_heading("Dependencies", 2),
            self._format_dependencies(data.get("dependencies", [])),
            self._create_heading("Blockers", 2),
            self._format_blockers(data.get("blockers", [])),
            self._create_footer(),
        ]
        return "\n".join(parts)

    def _build_agent_activity_report(self, data: Dict[str, Any]) -> str:
        """Build agent activity report document."""
        parts = [
            self._create_frontmatter(data.get("project", {})),
            self._create_heading("Agent Activity Report", 1),
            self._create_heading("Agent Metrics", 2),
            self._format_agent_metrics(data.get("agent_metrics", [])),
            self._create_heading("LLM Usage", 2),
            self._format_dict_as_list(data.get("llm_usage", {})),
            self._create_heading("Activity Timeline", 2),
            self._format_agent_timeline(data.get("agent_timeline", [])),
            self._create_heading("Message Statistics", 2),
            self._format_dict_as_list(data.get("message_statistics", {})),
            self._create_heading("Task Breakdown", 2),
            self._format_dict_as_list(data.get("task_breakdown", {})),
            self._create_heading("Performance Metrics", 2),
            self._format_dict_as_list(data.get("performance_metrics", {})),
            self._create_footer(),
        ]
        return "\n".join(parts)

    def _build_code_documentation(self, data: Dict[str, Any]) -> str:
        """Build code documentation document."""
        parts = [
            self._create_frontmatter(data.get("project", {})),
            self._create_heading("Code Documentation", 1),
            self._create_heading("Project Structure", 2),
            self._format_project_structure(data.get("project_structure", {})),
            self._create_heading("Code Files", 2),
            self._format_code_files(data.get("code_files", [])),
            self._create_heading("API Documentation", 2),
            self._format_dict_as_list(data.get("api_documentation", {})),
            self._create_heading("Database Schema", 2),
            self._format_dict_as_list(data.get("database_schema", {})),
            self._create_heading("Configuration", 2),
            self._format_dict_as_list(data.get("configuration", {})),
            self._create_heading("Dependencies", 2),
            self._format_list(data.get("dependencies", [])),
            self._create_heading("Setup Instructions", 2),
            f"```\n{data.get('setup_instructions', '')}\n```\n",
            self._create_footer(),
        ]
        return "\n".join(parts)

    def _build_analytics_metrics(self, data: Dict[str, Any]) -> str:
        """Build analytics and metrics document."""
        parts = [
            self._create_frontmatter(data.get("project", {})),
            self._create_heading("Analytics & Metrics Report", 1),
            self._create_heading("Project Timeline", 2),
            self._format_timeline(data.get("timeline_visualization", [])),
            self._create_heading("Velocity Metrics", 2),
            self._format_dict_as_list(data.get("velocity_metrics", {})),
            self._create_heading("Agent Utilization", 2),
            self._format_agent_involvement(data.get("agent_utilization", {}).get("agents", [])),
            self._create_heading("Task Completion Trends", 2),
            self._format_list(data.get("task_completion_trends", [])),
            self._create_heading("Escalation Metrics", 2),
            self._format_dict_as_list(data.get("escalation_metrics", {})),
            self._create_heading("Quality Metrics", 2),
            self._format_dict_as_list(data.get("quality_metrics", {})),
            self._create_footer(),
        ]
        return "\n".join(parts)

    # ==================== Formatting Helpers ====================

    def _create_frontmatter(self, project: Dict[str, Any]) -> str:
        """Create YAML frontmatter."""
        frontmatter = {
            "title": project.get("name", "Project Export"),
            "description": project.get("description", ""),
            "status": project.get("status", ""),
            "priority": project.get("priority", ""),
            "created_at": project.get("created_at", ""),
            "completed_at": project.get("completed_at", ""),
            "generated_by": "Retinue",
            "generated_at": datetime.now().isoformat(),
        }
        yaml_content = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
        return f"---\n{yaml_content}---\n"

    def _create_heading(self, text: str, level: int = 2) -> str:
        """Create a Markdown heading."""
        return f"{'#' * level} {text}\n"

    def _create_footer(self) -> str:
        """Create document footer."""
        return f"\n---\n\n*Document generated on {datetime.now().strftime('%B %d, %Y at %H:%M')} by Retinue*"

    def _format_project_overview(self, overview: Dict[str, Any]) -> str:
        """Format project overview."""
        return self._format_dict_as_list(overview)

    def _format_agent_involvement(self, agents: List[Dict[str, Any]]) -> str:
        """Format agent involvement as a table."""
        if not agents:
            return "No agents involved.\n"

        lines = [
            "| Agent Name | Role | Tasks Assigned |",
            "|-----------|------|----------------|",
        ]
        for agent in agents:
            lines.append(
                f"| {agent.get('agent_name', '')} | {agent.get('role', '')} | {agent.get('tasks_assigned', 0)} |"
            )
        return "\n".join(lines) + "\n"

    def _format_timeline(self, timeline: List[Dict[str, Any]]) -> str:
        """Format timeline events."""
        if not timeline:
            return "No timeline events.\n"

        lines = []
        for event in timeline:
            timestamp = event.get("timestamp", "")
            title = event.get("title", "")
            lines.append(f"- **{timestamp}**: {title}")
        return "\n".join(lines) + "\n"

    def _format_metrics(self, metrics: Dict[str, Any]) -> str:
        """Format metrics as a list."""
        return self._format_dict_as_list(metrics)

    def _format_list(self, items: List[str]) -> str:
        """Format a simple list."""
        if not items:
            return "No items.\n"
        return "\n".join([f"- {item}" for item in items]) + "\n"

    def _format_tasks(self, tasks: List[Dict[str, Any]]) -> str:
        """Format tasks as a table."""
        if not tasks:
            return "No tasks.\n"

        lines = [
            "| Task | Status | Assigned To | Est. Hours |",
            "|------|--------|-------------|------------|",
        ]
        for task in tasks:
            lines.append(
                f"| {task.get('title', '')} | {task.get('status', '')} | "
                f"{task.get('assigned_to', '')} | {task.get('estimated_hours', '')} |"
            )
        return "\n".join(lines) + "\n"

    def _format_conversations(self, messages: List[Dict[str, Any]]) -> str:
        """Format agent conversations."""
        if not messages:
            return "No conversations.\n"

        lines = []
        for msg in messages:
            from_agent = msg.get("from_agent", "Unknown")
            to_agent = msg.get("to_agent", "Unknown")
            content = msg.get("content", "")[:100] + "..." if len(msg.get("content", "")) > 100 else msg.get("content", "")
            lines.append(f"**{from_agent} → {to_agent}**: {content}")
        return "\n".join(lines) + "\n"

    def _format_decisions(self, decisions: List[Dict[str, Any]]) -> str:
        """Format decisions made."""
        if not decisions:
            return "No decisions recorded.\n"

        lines = []
        for decision in decisions:
            question = decision.get("question", "")
            decision_text = decision.get("decision", "")
            lines.append(f"**Q**: {question}")
            lines.append(f"**A**: {decision_text}\n")
        return "\n".join(lines) + "\n"

    def _format_code_files(self, code_files: List[Dict[str, Any]]) -> str:
        """Format code files."""
        if not code_files:
            return "No code files.\n"

        lines = []
        for idx, file_info in enumerate(code_files, 1):
            title = file_info.get("title", f"File {idx}")
            content = file_info.get("content", "")
            language = file_info.get("language", "")
            lines.append(f"### {title}\n")
            lines.append(f"```{language}\n{content}\n```\n")
        return "\n".join(lines) + "\n"

    def _format_escalations(self, escalations: List[Dict[str, Any]]) -> str:
        """Format escalations."""
        if not escalations:
            return "No escalations.\n"

        lines = [
            "| ID | Type | Priority | Status | Created |",
            "|----|----|----------|--------|---------|",
        ]
        for escalation in escalations:
            lines.append(
                f"| {escalation.get('id', '')[:8]} | {escalation.get('type', '')} | "
                f"{escalation.get('priority', '')} | {escalation.get('status', '')} | "
                f"{escalation.get('created_at', '')} |"
            )
        return "\n".join(lines) + "\n"

    def _format_dependencies(self, dependencies: List[Dict[str, Any]]) -> str:
        """Format task dependencies."""
        if not dependencies:
            return "No task dependencies.\n"

        lines = []
        for dep in dependencies:
            task = dep.get("task_title", "Unknown")
            deps = dep.get("dependencies", [])
            if deps:
                lines.append(f"- **{task}** depends on: {', '.join(str(d) for d in deps)}")
        return "\n".join(lines) + "\n" if lines else "No task dependencies.\n"

    def _format_blockers(self, blockers: List[Dict[str, Any]]) -> str:
        """Format blocked tasks."""
        if not blockers:
            return "No blocked tasks.\n"

        lines = []
        for blocker in blockers:
            task = blocker.get("task_title", "Unknown")
            reason = blocker.get("blocking_reason", "Not specified")
            lines.append(f"- **{task}**: {reason}")
        return "\n".join(lines) + "\n"

    def _format_agent_metrics(self, metrics: List[Dict[str, Any]]) -> str:
        """Format agent metrics."""
        if not metrics:
            return "No agent metrics.\n"

        lines = [
            "| Agent | Tasks Completed | Success Rate | Active Time (min) |",
            "|-------|-----------------|---------------|--------------------|",
        ]
        for metric in metrics:
            lines.append(
                f"| {metric.get('agent_id', '')} | {metric.get('tasks_completed', 0)} | "
                f"{metric.get('success_rate', 0):.1f}% | {metric.get('active_time_minutes', 0)} |"
            )
        return "\n".join(lines) + "\n"

    def _format_agent_timeline(self, timeline: List[Dict[str, Any]]) -> str:
        """Format agent activity timeline."""
        if not timeline:
            return "No agent activity.\n"

        lines = []
        for activity in timeline:
            agent = activity.get("agent_id", "Unknown")
            activity_type = activity.get("activity_type", "")
            progress = activity.get("progress", 0)
            lines.append(f"- **{agent}** ({activity_type}): {progress}% complete")
        return "\n".join(lines) + "\n"

    def _format_project_structure(self, structure: Dict[str, Any]) -> str:
        """Format project structure."""
        if not structure:
            return "No structure information.\n"

        lines = []

        def format_tree(obj, prefix=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    lines.append(f"{prefix}{key}/")
                    format_tree(value, prefix + "  ")
            elif isinstance(obj, list):
                for item in obj:
                    lines.append(f"{prefix}{item}")

        format_tree(structure.get("structure", {}))
        return "\n".join(lines) + "\n" if lines else "Empty structure.\n"

    def _format_dict_as_list(self, data: Dict[str, Any]) -> str:
        """Format dictionary as a list."""
        if not data:
            return "No data.\n"

        lines = []
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"- **{key}**: {str(value)}")
            elif isinstance(value, list):
                lines.append(f"- **{key}**: {', '.join(str(v) for v in value)}")
            else:
                lines.append(f"- **{key}**: {value}")
        return "\n".join(lines) + "\n"

    async def _write_markdown_file(self, content: str, output_path: Path) -> Path:
        """Write Markdown content to file."""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Markdown file generated successfully: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error writing Markdown file: {e}")
            raise
