"""
============================================================================
LectureNote CRUD Service
============================================================================
Provides complete CRUD operations for LectureNote entities with automatic
embedding generation, chunk creation, and relationship management.
============================================================================
"""

import logging
from typing import Any
from datetime import datetime

from neo4j import Driver

from note_service.ingestion.lexical_graph_manager import LexicalGraphManager
from note_service.ingestion.tag_generator import TagGenerationService
from note_service.ingestion.id_generator import IDGenerator
from note_service.retrieval.embedder import EmbeddingService

logger = logging.getLogger(__name__)


class LectureNoteService:
    """
    Service for LectureNote CRUD operations.

    Handles:
    - Create: Auto-generates ID, summary, tags, embeddings, and chunks
    - Read: Fetches note with metadata
    - Update: Updates note and regenerates embeddings/chunks if content changed
    - Delete: Removes note and all associated chunks
    - List: Query notes by student, course, or tags
    """

    def __init__(
        self,
        driver: Driver,
        embedding_service: EmbeddingService,
        lexical_graph_manager: LexicalGraphManager,
    ):
        """
        Initialize LectureNote service.

        Args:
            driver: Neo4j driver
            embedding_service: Embedding service for vectors
            lexical_graph_manager: Manager for Document/Chunk structure
        """
        self.driver = driver
        self.embedding_service = embedding_service
        self.lexical_graph_manager = lexical_graph_manager
        self.tag_generator = TagGenerationService()

    def _get_course_id_from_code(self, course_code: str, student_id: str | None = None) -> str | None:
        """
        Look up course_id from course_code, ensuring student is enrolled.

        Args:
            course_code: Course code (e.g., "CS301")
            student_id: Student ID - required to verify enrollment

        Returns:
            course_id if found and student is enrolled, None otherwise
        """
        # Parse course code into department code and number
        # E.g., "CS301" -> code="CS", number=301
        import re
        match = re.match(r'([A-Z]+)(\d+)', course_code)
        if not match:
            logger.warning(f"Invalid course code format: {course_code}")
            return None

        code, number_str = match.groups()

        if not student_id:
            logger.warning("student_id required to verify course enrollment")
            return None

        with self.driver.session() as session:
            # Verify student is enrolled in the course
            # Try both string and integer representations of number
            result = session.run(
                """
                MATCH (p:Profile {student_id: $student_id})-[:ENROLLED_IN]->(c:Course {code: $code})
                WHERE c.number = $number_str OR c.number = $number_int
                RETURN c.course_id AS course_id
                LIMIT 1
                """,
                student_id=student_id,
                code=code,
                number_str=number_str,
                number_int=int(number_str)
            )
            record = result.single()

            if record:
                logger.info(f"Student {student_id} is enrolled in {course_code}")
                return record["course_id"]
            else:
                logger.warning(f"Student {student_id} is not enrolled in {course_code} or course does not exist")
                return None

    async def create_note(
        self,
        student_id: str,
        title: str,
        content: str,
        course_id: str | None = None,
        summary: str | None = None,
        key_concepts: list[str] | None = None,
        tagged_topics: list[str] | None = None,
        lecture_note_id: str | None = None,
        **extra_properties,
    ) -> dict[str, Any]:
        """
        Create a new LectureNote with automatic processing.

        Automatically generates:
        - lecture_note_id (if not provided)
        - summary (if not provided)
        - tagged_topics (LLM-generated + manual merge)
        - embeddings (for document and chunks)
        - chunks (via lexical graph)

        Args:
            student_id: Student ID who owns the note
            title: Note title
            content: Full note content
            course_id: Optional course ID
            summary: Optional summary (auto-generated if not provided)
            key_concepts: Optional list of key concepts
            tagged_topics: Optional manual tags (will be merged with LLM-generated)
            lecture_note_id: Optional custom ID (auto-generated if not provided)
            **extra_properties: Additional properties to store

        Returns:
            Created LectureNote node properties
        """
        # Generate ID if not provided
        if not lecture_note_id:
            lecture_note_id = IDGenerator.generate_lecture_note_id(student_id=student_id)
            logger.info(f"Generated lecture_note_id: {lecture_note_id}")

        # Auto-generate summary if not provided
        if not summary and content:
            logger.info("Generating summary...")
            summary = self.tag_generator.generate_summary(
                title=title,
                content=content,
                max_sentences=3
            )
            if summary:
                logger.info(f"Generated summary: {summary[:100]}...")

        # Auto-generate and merge tags
        manual_tags = tagged_topics or []
        merged_tags = self.tag_generator.generate_and_merge_tags(
            manual_tags=manual_tags,
            title=title,
            content=content,
            summary=summary,
            key_concepts=key_concepts
        )
        logger.info(f"Merged tags: {merged_tags}")

        # Prepare properties
        properties = {
            "lecture_note_id": lecture_note_id,
            "student_id": student_id,
            "title": title,
            "content": content,
            "summary": summary,
            "key_concepts": key_concepts or [],
            "tagged_topics": merged_tags,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            **extra_properties
        }

        # Generate embedding for the document
        combined_text = "\n".join([
            title,
            content or "",
            summary or "",
            " ".join(key_concepts or [])
        ])
        embedding = self.embedding_service.embed_query(combined_text)
        properties["embedding_vector"] = embedding

        # Create lexical graph (Document + Chunks with embeddings)
        chunk_count = await self.lexical_graph_manager.create_lexical_graph_for_lecture_note(
            lecture_note_id=lecture_note_id,
            content=content,
            title=title,
            properties=properties
        )
        logger.info(f"Created {chunk_count} chunks for {lecture_note_id}")

        # Create course relationship if course_id provided
        if course_id:
            with self.driver.session() as session:
                session.run(
                    """
                    MATCH (ln:LectureNote {lecture_note_id: $lecture_note_id})
                    MATCH (c:Course {course_id: $course_id})
                    MERGE (ln)-[:BELONGS_TO]->(c)
                    """,
                    lecture_note_id=lecture_note_id,
                    course_id=course_id
                )
                logger.info(f"Linked {lecture_note_id} to course {course_id}")

        # Fetch and return the created note
        return self.get_note(lecture_note_id)

    def get_note(self, lecture_note_id: str) -> dict[str, Any]:
        """
        Fetch a LectureNote by ID.

        Args:
            lecture_note_id: Note ID

        Returns:
            Note properties with metadata

        Raises:
            ValueError: If note not found
        """
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (ln:LectureNote {lecture_note_id: $lecture_note_id})
                OPTIONAL MATCH (ln)-[:BELONGS_TO]->(c:Course)
                OPTIONAL MATCH (ln)<-[:PART_OF]-(chunk:Chunk)
                RETURN ln,
                       c.course_id AS course_id,
                       c.title AS course_title,
                       count(chunk) AS chunk_count
                """,
                lecture_note_id=lecture_note_id
            )
            record = result.single()

            if not record:
                raise ValueError(f"LectureNote {lecture_note_id} not found")

            note_data = dict(record["ln"])
            note_data["course_id"] = record["course_id"]
            note_data["course_title"] = record["course_title"]
            note_data["chunk_count"] = record["chunk_count"]

            return note_data

    async def update_note(
        self,
        lecture_note_id: str,
        title: str | None = None,
        content: str | None = None,
        summary: str | None = None,
        key_concepts: list[str] | None = None,
        tagged_topics: list[str] | None = None,
        course_id: str | None = None,
        **extra_properties,
    ) -> dict[str, Any]:
        """
        Update an existing LectureNote.

        If content is updated, automatically:
        - Regenerates summary (if not provided)
        - Regenerates tags
        - Regenerates embeddings
        - Regenerates chunks

        Args:
            lecture_note_id: Note ID to update
            title: New title (optional)
            content: New content (optional)
            summary: New summary (optional, auto-generated if content changes)
            key_concepts: New key concepts (optional)
            tagged_topics: New manual tags (optional)
            course_id: New course_id (optional)
            **extra_properties: Additional properties to update

        Returns:
            Updated LectureNote properties

        Raises:
            ValueError: If note not found
        """
        # Fetch existing note
        existing_note = self.get_note(lecture_note_id)

        # Determine what changed
        content_changed = content is not None and content != existing_note.get("content")

        # Prepare update properties
        updates = {"updated_at": datetime.utcnow().isoformat()}

        if title is not None:
            updates["title"] = title
        if content is not None:
            updates["content"] = content
        if key_concepts is not None:
            updates["key_concepts"] = key_concepts

        # Get final values for processing
        final_title = title if title is not None else existing_note.get("title", "")
        final_content = content if content is not None else existing_note.get("content", "")
        final_key_concepts = key_concepts if key_concepts is not None else existing_note.get("key_concepts", [])

        # Auto-generate summary if content changed and summary not provided
        if content_changed and summary is None:
            logger.info("Content changed - regenerating summary...")
            summary = self.tag_generator.generate_summary(
                title=final_title,
                content=final_content,
                max_sentences=3
            )

        if summary is not None:
            updates["summary"] = summary

        final_summary = summary if summary is not None else existing_note.get("summary", "")

        # Auto-generate and merge tags if content changed or tags provided
        if content_changed or tagged_topics is not None:
            manual_tags = tagged_topics or []
            merged_tags = self.tag_generator.generate_and_merge_tags(
                manual_tags=manual_tags,
                title=final_title,
                content=final_content,
                summary=final_summary,
                key_concepts=final_key_concepts
            )
            updates["tagged_topics"] = merged_tags
            logger.info(f"Updated tags: {merged_tags}")

        # Regenerate embedding if content changed
        if content_changed:
            logger.info("Content changed - regenerating embedding...")
            combined_text = "\n".join([
                final_title,
                final_content,
                final_summary,
                " ".join(final_key_concepts)
            ])
            embedding = self.embedding_service.embed_query(combined_text)
            updates["embedding_vector"] = embedding

        # Add extra properties
        updates.update(extra_properties)

        # Update the node
        with self.driver.session() as session:
            session.run(
                """
                MATCH (ln:LectureNote {lecture_note_id: $lecture_note_id})
                SET ln += $updates
                """,
                lecture_note_id=lecture_note_id,
                updates=updates
            )
            logger.info(f"Updated LectureNote {lecture_note_id}")

        # Regenerate chunks if content changed
        if content_changed:
            logger.info("Content changed - regenerating chunks...")
            # Delete old chunks
            await self.lexical_graph_manager.delete_lexical_graph_for_lecture_note(lecture_note_id)

            # Create new chunks
            updated_note = self.get_note(lecture_note_id)
            chunk_count = await self.lexical_graph_manager.create_lexical_graph_for_lecture_note(
                lecture_note_id=lecture_note_id,
                content=final_content,
                title=final_title,
                properties=updated_note
            )
            logger.info(f"Regenerated {chunk_count} chunks")

        # Update course relationship if provided
        if course_id is not None:
            with self.driver.session() as session:
                # Remove old relationship
                session.run(
                    """
                    MATCH (ln:LectureNote {lecture_note_id: $lecture_note_id})-[r:BELONGS_TO]->(:Course)
                    DELETE r
                    """,
                    lecture_note_id=lecture_note_id
                )

                # Create new relationship
                if course_id:  # Only create if not empty string
                    session.run(
                        """
                        MATCH (ln:LectureNote {lecture_note_id: $lecture_note_id})
                        MATCH (c:Course {course_id: $course_id})
                        MERGE (ln)-[:BELONGS_TO]->(c)
                        """,
                        lecture_note_id=lecture_note_id,
                        course_id=course_id
                    )
                    logger.info(f"Updated course relationship to {course_id}")

        # Return updated note
        return self.get_note(lecture_note_id)

    async def delete_note(self, lecture_note_id: str) -> bool:
        """
        Delete a LectureNote and all associated chunks.

        Args:
            lecture_note_id: Note ID to delete

        Returns:
            True if deleted, False if not found
        """
        # Delete lexical graph (chunks)
        deleted_chunks = await self.lexical_graph_manager.delete_lexical_graph_for_lecture_note(
            lecture_note_id
        )
        logger.info(f"Deleted {deleted_chunks} chunks for {lecture_note_id}")

        # Delete the LectureNote node
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (ln:LectureNote {lecture_note_id: $lecture_note_id})
                DETACH DELETE ln
                RETURN count(ln) as deleted_count
                """,
                lecture_note_id=lecture_note_id
            )
            deleted_count = result.single()["deleted_count"]

            if deleted_count > 0:
                logger.info(f"Deleted LectureNote {lecture_note_id}")
                return True
            else:
                logger.warning(f"LectureNote {lecture_note_id} not found")
                return False

    def find_note(
        self,
        student_id: str,
        title: str | None = None,
        course_code: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Find a single note by title and/or course code.

        Args:
            student_id: Student ID who owns the note
            title: Note title (case-insensitive partial match)
            course_code: Course code (e.g., "CS301")

        Returns:
            Note properties if found, None otherwise

        Raises:
            ValueError: If multiple notes match the criteria
        """
        # Build query dynamically
        query_parts = ["MATCH (ln:LectureNote {student_id: $student_id})"]
        params = {"student_id": student_id}

        where_clauses = []

        if title:
            where_clauses.append("toLower(ln.title) CONTAINS toLower($title)")
            params["title"] = title

        if course_code:
            # Parse course code
            import re
            match = re.match(r'([A-Z]+)(\d+)', course_code)
            if match:
                code, number_str = match.groups()
                query_parts.append("MATCH (ln)-[:BELONGS_TO]->(c:Course {code: $code})")
                where_clauses.append("(c.number = $number_str OR c.number = $number_int)")
                params["code"] = code
                params["number_str"] = number_str
                params["number_int"] = int(number_str)

        if where_clauses:
            query_parts.append(f"WHERE {' AND '.join(where_clauses)}")

        query_parts.extend([
            "OPTIONAL MATCH (ln)-[:BELONGS_TO]->(c2:Course)",
            "OPTIONAL MATCH (ln)<-[:PART_OF]-(chunk:Chunk)",
            """
            RETURN ln,
                   c2.course_id AS course_id,
                   c2.title AS course_title,
                   count(chunk) AS chunk_count
            """
        ])

        query = "\n".join(query_parts)

        with self.driver.session() as session:
            result = session.run(query, **params)
            records = list(result)

            if not records:
                return None

            if len(records) > 1:
                titles = [dict(r["ln"])["title"] for r in records]
                raise ValueError(
                    f"Multiple notes found matching criteria. Please be more specific.\n"
                    f"Matching notes: {', '.join(titles)}"
                )

            record = records[0]
            note_data = dict(record["ln"])
            note_data["course_id"] = record["course_id"]
            note_data["course_title"] = record["course_title"]
            note_data["chunk_count"] = record["chunk_count"]

            return note_data

    def list_notes(
        self,
        student_id: str | None = None,
        course_id: str | None = None,
        tags: list[str] | None = None,
        limit: int = 100,
        skip: int = 0,
    ) -> list[dict[str, Any]]:
        """
        List LectureNotes with optional filters.

        Args:
            student_id: Filter by student ID
            course_id: Filter by course ID
            tags: Filter by tags (notes must have at least one matching tag)
            limit: Maximum number of results
            skip: Number of results to skip

        Returns:
            List of LectureNote properties
        """
        # Build query dynamically based on filters
        query_parts = ["MATCH (ln:LectureNote)"]
        params = {"limit": limit, "skip": skip}

        # Add filters
        where_clauses = []
        if student_id:
            where_clauses.append("ln.student_id = $student_id")
            params["student_id"] = student_id

        if course_id:
            query_parts.append("MATCH (ln)-[:BELONGS_TO]->(c:Course {course_id: $course_id})")
            params["course_id"] = course_id

        if tags:
            where_clauses.append(
                f"ANY(tag IN $tags WHERE tag IN ln.tagged_topics)"
            )
            params["tags"] = tags

        if where_clauses:
            query_parts.append(f"WHERE {' AND '.join(where_clauses)}")

        # Add return and pagination
        query_parts.extend([
            "OPTIONAL MATCH (ln)-[:BELONGS_TO]->(c:Course)",
            "OPTIONAL MATCH (ln)<-[:PART_OF]-(chunk:Chunk)",
            """
            RETURN ln,
                   c.course_id AS course_id,
                   c.title AS course_title,
                   count(chunk) AS chunk_count
            ORDER BY ln.updated_at DESC
            SKIP $skip
            LIMIT $limit
            """
        ])

        query = "\n".join(query_parts)

        with self.driver.session() as session:
            result = session.run(query, **params)

            notes = []
            for record in result:
                note_data = dict(record["ln"])
                note_data["course_id"] = record["course_id"]
                note_data["course_title"] = record["course_title"]
                note_data["chunk_count"] = record["chunk_count"]
                notes.append(note_data)

            logger.info(f"Found {len(notes)} notes")
            return notes
