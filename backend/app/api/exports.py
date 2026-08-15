"""API routes for export and deployment functionality."""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID
import logging
import asyncio
import json

from app.db.database import get_session
from app.db.export_models import ExportFormat, ExportType
from app.services.export_service import ExportService
from app.services.export_content_analyzer import ExportContentAnalyzer
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["exports"])


# ==================== Pydantic Models ====================

class ExportOptions(BaseModel):
    """Export options for customization."""
    export_type: str  # 'project_summary', 'full_documentation', etc.
    export_format: str  # 'pdf' or 'markdown'
    include_sections: Optional[list[str]] = None
    syntax_theme: Optional[str] = "light"  # 'light' or 'dark'
    include_code: Optional[bool] = True
    include_images: Optional[bool] = True
    include_conversations: Optional[bool] = True
    date_range: Optional[Dict[str, str]] = None


class ExportJobResponse(BaseModel):
    """Response model for export job."""
    job_id: str
    project_id: str
    export_format: str
    export_type: str
    status: str
    progress_percentage: int
    current_step: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None
    file_size_bytes: Optional[int] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class ExportResponse(BaseModel):
    """Response for successful export creation."""
    job_id: str
    status: str
    message: str


class ContentAvailability(BaseModel):
    """Response model for content availability analysis."""
    available_export_types: list[str]
    content_flags: Dict[str, bool]
    recommendations: Dict[str, Any]


# ==================== Helper Functions ====================

async def get_export_service(session: AsyncSession = Depends(get_session)) -> ExportService:
    """Dependency to get export service."""
    return ExportService(session)


async def get_content_analyzer(session: AsyncSession = Depends(get_session)) -> ExportContentAnalyzer:
    """Dependency to get content analyzer."""
    return ExportContentAnalyzer(session)


# ==================== Export Endpoints ====================

@router.get("/projects/{project_id}/export-availability", response_model=ContentAvailability)
async def get_export_availability(
    project_id: UUID,
    content_analyzer: ExportContentAnalyzer = Depends(get_content_analyzer),
) -> Dict[str, Any]:
    """Analyze project content and determine available export options.

    This endpoint analyzes what content exists in the project and returns:
    - Which export types are relevant
    - Boolean flags for different content types
    - Recommendations for unavailable exports

    Args:
        project_id: Project to analyze
        content_analyzer: Content analyzer service

    Returns:
        Content availability analysis with recommendations
    """
    try:
        analysis = await content_analyzer.analyze_project_content(project_id)
        return analysis
    except Exception as e:
        logger.error(f"Error analyzing export availability: {e}")
        raise HTTPException(status_code=500, detail=f"Error analyzing export availability: {e}")


@router.post("/projects/{project_id}/export/pdf", response_model=ExportResponse)
async def export_project_as_pdf(
    project_id: UUID,
    options: ExportOptions,
    background_tasks: BackgroundTasks,
    export_service: ExportService = Depends(get_export_service),
    agent_id: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Create a PDF export of a project.

    Args:
        project_id: Project to export
        options: Export options
        background_tasks: FastAPI background tasks
        export_service: Export service
        agent_id: Optional agent requesting the export

    Returns:
        Job ID and status
    """
    try:
        # Map string to enum
        export_type = ExportType(options.export_type)
        export_format = ExportFormat.PDF

        # Create export job
        job = await export_service.create_export_job(
            project_id=project_id,
            export_format=export_format,
            export_type=export_type,
            options=options.dict(),
            created_by_agent_id=agent_id,
        )

        # Process in background
        background_tasks.add_task(
            export_service.process_export_job,
            job.job_id,
        )

        logger.info(f"Created PDF export job {job.job_id}")

        return {
            "job_id": str(job.job_id),
            "status": "pending",
            "message": "Export job created. Processing in background.",
        }

    except ValueError as e:
        logger.error(f"Invalid export options: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid export options: {e}")
    except Exception as e:
        logger.error(f"Error creating export: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating export: {e}")


@router.post("/projects/{project_id}/export/markdown", response_model=ExportResponse)
async def export_project_as_markdown(
    project_id: UUID,
    options: ExportOptions,
    background_tasks: BackgroundTasks,
    export_service: ExportService = Depends(get_export_service),
    agent_id: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Create a Markdown export of a project.

    Args:
        project_id: Project to export
        options: Export options
        background_tasks: FastAPI background tasks
        export_service: Export service
        agent_id: Optional agent requesting the export

    Returns:
        Job ID and status
    """
    try:
        # Map string to enum
        export_type = ExportType(options.export_type)
        export_format = ExportFormat.MARKDOWN

        # Create export job
        job = await export_service.create_export_job(
            project_id=project_id,
            export_format=export_format,
            export_type=export_type,
            options=options.dict(),
            created_by_agent_id=agent_id,
        )

        # Process in background
        background_tasks.add_task(
            export_service.process_export_job,
            job.job_id,
        )

        logger.info(f"Created Markdown export job {job.job_id}")

        return {
            "job_id": str(job.job_id),
            "status": "pending",
            "message": "Export job created. Processing in background.",
        }

    except ValueError as e:
        logger.error(f"Invalid export options: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid export options: {e}")
    except Exception as e:
        logger.error(f"Error creating export: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating export: {e}")


class ZIPExportOptions(BaseModel):
    """ZIP export specific options."""
    include_source_code: bool = True
    include_tests: bool = True
    include_documentation: bool = True
    include_assets: bool = True
    include_database_schema: bool = True
    include_docker_config: bool = False
    include_ci_cd_config: bool = False
    include_retinue_metadata: bool = True
    include_env_example: bool = True
    format_code: bool = False
    fix_linting_issues: bool = False
    documentation_level: str = "standard"  # minimal, standard, comprehensive
    generate_setup_script: bool = True
    compression_level: int = 6  # 0-9


@router.post("/projects/{project_id}/export/zip", response_model=ExportResponse)
async def export_project_as_zip(
    project_id: UUID,
    options: ZIPExportOptions,
    background_tasks: BackgroundTasks,
    export_service: ExportService = Depends(get_export_service),
    agent_id: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Create a ZIP export of a project with all files and documentation.

    Args:
        project_id: Project to export
        options: ZIP export options
        background_tasks: FastAPI background tasks
        export_service: Export service
        agent_id: Optional agent requesting the export

    Returns:
        Job ID and status
    """
    try:
        export_type = ExportType.PROJECT_FILES_ZIP
        export_format = ExportFormat.ZIP

        # Create export job
        job = await export_service.create_export_job(
            project_id=project_id,
            export_format=export_format,
            export_type=export_type,
            options=options.dict(),
            created_by_agent_id=agent_id,
        )

        # Process in background
        background_tasks.add_task(
            export_service.process_export_job,
            job.job_id,
        )

        logger.info(f"Created ZIP export job {job.job_id}")

        return {
            "job_id": str(job.job_id),
            "status": "pending",
            "message": "ZIP export job created. Processing in background.",
        }

    except ValueError as e:
        logger.error(f"Invalid ZIP export options: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid ZIP export options: {e}")
    except Exception as e:
        logger.error(f"Error creating ZIP export: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating ZIP export: {e}")


@router.get("/exports/{job_id}/status", response_model=ExportJobResponse)
async def get_export_status(
    job_id: UUID,
    export_service: ExportService = Depends(get_export_service),
) -> Dict[str, Any]:
    """Get status of an export job.

    Args:
        job_id: Export job ID
        export_service: Export service

    Returns:
        Export job status and details
    """
    try:
        job = await export_service.get_export_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Export job not found")

        return {
            "job_id": str(job.job_id),
            "project_id": str(job.project_id),
            "export_format": job.export_format.value,
            "export_type": job.export_type.value,
            "status": job.status.value,
            "progress_percentage": job.progress_percentage or 0,
            "current_step": job.current_step,
            "created_at": job.created_at.isoformat(),
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "file_size_bytes": job.file_size_bytes,
            "error_message": job.error_message,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting export status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting export status: {e}")


@router.get("/exports/{job_id}/stream")
async def stream_export_status(
    job_id: UUID,
    export_service: ExportService = Depends(get_export_service),
):
    """Stream export job status updates via Server-Sent Events (SSE).

    Args:
        job_id: Export job ID
        export_service: Export service

    Returns:
        SSE stream of status updates
    """
    async def event_generator():
        """Generate SSE events for export status updates."""
        try:
            # Check if job exists
            job = await export_service.get_export_job(job_id)
            if not job:
                yield f"event: error\ndata: {json.dumps({'error': 'Export job not found'})}\n\n"
                return

            # Send initial status
            status_data = {
                "job_id": str(job.job_id),
                "project_id": str(job.project_id),
                "export_format": job.export_format.value,
                "export_type": job.export_type.value,
                "status": job.status.value,
                "progress_percentage": job.progress_percentage or 0,
                "current_step": job.current_step,
                "created_at": job.created_at.isoformat(),
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "file_size_bytes": job.file_size_bytes,
                "error_message": job.error_message,
            }
            yield f"data: {json.dumps(status_data)}\n\n"

            # Poll for updates until job is complete or failed
            while True:
                await asyncio.sleep(0.5)  # Check every 500ms

                # Refresh job status
                job = await export_service.get_export_job(job_id)
                if not job:
                    yield f"event: error\ndata: {json.dumps({'error': 'Job not found'})}\n\n"
                    break

                # Send updated status
                status_data = {
                    "job_id": str(job.job_id),
                    "project_id": str(job.project_id),
                    "export_format": job.export_format.value,
                    "export_type": job.export_type.value,
                    "status": job.status.value,
                    "progress_percentage": job.progress_percentage or 0,
                    "current_step": job.current_step,
                    "created_at": job.created_at.isoformat(),
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                    "file_size_bytes": job.file_size_bytes,
                    "error_message": job.error_message,
                }
                yield f"data: {json.dumps(status_data)}\n\n"

                # Stop streaming if job is in a terminal state
                if job.status.value in ["completed", "failed", "cancelled"]:
                    yield f"event: done\ndata: {json.dumps({'status': job.status.value})}\n\n"
                    break

        except Exception as e:
            logger.error(f"Error streaming export status: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering in nginx
        },
    )


@router.get("/exports/{job_id}/download")
async def download_export(
    job_id: UUID,
    export_service: ExportService = Depends(get_export_service),
):
    """Download completed export file.

    Args:
        job_id: Export job ID
        export_service: Export service

    Returns:
        File stream or 404 if not found
    """
    try:
        job = await export_service.get_export_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Export job not found")

        if job.status.value != "completed":
            raise HTTPException(status_code=400, detail=f"Export is {job.status.value}, not completed")

        if not job.file_path:
            raise HTTPException(status_code=404, detail="Export file not found")

        # Determine media type and ensure proper file extension
        if job.export_format.value == "pdf":
            media_type = "application/pdf"
            # Ensure .pdf extension
            filename = job.file_name
            if not filename.endswith('.pdf'):
                filename = f"{filename}.pdf"
        else:  # markdown
            media_type = "text/markdown"
            # Ensure .md extension
            filename = job.file_name
            if not filename.endswith('.md'):
                filename = f"{filename}.md"

        return FileResponse(
            path=job.file_path,
            filename=filename,
            media_type=media_type,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading export: {e}")
        raise HTTPException(status_code=500, detail=f"Error downloading export: {e}")


@router.post("/exports/{job_id}/cancel", response_model=Dict[str, str])
async def cancel_export(
    job_id: UUID,
    export_service: ExportService = Depends(get_export_service),
) -> Dict[str, str]:
    """Cancel a pending or in-progress export job.

    Args:
        job_id: Export job ID
        export_service: Export service

    Returns:
        Status message
    """
    try:
        job = await export_service.get_export_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Export job not found")

        if job.status.value in ["completed", "failed", "cancelled"]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel job with status {job.status.value}"
            )

        from app.db.export_models import ExportStatus
        job.status = ExportStatus.CANCELLED
        await export_service.session.commit()

        logger.info(f"Cancelled export job {job_id}")

        return {"status": "cancelled", "message": "Export job cancelled"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling export: {e}")
        raise HTTPException(status_code=500, detail=f"Error cancelling export: {e}")


@router.get("/projects/{project_id}/exports")
async def list_project_exports(
    project_id: UUID,
    limit: int = Query(10, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    """List all exports for a project.

    Args:
        project_id: Project ID
        limit: Number of results to return
        offset: Offset for pagination
        session: Database session

    Returns:
        List of exports with pagination info
    """
    try:
        from sqlalchemy import select, desc

        query = (
            select(ExportJobResponse)
            .where(ExportJobResponse.project_id == str(project_id))
            .order_by(desc(ExportJobResponse.created_at))
            .limit(limit)
            .offset(offset)
        )

        # Actually we should use the model directly
        from app.db.export_models import ExportJob

        query = (
            select(ExportJob)
            .where(ExportJob.project_id == project_id)
            .order_by(desc(ExportJob.created_at))
            .limit(limit)
            .offset(offset)
        )

        result = await session.execute(query)
        exports = result.scalars().all()

        return {
            "exports": [
                {
                    "job_id": str(e.job_id),
                    "export_format": e.export_format.value,
                    "export_type": e.export_type.value,
                    "status": e.status.value,
                    "created_at": e.created_at.isoformat(),
                    "file_size_bytes": e.file_size_bytes,
                }
                for e in exports
            ],
            "total": len(exports),
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        logger.error(f"Error listing exports: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing exports: {e}")


@router.post("/exports/cleanup", response_model=Dict[str, Any])
async def cleanup_old_exports(
    hours: int = Query(24, ge=1),
    export_service: ExportService = Depends(get_export_service),
) -> Dict[str, Any]:
    """Clean up old export files.

    Args:
        hours: Keep files newer than this many hours
        export_service: Export service

    Returns:
        Number of files cleaned
    """
    try:
        count = await export_service.cleanup_old_exports(hours)
        return {"cleaned": count, "message": f"Cleaned up {count} old export files"}

    except Exception as e:
        logger.error(f"Error cleaning up exports: {e}")
        raise HTTPException(status_code=500, detail=f"Error cleaning up exports: {e}")


# ==================== Deployment Endpoints (Stub for Phase 3) ====================

@router.post("/projects/{project_id}/deployments")
async def create_deployment(
    project_id: UUID,
    platform: str = Query(...),
    agent_id: Optional[str] = Query(None),
) -> Dict[str, str]:
    """Create a deployment (Phase 3).

    Args:
        project_id: Project to deploy
        platform: Deployment platform
        agent_id: Agent requesting deployment

    Returns:
        Deployment ID and status
    """
    raise HTTPException(
        status_code=501,
        detail="Deployment functionality available in Phase 3"
    )


@router.get("/projects/{project_id}/deployments")
async def list_deployments(
    project_id: UUID,
) -> Dict[str, Any]:
    """List deployments for a project (Phase 3).

    Args:
        project_id: Project ID

    Returns:
        List of deployments
    """
    raise HTTPException(
        status_code=501,
        detail="Deployment functionality available in Phase 3"
    )
