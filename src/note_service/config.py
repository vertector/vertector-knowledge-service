"""
============================================================================
Academic Note-Taking GraphRAG System - Configuration
============================================================================
Environment-based configuration using Pydantic Settings
Supports .env files and environment variables
============================================================================
"""

from typing import Literal
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Neo4jSettings(BaseSettings):
    """Neo4j database connection settings."""

    model_config = SettingsConfigDict(
        env_prefix="NEO4J_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    uri: str = Field(
        default="bolt://localhost:7687",
        description="Neo4j connection URI (bolt://, neo4j://, or neo4j+s://)",
    )

    username: str = Field(
        default="neo4j",
        description="Neo4j database username",
    )

    password: SecretStr = Field(
        default=SecretStr("password"),
        description="Neo4j database password",
    )

    database: str = Field(
        default="neo4j",
        description="Neo4j database name",
    )

    max_connection_pool_size: int = Field(
        default=50,
        ge=1,
        le=1000,
        description="Maximum number of connections in the pool",
    )

    connection_timeout: float = Field(
        default=30.0,
        gt=0,
        description="Connection timeout in seconds",
    )

    max_transaction_retry_time: float = Field(
        default=30.0,
        gt=0,
        description="Maximum retry time for transactions in seconds",
    )

    encrypted: bool = Field(
        default=False,
        description="Use TLS/SSL encryption for connections",
    )

    trust: Literal["TRUST_ALL_CERTIFICATES", "TRUST_SYSTEM_CA_SIGNED_CERTIFICATES"] = Field(
        default="TRUST_ALL_CERTIFICATES",
        description="Certificate trust policy",
    )

    @field_validator("uri")
    @classmethod
    def validate_uri(cls, v: str) -> str:
        """Validate Neo4j URI format."""
        if not v.startswith(("bolt://", "neo4j://", "neo4j+s://", "bolt+s://")):
            raise ValueError(
                "URI must start with bolt://, neo4j://, bolt+s://, or neo4j+s://"
            )
        return v


class EmbeddingSettings(BaseSettings):
    """Embedding model configuration."""

    model_config = SettingsConfigDict(
        env_prefix="EMBEDDING_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    model_name: str = Field(
        default="Qwen/Qwen3-Embedding-0.6B",
        description="SentenceTransformer model name from HuggingFace",
    )

    dimensions: int = Field(
        default=896,
        ge=1,
        description="Embedding vector dimensions (Qwen3-0.6B = 896)",
    )

    device: Literal["cpu", "cuda", "mps"] = Field(
        default="cpu",
        description="Compute device (cpu, cuda for NVIDIA GPUs, mps for Apple Silicon)",
    )

    batch_size: int = Field(
        default=32,
        ge=1,
        le=512,
        description="Batch size for embedding generation",
    )

    normalize_embeddings: bool = Field(
        default=True,
        description="L2 normalize embeddings for cosine similarity",
    )

    cache_folder: str | None = Field(
        default=None,
        description="Local cache folder for downloaded models",
    )


class LLMSettings(BaseSettings):
    """LLM configuration for query generation."""

    model_config = SettingsConfigDict(
        env_prefix="LLM_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    provider: Literal["google"] = Field(
        default="google",
        description="LLM provider (currently only Google Gemini supported)",
    )

    model_name: str = Field(
        default="gemini-2.5-flash",
        description="Google Gemini model name",
    )

    api_key: SecretStr | None = Field(
        default=None,
        description="Google API key for Gemini (can also use GOOGLE_API_KEY env var)",
    )

    temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
        description="Temperature for query generation (0 for deterministic)",
    )

    max_tokens: int = Field(
        default=2048,
        ge=1,
        le=8192,
        description="Maximum tokens for LLM responses",
    )

    timeout: float = Field(
        default=30.0,
        gt=0,
        description="Request timeout in seconds",
    )


class ApplicationSettings(BaseSettings):
    """General application settings."""

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Application environment",
    )

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )

    enable_metrics: bool = Field(
        default=False,
        description="Enable Prometheus metrics collection",
    )

    max_workers: int = Field(
        default=4,
        ge=1,
        le=32,
        description="Maximum worker threads for concurrent operations",
    )


class Settings(BaseSettings):
    """Main application settings combining all sub-settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Sub-settings
    neo4j: Neo4jSettings = Field(default_factory=Neo4jSettings)
    embedding: EmbeddingSettings = Field(default_factory=EmbeddingSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    app: ApplicationSettings = Field(default_factory=ApplicationSettings)

    # Vector index settings
    vector_similarity_function: Literal["cosine", "euclidean"] = Field(
        default="cosine",
        description="Similarity function for vector indexes",
    )

    vector_index_name_note: str = Field(
        default="note_content_vector",
        description="Name of the Note content vector index",
    )

    vector_index_name_topic: str = Field(
        default="topic_description_vector",
        description="Name of the Topic description vector index",
    )

    vector_index_name_resource: str = Field(
        default="resource_description_vector",
        description="Name of the Resource description vector index",
    )

    # Query settings
    default_vector_search_k: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Default number of results for vector similarity search",
    )

    challenge_detection_threshold: float = Field(
        default=0.70,
        ge=0.0,
        le=1.0,
        description="Grade threshold below which challenges are flagged (0-1 scale)",
    )


# Global settings instance
settings = Settings()


# Example .env file content:
"""
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_secure_password_here
NEO4J_DATABASE=neo4j
NEO4J_MAX_CONNECTION_POOL_SIZE=50
NEO4J_ENCRYPTED=false

# Embedding Configuration
EMBEDDING_MODEL_NAME=Qwen/Qwen3-Embedding-0.6B
EMBEDDING_DIMENSIONS=896
EMBEDDING_DEVICE=cpu
EMBEDDING_BATCH_SIZE=32
EMBEDDING_NORMALIZE_EMBEDDINGS=true

# Application Configuration
APP_ENVIRONMENT=development
APP_LOG_LEVEL=INFO
APP_ENABLE_METRICS=false
APP_MAX_WORKERS=4
"""
