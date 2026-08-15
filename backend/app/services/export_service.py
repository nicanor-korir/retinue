"""Main export service orchestrating PDF and Markdown generation."""
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from uuid import UUID
import hashlib
import tempfile
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
import logging

from app.db.export_models import (
    ExportJob, ExportStatus, ExportFormat, ExportType,
    ExportCache
)
from app.services.export_data_service import ExportDataService
from app.services.pdf_generation import PDFGenerationService
from app.services.markdown_generation import MarkdownGenerationService
from app.services.zip_generation import ZIPGenerationService

logger = logging.getLogger(__name__)


class ExportService:
    """Main service for coordinating export operations."""

    def __init__(
        self,
        session: AsyncSession,
        temp_dir: Optional[Path] = None,
    ):
        """Initialize export service.

        Args:
            session: Database session
            temp_dir: Temporary directory for file storage (defaults to system temp)
        """
        self.session = session
        self.temp_dir = temp_dir or Path(tempfile.gettempdir()) / "retinue_exports"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # Set up templates directory
        templates_pdf_dir = Path(__file__).parent.parent / "templates" / "pdf"
        templates_md_dir = Path(__file__).parent.parent / "templates" / "markdown"

        self.data_service = ExportDataService(session)
        self.pdf_service = PDFGenerationService(templates_dir=templates_pdf_dir)
        self.markdown_service = MarkdownGenerationService(templates_dir=templates_md_dir)
        self.zip_service = ZIPGenerationService(session)

    async def create_export_job(
        self,
        project_id: UUID,
        export_format: ExportFormat,
        export_type: ExportType,
        options: Dict[str, Any],
        created_by_agent_id: Optional[str] = None,
    ) -> ExportJob:
        """Create a new export job.

        Args:
            project_id: Project to export
            export_format: PDF or Markdown
            export_type: Type of export
            options: Custom export options
            created_by_agent_id: Agent requesting the export

        Returns:
            Created ExportJob instance
        """
        job = ExportJob(
            project_id=project_id,
            export_format=export_format,
            export_type=export_type,
            status=ExportStatus.PENDING,
            options=options,
            created_by_agent_id=created_by_agent_id,
        )

        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)

        logger.info(f"Created export job {job.job_id} for project {project_id}")
        return job

    async def process_export_job(
        self,
        job_id: UUID,
        progress_callback: Optional[callable] = None,
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Process an export job.

        Args:
            job_id: ID of the export job to process
            progress_callback: Optional callback for progress updates (step, percentage)

        Returns:
            Tuple of (success, file_path, error_message)
        """
        job = await self.session.get(ExportJob, job_id)
        if not job:
            logger.error(f"Export job {job_id} not found")
            return False, None, "Export job not found"

        try:
            # Check cache
            cached_file = await self._check_cache(job)
            if cached_file:
                logger.info(f"Using cached export for job {job_id}")
                job.status = ExportStatus.COMPLETED
                job.file_path = str(cached_file)
                job.file_name = cached_file.name
                job.file_size_bytes = cached_file.stat().st_size
                job.is_cached = True
                job.completed_at = datetime.now()
                await self.session.commit()
                return True, str(cached_file), None

            # Update status to gathering data
            job.status = ExportStatus.GATHERING_DATA
            await self.session.commit()
            if progress_callback:
                progress_callback("Gathering data", 10)

            # Collect data based on export type
            data = await self._collect_export_data(job.export_type, job.project_id)
            if progress_callback:
                progress_callback("Collected data", 30)

            # Generate file
            job.status = ExportStatus.RENDERING
            await self.session.commit()
            if progress_callback:
                progress_callback("Rendering", 50)

            file_path = await self._generate_export_file(
                job,
                data,
                progress_callback
            )

            if not file_path:
                raise Exception("Failed to generate export file")

            # Calculate content hash for caching
            data_hash = await self._calculate_content_hash(data)

            # Update job with results
            job.status = ExportStatus.COMPLETED
            job.file_path = str(file_path)
            job.file_name = file_path.name
            job.file_size_bytes = file_path.stat().st_size
            job.completed_at = datetime.now()
            job.data_hash = data_hash
            job.progress_percentage = 100
            await self.session.commit()

            # Cache the file
            await self._cache_export(job, data_hash)

            logger.info(f"Export job {job_id} completed successfully")
            return True, str(file_path), None

        except Exception as e:
            logger.error(f"Error processing export job {job_id}: {e}")
            job.status = ExportStatus.FAILED
            job.error_message = str(e)
            job.error_details = {"exception_type": type(e).__name__}
            await self.session.commit()
            return False, None, str(e)

    async def _collect_export_data(
        self,
        export_type: ExportType,
        project_id: UUID,
    ) -> Dict[str, Any]:
        """Collect data based on export type.

        Args:
            export_type: Type of export
            project_id: Project ID

        Returns:
            Dictionary of collected data
        """
        if export_type == ExportType.PROJECT_SUMMARY:
            return await self.data_service.collect_project_summary(project_id)
        elif export_type == ExportType.FULL_DOCUMENTATION:
            return await self.data_service.collect_full_documentation(project_id)
        elif export_type == ExportType.TASK_REPORT:
            return await self.data_service.collect_task_report(project_id)
        elif export_type == ExportType.AGENT_ACTIVITY_REPORT:
            return await self.data_service.collect_agent_activity_report(project_id)
        elif export_type == ExportType.CODE_DOCUMENTATION:
            return await self.data_service.collect_code_documentation(project_id)
        elif export_type == ExportType.ANALYTICS_METRICS:
            return await self.data_service.collect_analytics_metrics(project_id)
        else:
            raise ValueError(f"Unknown export type: {export_type}")

    async def _generate_export_file(
        self,
        job: ExportJob,
        data: Dict[str, Any],
        progress_callback: Optional[callable] = None,
    ) -> Optional[Path]:
        """Generate export file (PDF or Markdown).

        Args:
            job: Export job
            data: Data to export
            progress_callback: Progress callback

        Returns:
            Path to generated file, or None if failed
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_name = data.get("project", {}).get("name", "project").replace(" ", "_").lower()
        export_type_name = job.export_type.value

        if job.export_format == ExportFormat.PDF:
            file_name = f"{project_name}_{export_type_name}_{timestamp}.pdf"
            file_path = self.temp_dir / file_name

            if progress_callback:
                progress_callback("Generating PDF", 70)

            try:
                if job.export_type == ExportType.PROJECT_SUMMARY:
                    await self.pdf_service.generate_project_summary_pdf(data, file_path)
                elif job.export_type == ExportType.FULL_DOCUMENTATION:
                    await self.pdf_service.generate_full_documentation_pdf(data, file_path)
                elif job.export_type == ExportType.TASK_REPORT:
                    await self.pdf_service.generate_task_report_pdf(data, file_path)
                elif job.export_type == ExportType.AGENT_ACTIVITY_REPORT:
                    await self.pdf_service.generate_agent_activity_report_pdf(data, file_path)
                elif job.export_type == ExportType.CODE_DOCUMENTATION:
                    await self.pdf_service.generate_code_documentation_pdf(data, file_path)
                elif job.export_type == ExportType.ANALYTICS_METRICS:
                    await self.pdf_service.generate_analytics_metrics_pdf(data, file_path)

                if progress_callback:
                    progress_callback("PDF generated", 90)

                return file_path

            except Exception as e:
                logger.error(f"Error generating PDF: {e}")
                raise

        elif job.export_format == ExportFormat.MARKDOWN:
            file_name = f"{project_name}_{export_type_name}_{timestamp}.md"
            file_path = self.temp_dir / file_name

            if progress_callback:
                progress_callback("Generating Markdown", 70)

            try:
                if job.export_type == ExportType.PROJECT_SUMMARY:
                    await self.markdown_service.generate_project_summary_markdown(data, file_path)
                elif job.export_type == ExportType.FULL_DOCUMENTATION:
                    await self.markdown_service.generate_full_documentation_markdown(data, file_path)
                elif job.export_type == ExportType.TASK_REPORT:
                    await self.markdown_service.generate_task_report_markdown(data, file_path)
                elif job.export_type == ExportType.AGENT_ACTIVITY_REPORT:
                    await self.markdown_service.generate_agent_activity_report_markdown(data, file_path)
                elif job.export_type == ExportType.CODE_DOCUMENTATION:
                    await self.markdown_service.generate_code_documentation_markdown(data, file_path)
                elif job.export_type == ExportType.ANALYTICS_METRICS:
                    await self.markdown_service.generate_analytics_metrics_markdown(data, file_path)

                if progress_callback:
                    progress_callback("Markdown generated", 90)

                return file_path

            except Exception as e:
                logger.error(f"Error generating Markdown: {e}")
                raise

        elif job.export_format == ExportFormat.ZIP:
            file_name = None
            if progress_callback:
                progress_callback("Generating ZIP archive", 70)

            try:
                if job.export_type == ExportType.PROJECT_FILES_ZIP:
                    zip_bytes, zip_filename = await self.zip_service.generate_project_zip(
                        job.project_id,
                        job.options
                    )
                    file_name = zip_filename
                    file_path = self.temp_dir / zip_filename

                    # Write ZIP bytes to file
                    with open(file_path, 'wb') as f:
                        f.write(zip_bytes)

                    if progress_callback:
                        progress_callback("ZIP archive created", 90)

                    return file_path
                else:
                    raise ValueError(f"Unsupported ZIP export type: {job.export_type}")

            except Exception as e:
                logger.error(f"Error generating ZIP: {e}")
                raise

        return None

    async def _check_cache(self, job: ExportJob) -> Optional[Path]:
        """Check if an export is already cached.

        Args:
            job: Export job

        Returns:
            Path to cached file if exists and valid, None otherwise
        """
        # Calculate content hash for current data
        data = await self._collect_export_data(job.export_type, job.project_id)
        data_hash = await self._calculate_content_hash(data)

        # Check cache table
        query = select(ExportCache).where(
            (ExportCache.data_hash == data_hash) &
            (ExportCache.project_id == job.project_id) &
            (ExportCache.export_format == job.export_format) &
            (ExportCache.export_type == job.export_type) &
            (ExportCache.expires_at > datetime.now())
        )

        result = await self.session.execute(query)
        cache_entry = result.scalars().first()

        if cache_entry and Path(cache_entry.file_path).exists():
            # Update hit count
            cache_entry.hit_count += 1
            await self.session.commit()
            return Path(cache_entry.file_path)

        return None

    async def _cache_export(self, job: ExportJob, data_hash: str) -> None:
        """Cache generated export file.

        Args:
            job: Export job
            data_hash: SHA256 hash of content
        """
        try:
            # Check if cache entry already exists
            query = select(ExportCache).where(ExportCache.data_hash == data_hash)
            result = await self.session.execute(query)
            existing_cache = result.scalars().first()

            if existing_cache:
                # Update existing cache entry
                existing_cache.file_path = job.file_path
                existing_cache.file_size_bytes = job.file_size_bytes
                existing_cache.expires_at = datetime.now() + timedelta(hours=1)
                existing_cache.hit_count += 1
                logger.info(f"Updated existing cache entry for job {job.job_id}")
            else:
                # Create new cache entry
                cache_entry = ExportCache(
                    data_hash=data_hash,
                    project_id=job.project_id,
                    export_format=job.export_format,
                    export_type=job.export_type,
                    file_path=job.file_path,
                    file_size_bytes=job.file_size_bytes,
                    expires_at=datetime.now() + timedelta(hours=1),
                    original_job_id=job.job_id,
                )
                self.session.add(cache_entry)
                logger.info(f"Cached export for job {job.job_id}")

            await self.session.commit()

        except Exception as e:
            logger.warning(f"Failed to cache export: {e}")
            # Rollback on error to prevent session issues
            await self.session.rollback()

    async def _calculate_content_hash(self, data: Dict[str, Any]) -> str:
        """Calculate SHA256 hash of content for caching.

        Args:
            data: Data to hash

        Returns:
            SHA256 hash string
        """
        import json
        content_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(content_str.encode()).hexdigest()

    async def get_export_job(self, job_id: UUID) -> Optional[ExportJob]:
        """Get export job by ID.

        Args:
            job_id: Job ID

        Returns:
            ExportJob or None
        """
        return await self.session.get(ExportJob, job_id)

    async def cleanup_old_exports(self, hours: int = 24) -> int:
        """Clean up temporary export files older than specified hours.

        Args:
            hours: Hours to keep files

        Returns:
            Number of files deleted
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        count = 0

        try:
            # Delete from cache
            query = delete(ExportCache).where(ExportCache.expires_at < datetime.now())
            result = await self.session.execute(query)
            await self.session.commit()

            # Delete old temporary files
            for file_path in self.temp_dir.glob("*"):
                if file_path.is_file():
                    stat = file_path.stat()
                    file_time = datetime.fromtimestamp(stat.st_mtime)
                    if file_time < cutoff_time:
                        file_path.unlink()
                        count += 1

            logger.info(f"Cleaned up {count} old export files")
            return count

        except Exception as e:
            logger.error(f"Error cleaning up exports: {e}")
            return 0

