"""
NATS Integration for GraphRAG Note Service

This module provides NATS JetStream integration for real-time academic data consumption.

Components:
- consumer: NATS JetStream consumer for event processing
- data_adapter: Adapter between NATS events and Neo4j DataLoader
- config: Configuration for NATS consumer
- profile_client: HTTP client for Profile Service REST API
- models: GraphRAG-aligned Pydantic event models

Usage:
    from note_service.nats_integration import NATSConsumer, ProfileServiceClient

    consumer = NATSConsumer()
    await consumer.run()

    profile_client = ProfileServiceClient()
    profile = await profile_client.get_profile("S12345")
"""

from .consumer import NATSConsumer
from .data_adapter import NATSDataAdapter
from .config import NATSConsumerConfig, get_nats_config, set_nats_config
from .profile_client import ProfileServiceClient

__all__ = [
    "NATSConsumer",
    "NATSDataAdapter",
    "NATSConsumerConfig",
    "get_nats_config",
    "set_nats_config",
    "ProfileServiceClient",
]
