"""
============================================================================
Note Service - Academic Note-Taking GraphRAG System
============================================================================
Production-ready note-taking service with dynamic GraphRAG retrieval
============================================================================
"""

__version__ = "0.1.0"

from note_service.config import Settings
from note_service.retrieval import RetrievalService, SchemaIntrospector, DynamicQueryBuilder
from note_service.db.connection import Neo4jConnection

__all__ = [
    "Settings",
    "RetrievalService",
    "SchemaIntrospector",
    "DynamicQueryBuilder",
    "Neo4jConnection",
]
