"""
Knowledge Management API Endpoints

REST API for the intelligent knowledge base system.
Provides endpoints for:
- Knowledge search and retrieval
- Knowledge entry management
- Extraction candidate review
- User preference management
- Agent involvement predictions
- Feedback and analytics
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from pydantic import BaseModel, Field, validator

from app.db.database import get_db
from app.db.knowledge_models import (
    KnowledgeEntry,
    KnowledgeCategory,
    ExtractionCandidate,
    KnowledgeFeedback,
    UserKnowledgeProfile,
    AgentInvolvementPrediction,
    KnowledgeEntryType,
    ExtractionStatus,
    FeedbackType,
    ValidationStatus
)
from app.services.knowledge_repository_service import get_knowledge_repository_service
from app.services.knowledge_extraction_service import get_knowledge_extraction_service
from app.services.knowledge_application_service import get_knowledge_application_service
from app.services.predictive_agent_involvement_service import get_predictive_involvement_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/knowledge", tags=["Knowledge Management"])


# ===== REQUEST/RESPONSE MODELS =====

class KnowledgeSearchRequest(BaseModel):
    """Request model for knowledge search."""
    query: str = Field(..., min_length=2, max_length=500, description="Search query")
    user_id: Optional[UUID] = Field(None, description="User ID for personalization")
    agent_id: Optional[str] = Field(None, description="Agent ID for context")
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Search filters")
    top_k: int = Field(10, ge=1, le=50, description="Number of results")
    include_relations: bool = Field(False, description="Include related entries")


class KnowledgeEntryResponse(BaseModel):
    """Response model for knowledge entry."""
    entry_id: str
    title: str
    summary: Optional[str]
    content_excerpt: str
    entry_type: str
    domain: Optional[str]
    tags: List[str]
    validation_status: str
    quality_score: float
    relevance_score: Optional[float] = None
    use_count: int
    helpfulness_ratio: float
    created_at: Optional[str]
    last_accessed_at: Optional[str]


class CreateKnowledgeEntryRequest(BaseModel):
    """Request to create knowledge entry."""
    title: str = Field(..., min_length=10, max_length=500)
    summary: Optional[str] = Field(None, max_length=1000)
    content: str = Field(..., min_length=50)
    entry_type: KnowledgeEntryType
    tags: List[str] = Field(default_factory=list)
    problem_context: Optional[str] = None
    applicable_scenarios: List[str] = Field(default_factory=list)
    source_project_id: Optional[UUID] = None
    source_task_id: Optional[UUID] = None


class ExtractionCandidateResponse(BaseModel):
    """Response model for extraction candidate."""
    candidate_id: str
    extraction_type: str
    title: str
    summary: str
    confidence_score: float
    novelty_score: float
    relevance_score: float
    extraction_quality: float
    trigger_type: str
    status: str
    created_at: str


class ReviewExtractionRequest(BaseModel):
    """Request to review extraction candidate."""
    decision: str = Field(..., pattern="^(approve|reject|modify)$")
    review_notes: Optional[str] = None
    modifications: Optional[Dict[str, Any]] = None


class SubmitFeedbackRequest(BaseModel):
    """Request to submit feedback on knowledge."""
    entry_id: UUID
    feedback_type: FeedbackType
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = None
    suggested_improvement: Optional[str] = None
    user_id: Optional[UUID] = None
    agent_id: Optional[str] = None


class AgentPredictionResponse(BaseModel):
    """Response model for agent involvement prediction."""
    agent_id: str
    agent_name: str
    agent_role: str
    involvement_probability: float
    confidence: float
    predicted_contribution_type: str
    suggested_timing: str
    introduction_approach: str
    trigger_reasons: List[str]
    signal_strength: float


# ===== SEARCH ENDPOINTS =====

@router.post("/search", response_model=List[KnowledgeEntryResponse])
async def search_knowledge(
    request: KnowledgeSearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Search knowledge base using hybrid search.

    Combines full-text, vector, and exact matching for optimal results.
    """
    try:
        repository = get_knowledge_repository_service()

        results = await repository.hybrid_search(
            db=db,
            query=request.query,
            user_id=request.user_id,
            agent_id=request.agent_id,
            filters=request.filters,
            top_k=request.top_k,
            include_relations=request.include_relations
        )

        return results

    except Exception as e:
        logger.error(f"Error in knowledge search: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Knowledge search failed: {str(e)}"
        )


@router.get("/entries/{entry_id}", response_model=Dict[str, Any])
async def get_knowledge_entry(
    entry_id: UUID,
    user_id: Optional[UUID] = None,
    agent_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed knowledge entry by ID."""
    try:
        entry = await db.get(KnowledgeEntry, entry_id)

        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge entry {entry_id} not found"
            )

        # Update view count and last accessed
        entry.view_count += 1
        entry.last_accessed_at = datetime.utcnow()
        await db.commit()

        # Log usage
        if agent_id:
            from app.db.knowledge_models import UsageType
            repository = get_knowledge_repository_service()
            await repository.log_knowledge_usage(
                db=db,
                entry_id=entry_id,
                agent_id=agent_id,
                usage_type=UsageType.RETRIEVED_FOR_CONTEXT
            )

        # Format response
        response = {
            "entry_id": str(entry.entry_id),
            "title": entry.title,
            "summary": entry.summary,
            "content": entry.content,
            "entry_type": entry.entry_type.value,
            "domain": entry.domain,
            "tags": entry.tags,
            "keywords": entry.keywords,
            "validation_status": entry.validation_status.value,
            "problem_context": entry.problem_context,
            "applicable_scenarios": entry.applicable_scenarios,
            "prerequisites": entry.prerequisites,
            "limitations": entry.limitations,
            "related_technologies": entry.related_technologies,
            "confidence_score": entry.confidence_score,
            "novelty_score": entry.novelty_score,
            "relevance_score": entry.relevance_score,
            "quality_score": entry.quality_score,
            "view_count": entry.view_count,
            "use_count": entry.use_count,
            "helpfulness_up": entry.helpfulness_up,
            "helpfulness_down": entry.helpfulness_down,
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
            "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
            "last_accessed_at": entry.last_accessed_at.isoformat() if entry.last_accessed_at else None
        }

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting knowledge entry: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve knowledge entry: {str(e)}"
        )


@router.post("/entries", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_knowledge_entry(
    request: CreateKnowledgeEntryRequest,
    created_by_id: str = Query(..., description="Creator ID (user or agent)"),
    db: AsyncSession = Depends(get_db)
):
    """Create new knowledge entry manually."""
    try:
        from app.services.knowledge_processing_service import get_knowledge_processing_service

        processing_service = get_knowledge_processing_service()

        # Normalize content
        normalized = await processing_service._normalize_content({
            "title": request.title,
            "summary": request.summary,
            "content": request.content,
            "problem_context": request.problem_context,
            "applicable_scenarios": request.applicable_scenarios
        })

        # Generate embeddings
        embeddings = await processing_service._generate_embeddings(normalized)

        # Create entry
        entry = KnowledgeEntry(
            title=normalized["title"],
            summary=normalized["summary"],
            content=normalized["content"],
            entry_type=request.entry_type,
            tags=request.tags,
            problem_context=normalized.get("problem_context"),
            applicable_scenarios=normalized.get("applicable_scenarios", []),
            source_type="manual",
            source_project_id=request.source_project_id,
            source_task_id=request.source_task_id,
            created_by_type="user",  # Assume user creation
            created_by_id=created_by_id,
            validation_status=ValidationStatus.UNVALIDATED,
            title_embedding=embeddings.get("title"),
            summary_embedding=embeddings.get("summary"),
            content_embedding=embeddings.get("content"),
            problem_embedding=embeddings.get("problem")
        )

        db.add(entry)
        await db.commit()
        await db.refresh(entry)

        logger.info(f"Created knowledge entry {entry.entry_id} by {created_by_id}")

        return {
            "entry_id": str(entry.entry_id),
            "title": entry.title,
            "status": "created",
            "message": "Knowledge entry created successfully"
        }

    except Exception as e:
        logger.error(f"Error creating knowledge entry: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create knowledge entry: {str(e)}"
        )


# ===== EXTRACTION ENDPOINTS =====

@router.get("/extractions/pending", response_model=List[ExtractionCandidateResponse])
async def get_pending_extractions(
    limit: int = Query(20, ge=1, le=100),
    min_quality: float = Query(0.5, ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_db)
):
    """Get pending extraction candidates for review."""
    try:
        query = select(ExtractionCandidate).where(
            and_(
                ExtractionCandidate.status == ExtractionStatus.PENDING,
                ExtractionCandidate.extraction_quality >= min_quality
            )
        ).order_by(
            ExtractionCandidate.extraction_quality.desc()
        ).limit(limit)

        result = await db.execute(query)
        candidates = result.scalars().all()

        formatted = []
        for candidate in candidates:
            formatted.append({
                "candidate_id": str(candidate.candidate_id),
                "extraction_type": candidate.extraction_type.value,
                "title": candidate.extracted_content.get("title", "Untitled"),
                "summary": candidate.extracted_content.get("summary", "")[:200],
                "confidence_score": candidate.confidence_score,
                "novelty_score": candidate.novelty_score,
                "relevance_score": candidate.relevance_score,
                "extraction_quality": candidate.extraction_quality,
                "trigger_type": candidate.trigger_type.value,
                "status": candidate.status.value,
                "created_at": candidate.created_at.isoformat()
            })

        return formatted

    except Exception as e:
        logger.error(f"Error getting pending extractions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve extraction candidates: {str(e)}"
        )


@router.post("/extractions/{candidate_id}/review")
async def review_extraction_candidate(
    candidate_id: UUID,
    request: ReviewExtractionRequest,
    reviewer_id: str = Query(..., description="Reviewer ID"),
    db: AsyncSession = Depends(get_db)
):
    """Review and approve/reject extraction candidate."""
    try:
        candidate = await db.get(ExtractionCandidate, candidate_id)

        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Extraction candidate {candidate_id} not found"
            )

        from app.services.knowledge_processing_service import get_knowledge_processing_service

        if request.decision == "approve":
            # Convert to knowledge entry
            processing_service = get_knowledge_processing_service()
            entry = await processing_service.convert_candidate_to_entry(db, candidate)

            if entry:
                candidate.status = ExtractionStatus.APPROVED
                candidate.converted_to_entry_id = entry.entry_id
                candidate.reviewed_by_id = reviewer_id
                candidate.review_decision = "approve"
                candidate.review_notes = request.review_notes
                candidate.reviewed_at = datetime.utcnow()

                await db.commit()

                return {
                    "status": "approved",
                    "entry_id": str(entry.entry_id),
                    "message": "Extraction approved and converted to knowledge entry"
                }

        elif request.decision == "reject":
            candidate.status = ExtractionStatus.REJECTED
            candidate.reviewed_by_id = reviewer_id
            candidate.review_decision = "reject"
            candidate.review_notes = request.review_notes
            candidate.reviewed_at = datetime.utcnow()

            await db.commit()

            return {
                "status": "rejected",
                "message": "Extraction rejected"
            }

        elif request.decision == "modify":
            # Apply modifications and re-process
            if request.modifications:
                candidate.extracted_content.update(request.modifications)
                candidate.status = ExtractionStatus.AWAITING_REVIEW
                candidate.processing_notes = "Modified by reviewer"

                await db.commit()

            return {
                "status": "modified",
                "message": "Extraction modified and awaiting re-review"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reviewing extraction: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to review extraction: {str(e)}"
        )


# ===== FEEDBACK ENDPOINTS =====

@router.post("/feedback", status_code=status.HTTP_201_CREATED)
async def submit_knowledge_feedback(
    request: SubmitFeedbackRequest,
    db: AsyncSession = Depends(get_db)
):
    """Submit feedback on knowledge entry."""
    try:
        # Verify entry exists
        entry = await db.get(KnowledgeEntry, request.entry_id)

        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge entry {request.entry_id} not found"
            )

        # Create feedback
        feedback = KnowledgeFeedback(
            entry_id=request.entry_id,
            user_id=request.user_id,
            agent_id=request.agent_id,
            feedback_type=request.feedback_type,
            rating=request.rating,
            comment=request.comment,
            suggested_improvement=request.suggested_improvement
        )

        db.add(feedback)

        # Update entry helpfulness counters
        if request.feedback_type == FeedbackType.HELPFUL:
            entry.helpfulness_up += 1
        elif request.feedback_type == FeedbackType.NOT_HELPFUL:
            entry.helpfulness_down += 1

        await db.commit()

        logger.info(f"Feedback submitted for entry {request.entry_id}")

        return {
            "status": "success",
            "message": "Feedback submitted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )


# ===== CATEGORIES ENDPOINTS =====

@router.get("/categories", response_model=List[Dict[str, Any]])
async def get_knowledge_categories(
    db: AsyncSession = Depends(get_db)
):
    """Get all knowledge categories."""
    try:
        query = select(KnowledgeCategory).order_by(
            KnowledgeCategory.level,
            KnowledgeCategory.display_order
        )

        result = await db.execute(query)
        categories = result.scalars().all()

        formatted = []
        for category in categories:
            formatted.append({
                "category_id": str(category.category_id),
                "name": category.name,
                "slug": category.slug,
                "description": category.description,
                "parent_category_id": str(category.parent_category_id) if category.parent_category_id else None,
                "level": category.level,
                "entry_count": category.entry_count,
                "icon": category.icon,
                "color": category.color
            })

        return formatted

    except Exception as e:
        logger.error(f"Error getting categories: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve categories: {str(e)}"
        )


# ===== AGENT PREDICTION ENDPOINTS =====

@router.post("/predict-agents", response_model=List[AgentPredictionResponse])
async def predict_agent_involvement(
    conversation_id: Optional[UUID] = None,
    project_id: Optional[UUID] = None,
    message_ids: List[UUID] = Query(..., description="Recent message IDs"),
    current_agent_ids: List[str] = Query(default_factory=list),
    user_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db)
):
    """Predict which agents should be involved in conversation/project."""
    try:
        from app.db.models import Message

        # Get messages
        query = select(Message).where(
            Message.message_id.in_(message_ids)
        ).order_by(Message.timestamp)

        result = await db.execute(query)
        messages = result.scalars().all()

        if not messages:
            return []

        # Generate predictions
        predictive_service = get_predictive_involvement_service()

        predictions = await predictive_service.predict_agent_involvement(
            db=db,
            conversation_id=conversation_id,
            messages=messages,
            project_id=project_id,
            current_agents=current_agent_ids,
            user_id=user_id
        )

        return predictions

    except Exception as e:
        logger.error(f"Error predicting agent involvement: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to predict agent involvement: {str(e)}"
        )


# ===== ANALYTICS ENDPOINTS =====

@router.get("/analytics/usage")
async def get_knowledge_usage_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """Get knowledge usage analytics."""
    try:
        from app.db.knowledge_models import KnowledgeUsageLog

        # Build query
        conditions = []
        if start_date:
            conditions.append(KnowledgeUsageLog.used_at >= start_date)
        if end_date:
            conditions.append(KnowledgeUsageLog.used_at <= end_date)

        query = select(KnowledgeUsageLog)
        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(KnowledgeUsageLog.used_at.desc()).limit(limit)

        result = await db.execute(query)
        logs = result.scalars().all()

        # Aggregate statistics
        stats = {
            "total_uses": len(logs),
            "by_usage_type": {},
            "by_agent": {},
            "helpfulness_rate": 0.0,
            "recent_uses": []
        }

        helpful_count = 0
        total_feedback = 0

        for log in logs:
            # Count by type
            usage_type = log.usage_type.value
            stats["by_usage_type"][usage_type] = stats["by_usage_type"].get(usage_type, 0) + 1

            # Count by agent
            stats["by_agent"][log.used_by_agent_id] = stats["by_agent"].get(log.used_by_agent_id, 0) + 1

            # Helpfulness
            if log.was_helpful is not None:
                total_feedback += 1
                if log.was_helpful:
                    helpful_count += 1

            # Recent uses (top 10)
            if len(stats["recent_uses"]) < 10:
                stats["recent_uses"].append({
                    "entry_id": str(log.entry_id),
                    "agent_id": log.used_by_agent_id,
                    "usage_type": usage_type,
                    "was_helpful": log.was_helpful,
                    "used_at": log.used_at.isoformat()
                })

        if total_feedback > 0:
            stats["helpfulness_rate"] = helpful_count / total_feedback

        return stats

    except Exception as e:
        logger.error(f"Error getting usage analytics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve usage analytics: {str(e)}"
        )


@router.get("/analytics/top-entries")
async def get_top_knowledge_entries(
    metric: str = Query("quality", pattern="^(quality|uses|helpfulness|views)$"),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Get top knowledge entries by various metrics."""
    try:
        # Build query based on metric
        query = select(KnowledgeEntry).where(
            KnowledgeEntry.status == "active"
        )

        if metric == "quality":
            query = query.order_by(KnowledgeEntry.quality_score.desc())
        elif metric == "uses":
            query = query.order_by(KnowledgeEntry.use_count.desc())
        elif metric == "views":
            query = query.order_by(KnowledgeEntry.view_count.desc())
        elif metric == "helpfulness":
            query = query.order_by(KnowledgeEntry.helpfulness_up.desc())

        query = query.limit(limit)

        result = await db.execute(query)
        entries = result.scalars().all()

        formatted = []
        for entry in entries:
            formatted.append({
                "entry_id": str(entry.entry_id),
                "title": entry.title,
                "entry_type": entry.entry_type.value,
                "quality_score": entry.quality_score,
                "use_count": entry.use_count,
                "view_count": entry.view_count,
                "helpfulness_up": entry.helpfulness_up,
                "helpfulness_down": entry.helpfulness_down,
                "created_at": entry.created_at.isoformat() if entry.created_at else None
            })

        return {
            "metric": metric,
            "entries": formatted
        }

    except Exception as e:
        logger.error(f"Error getting top entries: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve top entries: {str(e)}"
        )
