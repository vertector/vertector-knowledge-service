"""
============================================================================
Data Loader with Automatic Embedding Generation
============================================================================
Loads data into Neo4j and automatically generates embeddings and ensures
indices exist
============================================================================
"""

import logging
from typing import Any, Literal, List, Tuple

from note_service.config import Settings
from note_service.db.connection import Neo4jConnection
from note_service.retrieval.embedder import EmbeddingService
from note_service.ingestion.relationships import RelationshipManager

logger = logging.getLogger(__name__)


class DataLoader:
    """
    Loads data into Neo4j with automatic embedding generation.

    Features:
    - Auto-generates embeddings for nodes that support vector search
    - Ensures fulltext indices exist
    - Ensures vector indices exist with correct dimensions
    """

    # Node types that require embeddings
    EMBEDDING_NODE_TYPES = {
        # Original note-taking entities
        "Note": {"text_fields": ["title", "content"], "vector_field": "embedding_vector"},
        "Topic": {"text_fields": ["name", "description"], "vector_field": "embedding_vector"},
        "Resource": {"text_fields": ["title", "description"], "vector_field": "embedding_vector"},
        "Lecture": {"text_fields": ["title", "transcript", "key_concepts"], "vector_field": "embedding_vector"},
        "Challenge_Area": {"text_fields": ["title", "description"], "vector_field": "embedding_vector"},

        # Academic entities from NATS integration
        "Course": {"text_fields": ["title", "description", "learning_objectives"], "vector_field": "embedding_vector"},
        "Assignment": {"text_fields": ["title", "description"], "vector_field": "embedding_vector"},
        "Exam": {"text_fields": ["title", "topics_covered", "preparation_notes"], "vector_field": "embedding_vector"},
        "Quiz": {"text_fields": ["title", "topics_covered"], "vector_field": "embedding_vector"},
        "Lab_Session": {"text_fields": ["title", "experiment_title", "objectives"], "vector_field": "embedding_vector"},
        "Study_Todo": {"text_fields": ["title", "description"], "vector_field": "embedding_vector"},
        "Challenge_Area": {"text_fields": ["title", "description", "related_topics"], "vector_field": "embedding_vector"},
    }

    # Fulltext index definitions
    FULLTEXT_INDICES = [
        # Original note-taking entities
        {"name": "note_title_text", "label": "Note", "property": "title"},
        {"name": "note_content_text", "label": "Note", "property": "content"},
        {"name": "topic_name_text", "label": "Topic", "property": "name"},
        {"name": "topic_description_text", "label": "Topic", "property": "description"},
        {"name": "resource_title_text", "label": "Resource", "property": "title"},
        {"name": "resource_description_text", "label": "Resource", "property": "description"},

        # Academic entities from NATS integration
        {"name": "course_title_text", "label": "Course", "property": "title"},
        {"name": "course_description_text", "label": "Course", "property": "description"},
        {"name": "assignment_title_text", "label": "Assignment", "property": "title"},
        {"name": "assignment_description_text", "label": "Assignment", "property": "description"},
        {"name": "exam_title_text", "label": "Exam", "property": "title"},
        {"name": "exam_preparation_text", "label": "Exam", "property": "preparation_notes"},
        {"name": "quiz_title_text", "label": "Quiz", "property": "title"},
        {"name": "lab_title_text", "label": "Lab_Session", "property": "title"},
        {"name": "lab_experiment_text", "label": "Lab_Session", "property": "experiment_title"},
        {"name": "study_todo_title_text", "label": "Study_Todo", "property": "title"},
        {"name": "study_todo_description_text", "label": "Study_Todo", "property": "description"},
        {"name": "challenge_title_text", "label": "Challenge_Area", "property": "title"},
        {"name": "challenge_description_text", "label": "Challenge_Area", "property": "description"},
    ]

    def __init__(self, connection: Neo4jConnection, settings: Settings):
        """
        Initialize data loader.

        Args:
            connection: Neo4j connection
            settings: Application settings
        """
        self.connection = connection
        self.settings = settings
        self.embedder = EmbeddingService(
            model_name=settings.embedding.model_name,
            device=settings.embedding.device,
            cache_folder=settings.embedding.cache_folder,
            normalize_embeddings=settings.embedding.normalize_embeddings,
            batch_size=settings.embedding.batch_size,
        )

    def ensure_indices_exist(self):
        """Ensure all required fulltext and vector indices exist."""
        logger.info("Ensuring indices exist...")
        self._ensure_fulltext_indices()
        self._ensure_vector_indices()
        logger.info("All indices verified/created")

    def _ensure_fulltext_indices(self):
        """Create fulltext indices compatible with db.index.fulltext.queryNodes()."""
        with self.connection.session() as session:
            for index_def in self.FULLTEXT_INDICES:
                try:
                    # CRITICAL: Must include OPTIONS clause to create queryable fulltext index
                    session.run(
                        f"""
                        CREATE FULLTEXT INDEX {index_def['name']} IF NOT EXISTS
                        FOR (n:{index_def['label']})
                        ON EACH [n.{index_def['property']}]
                        OPTIONS {{
                          indexConfig: {{
                            `fulltext.analyzer`: 'standard'
                          }}
                        }}
                        """
                    )
                    logger.info(f"  ✓ Fulltext index: {index_def['name']}")
                except Exception as e:
                    # Index might already exist
                    if "already exists" in str(e).lower() or "equivalent" in str(e).lower():
                        logger.info(f"  ✓ Fulltext index: {index_def['name']} (already exists)")
                    else:
                        logger.warning(f"  ⚠ Could not create {index_def['name']}: {e}")

    def _ensure_vector_indices(self):
        """Create vector indices if they don't exist."""
        dimensions = self.settings.embedding.dimensions
        similarity_fn = self.settings.vector_similarity_function

        vector_indices = [
            {"name": "note_content_vector", "label": "Note", "property": "embedding_vector"},
            {"name": "topic_description_vector", "label": "Topic", "property": "embedding_vector"},
            {"name": "resource_description_vector", "label": "Resource", "property": "embedding_vector"},
            {"name": "lecture_content_vector", "label": "Lecture", "property": "embedding_vector"},
            {"name": "challenge_description_vector", "label": "Challenge_Area", "property": "embedding_vector"},
        ]

        with self.connection.session() as session:
            for index_def in vector_indices:
                try:
                    session.run(
                        f"""
                        CREATE VECTOR INDEX {index_def['name']} IF NOT EXISTS
                        FOR (n:{index_def['label']})
                        ON n.{index_def['property']}
                        OPTIONS {{
                          indexConfig: {{
                            `vector.dimensions`: {dimensions},
                            `vector.similarity_function`: '{similarity_fn}'
                          }}
                        }}
                        """
                    )
                    logger.info(f"  ✓ Vector index: {index_def['name']} ({dimensions}d)")
                except Exception as e:
                    logger.warning(f"  ⚠ Could not create {index_def['name']}: {e}")

    def create_node(
        self,
        label: str,
        properties: dict[str, Any],
        id_field: str,
        auto_embed: bool = True,
        create_relationships: bool = True,
    ) -> dict[str, Any]:
        """
        Create or update a node with automatic embedding generation and relationships.

        Args:
            label: Node label (e.g., "Note", "Topic")
            properties: Node properties
            id_field: Name of the ID field (e.g., "note_id", "topic_id")
            auto_embed: Whether to automatically generate embeddings
            create_relationships: Whether to automatically create relationships

        Returns:
            Created/updated node properties
        """
        # Generate embedding if this node type supports it
        if auto_embed and label in self.EMBEDDING_NODE_TYPES:
            logger.info(f"Auto-embedding enabled for {label}")
            embedding_config = self.EMBEDDING_NODE_TYPES[label]
            embedding = self._generate_embedding_for_node(properties, embedding_config)
            if embedding:
                logger.info(f"Generated embedding for {label}: {len(embedding)} dimensions")
                properties[embedding_config["vector_field"]] = embedding
            else:
                logger.warning(f"No embedding generated for {label} - no text content found")
        elif auto_embed:
            logger.warning(f"{label} not in EMBEDDING_NODE_TYPES - skipping embedding generation")

        # Create or update node
        with self.connection.session() as session:
            result = session.run(
                f"""
                MERGE (n:{label} {{{id_field}: $id}})
                ON CREATE SET n.created_at = datetime()
                SET n += $properties,
                    n.updated_at = datetime()
                RETURN n
                """,
                id=properties[id_field],
                properties=properties
            )
            node = result.single()["n"]
            node_id = properties[id_field]
            logger.info(f"Created/updated {label}: {properties.get('title') or properties.get('name') or node_id}")

            # Create relationships if enabled
            if create_relationships:
                relationship_manager = RelationshipManager(session)
                created_rels = relationship_manager.create_relationships_for_node(
                    label=label,
                    node_id=node_id,
                    id_field=id_field,
                    properties=properties
                )
                if created_rels:
                    logger.info(f"Created {len(created_rels)} relationship(s) for {label} {node_id}")

            return dict(node)

    def generate_embeddings_for_existing_nodes(self, label: str | None = None):
        """
        Generate embeddings for existing nodes without embeddings.

        Args:
            label: Specific node label to process, or None for all embedding types
        """
        labels_to_process = [label] if label else list(self.EMBEDDING_NODE_TYPES.keys())

        for node_label in labels_to_process:
            if node_label not in self.EMBEDDING_NODE_TYPES:
                logger.warning(f"Node type {node_label} does not support embeddings")
                continue

            self._generate_embeddings_for_label(node_label)

    def rebuild_all_relationships(self) -> dict[str, int]:
        """
        Rebuild all relationships for existing nodes in the knowledge graph.

        Useful for backfilling relationships after implementing relationship logic
        or for fixing broken relationships.

        Returns:
            Dictionary mapping relationship types to count created
        """
        logger.info("Rebuilding all relationships in the knowledge graph...")

        with self.connection.session() as session:
            relationship_manager = RelationshipManager(session)
            relationship_counts = relationship_manager.rebuild_all_relationships()

        logger.info(f"Relationship rebuild complete: {relationship_counts}")
        return relationship_counts

    def _generate_embeddings_for_label(self, label: str):
        """Generate embeddings for all nodes of a specific label."""
        config = self.EMBEDDING_NODE_TYPES[label]
        logger.info(f"Generating embeddings for {label} nodes...")

        with self.connection.session() as session:
            # Find nodes without embeddings
            result = session.run(
                f"""
                MATCH (n:{label})
                WHERE n.{config['vector_field']} IS NULL
                RETURN n
                """
            )
            nodes = list(result)

            if not nodes:
                logger.info(f"  No {label} nodes need embeddings")
                return

            logger.info(f"  Found {len(nodes)} {label} nodes without embeddings")

            # Generate embeddings
            for i, record in enumerate(nodes, 1):
                node = record["n"]
                node_props = dict(node)

                # Generate embedding
                embedding = self._generate_embedding_for_node(node_props, config)

                if embedding:
                    # Update node
                    session.run(
                        f"""
                        MATCH (n:{label})
                        WHERE elementId(n) = $element_id
                        SET n.{config['vector_field']} = $embedding
                        """,
                        element_id=node.element_id,
                        embedding=embedding
                    )

                    name = node_props.get('title') or node_props.get('name') or f"{label}_{i}"
                    logger.info(f"  [{i}/{len(nodes)}] ✓ {name}")

        logger.info(f"Completed {label} embeddings\n")

    def _generate_embedding_for_node(
        self, properties: dict[str, Any], config: dict[str, Any]
    ) -> list[float] | None:
        """
        Generate embedding from node properties.

        Args:
            properties: Node properties
            config: Embedding configuration with text_fields

        Returns:
            Embedding vector or None if no text available
        """
        # Collect text from specified fields
        text_parts = []
        for field in config["text_fields"]:
            value = properties.get(field)
            if value:
                if isinstance(value, str):
                    text_parts.append(value)
                elif isinstance(value, list):
                    # Handle list fields like key_concepts
                    text_parts.append(" ".join(str(v) for v in value))

        if not text_parts:
            return None

        # Combine text
        combined_text = "\n".join(text_parts)

        # Generate embedding
        return self.embedder.embed_query(combined_text)
