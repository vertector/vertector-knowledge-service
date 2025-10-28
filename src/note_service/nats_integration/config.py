"""
NATS Consumer Configuration for GraphRAG Note Service

Integrates with vertector-nats-jetstream project for real-time academic data consumption.
"""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class NATSConsumerConfig(BaseSettings):
    """
    Configuration for NATS JetStream consumer.

    Connects to vertector-nats-jetstream for real-time academic event consumption.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="NATS_",
        case_sensitive=False,
        extra="ignore"
    )

    # NATS Connection Settings
    servers: List[str] = Field(
        default=["nats://localhost:4222"],
        description="NATS server URLs"
    )

    client_name: str = Field(
        default="graphrag-note-service",
        description="Client identifier for NATS connection"
    )

    max_reconnect_attempts: int = Field(
        default=10,
        description="Maximum reconnection attempts"
    )

    reconnect_wait_seconds: int = Field(
        default=2,
        description="Seconds to wait between reconnection attempts"
    )

    # Authentication (optional)
    username: Optional[str] = Field(
        default=None,
        description="NATS username for authentication"
    )

    password: Optional[str] = Field(
        default=None,
        description="NATS password for authentication"
    )

    token: Optional[str] = Field(
        default=None,
        description="NATS authentication token"
    )

    # TLS/SSL (optional)
    enable_tls: bool = Field(
        default=False,
        description="Enable TLS/SSL connection"
    )

    tls_cert_file: Optional[str] = Field(
        default=None,
        description="Path to TLS certificate file"
    )

    tls_key_file: Optional[str] = Field(
        default=None,
        description="Path to TLS private key file"
    )

    tls_ca_file: Optional[str] = Field(
        default=None,
        description="Path to TLS CA certificate file"
    )

    # JetStream Consumer Settings
    stream_name: str = Field(
        default="ACADEMIC_EVENTS",
        description="JetStream stream name to consume from"
    )

    durable_name: str = Field(
        default="graphrag-note-service-consumer-v2",
        description="Durable consumer name for persistence"
    )

    filter_subjects: List[str] = Field(
        default=[
            "academic.course.*",
            "academic.assignment.*",
            "academic.exam.*",
            "academic.quiz.*",
            "academic.lab.*",
            "academic.study.*",
            "academic.challenge.*",
            "academic.schedule.*",
            "academic.profile.*",
        ],
        description="Subjects to subscribe to"
    )

    batch_size: int = Field(
        default=10,
        description="Number of messages to fetch per batch"
    )

    max_waiting: int = Field(
        default=100,
        description="Maximum number of waiting pull requests"
    )

    ack_wait_seconds: int = Field(
        default=60,
        description="Seconds to wait for message acknowledgment"
    )

    max_deliver: int = Field(
        default=3,
        description="Maximum delivery attempts for failed messages"
    )

    # Processing Settings
    enable_auto_embeddings: bool = Field(
        default=True,
        description="Automatically generate embeddings during ingestion"
    )

    enable_idempotency: bool = Field(
        default=True,
        description="Track processed event IDs to prevent duplicates"
    )

    idempotency_cache_size: int = Field(
        default=10000,
        description="Maximum number of event IDs to cache for idempotency"
    )

    fetch_timeout_seconds: int = Field(
        default=5,
        description="Timeout in seconds for fetching messages from stream"
    )

    error_backoff_seconds: int = Field(
        default=5,
        description="Seconds to wait after error before retrying"
    )

    # Monitoring
    enable_metrics: bool = Field(
        default=True,
        description="Enable Prometheus metrics"
    )

    metrics_port: int = Field(
        default=9090,
        description="Port for Prometheus metrics endpoint"
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )

    log_format: str = Field(
        default="json",
        description="Log format (json or text)"
    )

    # Graceful Shutdown
    shutdown_timeout_seconds: int = Field(
        default=30,
        description="Seconds to wait for graceful shutdown"
    )

    def get_nats_connection_options(self) -> dict:
        """Get NATS connection options for client initialization."""
        options = {
            "servers": self.servers,
            "name": self.client_name,
            "max_reconnect_attempts": self.max_reconnect_attempts,
            "reconnect_time_wait": self.reconnect_wait_seconds,
        }

        if self.username and self.password:
            options["user"] = self.username
            options["password"] = self.password

        if self.token:
            options["token"] = self.token

        if self.enable_tls:
            tls_options = {}
            if self.tls_cert_file:
                tls_options["certfile"] = self.tls_cert_file
            if self.tls_key_file:
                tls_options["keyfile"] = self.tls_key_file
            if self.tls_ca_file:
                tls_options["ca_certs"] = self.tls_ca_file
            options["tls"] = tls_options

        return options

    def get_consumer_config(self) -> dict:
        """Get JetStream consumer configuration."""
        return {
            "durable_name": self.durable_name,
            "filter_subjects": self.filter_subjects,
            "ack_policy": "explicit",
            "ack_wait": self.ack_wait_seconds,
            "max_deliver": self.max_deliver,
            "max_ack_pending": self.batch_size * 2,
        }


# Global config instance
_config: Optional[NATSConsumerConfig] = None


def get_nats_config() -> NATSConsumerConfig:
    """Get or create global NATS consumer configuration."""
    global _config
    if _config is None:
        _config = NATSConsumerConfig()
    return _config


def set_nats_config(config: NATSConsumerConfig) -> None:
    """Set global NATS consumer configuration (for testing)."""
    global _config
    _config = config
