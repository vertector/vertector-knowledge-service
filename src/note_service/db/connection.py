"""
============================================================================
Academic Note-Taking GraphRAG System - Neo4j Connection Manager
============================================================================
Production-ready connection pooling with retry logic and error handling
Supports both synchronous and asynchronous operations
============================================================================
"""

import logging
from contextlib import contextmanager
from typing import Any, Generator

from neo4j import GraphDatabase, Driver, Session, Transaction, ManagedTransaction
from neo4j.exceptions import ServiceUnavailable, TransientError, SessionExpired
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from ..config import Settings, settings as default_settings

logger = logging.getLogger(__name__)


class Neo4jConnection:
    """
    Thread-safe Neo4j connection manager with connection pooling.

    Features:
    - Automatic connection pooling
    - Retry logic for transient failures
    - Context managers for safe session/transaction handling
    - Health checks and connection verification

    Example:
        ```python
        conn = Neo4jConnection(settings)

        # Using context manager for sessions
        with conn.session() as session:
            result = session.run("MATCH (n:Note) RETURN count(n)")
            count = result.single()[0]

        # Using read/write transactions
        with conn.read_transaction() as tx:
            result = tx.run("MATCH (n:Note) RETURN n LIMIT 10")
            notes = list(result)
        ```
    """

    def __init__(self, settings: Settings = default_settings):
        """
        Initialize Neo4j connection manager.

        Args:
            settings: Application settings with Neo4j configuration
        """
        self.settings = settings
        self._driver: Driver | None = None
        self._connect()

    def _connect(self) -> None:
        """Establish connection to Neo4j database."""
        try:
            neo4j_config = self.settings.neo4j

            self._driver = GraphDatabase.driver(
                neo4j_config.uri,
                auth=(
                    neo4j_config.username,
                    neo4j_config.password.get_secret_value(),
                ),
                max_connection_pool_size=neo4j_config.max_connection_pool_size,
                connection_timeout=neo4j_config.connection_timeout,
                max_transaction_retry_time=neo4j_config.max_transaction_retry_time,
                encrypted=neo4j_config.encrypted,
                trust=neo4j_config.trust,
            )

            # Verify connection
            self._driver.verify_connectivity()
            logger.info(
                f"Successfully connected to Neo4j at {neo4j_config.uri}, "
                f"database: {neo4j_config.database}"
            )

        except ServiceUnavailable as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error connecting to Neo4j: {e}")
            raise

    @property
    def driver(self) -> Driver:
        """Get the Neo4j driver instance."""
        if self._driver is None:
            raise RuntimeError("Neo4j driver not initialized. Call _connect() first.")
        return self._driver

    @contextmanager
    def session(
        self,
        database: str | None = None,
        **kwargs: Any,
    ) -> Generator[Session, None, None]:
        """
        Context manager for Neo4j sessions.

        Args:
            database: Database name (defaults to settings)
            **kwargs: Additional session configuration

        Yields:
            Neo4j Session object

        Example:
            ```python
            with conn.session() as session:
                result = session.run("MATCH (n) RETURN count(n)")
            ```
        """
        db_name = database or self.settings.neo4j.database
        session_obj = self.driver.session(database=db_name, **kwargs)

        try:
            yield session_obj
        finally:
            session_obj.close()

    @retry(
        retry=retry_if_exception_type((ServiceUnavailable, TransientError, SessionExpired)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def execute_read(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
        database: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Execute a read query with automatic retry logic.

        Args:
            query: Cypher query string
            parameters: Query parameters
            database: Database name (defaults to settings)

        Returns:
            List of result records as dictionaries

        Example:
            ```python
            results = conn.execute_read(
                "MATCH (n:Note {note_id: $id}) RETURN n",
                parameters={"id": "NOTE-001"}
            )
            ```
        """
        with self.session(database=database) as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    @retry(
        retry=retry_if_exception_type((ServiceUnavailable, TransientError, SessionExpired)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def execute_write(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
        database: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Execute a write query with automatic retry logic.

        Args:
            query: Cypher query string
            parameters: Query parameters
            database: Database name (defaults to settings)

        Returns:
            List of result records as dictionaries

        Example:
            ```python
            result = conn.execute_write(
                '''
                MERGE (n:Note {note_id: $note_id})
                ON CREATE SET n.title = $title, n.created_at = datetime()
                RETURN n
                ''',
                parameters={"note_id": "NOTE-001", "title": "My Note"}
            )
            ```
        """
        with self.session(database=database) as session:
            result = session.execute_write(
                lambda tx: list(tx.run(query, parameters or {}))
            )
            return [record.data() for record in result]

    @contextmanager
    def read_transaction(
        self, database: str | None = None
    ) -> Generator[ManagedTransaction, None, None]:
        """
        Context manager for read transactions.

        Args:
            database: Database name (defaults to settings)

        Yields:
            Transaction object for read operations

        Example:
            ```python
            with conn.read_transaction() as tx:
                result = tx.run("MATCH (n:Note) RETURN n LIMIT 10")
                notes = list(result)
            ```
        """
        with self.session(database=database) as session:
            tx = session.begin_transaction()
            try:
                yield tx
                tx.commit()
            except Exception:
                tx.rollback()
                raise

    @contextmanager
    def write_transaction(
        self, database: str | None = None
    ) -> Generator[ManagedTransaction, None, None]:
        """
        Context manager for write transactions.

        Args:
            database: Database name (defaults to settings)

        Yields:
            Transaction object for write operations

        Example:
            ```python
            with conn.write_transaction() as tx:
                tx.run("CREATE (n:Note {note_id: $id})", id="NOTE-001")
                tx.run("CREATE (t:Topic {topic_id: $id})", id="TOPIC-001")
            # Auto-commits on success, auto-rolls back on exception
            ```
        """
        with self.session(database=database) as session:
            tx = session.begin_transaction()
            try:
                yield tx
                tx.commit()
            except Exception:
                tx.rollback()
                raise

    def health_check(self) -> dict[str, Any]:
        """
        Perform health check on Neo4j connection.

        Returns:
            Health status dictionary with connection info

        Example:
            ```python
            health = conn.health_check()
            if health["status"] == "healthy":
                print(f"Connected to Neo4j {health['version']}")
            ```
        """
        try:
            with self.session() as session:
                result = session.run("CALL dbms.components() YIELD versions RETURN versions")
                versions = result.single()["versions"]
                neo4j_version = versions[0] if versions else "unknown"

                # Get database stats
                stats_result = session.run(
                    """
                    MATCH (n)
                    WITH labels(n) AS labels, count(n) AS count
                    UNWIND labels AS label
                    RETURN label, sum(count) AS total
                    ORDER BY total DESC
                    """
                )
                node_counts = {record["label"]: record["total"] for record in stats_result}

                return {
                    "status": "healthy",
                    "version": neo4j_version,
                    "database": self.settings.neo4j.database,
                    "uri": self.settings.neo4j.uri,
                    "node_counts": node_counts,
                }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    def close(self) -> None:
        """Close the Neo4j driver and release all connections."""
        if self._driver:
            self._driver.close()
            logger.info("Neo4j connection closed")
            self._driver = None

    def __enter__(self) -> "Neo4jConnection":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()

    def __del__(self) -> None:
        """Destructor to ensure connections are closed."""
        self.close()


# Global connection instance (lazy initialization)
_global_connection: Neo4jConnection | None = None


def get_connection(settings: Settings = default_settings) -> Neo4jConnection:
    """
    Get or create the global Neo4j connection instance.

    Args:
        settings: Application settings

    Returns:
        Global Neo4jConnection instance

    Example:
        ```python
        from db.connection import get_connection

        conn = get_connection()
        results = conn.execute_read("MATCH (n:Note) RETURN count(n)")
        ```
    """
    global _global_connection

    if _global_connection is None:
        _global_connection = Neo4jConnection(settings)

    return _global_connection


def close_global_connection() -> None:
    """Close the global connection instance."""
    global _global_connection

    if _global_connection:
        _global_connection.close()
        _global_connection = None
