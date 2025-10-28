"""
NATS Data Adapter for GraphRAG Note Service

Adapts NATS event data to Neo4j ingestion via DataLoader.
Provides a clean interface for the NATS consumer to work with.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional

from ..ingestion.data_loader import DataLoader
from ..db.connection import Neo4jConnection
from ..config import Settings

logger = logging.getLogger(__name__)


class NATSDataAdapter:
    """
    Adapter between NATS events and Neo4j DataLoader.

    Translates NATS event payloads into DataLoader operations,
    handling entity creation, updates, and deletions.
    """

    def __init__(
        self,
        connection: Optional[Neo4jConnection] = None,
        settings: Optional[Settings] = None
    ):
        """
        Initialize NATS data adapter.

        Args:
            connection: Neo4j connection instance
            settings: Application settings
        """
        self.settings = settings or Settings()
        self.connection = connection or Neo4jConnection(settings=self.settings)
        self.data_loader = DataLoader(
            connection=self.connection,
            settings=self.settings
        )

        # Entity type to ID field mapping
        self.id_field_map = {
            "Course": "course_id",
            "Assignment": "assignment_id",
            "Exam": "exam_id",
            "Quiz": "quiz_id",
            "Lab_Session": "lab_id",
            "Study_Todo": "todo_id",
            "Challenge_Area": "challenge_id",
            "Class_Schedule": "schedule_id",
            "Profile": "student_id",
        }

    async def load_entity_with_embeddings(
        self,
        entity_type: str,
        entity_data: Dict[str, Any]
    ) -> None:
        """
        Create entity in Neo4j with automatic embedding generation.

        Args:
            entity_type: Type of entity (Course, Assignment, etc.)
            entity_data: Entity properties
        """
        logger.info(f"Creating {entity_type} with embeddings")

        # Add timestamps if not present
        if 'created_at' not in entity_data:
            entity_data['created_at'] = datetime.utcnow().isoformat()
        if 'updated_at' not in entity_data:
            entity_data['updated_at'] = datetime.utcnow().isoformat()

        # Get the ID field for this entity type
        id_field = self.id_field_map.get(entity_type)
        if not id_field:
            raise ValueError(f"Unknown entity type: {entity_type}")

        # Create node using DataLoader (which auto-generates embeddings)
        self.data_loader.create_node(
            label=entity_type,
            properties=entity_data,
            id_field=id_field,
            auto_embed=True
        )

        logger.info(f"Successfully created {entity_type}")

    async def load_entity(
        self,
        entity_type: str,
        entity_data: Dict[str, Any]
    ) -> None:
        """
        Create entity in Neo4j without embedding generation.

        Args:
            entity_type: Type of entity
            entity_data: Entity properties
        """
        logger.info(f"Creating {entity_type} without embeddings")

        # Add timestamps
        if 'created_at' not in entity_data:
            entity_data['created_at'] = datetime.utcnow().isoformat()
        if 'updated_at' not in entity_data:
            entity_data['updated_at'] = datetime.utcnow().isoformat()

        # Create node directly without embedding generation
        with self.connection.session() as session:
            id_field = self.id_field_map.get(entity_type)
            if not id_field:
                raise ValueError(f"Unknown entity type: {entity_type}")

            # Build property string
            props_str = ", ".join([f"{k}: ${k}" for k in entity_data.keys()])

            query = f"""
                CREATE (n:{entity_type} {{ {props_str} }})
                RETURN n
            """

            session.run(query, **entity_data)

        logger.info(f"Successfully created {entity_type}")

    async def update_entity(
        self,
        entity_type: str,
        entity_id: str,
        updates: Dict[str, Any]
    ) -> None:
        """
        Update entity properties in Neo4j.

        Args:
            entity_type: Type of entity
            entity_id: Entity identifier
            updates: Properties to update
        """
        logger.info(f"Updating {entity_type} {entity_id}")

        id_field = self.id_field_map.get(entity_type)
        if not id_field:
            raise ValueError(f"Unknown entity type: {entity_type}")

        # Add updated timestamp
        updates['updated_at'] = datetime.utcnow().isoformat()

        # Build SET clause
        set_clauses = [f"n.{k} = ${k}" for k in updates.keys()]
        set_clause = ", ".join(set_clauses)

        with self.connection.session() as session:
            query = f"""
                MATCH (n:{entity_type} {{ {id_field}: $entity_id }})
                SET {set_clause}
                RETURN n
            """

            result = session.run(query, entity_id=entity_id, **updates)
            if not result.single():
                logger.warning(f"{entity_type} {entity_id} not found for update")

        logger.info(f"Successfully updated {entity_type} {entity_id}")

    async def regenerate_embedding(
        self,
        entity_type: str,
        entity_id: str
    ) -> None:
        """
        Regenerate embedding for an entity.

        Args:
            entity_type: Type of entity
            entity_id: Entity identifier
        """
        logger.info(f"Regenerating embedding for {entity_type} {entity_id}")

        id_field = self.id_field_map.get(entity_type)
        if not id_field:
            raise ValueError(f"Unknown entity type: {entity_type}")

        # Check if entity type supports embeddings
        if entity_type not in self.data_loader.EMBEDDING_NODE_TYPES:
            logger.info(f"{entity_type} does not support embeddings, skipping")
            return

        # Get entity data
        with self.connection.session() as session:
            query = f"""
                MATCH (n:{entity_type} {{ {id_field}: $entity_id }})
                RETURN n
            """

            result = session.run(query, entity_id=entity_id)
            record = result.single()

            if not record:
                logger.warning(f"{entity_type} {entity_id} not found")
                return

            node_data = dict(record['n'])

        # Generate embedding
        embedding_config = self.data_loader.EMBEDDING_NODE_TYPES[entity_type]
        text_fields = embedding_config['text_fields']
        vector_field = embedding_config['vector_field']

        # Concatenate text fields
        text_parts = []
        for field in text_fields:
            if field in node_data and node_data[field]:
                text_parts.append(str(node_data[field]))

        if not text_parts:
            logger.warning(f"No text content found for {entity_type} {entity_id}")
            return

        combined_text = " ".join(text_parts)

        # Generate embedding
        embedding = self.data_loader.embedder.embed([combined_text])[0]

        # Update node with new embedding
        with self.connection.session() as session:
            query = f"""
                MATCH (n:{entity_type} {{ {id_field}: $entity_id }})
                SET n.{vector_field} = $embedding,
                    n.updated_at = $updated_at
                RETURN n
            """

            session.run(
                query,
                entity_id=entity_id,
                embedding=embedding.tolist(),
                updated_at=datetime.utcnow().isoformat()
            )

        logger.info(f"Successfully regenerated embedding for {entity_type} {entity_id}")

    async def soft_delete_entity(
        self,
        entity_type: str,
        entity_id: str,
        deletion_reason: Optional[str] = None
    ) -> None:
        """
        Soft delete an entity (mark as deleted).

        Args:
            entity_type: Type of entity
            entity_id: Entity identifier
            deletion_reason: Optional reason for deletion
        """
        logger.info(f"Soft deleting {entity_type} {entity_id}")

        id_field = self.id_field_map.get(entity_type)
        if not id_field:
            raise ValueError(f"Unknown entity type: {entity_type}")

        with self.connection.session() as session:
            query = f"""
                MATCH (n:{entity_type} {{ {id_field}: $entity_id }})
                SET n.deleted = true,
                    n.deleted_at = $deleted_at,
                    n.deletion_reason = $deletion_reason,
                    n.updated_at = $updated_at
                RETURN n
            """

            result = session.run(
                query,
                entity_id=entity_id,
                deleted_at=datetime.utcnow().isoformat(),
                deletion_reason=deletion_reason,
                updated_at=datetime.utcnow().isoformat()
            )

            if not result.single():
                logger.warning(f"{entity_type} {entity_id} not found for soft delete")

        logger.info(f"Successfully soft deleted {entity_type} {entity_id}")

    async def delete_entity(
        self,
        entity_type: str,
        entity_id: str
    ) -> None:
        """
        Hard delete an entity (permanently remove).

        Args:
            entity_type: Type of entity
            entity_id: Entity identifier
        """
        logger.info(f"Hard deleting {entity_type} {entity_id}")

        id_field = self.id_field_map.get(entity_type)
        if not id_field:
            raise ValueError(f"Unknown entity type: {entity_type}")

        with self.connection.session() as session:
            query = f"""
                MATCH (n:{entity_type} {{ {id_field}: $entity_id }})
                DETACH DELETE n
                RETURN count(n) as deleted_count
            """

            result = session.run(query, entity_id=entity_id)
            record = result.single()

            if record and record['deleted_count'] == 0:
                logger.warning(f"{entity_type} {entity_id} not found for delete")

        logger.info(f"Successfully hard deleted {entity_type} {entity_id}")

    def close(self):
        """Close Neo4j connection."""
        self.connection.close()
