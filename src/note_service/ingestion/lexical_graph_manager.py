"""
============================================================================
Lexical Graph Manager
============================================================================
Manages Document and Chunk nodes using Neo4j GraphRAG official structure.

Uses Neo4j's official lexical graph pattern:
- Document nodes (LectureNote as documents)
- Chunk nodes (text segments)
- PART_OF_DOCUMENT relationships
- NEXT_CHUNK relationships
============================================================================
"""

import logging
from typing import Any
from dataclasses import dataclass

from neo4j import Driver
from neo4j_graphrag.experimental.components.text_splitters.fixed_size_splitter import FixedSizeSplitter
from neo4j_graphrag.experimental.components.types import (
    LexicalGraphConfig,
    TextChunk,
    TextChunks,
    DocumentInfo,
)
from neo4j_graphrag.experimental.components.embedder import TextChunkEmbedder
from neo4j_graphrag.experimental.components.lexical_graph import LexicalGraphBuilder
from neo4j_graphrag.experimental.components.kg_writer import Neo4jWriter

from note_service.retrieval.embedder import EmbeddingService

logger = logging.getLogger(__name__)


@dataclass
class LectureNoteLexicalGraphConfig:
    """
    Configuration for LectureNote lexical graph.

    Maps LectureNote concepts to Neo4j GraphRAG lexical graph:
    - LectureNote → Document node
    - Content chunks → Chunk nodes
    """
    chunk_size: int = 500  # Characters per chunk (not tokens)
    chunk_overlap: int = 100  # Character overlap between chunks

    # Neo4j GraphRAG lexical graph structure
    document_node_label: str = "LectureNote"  # Use LectureNote as document
    chunk_node_label: str = "Chunk"
    chunk_to_document_relationship_type: str = "PART_OF"
    next_chunk_relationship_type: str = "NEXT_CHUNK"
    chunk_embedding_property: str = "embedding_vector"
    chunk_id_property: str = "chunk_id"
    chunk_text_property: str = "content"


class LexicalGraphManager:
    """
    Manages lexical graph creation using Neo4j GraphRAG official components.

    Architecture:
    1. Text Splitting: FixedSizeSplitter
    2. Embedding: TextChunkEmbedder (wraps our EmbeddingService)
    3. Graph Building: LexicalGraphBuilder
    """

    def __init__(
        self,
        driver: Driver,
        embedding_service: EmbeddingService,
        config: LectureNoteLexicalGraphConfig | None = None
    ):
        """
        Initialize lexical graph manager.

        Args:
            driver: Neo4j driver instance
            embedding_service: Embedding service for generating vectors
            config: Optional configuration (uses defaults if not provided)
        """
        self.driver = driver
        self.embedding_service = embedding_service
        self.config = config or LectureNoteLexicalGraphConfig()

        # Initialize Neo4j GraphRAG components
        self._init_components()

    def _init_components(self):
        """Initialize Neo4j GraphRAG components."""
        # Text splitter with approximate=True to avoid splitting words
        self.text_splitter = FixedSizeSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            approximate=True  # Clean chunk boundaries
        )

        # Lexical graph configuration
        self.lexical_config = LexicalGraphConfig(
            document_node_label=self.config.document_node_label,
            chunk_node_label=self.config.chunk_node_label,
            chunk_to_document_relationship_type=self.config.chunk_to_document_relationship_type,
            next_chunk_relationship_type=self.config.next_chunk_relationship_type,
            chunk_embedding_property=self.config.chunk_embedding_property,
            chunk_id_property=self.config.chunk_id_property,
            chunk_text_property=self.config.chunk_text_property,
        )

        # Lexical graph builder (creates in-memory graph structure)
        self.graph_builder = LexicalGraphBuilder(
            config=self.lexical_config
        )

        # Neo4j writer (persists graph to database)
        self.neo4j_writer = Neo4jWriter(driver=self.driver)

        logger.info(
            f"Initialized LexicalGraphManager: "
            f"chunk_size={self.config.chunk_size}, "
            f"overlap={self.config.chunk_overlap}"
        )

    async def create_lexical_graph_for_lecture_note(
        self,
        lecture_note_id: str,
        content: str,
        title: str,
        properties: dict[str, Any] | None = None
    ) -> int:
        """
        Create lexical graph for a LectureNote.

        Process:
        1. Split content into chunks
        2. Generate embeddings for each chunk
        3. Build graph with Document and Chunk nodes
        4. Create PART_OF and NEXT_CHUNK relationships

        Args:
            lecture_note_id: Unique ID for the lecture note
            content: Full text content
            title: Note title
            properties: Optional additional properties for the document node

        Returns:
            Number of chunks created
        """
        if not content or len(content.strip()) == 0:
            logger.info(f"Skipping chunk generation for {lecture_note_id} - no content")
            return 0

        try:
            logger.info(f"🔄 Creating lexical graph for LectureNote {lecture_note_id}...")

            # Step 1: Split text into chunks
            logger.info(f"Splitting text ({len(content)} chars)...")
            text_chunks_result = await self.text_splitter.run(text=content)
            raw_chunks = text_chunks_result.chunks

            if not raw_chunks:
                logger.warning(f"No chunks generated for {lecture_note_id}")
                return 0

            logger.info(f"✅ Created {len(raw_chunks)} chunks")

            # Step 2: Generate embeddings for chunks
            logger.info(f"Generating embeddings for {len(raw_chunks)} chunks...")
            chunk_texts = [chunk.text for chunk in raw_chunks]
            embeddings = self.embedding_service.embed_documents(
                chunk_texts,
                prompt_name="document"
            )

            # Add embeddings to chunks
            chunks_with_embeddings = []
            for i, chunk in enumerate(raw_chunks):
                embedding_vector = (
                    embeddings[i].tolist()
                    if hasattr(embeddings[i], 'tolist')
                    else embeddings[i]
                )

                # Create TextChunk with embedding
                chunks_with_embeddings.append(
                    TextChunk(
                        text=chunk.text,
                        index=chunk.index,
                        metadata={
                            "embedding": embedding_vector,
                            "chunk_id": f"{lecture_note_id}-chunk-{chunk.index:03d}"
                        }
                    )
                )

            logger.info(f"✅ Generated {len(embeddings)} embeddings")

            # Step 3: Build lexical graph
            logger.info(f"Building lexical graph in Neo4j...")

            # Create DocumentInfo for the LectureNote
            # Filter metadata to only include string values (DocumentInfo requirement)
            doc_properties = properties or {}
            filtered_metadata = {
                "lecture_note_id": lecture_note_id,
                "title": title,
            }

            # Only include string/number/bool values in metadata
            for key, value in doc_properties.items():
                if isinstance(value, (str, int, float, bool)) and value is not None:
                    filtered_metadata[key] = str(value)

            document_info = DocumentInfo(
                document_id=lecture_note_id,
                path=title,  # Use title as path
                metadata=filtered_metadata
            )

            # Build graph using Neo4j GraphRAG (creates in-memory graph)
            graph_result = await self.graph_builder.run(
                text_chunks=TextChunks(chunks=chunks_with_embeddings),
                document_info=document_info
            )

            logger.info(f"✅ Built in-memory lexical graph")

            # Write graph to Neo4j database
            # Note: graph_result.graph contains the actual Neo4jGraph object
            logger.info(f"Writing lexical graph to Neo4j...")
            await self.neo4j_writer.run(graph_result.graph)

            logger.info(
                f"✅ Created lexical graph in Neo4j: "
                f"1 Document ({lecture_note_id}), "
                f"{len(chunks_with_embeddings)} Chunks"
            )

            return len(chunks_with_embeddings)

        except Exception as e:
            logger.error(f"Error creating lexical graph for {lecture_note_id}: {e}", exc_info=True)
            raise

    async def delete_lexical_graph_for_lecture_note(self, lecture_note_id: str) -> int:
        """
        Delete all chunks for a LectureNote.

        Args:
            lecture_note_id: ID of the LectureNote

        Returns:
            Number of chunks deleted
        """
        logger.info(f"Deleting lexical graph for LectureNote: {lecture_note_id}")

        with self.driver.session() as session:
            result = session.run(
                f"""
                MATCH (c:{self.config.chunk_node_label})-[:{self.config.chunk_to_document_relationship_type}]->
                      (d:{self.config.document_node_label} {{lecture_note_id: $lecture_note_id}})
                DETACH DELETE c
                RETURN count(c) as deleted_count
                """,
                lecture_note_id=lecture_note_id,
            )
            deleted_count = result.single()["deleted_count"]

        logger.info(f"Deleted {deleted_count} chunks")
        return deleted_count
