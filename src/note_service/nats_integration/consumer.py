"""
NATS JetStream Consumer for GraphRAG Note Service

This consumer subscribes to NATS JetStream academic events and ingests them
into Neo4j using the existing DataLoader infrastructure with automatic
embedding generation.

Features:
- Idempotent event processing using event_id
- Automatic embedding generation via DataLoader
- Prometheus metrics for monitoring
- Graceful error handling and retry logic
- Pull-based consumption for scalability
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Set
from uuid import UUID

import nats
from nats.aio.client import Client as NATS
from nats.js import JetStreamContext
from nats.js.api import ConsumerConfig, AckPolicy
from prometheus_client import Counter, Histogram, Gauge

from .config import NATSConsumerConfig
from .data_adapter import NATSDataAdapter

# Configure logging
logger = logging.getLogger(__name__)

# Prometheus metrics
EVENTS_RECEIVED = Counter(
    'graphrag_nats_events_received_total',
    'Total number of NATS events received',
    ['event_type', 'status']
)

EVENTS_PROCESSED = Counter(
    'graphrag_nats_events_processed_total',
    'Total number of NATS events successfully processed',
    ['event_type']
)

EVENTS_FAILED = Counter(
    'graphrag_nats_events_failed_total',
    'Total number of NATS events that failed processing',
    ['event_type', 'error_type']
)

PROCESSING_TIME = Histogram(
    'graphrag_nats_event_processing_seconds',
    'Time spent processing NATS events',
    ['event_type']
)

CONSUMER_LAG = Gauge(
    'graphrag_nats_consumer_lag',
    'Number of pending messages in NATS stream'
)


class NATSConsumer:
    """
    NATS JetStream consumer for GraphRAG Note Service.

    Subscribes to academic events and ingests them into Neo4j with
    automatic embedding generation.
    """

    def __init__(
        self,
        config: Optional[NATSConsumerConfig] = None,
        data_adapter: Optional[NATSDataAdapter] = None
    ):
        """
        Initialize NATS consumer.

        Args:
            config: NATS consumer configuration
            data_adapter: NATSDataAdapter instance for Neo4j ingestion
        """
        self.config = config or NATSConsumerConfig()
        self.data_adapter = data_adapter or NATSDataAdapter()

        self.nc: Optional[NATS] = None
        self.js: Optional[JetStreamContext] = None
        self.running = False

        # Track processed event IDs for idempotency
        self.processed_event_ids: Set[str] = set()

        # Event type to entity type mapping
        self.event_to_entity_map = {
            # Course events
            "academic.course.created": "Course",
            "academic.course.updated": "Course",
            "academic.course.deleted": "Course",

            # Assignment events
            "academic.assignment.created": "Assignment",
            "academic.assignment.updated": "Assignment",
            "academic.assignment.deleted": "Assignment",

            # Exam events
            "academic.exam.created": "Exam",
            "academic.exam.updated": "Exam",
            "academic.exam.deleted": "Exam",

            # Quiz events
            "academic.quiz.created": "Quiz",
            "academic.quiz.updated": "Quiz",
            "academic.quiz.deleted": "Quiz",

            # Lab events
            "academic.lab.created": "Lab_Session",
            "academic.lab.updated": "Lab_Session",
            "academic.lab.deleted": "Lab_Session",

            # Study todo events
            "academic.study.created": "Study_Todo",
            "academic.study.updated": "Study_Todo",
            "academic.study.deleted": "Study_Todo",

            # Challenge events
            "academic.challenge.created": "Challenge_Area",
            "academic.challenge.updated": "Challenge_Area",
            "academic.challenge.deleted": "Challenge_Area",

            # Schedule events
            "academic.schedule.created": "Class_Schedule",
            "academic.schedule.updated": "Class_Schedule",
            "academic.schedule.deleted": "Class_Schedule",

            # Profile events
            "academic.profile.created": "Profile",
            "academic.profile.updated": "Profile",
            "academic.profile.enrolled": "Profile",
            "academic.profile.unenrolled": "Profile",
        }

    async def connect(self) -> None:
        """Connect to NATS server and initialize JetStream."""
        try:
            logger.info(f"Connecting to NATS servers: {self.config.servers}")

            self.nc = await nats.connect(
                servers=self.config.servers,
                name=self.config.client_name,
                max_reconnect_attempts=self.config.max_reconnect_attempts,
                reconnect_time_wait=self.config.reconnect_wait_seconds,
            )

            self.js = self.nc.jetstream()

            logger.info("Successfully connected to NATS and initialized JetStream")

        except Exception as e:
            logger.error(f"Failed to connect to NATS: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from NATS server."""
        if self.nc:
            await self.nc.drain()
            await self.nc.close()
            logger.info("Disconnected from NATS")

    def _is_event_processed(self, event_id: str) -> bool:
        """
        Check if event has already been processed (idempotency check).

        Args:
            event_id: Unique event identifier

        Returns:
            True if event has been processed, False otherwise
        """
        if not self.config.enable_idempotency:
            return False

        return event_id in self.processed_event_ids

    def _mark_event_processed(self, event_id: str) -> None:
        """
        Mark event as processed for idempotency tracking.

        Args:
            event_id: Unique event identifier
        """
        if not self.config.enable_idempotency:
            return

        self.processed_event_ids.add(event_id)

        # Prevent memory leak by limiting set size
        if len(self.processed_event_ids) > self.config.idempotency_cache_size:
            # Remove oldest 20% of entries (simple FIFO approximation)
            remove_count = self.config.idempotency_cache_size // 5
            for _ in range(remove_count):
                self.processed_event_ids.pop()

    def _extract_entity_data(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract entity data from event payload.

        Args:
            event_data: Full event payload

        Returns:
            Entity data suitable for DataLoader
        """
        # Remove event metadata fields
        entity_data = {
            k: v for k, v in event_data.items()
            if k not in ['event_id', 'event_type', 'event_version', 'timestamp', 'metadata']
        }

        # CRITICAL: Extract student_id from metadata.user_id for data isolation and linking
        # ASMS publishes student_id in metadata.user_id since CourseCreatedEvent schema doesn't have student_id field
        if 'metadata' in event_data and event_data['metadata']:
            metadata = event_data['metadata']
            if isinstance(metadata, dict) and 'user_id' in metadata and metadata['user_id']:
                entity_data['student_id'] = metadata['user_id']
                logger.debug(f"Extracted student_id from metadata: {metadata['user_id']}")

        return entity_data

    async def _process_created_event(
        self,
        entity_type: str,
        event_data: Dict[str, Any]
    ) -> None:
        """
        Process entity created event.

        Args:
            entity_type: Type of entity (Course, Assignment, etc.)
            event_data: Event payload
        """
        entity_data = self._extract_entity_data(event_data)

        # Use DataAdapter to create entity with automatic embedding generation
        if self.config.enable_auto_embeddings:
            logger.info(f"Creating {entity_type} with auto-embedding generation")
            await self.data_adapter.load_entity_with_embeddings(
                entity_type=entity_type,
                entity_data=entity_data
            )
        else:
            logger.info(f"Creating {entity_type} without embeddings")
            await self.data_adapter.load_entity(
                entity_type=entity_type,
                entity_data=entity_data
            )

        # Special handling: If Course has student_id, create implicit ENROLLED_IN relationship
        if entity_type == "Course" and "student_id" in entity_data:
            await self._create_enrollment_from_course(entity_data)

    async def _process_updated_event(
        self,
        entity_type: str,
        event_data: Dict[str, Any]
    ) -> None:
        """
        Process entity updated event.

        Args:
            entity_type: Type of entity (Course, Assignment, etc.)
            event_data: Event payload with 'changes' field
        """
        entity_id = self._get_entity_id(entity_type, event_data)
        changes = event_data.get('changes', {})

        logger.info(f"Updating {entity_type} {entity_id} with changes: {list(changes.keys())}")

        # Update entity properties
        await self.data_adapter.update_entity(
            entity_type=entity_type,
            entity_id=entity_id,
            updates=changes
        )

        # Regenerate embedding if text fields changed and auto-embedding is enabled
        if self.config.enable_auto_embeddings:
            text_fields = ['description', 'title', 'objectives', 'notes']
            if any(field in changes for field in text_fields):
                logger.info(f"Regenerating embedding for {entity_type} {entity_id}")
                await self.data_adapter.regenerate_embedding(
                    entity_type=entity_type,
                    entity_id=entity_id
                )

    async def _process_deleted_event(
        self,
        entity_type: str,
        event_data: Dict[str, Any]
    ) -> None:
        """
        Process entity deleted event.

        Args:
            entity_type: Type of entity (Course, Assignment, etc.)
            event_data: Event payload
        """
        entity_id = self._get_entity_id(entity_type, event_data)
        soft_delete = event_data.get('soft_delete', True)

        if soft_delete:
            logger.info(f"Soft deleting {entity_type} {entity_id}")
            await self.data_adapter.soft_delete_entity(
                entity_type=entity_type,
                entity_id=entity_id,
                deletion_reason=event_data.get('deletion_reason')
            )
        else:
            logger.info(f"Hard deleting {entity_type} {entity_id}")
            await self.data_adapter.delete_entity(
                entity_type=entity_type,
                entity_id=entity_id
            )

    def _get_entity_id(self, entity_type: str, event_data: Dict[str, Any]) -> str:
        """
        Extract entity ID from event data.

        Args:
            entity_type: Type of entity
            event_data: Event payload

        Returns:
            Entity identifier
        """
        # Map entity type to ID field name
        id_field_map = {
            "Profile": "student_id",
            "Course": "course_id",
            "Assignment": "assignment_id",
            "Exam": "exam_id",
            "Quiz": "quiz_id",
            "Lab_Session": "lab_id",
            "Study_Todo": "todo_id",
            "Challenge_Area": "challenge_id",
            "Class_Schedule": "schedule_id",
        }

        id_field = id_field_map.get(entity_type)
        if not id_field:
            raise ValueError(f"Unknown entity type: {entity_type}")

        entity_id = event_data.get(id_field)
        if not entity_id:
            raise ValueError(f"Missing {id_field} in event data")

        return entity_id

    async def _process_enrolled_event(
        self,
        event_data: Dict[str, Any]
    ) -> None:
        """
        Process profile enrolled event to create ENROLLED_IN relationship.

        Args:
            event_data: Event payload containing student_id, course_id, enrollment details
        """
        student_id = event_data.get('student_id')
        course_id = event_data.get('course_id')

        if not student_id or not course_id:
            logger.warning(f"Missing student_id or course_id in enrollment event")
            return

        logger.info(f"Creating ENROLLED_IN relationship: {student_id} → {course_id}")

        # Create ENROLLED_IN relationship using Neo4j client directly
        query = """
        MATCH (p:Profile {student_id: $student_id})
        MATCH (c:Course {course_id: $course_id})
        MERGE (p)-[r:ENROLLED_IN]->(c)
        ON CREATE SET
            r.enrollment_date = datetime($enrollment_date),
            r.grading_basis = $grading_basis,
            r.enrollment_status = $enrollment_status,
            r.created_at = datetime()
        ON MATCH SET
            r.enrollment_status = $enrollment_status,
            r.updated_at = datetime()
        RETURN r
        """

        # Handle enrollment_date - may be datetime or string
        enrollment_date = event_data.get('enrollment_date', datetime.utcnow())
        if isinstance(enrollment_date, str):
            enrollment_date_str = enrollment_date
        else:
            enrollment_date_str = enrollment_date.isoformat()

        params = {
            'student_id': student_id,
            'course_id': course_id,
            'enrollment_date': enrollment_date_str,
            'grading_basis': event_data.get('grading_basis', 'Letter'),
            'enrollment_status': event_data.get('enrollment_status', 'Active'),
        }

        try:
            # Use the connection's session context manager
            with self.data_adapter.connection.session() as session:
                result = session.run(query, params)
                record = result.single()
                if record:
                    logger.info(f"✅ Created/Updated ENROLLED_IN relationship: {student_id} → {course_id}")
                else:
                    logger.warning(f"Failed to create ENROLLED_IN relationship (Profile or Course may not exist)")
        except Exception as e:
            logger.error(f"Error creating ENROLLED_IN relationship: {e}", exc_info=True)
            raise

    async def _create_enrollment_from_course(
        self,
        course_data: Dict[str, Any]
    ) -> None:
        """
        Create implicit ENROLLED_IN relationship when Course has student_id.

        When Academic Schedule Management creates a Course with student_id,
        it automatically means the student is enrolled in that course.

        Args:
            course_data: Course entity data containing student_id and course_id
        """
        student_id = course_data.get('student_id')
        course_id = course_data.get('course_id')

        if not student_id or not course_id:
            logger.warning(f"Missing student_id or course_id in Course data")
            return

        logger.info(f"Creating implicit ENROLLED_IN relationship from Course: {student_id} → {course_id}")

        # Create ENROLLED_IN relationship
        query = """
        MATCH (p:Profile {student_id: $student_id})
        MATCH (c:Course {course_id: $course_id})
        MERGE (p)-[r:ENROLLED_IN]->(c)
        ON CREATE SET
            r.enrollment_date = datetime(),
            r.enrollment_status = 'Active',
            r.created_at = datetime()
        RETURN r
        """

        params = {
            'student_id': student_id,
            'course_id': course_id,
        }

        try:
            with self.data_adapter.connection.session() as session:
                result = session.run(query, params)
                record = result.single()
                if record:
                    logger.info(f"✅ Created implicit ENROLLED_IN relationship: {student_id} → {course_id}")
                else:
                    logger.warning(
                        f"Failed to create ENROLLED_IN relationship - Profile {student_id} may not exist yet. "
                        f"Ensure Profile is created before Course."
                    )
        except Exception as e:
            logger.error(f"Error creating implicit ENROLLED_IN relationship: {e}", exc_info=True)
            raise

    async def process_event(self, event_data: Dict[str, Any]) -> None:
        """
        Process a single NATS event.

        Args:
            event_data: Event payload
        """
        event_type = event_data.get('event_type')
        event_id = str(event_data.get('event_id'))

        start_time = datetime.utcnow()

        try:
            # Idempotency check
            if self._is_event_processed(event_id):
                logger.info(f"Event {event_id} already processed, skipping")
                EVENTS_RECEIVED.labels(event_type=event_type, status='duplicate').inc()
                return

            EVENTS_RECEIVED.labels(event_type=event_type, status='new').inc()

            # Get entity type from event type
            entity_type = self.event_to_entity_map.get(event_type)
            if not entity_type:
                logger.warning(f"Unknown event type: {event_type}")
                EVENTS_FAILED.labels(event_type=event_type, error_type='unknown_event_type').inc()
                return

            # Route event based on operation (created/updated/deleted/enrolled)
            if event_type.endswith('.created'):
                await self._process_created_event(entity_type, event_data)
            elif event_type.endswith('.updated'):
                await self._process_updated_event(entity_type, event_data)
            elif event_type.endswith('.deleted'):
                await self._process_deleted_event(entity_type, event_data)
            elif event_type.endswith('.enrolled'):
                await self._process_enrolled_event(event_data)
            elif event_type.endswith('.unenrolled'):
                # TODO: Handle unenrollment (remove ENROLLED_IN relationship)
                logger.info(f"Unenrollment event received, not yet implemented: {event_type}")
            else:
                logger.warning(f"Unknown event operation: {event_type}")
                return

            # Mark as processed
            self._mark_event_processed(event_id)

            # Update metrics
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            EVENTS_PROCESSED.labels(event_type=event_type).inc()
            PROCESSING_TIME.labels(event_type=event_type).observe(processing_time)

            logger.info(f"Successfully processed event {event_id} ({event_type}) in {processing_time:.2f}s")

        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"Failed to process event {event_id} ({event_type}): {e}", exc_info=True)
            EVENTS_FAILED.labels(event_type=event_type, error_type=error_type).inc()
            raise

    async def consume(self) -> None:
        """
        Start consuming events from NATS JetStream.

        Uses pull-based consumption for scalability and back-pressure handling.
        """
        if not self.js:
            raise RuntimeError("Not connected to NATS JetStream. Call connect() first.")

        logger.info(f"Starting NATS consumer for stream: {self.config.stream_name}")
        logger.info(f"Filter subjects: {self.config.filter_subjects}")

        # Create pull-based consumer
        # Use wildcard subject to subscribe to ALL academic events
        consumer_config = ConsumerConfig(
            durable_name=self.config.durable_name,
            ack_policy=AckPolicy.EXPLICIT,
            ack_wait=self.config.ack_wait_seconds,
            max_deliver=self.config.max_deliver,
            filter_subject="academic.>",  # Subscribe to ALL academic.* events
        )

        # Get or create consumer
        consumer = await self.js.pull_subscribe(
            subject="academic.>",  # Subscribe to ALL academic events
            durable=self.config.durable_name,
            config=consumer_config,
        )

        self.running = True

        logger.info("NATS consumer started successfully")

        try:
            while self.running:
                try:
                    # Fetch batch of messages
                    messages = await consumer.fetch(
                        batch=self.config.batch_size,
                        timeout=self.config.fetch_timeout_seconds,
                    )

                    # Update consumer lag metric
                    pending = await consumer.consumer_info()
                    CONSUMER_LAG.set(pending.num_pending)

                    # Process each message
                    for msg in messages:
                        try:
                            # Decode JSON payload
                            import json
                            event_data = json.loads(msg.data.decode())

                            # Process event
                            await self.process_event(event_data)

                            # Acknowledge successful processing
                            await msg.ack()

                        except Exception as e:
                            logger.error(f"Error processing message: {e}", exc_info=True)

                            # Negative acknowledge for retry
                            await msg.nak()

                except asyncio.TimeoutError:
                    # No messages available, continue polling
                    continue

                except Exception as e:
                    logger.error(f"Error fetching messages: {e}", exc_info=True)
                    await asyncio.sleep(self.config.error_backoff_seconds)

        except asyncio.CancelledError:
            logger.info("Consumer cancelled, shutting down...")
        finally:
            self.running = False

    async def run(self) -> None:
        """
        Run the NATS consumer (connect + consume).

        This is the main entry point for running the consumer.
        """
        try:
            await self.connect()
            await self.consume()
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
        finally:
            await self.disconnect()


async def main():
    """Main entry point for running the consumer as a standalone service."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    consumer = NATSConsumer()
    await consumer.run()


if __name__ == "__main__":
    asyncio.run(main())
