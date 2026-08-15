"""Configuration management for the Retinue platform."""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Retinue - AI Agent Company Platform"
    APP_VERSION: str = "1.0.0-phase1"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://nicanor:admin@localhost:5432/deviant_dev"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # API Keys
    ANTHROPIC_API_KEY: str
    OPENAI_API_KEY: Optional[str] = None

    # LLM Model Configuration
    DEFAULT_LLM_MODEL: str = "claude-sonnet-4-20250514"  # Default model for various services

    # Security
    JWT_SECRET: str = "dev-secret-change-in-production"

    # Explicit origins only. A wildcard is invalid alongside allow_credentials=True
    # (browsers reject it), so production must list real origins. Override with the
    # CORS_ORIGINS env var, e.g.
    #   CORS_ORIGINS=["https://retinue.nicanor.xyz"]
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Agent Configuration - Event-Driven Mode
    AGENT_EXECUTION_MODE: str = "event_driven"  # Options: "event_driven", "hybrid", "polling"

    # Legacy polling configuration (used only in "polling" mode)
    AGENT_CHECK_INTERVAL: int = 900  # 15 minutes in seconds (DEPRECATED in event_driven mode)

    # Health monitoring thresholds (used in all modes)
    AGENT_INACTIVE_WARNING_THRESHOLD: int = 1800  # 30 minutes
    AGENT_INACTIVE_CRITICAL_THRESHOLD: int = 3600  # 1 hour (reduced from 2 hours)
    AGENT_OFFLINE_THRESHOLD: int = 14400  # 4 hours

    # Task monitoring thresholds
    TASK_STUCK_THRESHOLD: int = 7200  # 2 hours (reduced from 8 hours)
    TASK_DEPENDENCY_CHECK_INTERVAL: int = 30  # 30 seconds (for immediate dependency resolution)

    # Approval timeout
    APPROVAL_TIMEOUT_THRESHOLD: int = 14400  # 4 hours

    # Event bus configuration
    EVENT_BUS_BACKEND: str = "memory"  # Options: "memory", "redis"
    EVENT_BUS_MAX_QUEUE_SIZE: int = 10000
    EVENT_DELIVERY_TIMEOUT_MS: int = 5000  # 5 seconds max for event delivery
    EVENT_TARGET_LATENCY_MS: int = 100  # Target <100ms event delivery

    # HR Monitoring configuration
    HR_MONITORING_ENABLED: bool = True
    HR_MONITORING_INTERVAL: int = 30  # 30 seconds (continuous monitoring check interval)
    HR_INTERVENTION_COOLDOWN: int = 900  # 15 minutes between interventions per agent

    # Optional: Error Tracking
    SENTRY_DSN: Optional[str] = None

    # RAG Configuration (Phase 1)
    RAG_ENABLED: bool = True
    RAG_VECTOR_STORE: str = "chromadb"  # Options: "chromadb", "qdrant", "pinecone"

    # Embedding Configuration
    # Backend options: "openai", "sentence-transformers", "huggingface"
    # Recommended for Claude: "sentence-transformers" (local, free, good quality)
    RAG_EMBEDDING_BACKEND: str = "sentence-transformers"
    RAG_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"  # Sentence Transformers model name

    # Model options by backend:
    # sentence-transformers:
    #   - "all-MiniLM-L6-v2" (384 dims, fastest, recommended)
    #   - "all-mpnet-base-v2" (768 dims, better quality)
    #   - "distiluse-base-multilingual-cased-v1" (512 dims, multi-lang)
    # openai:
    #   - "text-embedding-3-small" (1536 dims, cost-effective)
    #   - "text-embedding-3-large" (3072 dims, higher quality but more expensive)
    # huggingface:
    #   - "sentence-transformers/all-MiniLM-L6-v2"
    #   - "sentence-transformers/all-mpnet-base-v2"

    RAG_CHUNK_SIZE: int = 512
    RAG_CHUNK_OVERLAP: int = 50
    RAG_TOP_K: int = 5  # Number of results to retrieve
    RAG_SIMILARITY_THRESHOLD: float = 0.7
    RAG_MAX_CONTEXT_LENGTH: int = 50000  # Token limit for context

    # ChromaDB Configuration
    CHROMADB_PATH: str = "./data/chromadb"
    CHROMADB_PERSIST: bool = True

    # Qdrant Configuration
    QDRANT_URL: Optional[str] = None
    QDRANT_API_KEY: Optional[str] = None

    # Pinecone Configuration
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_ENVIRONMENT: Optional[str] = None
    PINECONE_INDEX_NAME: str = "Deviant-knowledge"

    # RAG Caching Configuration (Phase 3)
    RAG_CACHE_ENABLED: bool = True
    RAG_CACHE_TTL: int = 3600  # 1 hour cache TTL in seconds
    RAG_CACHE_MAX_SIZE: int = 1000  # Max number of cached queries
    RAG_CACHE_SIMILARITY_THRESHOLD: float = 0.95  # Threshold for considering queries identical
    RAG_CACHE_ANALYTICS_ENABLED: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env


# Create global settings instance
settings = Settings()


# Validate critical settings on import
def validate_settings():
    """Validate that critical settings are configured."""
    if not settings.ANTHROPIC_API_KEY:
        raise ValueError(
            "ANTHROPIC_API_KEY is required. Please set it in your .env file. "
            "Get your API key from https://console.anthropic.com/"
        )

    if settings.ENVIRONMENT == "production":
        if settings.JWT_SECRET == "dev-secret-change-in-production":
            raise ValueError(
                "JWT_SECRET must be changed in production environment!"
            )
        if "dev_password" in settings.DATABASE_URL:
            raise ValueError(
                "Database password must be changed in production environment!"
            )

    return True


# Run validation on import
try:
    validate_settings()
except ValueError as e:
    # In development, we warn but don't fail
    if settings.ENVIRONMENT == "development":
        print(f"⚠️  Configuration Warning: {e}")
    else:
        raise
