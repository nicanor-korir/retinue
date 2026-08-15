"""
Export API v2 - Simple, clean export endpoints.

Design principles:
1. One endpoint to get project info
2. One endpoint to create export
3. One endpoint to download
4. No complex job queues for simple exports
"""
import logging
from pathlib import Path
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_session
from app.schemas.export_schemas import (
    ExportFormat,
    ExportJobResponse,
    ExportRequest,
    ExportStatus,
    ProjectExportInfo,
)
from app.services.export_service_v2 import ExportServiceV2

logger = logging.getLogger(__name__)

router = APIRouter(tags=["exports-v2"])


@router.get("/projects/{project_id}/info", response_model=ProjectExportInfo)
async def get_export_info(
    project_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """
    Get export info for a project.

    Returns what can be exported and recommended format.
    Call this when opening the export dialog.
    """
    try:
        service = ExportServiceV2(session)
        info = await service.get_project_export_info(project_id)
        return info
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Error getting export info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get export info")


@router.post("/projects/{project_id}/export", response_model=ExportJobResponse)
async def create_export(
    project_id: UUID,
    request: ExportRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    """
    Create and generate an export.

    For most projects, this completes synchronously in a few seconds.
    Returns download URL immediately when done.
    """
    try:
        service = ExportServiceV2(session)

        # Generate export synchronously - most complete in <5 seconds
        file_path, file_name = await service.create_export(project_id, request)

        # Get file size
        file_size = Path(file_path).stat().st_size

        # Schedule cleanup of old files
        background_tasks.add_task(service.cleanup_old_exports, 24)

        # Extract job_id from filename (timestamp portion)
        job_id = file_name.rsplit("_", 1)[-1].split(".")[0]

        return ExportJobResponse(
            job_id=job_id,
            status=ExportStatus.COMPLETED,
            progress=100,
            message="Export ready for download",
            download_url=f"/api/v2/exports/download/{file_name}",
            file_name=file_name,
            file_size=file_size,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Export failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Export failed. Please try again.",
        )


@router.get("/download/{file_name}")
async def download_export(file_name: str):
    """
    Download an exported file.

    Files are available for 24 hours after creation.
    """
    import tempfile

    export_dir = Path(tempfile.gettempdir()) / "retinue_exports"
    file_path = export_dir / file_name

    # Security: validate filename doesn't contain path traversal
    if ".." in file_name or "/" in file_name or "\\" in file_name:
        raise HTTPException(status_code=400, detail="Invalid filename")

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Export not found. Exports are available for 24 hours.",
        )

    # Determine media type
    media_types = {
        ".pdf": "application/pdf",
        ".md": "text/markdown",
        ".zip": "application/zip",
    }
    suffix = file_path.suffix.lower()
    media_type = media_types.get(suffix, "application/octet-stream")

    return FileResponse(
        path=str(file_path),
        filename=file_name,
        media_type=media_type,
    )


# Keep old endpoints for backwards compatibility but mark deprecated
@router.post(
    "/projects/{project_id}/export/pdf",
    deprecated=True,
    response_model=ExportJobResponse,
    summary="[Deprecated] Use /projects/{project_id}/export instead",
)
async def export_pdf_deprecated(
    project_id: UUID,
    session: AsyncSession = Depends(get_session),
    background_tasks: BackgroundTasks = None,
):
    """Deprecated: Use the unified /export endpoint with format='pdf'."""
    request = ExportRequest(format=ExportFormat.PDF)
    return await create_export(project_id, request, background_tasks, session)


@router.post(
    "/projects/{project_id}/export/markdown",
    deprecated=True,
    response_model=ExportJobResponse,
    summary="[Deprecated] Use /projects/{project_id}/export instead",
)
async def export_markdown_deprecated(
    project_id: UUID,
    session: AsyncSession = Depends(get_session),
    background_tasks: BackgroundTasks = None,
):
    """Deprecated: Use the unified /export endpoint with format='markdown'."""
    request = ExportRequest(format=ExportFormat.MARKDOWN)
    return await create_export(project_id, request, background_tasks, session)


@router.post(
    "/projects/{project_id}/export/zip",
    deprecated=True,
    response_model=ExportJobResponse,
    summary="[Deprecated] Use /projects/{project_id}/export instead",
)
async def export_zip_deprecated(
    project_id: UUID,
    session: AsyncSession = Depends(get_session),
    background_tasks: BackgroundTasks = None,
):
    """Deprecated: Use the unified /export endpoint with format='zip'."""
    request = ExportRequest(format=ExportFormat.ZIP)
    return await create_export(project_id, request, background_tasks, session)
