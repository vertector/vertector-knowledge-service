"""
============================================================================
Security Audit Service
============================================================================
Provides database-level audit logging for student data access.
Tracks who accessed what data and when for compliance and security.
============================================================================
"""

import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import uuid4

from neo4j import Driver, Session

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Logs student data access to Neo4j for audit trail.

    Creates AccessLog nodes that track:
    - Who accessed data (student_id)
    - What was accessed (entity_type, entity_id)
    - When (timestamp)
    - How (operation_type: search, read, update, delete)
    - Why (context: query_text, filters, etc.)
    """

    def __init__(self, driver: Driver):
        """
        Initialize audit logger.

        Args:
            driver: Neo4j driver for database access
        """
        self.driver = driver

    def log_access(
        self,
        student_id: str,
        operation_type: str,
        entity_type: str,
        entity_ids: list[str] | None = None,
        context: Dict[str, Any] | None = None,
        session: Optional[Session] = None
    ) -> str:
        """
        Log a data access event.

        Args:
            student_id: Student who performed the operation
            operation_type: Type of operation (search, read, update, delete)
            entity_type: Type of entity accessed (LectureNote, Chunk, etc.)
            entity_ids: Optional list of specific entity IDs accessed
            context: Optional additional context (query text, filters, etc.)
            session: Optional existing Neo4j session to use

        Returns:
            Log entry ID
        """
        log_id = str(uuid4())
        timestamp = datetime.utcnow().isoformat()

        # Convert context dict to JSON string (Neo4j doesn't support nested maps as properties)
        context_json = json.dumps(context or {})

        query = """
        CREATE (log:AccessLog {
            log_id: $log_id,
            student_id: $student_id,
            operation_type: $operation_type,
            entity_type: $entity_type,
            entity_ids: $entity_ids,
            timestamp: datetime($timestamp),
            context: $context
        })
        RETURN log.log_id AS log_id
        """

        params = {
            'log_id': log_id,
            'student_id': student_id,
            'operation_type': operation_type,
            'entity_type': entity_type,
            'entity_ids': entity_ids or [],
            'timestamp': timestamp,
            'context': context_json
        }

        try:
            if session:
                # Use provided session
                result = session.run(query, params)
                result.single()
            else:
                # Create own session
                with self.driver.session() as new_session:
                    result = new_session.run(query, params)
                    result.single()

            logger.debug(
                f"Audit log created: {operation_type} on {entity_type} "
                f"by student {student_id}"
            )

            return log_id

        except Exception as e:
            # Don't fail the main operation if audit logging fails
            logger.error(f"Failed to create audit log: {e}", exc_info=True)
            return ""

    def log_search(
        self,
        student_id: str,
        query_text: str,
        result_count: int,
        filters: Dict[str, Any] | None = None,
        session: Optional[Session] = None
    ) -> str:
        """
        Log a search operation.

        Args:
            student_id: Student who performed the search
            query_text: Search query text
            result_count: Number of results returned
            filters: Optional search filters applied
            session: Optional existing Neo4j session

        Returns:
            Log entry ID
        """
        context = {
            'query_text': query_text,
            'result_count': result_count,
            'filters': filters or {}
        }

        return self.log_access(
            student_id=student_id,
            operation_type='search',
            entity_type='LectureNote',
            context=context,
            session=session
        )

    def get_student_access_history(
        self,
        student_id: str,
        limit: int = 100,
        operation_type: Optional[str] = None
    ) -> list[Dict[str, Any]]:
        """
        Retrieve access history for a student.

        Args:
            student_id: Student ID to get history for
            limit: Maximum number of records to return
            operation_type: Optional filter by operation type

        Returns:
            List of access log entries
        """
        query = """
        MATCH (log:AccessLog {student_id: $student_id})
        WHERE $operation_type IS NULL OR log.operation_type = $operation_type
        RETURN log
        ORDER BY log.timestamp DESC
        LIMIT $limit
        """

        with self.driver.session() as session:
            result = session.run(
                query,
                student_id=student_id,
                operation_type=operation_type,
                limit=limit
            )

            logs = []
            for record in result:
                log_data = dict(record['log'])
                # Parse context JSON string back to dict
                if 'context' in log_data and isinstance(log_data['context'], str):
                    try:
                        log_data['context'] = json.loads(log_data['context'])
                    except json.JSONDecodeError:
                        log_data['context'] = {}
                logs.append(log_data)

            return logs

    def cleanup_old_logs(self, days_to_keep: int = 90) -> int:
        """
        Clean up audit logs older than specified days.

        Args:
            days_to_keep: Number of days of logs to retain

        Returns:
            Number of logs deleted
        """
        query = """
        MATCH (log:AccessLog)
        WHERE log.timestamp < datetime() - duration({days: $days_to_keep})
        DELETE log
        RETURN count(log) AS deleted_count
        """

        with self.driver.session() as session:
            result = session.run(query, days_to_keep=days_to_keep)
            record = result.single()
            deleted_count = record['deleted_count'] if record else 0

            logger.info(f"Cleaned up {deleted_count} old audit logs")
            return deleted_count
