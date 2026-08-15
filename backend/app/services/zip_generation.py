"""Service for generating ZIP exports of projects with all files and documentation."""
import io
import json
import zipfile
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import Project, Task
from app.services.readme_generator import ReadmeGenerator
from app.services.gitignore_generator import GitignoreGenerator
from app.services.env_example_generator import EnvExampleGenerator

logger = logging.getLogger(__name__)


class ZIPGenerationService:
    """Service for creating ZIP archives of project files."""

    def __init__(self, session: AsyncSession):
        """Initialize ZIP generation service.

        Args:
            session: Database session for fetching project data
        """
        self.session = session
        self.readme_generator = ReadmeGenerator()
        self.gitignore_generator = GitignoreGenerator()
        self.env_generator = EnvExampleGenerator()

    async def generate_project_zip(
        self,
        project_id: UUID,
        zip_options: Dict[str, Any],
    ) -> Tuple[bytes, str]:
        """Generate a ZIP archive of the project.

        Args:
            project_id: Project to export
            zip_options: Options for ZIP generation (which files to include, etc.)

        Returns:
            Tuple of (zip_bytes, filename)

        Raises:
            ValueError: If project not found or has invalid data
        """
        try:
            # Fetch project data
            stmt = select(Project).where(Project.project_id == project_id)
            result = await self.session.execute(stmt)
            project = result.scalar_one_or_none()

            if not project:
                raise ValueError(f"Project {project_id} not found")

            # Create ZIP archive in memory
            zip_buffer = io.BytesIO()

            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Generate and add auto-generated files
                await self._add_auto_generated_files(
                    zip_file, project, zip_options
                )

                # Add project files from tasks
                if zip_options.get("include_source_code", True):
                    await self._add_project_files(zip_file, project)

                # Add Deviant metadata
                if zip_options.get("include_Deviant_metadata", True):
                    await self._add_Deviant_metadata(zip_file, project)

            zip_buffer.seek(0)
            filename = self._generate_zip_filename(project)

            return zip_buffer.getvalue(), filename

        except Exception as e:
            logger.error(f"Error generating ZIP for project {project_id}: {e}")
            raise

    async def _add_auto_generated_files(
        self,
        zip_file: zipfile.ZipFile,
        project: Project,
        options: Dict[str, Any],
    ) -> None:
        """Add auto-generated files to ZIP.

        Args:
            zip_file: ZIP file object to add files to
            project: Project data
            options: Export options
        """
        # Detect tech stack from tasks
        tech_stack = await self._detect_tech_stack(project)

        # Generate and add README.md
        readme_content = self.readme_generator.generate(
            project=project,
            tech_stack=tech_stack,
            documentation_level=options.get("documentation_level", "standard"),
        )
        zip_file.writestr("README.md", readme_content)

        # Generate and add .gitignore
        if tech_stack:
            gitignore_content = self.gitignore_generator.generate(tech_stack)
            zip_file.writestr(".gitignore", gitignore_content)

        # Generate and add .env.example
        if options.get("include_env_example", True):
            env_example = await self.env_generator.generate(project)
            if env_example:
                zip_file.writestr(".env.example", env_example)

        # Add LICENSE file if available
        if hasattr(project, "meta_data") and project.meta_data:
            license_text = project.meta_data.get("license_text")
            if license_text:
                zip_file.writestr("LICENSE", license_text)

    async def _add_project_files(
        self,
        zip_file: zipfile.ZipFile,
        project: Project,
    ) -> None:
        """Add project source code files to ZIP.

        Args:
            zip_file: ZIP file object to add files to
            project: Project data
        """
        try:
            # Fetch all tasks for the project
            stmt = select(Task).where(Task.project_id == project.project_id)
            result = await self.session.execute(stmt)
            tasks = result.scalars().all()

            for task in tasks:
                if not task.output:
                    continue

                output = task.output if isinstance(task.output, dict) else {}

                # Extract code files from task output
                code_files = output.get("files_created", [])
                if isinstance(code_files, str):
                    try:
                        code_files = json.loads(code_files)
                    except (json.JSONDecodeError, TypeError):
                        code_files = []

                for file_info in code_files:
                    if isinstance(file_info, dict):
                        file_path = file_info.get("path")
                        file_content = file_info.get("content")
                    else:
                        # String path
                        file_path = file_info
                        file_content = output.get(f"content_{file_path}")

                    if file_path and file_content:
                        # Clean path (remove leading slashes, resolve relative paths)
                        clean_path = str(file_path).lstrip("/").lstrip("\\")

                        # Add to ZIP under src directory
                        zip_path = f"src/{clean_path}"
                        zip_file.writestr(zip_path, file_content)
                        logger.info(f"Added file to ZIP: {zip_path}")

                # Extract code_generated as well
                if output.get("code_generated"):
                    code_content = output.get("code_generated")
                    # Infer file type from task title
                    file_ext = self._infer_file_extension(task.title)
                    if not file_ext:
                        file_ext = ".py"  # Default to Python

                    filename = f"src/{task.title.replace(' ', '_')}{file_ext}"
                    zip_file.writestr(filename, code_content)
                    logger.info(f"Added generated code to ZIP: {filename}")

        except Exception as e:
            logger.error(f"Error adding project files to ZIP: {e}")
            # Don't fail the entire export if file adding fails
            pass

    async def _add_Deviant_metadata(
        self,
        zip_file: zipfile.ZipFile,
        project: Project,
    ) -> None:
        """Add Deviant metadata files to ZIP.

        Args:
            zip_file: ZIP file object to add files to
            project: Project data
        """
        try:
            # Create Deviant directory
            metadata_dir = "Deviant"

            # Add project info
            project_info = {
                "name": project.name,
                "description": project.description,
                "status": project.status.value if hasattr(project.status, 'value') else str(project.status),
                "priority": project.priority.value if hasattr(project.priority, 'value') else str(project.priority),
                "created_at": project.created_at.isoformat() if project.created_at else None,
                "updated_at": project.updated_at.isoformat() if project.updated_at else None,
                "completed_at": project.completed_at.isoformat() if project.completed_at else None,
                "owner_agent_id": project.owner_agent_id,
                "version": project.version,
                "agent_days_elapsed": project.agent_days_elapsed,
            }
            zip_file.writestr(
                f"{metadata_dir}/project_info.json",
                json.dumps(project_info, indent=2),
            )

            # Add tasks info
            stmt = select(Task).where(Task.project_id == project.project_id)
            result = await self.session.execute(stmt)
            tasks = result.scalars().all()

            tasks_info = {
                "total": len(tasks),
                "tasks": [
                    {
                        "title": task.title,
                        "status": task.status.value if hasattr(task.status, 'value') else str(task.status),
                        "assigned_to": task.assigned_to_agent_id,
                        "created_at": task.created_at.isoformat() if task.created_at else None,
                        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
                        "estimated_hours": task.estimated_hours,
                        "actual_hours": task.actual_hours,
                    }
                    for task in tasks
                ]
            }
            zip_file.writestr(
                f"{metadata_dir}/tasks.json",
                json.dumps(tasks_info, indent=2),
            )

            logger.info(f"Added Deviant metadata to ZIP: {len(tasks)} tasks")

        except Exception as e:
            logger.error(f"Error adding Deviant metadata to ZIP: {e}")
            # Don't fail the entire export if metadata adding fails
            pass

    async def _detect_tech_stack(self, project: Project) -> List[str]:
        """Detect technology stack from project tasks.

        Args:
            project: Project to analyze

        Returns:
            List of detected technologies
        """
        try:
            stmt = select(Task).where(Task.project_id == project.project_id)
            result = await self.session.execute(stmt)
            tasks = result.scalars().all()

            tech_stack = set()
            keywords = {
                "python": ["python", "flask", "django", "fastapi"],
                "nodejs": ["node", "javascript", "typescript", "react", "next.js", "express"],
                "rust": ["rust", "cargo"],
                "java": ["java", "maven", "gradle", "spring"],
                "ruby": ["ruby", "rails"],
                "go": ["go", "golang"],
                "docker": ["docker", "dockerfile"],
                "kubernetes": ["kubernetes", "k8s"],
                "postgresql": ["postgresql", "postgres", "sql"],
                "mongodb": ["mongodb", "mongo"],
                "redis": ["redis"],
            }

            for task in tasks:
                task_text = f"{task.title} {task.description or ''}".lower()
                for tech, keywords_list in keywords.items():
                    if any(kw in task_text for kw in keywords_list):
                        tech_stack.add(tech)

            return list(tech_stack)

        except Exception as e:
            logger.error(f"Error detecting tech stack: {e}")
            return []

    def _infer_file_extension(self, filename: str) -> str:
        """Infer file extension from filename/task title.

        Args:
            filename: Filename or task title

        Returns:
            File extension (e.g., '.py', '.js') or empty string
        """
        name_lower = filename.lower()

        extensions = {
            "python": ".py",
            "javascript": ".js",
            "typescript": ".ts",
            "react": ".jsx",
            "java": ".java",
            "cpp": ".cpp",
            "c++": ".cpp",
            "golang": ".go",
            "go": ".go",
            "rust": ".rs",
            "ruby": ".rb",
            "php": ".php",
            "sql": ".sql",
            "html": ".html",
            "css": ".css",
            "json": ".json",
            "yaml": ".yaml",
            "yml": ".yml",
        }

        for lang, ext in extensions.items():
            if lang in name_lower:
                return ext

        return ""

    def _generate_zip_filename(self, project: Project) -> str:
        """Generate ZIP filename based on project.

        Args:
            project: Project data

        Returns:
            Filename for the ZIP archive
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        project_name = project.name.replace(" ", "_").replace("/", "_").replace("\\", "_")
        return f"{project_name}_project_{timestamp}.zip"
