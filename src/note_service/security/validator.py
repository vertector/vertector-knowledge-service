"""
============================================================================
Security Validator
============================================================================
Database-level validation of student data access permissions.
Verifies ownership and prevents unauthorized access.
============================================================================
"""

import logging
from typing import List, Optional

from neo4j import Driver, Session

logger = logging.getLogger(__name__)


class SecurityValidator:
    """
    Validates student data access at the database level.

    Provides methods to verify that a student owns specific data
    before allowing access. This creates a defense-in-depth security layer
    beyond application-level filtering.
    """

    def __init__(self, driver: Driver):
        """
        Initialize security validator.

        Args:
            driver: Neo4j driver for database access
        """
        self.driver = driver

    def verify_note_ownership(
        self,
        student_id: str,
        lecture_note_id: str,
        session: Optional[Session] = None
    ) -> bool:
        """
        Verify that a student owns a specific lecture note.

        Args:
            student_id: Student ID to check
            lecture_note_id: Lecture note ID to verify
            session: Optional existing Neo4j session

        Returns:
            True if student owns the note, False otherwise
        """
        query = """
        MATCH (p:Profile {student_id: $student_id})-[:CREATED_NOTE]->(ln:LectureNote {lecture_note_id: $lecture_note_id})
        RETURN count(ln) > 0 AS owns
        """

        params = {
            'student_id': student_id,
            'lecture_note_id': lecture_note_id
        }

        try:
            if session:
                result = session.run(query, params)
                record = result.single()
            else:
                with self.driver.session() as new_session:
                    result = new_session.run(query, params)
                    record = result.single()

            owns = record['owns'] if record else False

            if not owns:
                logger.warning(
                    f"Access denied: Student {student_id} attempted to access "
                    f"lecture note {lecture_note_id} they don't own"
                )

            return owns

        except Exception as e:
            logger.error(f"Error verifying note ownership: {e}", exc_info=True)
            return False

    def verify_chunk_ownership(
        self,
        student_id: str,
        chunk_id: str,
        session: Optional[Session] = None
    ) -> bool:
        """
        Verify that a student owns a specific chunk (via parent note).

        Args:
            student_id: Student ID to check
            chunk_id: Chunk ID to verify
            session: Optional existing Neo4j session

        Returns:
            True if student owns the chunk's parent note, False otherwise
        """
        query = """
        MATCH (p:Profile {student_id: $student_id})-[:CREATED_NOTE]->(ln:LectureNote)<-[:PART_OF]-(c:Chunk {chunk_id: $chunk_id})
        RETURN count(c) > 0 AS owns
        """

        params = {
            'student_id': student_id,
            'chunk_id': chunk_id
        }

        try:
            if session:
                result = session.run(query, params)
                record = result.single()
            else:
                with self.driver.session() as new_session:
                    result = new_session.run(query, params)
                    record = result.single()

            owns = record['owns'] if record else False

            if not owns:
                logger.warning(
                    f"Access denied: Student {student_id} attempted to access "
                    f"chunk {chunk_id} they don't own"
                )

            return owns

        except Exception as e:
            logger.error(f"Error verifying chunk ownership: {e}", exc_info=True)
            return False

    def verify_profile_exists(
        self,
        student_id: str,
        session: Optional[Session] = None
    ) -> bool:
        """
        Verify that a student profile exists in the database.

        Args:
            student_id: Student ID to check
            session: Optional existing Neo4j session

        Returns:
            True if profile exists, False otherwise
        """
        query = """
        MATCH (p:Profile {student_id: $student_id})
        RETURN count(p) > 0 AS exists
        """

        params = {'student_id': student_id}

        try:
            if session:
                result = session.run(query, params)
                record = result.single()
            else:
                with self.driver.session() as new_session:
                    result = new_session.run(query, params)
                    record = result.single()

            exists = record['exists'] if record else False

            if not exists:
                logger.warning(f"Profile not found for student {student_id}")

            return exists

        except Exception as e:
            logger.error(f"Error verifying profile existence: {e}", exc_info=True)
            return False

    def get_student_note_ids(
        self,
        student_id: str,
        session: Optional[Session] = None
    ) -> List[str]:
        """
        Get all lecture note IDs owned by a student.

        Useful for batch validation operations.

        Args:
            student_id: Student ID
            session: Optional existing Neo4j session

        Returns:
            List of lecture note IDs owned by the student
        """
        query = """
        MATCH (p:Profile {student_id: $student_id})-[:CREATED_NOTE]->(ln:LectureNote)
        RETURN collect(ln.lecture_note_id) AS note_ids
        """

        params = {'student_id': student_id}

        try:
            if session:
                result = session.run(query, params)
                record = result.single()
            else:
                with self.driver.session() as new_session:
                    result = new_session.run(query, params)
                    record = result.single()

            return record['note_ids'] if record else []

        except Exception as e:
            logger.error(f"Error getting student note IDs: {e}", exc_info=True)
            return []

    def filter_owned_notes(
        self,
        student_id: str,
        note_ids: List[str],
        session: Optional[Session] = None
    ) -> List[str]:
        """
        Filter a list of note IDs to only those owned by the student.

        Args:
            student_id: Student ID
            note_ids: List of note IDs to filter
            session: Optional existing Neo4j session

        Returns:
            List of note IDs that the student owns
        """
        if not note_ids:
            return []

        query = """
        MATCH (p:Profile {student_id: $student_id})-[:CREATED_NOTE]->(ln:LectureNote)
        WHERE ln.lecture_note_id IN $note_ids
        RETURN collect(ln.lecture_note_id) AS owned_note_ids
        """

        params = {
            'student_id': student_id,
            'note_ids': note_ids
        }

        try:
            if session:
                result = session.run(query, params)
                record = result.single()
            else:
                with self.driver.session() as new_session:
                    result = new_session.run(query, params)
                    record = result.single()

            owned = record['owned_note_ids'] if record else []

            # Log unauthorized attempts
            unauthorized = set(note_ids) - set(owned)
            if unauthorized:
                logger.warning(
                    f"Student {student_id} attempted to access {len(unauthorized)} "
                    f"notes they don't own: {list(unauthorized)[:5]}"
                )

            return owned

        except Exception as e:
            logger.error(f"Error filtering owned notes: {e}", exc_info=True)
            return []
