"""
============================================================================
Schema Introspection Service
============================================================================
Dynamically extracts and caches Neo4j graph schema using APOC procedures
============================================================================
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from neo4j import Driver

logger = logging.getLogger(__name__)


@dataclass
class PropertyMetadata:
    """Metadata for a node or relationship property."""

    name: str
    type: str
    indexed: bool = False
    unique: bool = False
    existence: bool = False
    array: bool = False


@dataclass
class RelationshipMetadata:
    """Metadata for a relationship type."""

    type: str
    direction: str
    target_labels: list[str]
    count: int
    properties: dict[str, PropertyMetadata]


@dataclass
class NodeMetadata:
    """Metadata for a node label."""

    label: str
    count: int
    properties: dict[str, PropertyMetadata]
    relationships: dict[str, RelationshipMetadata]


@dataclass
class GraphSchema:
    """Complete graph schema representation."""

    nodes: dict[str, NodeMetadata]
    relationships: dict[str, dict[str, Any]]
    vector_indexes: list[dict[str, Any]]
    fulltext_indexes: list[dict[str, Any]]
    constraints: list[dict[str, Any]]
    last_updated: datetime


class SchemaIntrospector:
    """
    Introspects Neo4j graph schema dynamically using APOC procedures.
    Caches results to minimize database queries.
    """

    def __init__(
        self,
        driver: Driver,
        cache_ttl_seconds: int = 300,
        sample_size: int = 1000,
    ):
        """
        Initialize schema introspector.

        Args:
            driver: Neo4j driver instance
            cache_ttl_seconds: How long to cache schema (default 5 minutes)
            sample_size: Number of nodes to sample for schema analysis
        """
        self.driver = driver
        self.cache_ttl = timedelta(seconds=cache_ttl_seconds)
        self.sample_size = sample_size
        self._cached_schema: GraphSchema | None = None
        self._cache_timestamp: datetime | None = None

    def get_schema(self, use_cache: bool = True) -> GraphSchema:
        """
        Get complete graph schema.

        Args:
            use_cache: Whether to use cached schema if available

        Returns:
            GraphSchema object with complete schema metadata
        """
        if use_cache and self._is_cache_valid():
            logger.debug("Using cached schema")
            return self._cached_schema

        logger.info("Introspecting graph schema from database")
        schema = self._introspect_schema()
        self._cached_schema = schema
        self._cache_timestamp = datetime.now()
        return schema

    def invalidate_cache(self) -> None:
        """Force cache invalidation to refresh schema on next request."""
        self._cached_schema = None
        self._cache_timestamp = None
        logger.info("Schema cache invalidated")

    def _is_cache_valid(self) -> bool:
        """Check if cached schema is still valid."""
        if self._cached_schema is None or self._cache_timestamp is None:
            return False
        age = datetime.now() - self._cache_timestamp
        return age < self.cache_ttl

    def _introspect_schema(self) -> GraphSchema:
        """Introspect schema from Neo4j using APOC procedures."""
        with self.driver.session() as session:
            meta_schema = self._get_apoc_meta_schema(session)
            vector_indexes = self._get_vector_indexes(session)
            fulltext_indexes = self._get_fulltext_indexes(session)
            constraints = self._get_constraints(session)

        nodes, relationships = self._parse_meta_schema(meta_schema)

        return GraphSchema(
            nodes=nodes,
            relationships=relationships,
            vector_indexes=vector_indexes,
            fulltext_indexes=fulltext_indexes,
            constraints=constraints,
            last_updated=datetime.now(),
        )

    def _get_apoc_meta_schema(self, session) -> dict[str, Any]:
        """Get schema metadata using apoc.meta.schema()."""
        query = f"""
        CALL apoc.meta.schema({{sample: {self.sample_size}}})
        YIELD value
        RETURN value
        """
        result = session.run(query)
        record = result.single()
        if not record:
            raise RuntimeError("Failed to retrieve schema from apoc.meta.schema()")
        return record["value"]

    def _get_vector_indexes(self, session) -> list[dict[str, Any]]:
        """Get all vector indexes."""
        query = """
        SHOW INDEXES
        YIELD name, type, labelsOrTypes, properties, options
        WHERE type = 'VECTOR'
        RETURN name, labelsOrTypes, properties, options
        """
        result = session.run(query)
        return [
            {
                "name": record["name"],
                "labels": record["labelsOrTypes"],
                "properties": record["properties"],
                "options": record["options"],
            }
            for record in result
        ]

    def _get_fulltext_indexes(self, session) -> list[dict[str, Any]]:
        """Get all full-text indexes (FULLTEXT type with OPTIONS)."""
        query = """
        SHOW INDEXES
        YIELD name, type, labelsOrTypes, properties
        WHERE type = 'FULLTEXT'
        RETURN name, labelsOrTypes, properties
        """
        result = session.run(query)
        return [
            {
                "name": record["name"],
                "labels": record["labelsOrTypes"],
                "properties": record["properties"],
            }
            for record in result
        ]

    def _get_constraints(self, session) -> list[dict[str, Any]]:
        """Get all constraints."""
        query = """
        SHOW CONSTRAINTS
        YIELD name, type, labelsOrTypes, properties
        RETURN name, type, labelsOrTypes, properties
        """
        result = session.run(query)
        return [
            {
                "name": record["name"],
                "type": record["type"],
                "labels": record["labelsOrTypes"],
                "properties": record["properties"],
            }
            for record in result
        ]

    def _parse_meta_schema(
        self, meta_schema: dict[str, Any]
    ) -> tuple[dict[str, NodeMetadata], dict[str, dict[str, Any]]]:
        """Parse APOC meta.schema output into structured format."""
        nodes: dict[str, NodeMetadata] = {}
        relationships: dict[str, dict[str, Any]] = {}

        for label, metadata in meta_schema.items():
            if metadata.get("type") == "node":
                nodes[label] = self._parse_node_metadata(label, metadata)
            elif metadata.get("type") == "relationship":
                relationships[label] = self._parse_relationship_only_metadata(metadata)

        return nodes, relationships

    def _parse_node_metadata(self, label: str, metadata: dict[str, Any]) -> NodeMetadata:
        """Parse node metadata from APOC output."""
        properties = {}
        for prop_name, prop_data in metadata.get("properties", {}).items():
            properties[prop_name] = PropertyMetadata(
                name=prop_name,
                type=prop_data.get("type", "UNKNOWN"),
                indexed=prop_data.get("indexed", False),
                unique=prop_data.get("unique", False),
                existence=prop_data.get("existence", False),
                array=prop_data.get("array", False),
            )

        relationships = {}
        for rel_type, rel_data in metadata.get("relationships", {}).items():
            relationships[rel_type] = self._parse_relationship_metadata(rel_type, rel_data)

        return NodeMetadata(
            label=label,
            count=metadata.get("count", 0),
            properties=properties,
            relationships=relationships,
        )

    def _parse_relationship_metadata(
        self, rel_type: str, rel_data: dict[str, Any]
    ) -> RelationshipMetadata:
        """Parse relationship metadata from node's relationships."""
        properties = {}
        for prop_name, prop_data in rel_data.get("properties", {}).items():
            properties[prop_name] = PropertyMetadata(
                name=prop_name,
                type=prop_data.get("type", "UNKNOWN"),
                array=prop_data.get("array", False),
            )

        return RelationshipMetadata(
            type=rel_type,
            direction=rel_data.get("direction", "out"),
            target_labels=rel_data.get("labels", []),
            count=rel_data.get("count", 0),
            properties=properties,
        )

    def _parse_relationship_only_metadata(self, metadata: dict[str, Any]) -> dict[str, Any]:
        """Parse standalone relationship metadata."""
        properties = {}
        for prop_name, prop_data in metadata.get("properties", {}).items():
            properties[prop_name] = {
                "type": prop_data.get("type", "UNKNOWN"),
                "array": prop_data.get("array", False),
            }

        return {
            "count": metadata.get("count", 0),
            "properties": properties,
        }

    def format_schema_for_llm(self, schema: GraphSchema | None = None) -> str:
        """
        Format schema as text for LLM consumption.

        Args:
            schema: GraphSchema to format, or None to use cached schema

        Returns:
            Formatted schema string for LLM prompts
        """
        if schema is None:
            schema = self.get_schema()

        lines = ["# Graph Schema\n"]

        lines.append("## Node Labels and Properties\n")
        for label, node in sorted(schema.nodes.items()):
            props = ", ".join(
                f"{name}: {prop.type}" for name, prop in node.properties.items()
            )
            lines.append(f"{label} {{{props}}}")

        lines.append("\n## Relationships\n")
        for label, node in sorted(schema.nodes.items()):
            for rel_type, rel in node.relationships.items():
                targets = ", ".join(rel.target_labels)
                if rel.direction == "out":
                    lines.append(f"(:{label})-[:{rel_type}]->(:{targets})")
                else:
                    lines.append(f"(:{label})<-[:{rel_type}]-(:{targets})")

        lines.append("\n## Vector Indexes\n")
        for idx in schema.vector_indexes:
            labels = ", ".join(idx["labels"])
            props = ", ".join(idx["properties"])
            dims = idx["options"].get("indexConfig", {}).get("vector.dimensions", "?")
            lines.append(f"- {idx['name']}: {labels}.{props} ({dims} dimensions)")

        lines.append("\n## Full-Text Indexes\n")
        for idx in schema.fulltext_indexes:
            labels = ", ".join(idx["labels"])
            props = ", ".join(idx["properties"])
            lines.append(f"- {idx['name']}: {labels}.{props}")

        return "\n".join(lines)

    def get_vector_index_names(self, schema: GraphSchema | None = None) -> list[str]:
        """Get list of all vector index names."""
        if schema is None:
            schema = self.get_schema()
        return [idx["name"] for idx in schema.vector_indexes]

    def get_fulltext_index_names(self, schema: GraphSchema | None = None) -> list[str]:
        """Get list of all full-text index names."""
        if schema is None:
            schema = self.get_schema()
        return [idx["name"] for idx in schema.fulltext_indexes]
