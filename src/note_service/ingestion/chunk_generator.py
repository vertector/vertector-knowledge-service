"""
============================================================================
Chunk Generator Service
============================================================================
Generates semantic chunks from LectureNote content for granular retrieval
============================================================================
"""

import hashlib
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from neo4j import Driver

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """Represents a single chunk of content."""

    chunk_id: str
    lecture_note_id: str
    content: str
    chunk_index: int
    heading: str | None
    chunk_type: str
    token_count: int
    char_start: int
    char_end: int
    summary: str | None = None


class ChunkGenerator:
    """
    Generates semantic chunks from LectureNote content.

    Chunking Strategy:
    - Semantic chunking: Split by markdown headings (##, ###, etc.)
    - Preserve code blocks and lists as single chunks
    - Fallback to fixed-size chunking (512 tokens) for large sections
    - Add overlap between chunks for context preservation
    """

    def __init__(
        self,
        driver: Driver,
        max_chunk_tokens: int = 512,
        overlap_tokens: int = 50,
        min_chunk_tokens: int = 50,
    ):
        """
        Initialize ChunkGenerator.

        Args:
            driver: Neo4j driver instance
            max_chunk_tokens: Maximum tokens per chunk
            overlap_tokens: Overlap between consecutive chunks
            min_chunk_tokens: Minimum tokens to create a chunk
        """
        self.driver = driver
        self.max_chunk_tokens = max_chunk_tokens
        self.overlap_tokens = overlap_tokens
        self.min_chunk_tokens = min_chunk_tokens

    def generate_chunks(
        self,
        lecture_note_id: str,
        content: str,
        title: str | None = None,
    ) -> list[Chunk]:
        """
        Generate chunks from LectureNote content.

        Args:
            lecture_note_id: ID of the parent LectureNote
            content: Full content text
            title: Optional title for context

        Returns:
            List of Chunk objects
        """
        logger.info(f"Generating chunks for LectureNote: {lecture_note_id}")

        # Use semantic chunking by markdown headers
        chunks = self._semantic_chunking(content)

        # If no markdown structure, fall back to fixed-size chunking
        if len(chunks) == 1 and len(content) > self.max_chunk_tokens * 4:
            logger.info("No markdown structure found, using fixed-size chunking")
            chunks = self._fixed_size_chunking(content)

        # Merge small chunks into adjacent chunks to prevent data loss
        merged_chunks = self._merge_small_chunks(chunks)

        # Create Chunk objects with metadata
        chunk_objects = []
        char_position = 0
        actual_index = 0  # Use separate counter for sequential indexing

        for (chunk_content, heading, chunk_type) in merged_chunks:
            chunk_content = chunk_content.strip()
            if not chunk_content:
                continue

            chunk_id = self._generate_chunk_id(lecture_note_id, actual_index)
            token_count = self._estimate_tokens(chunk_content)

            # Find actual position in original content
            start_pos = content.find(chunk_content, char_position)
            if start_pos == -1:
                # Fallback if exact match not found (shouldn't happen)
                start_pos = char_position
            end_pos = start_pos + len(chunk_content)

            chunk = Chunk(
                chunk_id=chunk_id,
                lecture_note_id=lecture_note_id,
                content=chunk_content,
                chunk_index=actual_index,  # Sequential index
                heading=heading,
                chunk_type=chunk_type,
                token_count=token_count,
                char_start=start_pos,
                char_end=end_pos,
            )

            chunk_objects.append(chunk)
            char_position = end_pos
            actual_index += 1  # Increment for next chunk

        logger.info(f"Generated {len(chunk_objects)} chunks for {lecture_note_id}")
        return chunk_objects

    def _semantic_chunking(self, content: str) -> list[tuple[str, str | None, str]]:
        """
        Split content by markdown headings.

        Returns:
            List of (content, heading, chunk_type) tuples
        """
        chunks = []
        current_chunk = []
        current_heading = None
        current_type = "paragraph"

        lines = content.split("\n")
        in_code_block = False

        for line in lines:
            # Detect code blocks
            if line.strip().startswith("```"):
                if in_code_block:
                    current_chunk.append(line)
                    # End of code block - create chunk
                    chunks.append(
                        ("\n".join(current_chunk), current_heading, "code")
                    )
                    current_chunk = []
                    current_type = "paragraph"
                    in_code_block = False
                else:
                    # Start of code block
                    if current_chunk:
                        chunks.append(
                            ("\n".join(current_chunk), current_heading, current_type)
                        )
                    current_chunk = [line]
                    current_type = "code"
                    in_code_block = True
                continue

            if in_code_block:
                current_chunk.append(line)
                continue

            # Detect markdown headings
            heading_match = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
            if heading_match:
                # Save previous chunk
                if current_chunk:
                    chunks.append(
                        ("\n".join(current_chunk), current_heading, current_type)
                    )
                    current_chunk = []

                # Start new chunk with new heading
                current_heading = heading_match.group(2).strip()
                current_type = "heading"
                current_chunk = [line]
            else:
                current_chunk.append(line)

        # Add final chunk
        if current_chunk:
            chunks.append(
                ("\n".join(current_chunk), current_heading, current_type)
            )

        return chunks if chunks else [(content, None, "paragraph")]

    def _fixed_size_chunking(self, content: str) -> list[tuple[str, str | None, str]]:
        """
        Split content into fixed-size chunks with overlap.

        Returns:
            List of (content, heading, chunk_type) tuples
        """
        chunks = []
        words = content.split()
        start = 0

        while start < len(words):
            end = start + self.max_chunk_tokens
            chunk_words = words[start:end]
            chunk_content = " ".join(chunk_words)

            chunks.append((chunk_content, None, "paragraph"))

            # Move start position with overlap
            start = end - self.overlap_tokens

        return chunks

    def _merge_small_chunks(
        self,
        chunks: list[tuple[str, str | None, str]]
    ) -> list[tuple[str, str | None, str]]:
        """
        Merge small chunks into adjacent chunks to prevent data loss.

        Strategy:
        - If chunk < min_chunk_tokens, merge with previous chunk
        - If no previous chunk, merge with next chunk
        - Preserve heading from the larger chunk
        - Never discard content

        Args:
            chunks: List of (content, heading, chunk_type) tuples

        Returns:
            Merged list with no small chunks (or single small chunk if that's all there is)
        """
        if not chunks:
            return []

        # If only one chunk, keep it regardless of size
        if len(chunks) == 1:
            return chunks

        merged = []
        i = 0

        while i < len(chunks):
            current_content, current_heading, current_type = chunks[i]
            current_tokens = self._estimate_tokens(current_content)

            # If current chunk is large enough, keep it as-is
            if current_tokens >= self.min_chunk_tokens:
                merged.append((current_content, current_heading, current_type))
                i += 1
                continue

            # Current chunk is too small - need to merge
            logger.debug(
                f"Small chunk detected ({current_tokens} tokens < {self.min_chunk_tokens}): "
                f"'{current_content[:50]}...'"
            )

            # Strategy: Try to merge with previous chunk first (if exists)
            if merged:
                # Merge with previous chunk
                prev_content, prev_heading, prev_type = merged[-1]

                # Concatenate content with newline separator
                merged_content = f"{prev_content}\n\n{current_content}"

                # Keep heading from the larger chunk
                if current_tokens > self._estimate_tokens(prev_content):
                    merged_heading = current_heading
                else:
                    merged_heading = prev_heading

                # Update the previous chunk in merged list
                merged[-1] = (merged_content, merged_heading, prev_type)

                logger.debug(f"Merged small chunk into previous chunk")
                i += 1

            else:
                # No previous chunk - try to merge with next chunk
                if i + 1 < len(chunks):
                    next_content, next_heading, next_type = chunks[i + 1]

                    # Concatenate content with newline separator
                    merged_content = f"{current_content}\n\n{next_content}"

                    # Keep heading from the larger chunk
                    next_tokens = self._estimate_tokens(next_content)
                    if current_tokens > next_tokens:
                        merged_heading = current_heading
                    else:
                        merged_heading = next_heading

                    # Add merged chunk and skip next iteration
                    merged.append((merged_content, merged_heading, next_type))
                    logger.debug(f"Merged small chunk with next chunk")
                    i += 2  # Skip both current and next

                else:
                    # Only chunk left and it's small - keep it anyway
                    merged.append((current_content, current_heading, current_type))
                    logger.debug(f"Keeping small chunk as it's the only/last one")
                    i += 1

        logger.info(
            f"Merged {len(chunks)} chunks into {len(merged)} chunks "
            f"(avoided losing {len(chunks) - len(merged)} small chunks)"
        )
        return merged

    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count (rough approximation: 1 token ≈ 4 characters).

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        return len(text) // 4

    def _generate_chunk_id(self, lecture_note_id: str, index: int) -> str:
        """
        Generate unique chunk ID.

        Format: CHUNK-{lecture_note_id}-{index:03d}

        Args:
            lecture_note_id: Parent LectureNote ID
            index: Chunk index

        Returns:
            Generated chunk ID
        """
        return f"CHUNK-{lecture_note_id}-{index:03d}"

    def save_chunks_to_neo4j(
        self,
        chunks: list[Chunk],
        embedding_vectors: dict[str, list[float]] | None = None,
    ) -> int:
        """
        Save chunks to Neo4j with relationships.

        Args:
            chunks: List of Chunk objects
            embedding_vectors: Optional dict mapping chunk_id -> embedding vector

        Returns:
            Number of chunks saved
        """
        if not chunks:
            logger.warning("No chunks to save")
            return 0

        logger.info(f"Saving {len(chunks)} chunks to Neo4j")

        with self.driver.session() as session:
            # Create chunk nodes
            for chunk in chunks:
                embedding = (
                    embedding_vectors.get(chunk.chunk_id) if embedding_vectors else None
                )

                session.run(
                    """
                    MERGE (c:Chunk {chunk_id: $chunk_id})
                    ON CREATE SET
                        c.lecture_note_id = $lecture_note_id,
                        c.content = $content,
                        c.chunk_index = $chunk_index,
                        c.heading = $heading,
                        c.summary = $summary,
                        c.chunk_type = $chunk_type,
                        c.token_count = $token_count,
                        c.char_start = $char_start,
                        c.char_end = $char_end,
                        c.embedding_vector = $embedding_vector,
                        c.created_at = datetime(),
                        c.updated_at = datetime()
                    ON MATCH SET
                        c.content = $content,
                        c.heading = $heading,
                        c.summary = $summary,
                        c.chunk_type = $chunk_type,
                        c.token_count = $token_count,
                        c.char_start = $char_start,
                        c.char_end = $char_end,
                        c.embedding_vector = $embedding_vector,
                        c.updated_at = datetime()
                    """,
                    chunk_id=chunk.chunk_id,
                    lecture_note_id=chunk.lecture_note_id,
                    content=chunk.content,
                    chunk_index=chunk.chunk_index,
                    heading=chunk.heading,
                    summary=chunk.summary,
                    chunk_type=chunk.chunk_type,
                    token_count=chunk.token_count,
                    char_start=chunk.char_start,
                    char_end=chunk.char_end,
                    embedding_vector=embedding,
                )

            # Create PART_OF relationships
            for chunk in chunks:
                session.run(
                    """
                    MATCH (c:Chunk {chunk_id: $chunk_id})
                    MATCH (ln:LectureNote {lecture_note_id: $lecture_note_id})
                    MERGE (c)-[r:PART_OF]->(ln)
                    ON CREATE SET r.created_at = datetime()
                    """,
                    chunk_id=chunk.chunk_id,
                    lecture_note_id=chunk.lecture_note_id,
                )

            # Create NEXT_CHUNK relationships
            for i in range(len(chunks) - 1):
                session.run(
                    """
                    MATCH (c1:Chunk {chunk_id: $chunk_id1})
                    MATCH (c2:Chunk {chunk_id: $chunk_id2})
                    MERGE (c1)-[r:NEXT_CHUNK]->(c2)
                    ON CREATE SET r.created_at = datetime()
                    """,
                    chunk_id1=chunks[i].chunk_id,
                    chunk_id2=chunks[i + 1].chunk_id,
                )

        logger.info(f"Successfully saved {len(chunks)} chunks")
        return len(chunks)

    def delete_chunks_for_lecture_note(self, lecture_note_id: str) -> int:
        """
        Delete all chunks for a given LectureNote.

        Args:
            lecture_note_id: ID of the LectureNote

        Returns:
            Number of chunks deleted
        """
        logger.info(f"Deleting chunks for LectureNote: {lecture_note_id}")

        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (c:Chunk {lecture_note_id: $lecture_note_id})
                DETACH DELETE c
                RETURN count(c) as deleted_count
                """,
                lecture_note_id=lecture_note_id,
            )
            deleted_count = result.single()["deleted_count"]

        logger.info(f"Deleted {deleted_count} chunks")
        return deleted_count
