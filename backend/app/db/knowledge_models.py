"""
Intelligent Knowledge Base Models for Deviant

Implements the comprehensive knowledge system as specified in
INTELLIGENT_KNOWLEDGE_BASE.md including:
- Knowledge entries with full metadata
- Knowledge relationships and graph
- User knowledge profiles
- Extraction candidates
- Usage tracking
- Agent involvement predictions
- Feedback and evolution tracking
"""

from sqlalchemy import Column, String, Text, Integer, Boolean, TIMESTAMP, ForeignKey, Float
from sqlalchemy import Enum as SQLEnum, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

try:
    from pgvector.sqlalchemy import Vector as VECTOR
    HAS_PGVECTOR = True
except ImportError:
    # Fallback if pgvector not installed - use ARRAY for compatibility
    VECTOR = None
    HAS_PGVECTOR = False

from app.db.database import Base


# Helper function to create vector columns
def vector_column(dimensions, **kwargs):
    """Create a vector column with fallback to ARRAY if pgvector not available."""
    if HAS_PGVECTOR and VECTOR is not None:
        return Column(VECTOR(dimensions), **kwargs)
    else:
        # Fallback to ARRAY(Float) for compatibility
        return Column(ARRAY(Float), **kwargs)


# ===== ENUMS =====

class KnowledgeEntryType(str, enum.Enum):
    """Type of knowledge entry."""
    SOLUTION = "solution"
    DECISION = "decision"
    PREFERENCE = "preference"
    STANDARD = "standard"
    LESSON_LEARNED = "lesson_learned"
    PATTERN = "pattern"
    TEMPLATE = "template"
    DEFINITION = "definition"
    BEST_PRACTICE = "best_practice"
    TECHNICAL_INSIGHT = "technical_insight"


class ValidationStatus(str, enum.Enum):
    """Validation level of knowledge entry."""
    UNVALIDATED = "unvalidated"
    AGENT_VALIDATED = "agent_validated"
    HUMAN_VALIDATED = "human_validated"
    ORGANIZATIONAL_STANDARD = "organizational_standard"


class KnowledgeStatus(str, enum.Enum):
    """Lifecycle status of knowledge entry."""
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class RelationshipType(str, enum.Enum):
    """Types of relationships between knowledge entries."""
    RELATED_TO = "related_to"
    SIMILAR_TO = "similar_to"
    ALTERNATIVE_TO = "alternative_to"
    COMPLEMENTS = "complements"
    CONTRADICTS = "contradicts"
    SUPERSEDES = "supersedes"
    DEPENDS_ON = "depends_on"
    PREREQUISITE_FOR = "prerequisite_for"
    PARENT_OF = "parent_of"
    CHILD_OF = "child_of"
    DERIVED_FROM = "derived_from"
    VALIDATES = "validates"


class ExtractionTriggerType(str, enum.Enum):
    """What triggered knowledge extraction."""
    EXPLICIT_REQUEST = "explicit_request"
    PATTERN_DETECTION = "pattern_detection"
    DECISION_DETECTED = "decision_detected"
    PROBLEM_SOLVED = "problem_solved"
    CORRECTION_MADE = "correction_made"
    USER_FEEDBACK = "user_feedback"
    AUTOMATIC = "automatic"


class ExtractionStatus(str, enum.Enum):
    """Status of extraction candidate."""
    PENDING = "pending"
    PROCESSING = "processing"
    AWAITING_REVIEW = "awaiting_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    MERGED = "merged"


class UsageType(str, enum.Enum):
    """How knowledge was used."""
    RETRIEVED_FOR_CONTEXT = "retrieved_for_context"
    CITED_IN_RESPONSE = "cited_in_response"
    APPLIED_AS_SOLUTION = "applied_as_solution"
    SUGGESTED_TO_USER = "suggested_to_user"
    USED_FOR_VALIDATION = "used_for_validation"


class FeedbackType(str, enum.Enum):
    """Type of feedback on knowledge."""
    HELPFUL = "helpful"
    NOT_HELPFUL = "not_helpful"
    OUTDATED = "outdated"
    INCORRECT = "incorrect"
    PARTIALLY_HELPFUL = "partially_helpful"


class AgentInvolvementType(str, enum.Enum):
    """Type of agent involvement prediction."""
    PRIMARY_EXPERT = "primary_expert"
    SECONDARY_SUPPORT = "secondary_support"
    REVIEWER = "reviewer"
    OPTIONAL = "optional"


class InvolvementTiming(str, enum.Enum):
    """When agent should be involved."""
    IMMEDIATE = "immediate"
    AFTER_INITIAL_DISCUSSION = "after_initial_discussion"
    WHEN_TOPIC_ARISES = "when_topic_arises"
    ON_DEMAND = "on_demand"


class InvolvementApproach(str, enum.Enum):
    """How to introduce agent."""
    AUTO_JOIN = "auto_join"
    SUGGEST_TO_USER = "suggest_to_user"
    PREPARE_STANDBY = "prepare_standby"


# ===== CORE KNOWLEDGE MODELS =====

class KnowledgeEntry(Base):
    """
    Core knowledge entry storing extracted organizational intelligence.
    """
    __tablename__ = "knowledge_entries"

    # Primary Key
    entry_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Core Content
    title = Column(String(500), nullable=False, index=True)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    content_format = Column(String(20), default="markdown")  # markdown, plain, structured
    content_structured = Column(JSONB, default={})

    # Classification
    entry_type = Column(SQLEnum(KnowledgeEntryType), nullable=False, index=True)
    primary_category_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_categories.category_id"), nullable=True)
    categories = Column(ARRAY(UUID(as_uuid=True)), default=[])  # Multiple categories
    tags = Column(ARRAY(String(100)), default=[])
    keywords = Column(ARRAY(String(100)), default=[])
    domain = Column(String(100), nullable=True, index=True)  # technical, business, process

    # Scoring (0.0 - 1.0)
    confidence_score = Column(Float, nullable=False, default=0.0)
    novelty_score = Column(Float, nullable=False, default=0.0)
    relevance_score = Column(Float, nullable=False, default=0.0)
    quality_score = Column(Float, nullable=False, default=0.0)  # Computed from usage

    # Context
    problem_context = Column(Text, nullable=True)
    applicable_scenarios = Column(JSONB, default=[])
    prerequisites = Column(JSONB, default=[])
    limitations = Column(JSONB, default=[])
    related_technologies = Column(ARRAY(String(100)), default=[])

    # Validation
    validation_status = Column(SQLEnum(ValidationStatus), nullable=False, default=ValidationStatus.UNVALIDATED, index=True)
    validated_by_agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=True)
    validated_at = Column(TIMESTAMP, nullable=True)
    validation_notes = Column(Text, nullable=True)

    # Provenance
    source_type = Column(String(50), nullable=False)  # conversation, project, manual, import
    source_conversation_id = Column(UUID(as_uuid=True), nullable=True)  # If from conversation
    source_project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id"), nullable=True)
    source_task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.task_id"), nullable=True)
    source_message_ids = Column(ARRAY(UUID(as_uuid=True)), default=[])

    created_by_type = Column(String(20), nullable=False)  # user, agent, system
    created_by_id = Column(String(100), nullable=False)  # agent_id or user_id
    contributors = Column(ARRAY(String(100)), default=[])

    # Lifecycle
    status = Column(SQLEnum(KnowledgeStatus), nullable=False, default=KnowledgeStatus.DRAFT, index=True)
    version = Column(Integer, nullable=False, default=1)
    superseded_by_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_entries.entry_id"), nullable=True)

    # Timestamps
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), index=True)
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())
    last_accessed_at = Column(TIMESTAMP, nullable=True, index=True)

    # Usage Metrics
    view_count = Column(Integer, default=0)
    use_count = Column(Integer, default=0)
    helpfulness_up = Column(Integer, default=0)
    helpfulness_down = Column(Integer, default=0)

    # Embeddings for Vector Search (using pgvector extension)
    title_embedding = vector_column(1536, nullable=True)  # For title search
    summary_embedding = vector_column(1536, nullable=True)  # For summary search
    content_embedding = vector_column(1536, nullable=True)  # For full content search
    problem_embedding = vector_column(1536, nullable=True)  # For problem matching

    # Additional metadata
    meta_data = Column(JSONB, default={})

    __table_args__ = (
        Index('idx_knowledge_entries_status', status),
        Index('idx_knowledge_entries_type', entry_type),
        Index('idx_knowledge_entries_domain', domain),
        Index('idx_knowledge_entries_created_at', created_at.desc()),
        Index('idx_knowledge_entries_quality', quality_score.desc()),
        Index('idx_knowledge_entries_tags', tags, postgresql_using='gin'),
        Index('idx_knowledge_entries_keywords', keywords, postgresql_using='gin'),
        Index('idx_knowledge_entries_categories', categories, postgresql_using='gin'),
        CheckConstraint('confidence_score >= 0 AND confidence_score <= 1', name='check_confidence_score'),
        CheckConstraint('novelty_score >= 0 AND novelty_score <= 1', name='check_novelty_score'),
        CheckConstraint('relevance_score >= 0 AND relevance_score <= 1', name='check_relevance_score'),
        CheckConstraint('quality_score >= 0 AND quality_score <= 1', name='check_quality_score'),
    )


class KnowledgeRelationship(Base):
    """
    Relationships between knowledge entries forming a knowledge graph.
    """
    __tablename__ = "knowledge_relationships"

    relationship_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_entry_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_entries.entry_id", ondelete="CASCADE"), nullable=False, index=True)
    target_entry_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_entries.entry_id", ondelete="CASCADE"), nullable=False, index=True)

    relationship_type = Column(SQLEnum(RelationshipType), nullable=False, index=True)
    strength = Column(Float, nullable=False, default=0.5)  # 0.0 - 1.0
    bidirectional = Column(Boolean, default=False)
    auto_generated = Column(Boolean, default=False)

    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    meta_data = Column(JSONB, default={})

    __table_args__ = (
        Index('idx_knowledge_rel_source', source_entry_id),
        Index('idx_knowledge_rel_target', target_entry_id),
        Index('idx_knowledge_rel_type', relationship_type),
        CheckConstraint('strength >= 0 AND strength <= 1', name='check_strength'),
        CheckConstraint('source_entry_id != target_entry_id', name='check_no_self_reference'),
    )


class KnowledgeCategory(Base):
    """
    Hierarchical categorization of knowledge.
    """
    __tablename__ = "knowledge_categories"

    category_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, index=True)
    slug = Column(String(200), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Hierarchy support
    parent_category_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_categories.category_id"), nullable=True)
    path = Column(ARRAY(String(200)), default=[])  # Materialized path for fast queries
    level = Column(Integer, nullable=False, default=0)

    # Display
    display_order = Column(Integer, default=0)
    icon = Column(String(50), nullable=True)
    color = Column(String(20), nullable=True)

    # Metrics (denormalized for performance)
    entry_count = Column(Integer, default=0)

    # Metadata
    meta_data = Column(JSONB, default={})
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_knowledge_category_parent', parent_category_id),
        Index('idx_knowledge_category_level', level),
        Index('idx_knowledge_category_path', path, postgresql_using='gin'),
    )


class KnowledgeVersion(Base):
    """
    Version history for knowledge entries.
    """
    __tablename__ = "knowledge_versions"

    version_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entry_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_entries.entry_id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)

    # Snapshot of content
    title = Column(String(500), nullable=False)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=False)

    # Change tracking
    change_type = Column(String(50), nullable=False)  # created, minor_edit, major_update, correction, expansion, deprecation
    change_summary = Column(Text, nullable=True)
    change_reason = Column(Text, nullable=True)

    changed_by_type = Column(String(20), nullable=False)  # user, agent, system
    changed_by_id = Column(String(100), nullable=False)

    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), index=True)
    meta_data = Column(JSONB, default={})

    __table_args__ = (
        Index('idx_knowledge_version_entry', entry_id, version_number.desc()),
    )


# ===== USER KNOWLEDGE PROFILES =====

class UserKnowledgeProfile(Base):
    """
    User-specific knowledge profile tracking preferences, expertise, and patterns.
    """
    __tablename__ = "user_knowledge_profiles"

    profile_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.user_id"), unique=True, nullable=False, index=True)

    # Communication Preferences
    preferred_response_length = Column(String(20), default="moderate")  # brief, moderate, detailed, comprehensive
    preferred_technical_depth = Column(String(20), default="intermediate")  # beginner, intermediate, advanced, expert
    preferred_communication_style = Column(String(20), default="professional")  # formal, casual, technical, friendly
    formatting_preferences = Column(JSONB, default={})  # likes_bullet_points, prefers_code_examples, etc

    # Expertise Profile
    expertise_areas = Column(JSONB, default={})  # {topic: {level: "expert", confidence: 0.9}}
    learning_goals = Column(ARRAY(Text), default=[])
    technologies_used = Column(ARRAY(String(100)), default=[])
    domains_worked_in = Column(ARRAY(String(100)), default=[])

    # Working Patterns
    typical_active_hours = Column(JSONB, default={})  # {monday: {start: "09:00", end: "17:00"}}
    response_time_patterns = Column(JSONB, default={})
    decision_making_style = Column(String(30), default="deliberate")  # quick, deliberate, collaborative, data_driven

    # Interaction Patterns
    topics_discussed = Column(JSONB, default={})  # {topic: frequency}
    preferred_agents = Column(JSONB, default={})  # {agent_id: {interactions: 25, satisfaction: 0.9}}
    common_requests = Column(ARRAY(Text), default=[])

    # Inferred Insights
    inferred_preferences = Column(JSONB, default={})
    communication_quirks = Column(JSONB, default={})
    known_pet_peeves = Column(ARRAY(Text), default=[])

    # Meta
    profile_confidence = Column(Float, default=0.0)  # 0.0 - 1.0
    profile_completeness = Column(Float, default=0.0)  # 0.0 - 1.0

    last_updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())
    update_history = Column(JSONB, default=[])

    # Embedding for matching
    interest_embedding = vector_column(1536, nullable=True)

    __table_args__ = (
        CheckConstraint('profile_confidence >= 0 AND profile_confidence <= 1', name='check_profile_confidence'),
        CheckConstraint('profile_completeness >= 0 AND profile_completeness <= 1', name='check_profile_completeness'),
    )


class UserPreference(Base):
    """
    Individual user preferences extracted from interactions.
    """
    __tablename__ = "user_preferences"

    preference_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.user_id"), nullable=False, index=True)

    preference_type = Column(String(20), nullable=False)  # explicit, inferred, corrected
    category = Column(String(100), nullable=False, index=True)  # technical, communication, workflow
    key = Column(String(200), nullable=False, index=True)  # e.g., prefers_detailed_explanations
    value = Column(JSONB, nullable=False)

    confidence = Column(Float, nullable=False, default=0.0)  # 0.0 - 1.0

    # Source tracking
    source_conversation_id = Column(UUID(as_uuid=True), nullable=True)
    source_message_ids = Column(ARRAY(UUID(as_uuid=True)), default=[])

    # Validation tracking
    times_confirmed = Column(Integer, default=0)
    times_contradicted = Column(Integer, default=0)

    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())
    valid_until = Column(TIMESTAMP, nullable=True)  # For temporal preferences

    __table_args__ = (
        Index('idx_user_pref_user_category', user_id, category),
        CheckConstraint('confidence >= 0 AND confidence <= 1', name='check_confidence'),
    )


# ===== EXTRACTION & PROCESSING =====

class ExtractionCandidate(Base):
    """
    Candidate knowledge extracted but awaiting review/approval.
    """
    __tablename__ = "extraction_candidates"

    candidate_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Source
    conversation_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id"), nullable=True)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.task_id"), nullable=True)
    message_range_start = Column(UUID(as_uuid=True), nullable=True)
    message_range_end = Column(UUID(as_uuid=True), nullable=True)

    # Extracted Content (structured)
    extracted_content = Column(JSONB, nullable=False)  # Complete structured extraction

    # Classification
    extraction_type = Column(SQLEnum(KnowledgeEntryType), nullable=False, index=True)
    primary_category_guess = Column(String(200), nullable=True)

    # Scoring
    confidence_score = Column(Float, nullable=False, default=0.0)
    novelty_score = Column(Float, nullable=False, default=0.0)
    relevance_score = Column(Float, nullable=False, default=0.0)
    extraction_quality = Column(Float, nullable=False, default=0.0)  # Combined score

    # Trigger
    trigger_type = Column(SQLEnum(ExtractionTriggerType), nullable=False, index=True)
    trigger_details = Column(JSONB, default={})

    # Processing
    status = Column(SQLEnum(ExtractionStatus), nullable=False, default=ExtractionStatus.PENDING, index=True)
    processing_notes = Column(Text, nullable=True)

    # Review
    reviewed_by_type = Column(String(20), nullable=True)  # user, agent, system
    reviewed_by_id = Column(String(100), nullable=True)
    review_decision = Column(String(20), nullable=True)  # approve, reject, merge, modify
    review_notes = Column(Text, nullable=True)
    reviewed_at = Column(TIMESTAMP, nullable=True)

    # Conversion
    converted_to_entry_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_entries.entry_id"), nullable=True)
    merged_with_entry_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_entries.entry_id"), nullable=True)

    # Timestamps
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), index=True)
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_extraction_status', status),
        Index('idx_extraction_created', created_at.desc()),
        CheckConstraint('confidence_score >= 0 AND confidence_score <= 1', name='check_extraction_confidence'),
        CheckConstraint('novelty_score >= 0 AND novelty_score <= 1', name='check_extraction_novelty'),
        CheckConstraint('relevance_score >= 0 AND relevance_score <= 1', name='check_extraction_relevance'),
        CheckConstraint('extraction_quality >= 0 AND extraction_quality <= 1', name='check_extraction_quality'),
    )


# ===== USAGE & FEEDBACK =====

class KnowledgeUsageLog(Base):
    """
    Log of knowledge usage for analytics and quality improvement.
    """
    __tablename__ = "knowledge_usage_log"

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entry_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_entries.entry_id", ondelete="CASCADE"), nullable=False, index=True)

    # Usage Context
    used_in_conversation_id = Column(UUID(as_uuid=True), nullable=True)
    used_in_message_id = Column(UUID(as_uuid=True), nullable=True)
    used_by_agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=False)

    # Usage Details
    usage_type = Column(SQLEnum(UsageType), nullable=False, index=True)
    retrieval_query = Column(Text, nullable=True)
    retrieval_rank = Column(Integer, nullable=True)  # Position in search results

    # Outcome
    was_helpful = Column(Boolean, nullable=True)
    feedback_type = Column(SQLEnum(FeedbackType), nullable=True)
    feedback_text = Column(Text, nullable=True)
    led_to_update = Column(Boolean, default=False)

    # Timing
    used_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), index=True)

    # Context snapshot
    conversation_context = Column(JSONB, default={})  # topic, user_question, problem_type

    __table_args__ = (
        Index('idx_usage_entry_time', entry_id, used_at.desc()),
        Index('idx_usage_agent', used_by_agent_id),
        Index('idx_usage_type', usage_type),
    )


class KnowledgeFeedback(Base):
    """
    User/agent feedback on knowledge entries.
    """
    __tablename__ = "knowledge_feedback"

    feedback_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entry_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_entries.entry_id", ondelete="CASCADE"), nullable=False, index=True)

    # Feedback source
    user_id = Column(UUID(as_uuid=True), nullable=True)
    agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=True)

    feedback_type = Column(SQLEnum(FeedbackType), nullable=False, index=True)
    rating = Column(Integer, nullable=True)  # 1-5 scale
    comment = Column(Text, nullable=True)
    suggested_improvement = Column(Text, nullable=True)

    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), index=True)
    addressed = Column(Boolean, default=False)
    addressed_at = Column(TIMESTAMP, nullable=True)

    __table_args__ = (
        Index('idx_feedback_entry', entry_id),
        CheckConstraint('rating >= 1 AND rating <= 5', name='check_feedback_rating'),
    )


# ===== PREDICTIVE AGENT INVOLVEMENT =====

class AgentInvolvementPrediction(Base):
    """
    Predictions for which agents should be involved in conversations.
    """
    __tablename__ = "agent_involvement_predictions"

    prediction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Context
    conversation_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    message_id = Column(UUID(as_uuid=True), nullable=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id"), nullable=True)

    # Prediction
    agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=False, index=True)
    involvement_probability = Column(Float, nullable=False)  # 0.0 - 1.0
    confidence = Column(Float, nullable=False)  # 0.0 - 1.0

    predicted_contribution_type = Column(SQLEnum(AgentInvolvementType), nullable=False)
    suggested_timing = Column(SQLEnum(InvolvementTiming), nullable=False)
    introduction_approach = Column(SQLEnum(InvolvementApproach), nullable=False)

    # Reasoning
    trigger_reasons = Column(JSONB, default=[])  # List of reason strings
    signal_strength = Column(Float, nullable=False)  # 0.0 - 1.0

    # Outcome tracking
    actual_involvement = Column(String(50), nullable=True)  # joined, suggested_accepted, suggested_declined, not_involved, manually_invited
    involvement_timing = Column(TIMESTAMP, nullable=True)
    user_satisfaction = Column(Float, nullable=True)  # 0.0 - 1.0
    contribution_quality = Column(Float, nullable=True)  # 0.0 - 1.0

    # Timestamps
    predicted_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), index=True)
    resolved_at = Column(TIMESTAMP, nullable=True)

    __table_args__ = (
        Index('idx_involvement_pred_agent', agent_id),
        Index('idx_involvement_pred_conv', conversation_id),
        Index('idx_involvement_pred_time', predicted_at.desc()),
        CheckConstraint('involvement_probability >= 0 AND involvement_probability <= 1', name='check_involvement_probability'),
        CheckConstraint('confidence >= 0 AND confidence <= 1', name='check_involvement_confidence'),
        CheckConstraint('signal_strength >= 0 AND signal_strength <= 1', name='check_signal_strength'),
    )


class AgentInvolvementOutcome(Base):
    """
    Actual outcomes of agent involvement for learning.
    """
    __tablename__ = "agent_involvement_outcomes"

    outcome_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    conversation_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id"), nullable=True)
    agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=False, index=True)

    # Involvement details
    involvement_type = Column(String(50), nullable=False)  # primary, secondary, handoff_target, brief_contribution
    joined_at = Column(TIMESTAMP, nullable=False)
    left_at = Column(TIMESTAMP, nullable=True)
    messages_sent = Column(Integer, default=0)

    # Quality metrics
    user_satisfaction_rating = Column(Float, nullable=True)  # 0.0 - 1.0
    contribution_helpfulness = Column(Float, nullable=True)  # 0.0 - 1.0
    response_quality_score = Column(Float, nullable=True)  # 0.0 - 1.0
    timing_appropriateness = Column(Float, nullable=True)  # 0.0 - 1.0

    # Prediction comparison
    was_predicted = Column(Boolean, default=False)
    prediction_id = Column(UUID(as_uuid=True), ForeignKey("agent_involvement_predictions.prediction_id"), nullable=True)
    prediction_accuracy = Column(Float, nullable=True)  # 0.0 - 1.0

    # User feedback
    user_feedback = Column(JSONB, default={})  # {was_helpful, timing_appropriate, would_want_again, comments}

    # Timestamps
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    __table_args__ = (
        Index('idx_involvement_outcome_agent', agent_id),
        Index('idx_involvement_outcome_conv', conversation_id),
    )


# ===== CONVERSATIONS =====
# Note: Conversation model is defined in conversation_models.py
# The knowledge system uses the existing conversations table


# ===== INDEXES FOR PERFORMANCE =====

# Vector similarity indexes will be created via migration
# CREATE INDEX idx_knowledge_content_vector ON knowledge_entries
#     USING ivfflat (content_embedding vector_cosine_ops) WITH (lists = 100);
# CREATE INDEX idx_knowledge_problem_vector ON knowledge_entries
#     USING ivfflat (problem_embedding vector_cosine_ops) WITH (lists = 100);
