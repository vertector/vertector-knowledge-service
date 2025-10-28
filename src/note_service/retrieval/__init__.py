"""
============================================================================
Note Service - Retrieval Module
============================================================================
Dynamic retrieval with on-demand query generation for note-taking system
============================================================================
"""

from note_service.retrieval.schema_introspector import SchemaIntrospector
from note_service.retrieval.query_builder import DynamicQueryBuilder
from note_service.retrieval.service import RetrievalService
from note_service.retrieval.embedder import EmbeddingService

__all__ = [
    "SchemaIntrospector",
    "DynamicQueryBuilder",
    "RetrievalService",
    "EmbeddingService",
]
