# NATS Integration for GraphRAG Note Service

Real-time academic data consumption from NATS JetStream with automatic ingestion into Neo4j.

## Overview

This module provides a production-ready NATS JetStream consumer that:

- Subscribes to academic events from the `vertector-nats-jetstream` service
- Automatically generates embeddings for text content using Qwen3-Embedding-0.6B
- Ingests data into Neo4j with proper relationships
- Implements idempotent event processing
- Provides Prometheus metrics for monitoring
- Handles errors gracefully with retry logic

## Architecture

```
NATS JetStream (academic.*.*)
    ↓
NATSConsumer (consumer.py)
    ↓
NATSDataAdapter (data_adapter.py)
    ↓
DataLoader (ingestion/data_loader.py)
    ↓
Neo4j Graph Database
```

## Components

### 1. NATSConsumer (`consumer.py`)

Main consumer service that:
- Connects to NATS JetStream
- Subscribes to academic event subjects
- Processes events in batches using pull-based consumption
- Tracks processed event IDs for idempotency
- Emits Prometheus metrics

### 2. NATSDataAdapter (`data_adapter.py`)

Adapter layer that:
- Translates NATS event payloads to Neo4j operations
- Wraps the existing DataLoader with NATS-friendly interface
- Handles entity creation, updates, and deletion
- Manages embedding generation and regeneration

### 3. NATSConsumerConfig (`config.py`)

Configuration management with:
- NATS connection settings
- JetStream consumer settings
- Processing options (auto-embeddings, idempotency)
- Monitoring configuration
- Environment variable support via `.env`

### 4. Event Models (`models/`)

GraphRAG-aligned Pydantic models for:
- Course events
- Assignment events
- Exam events
- Quiz events
- Lab session events
- Study todo events
- Challenge area events
- Class schedule events

## Event Schema Alignment

The NATS event schemas have been updated to match the GraphRAG Note Service schema. See `/Users/en_tetteh/Documents/graphrag/docs/NATS_SCHEMA_MIGRATION.md` for complete field mappings.

## Usage

### Basic Usage

```python
import asyncio
from note_service.nats_integration import NATSConsumer

async def main():
    consumer = NATSConsumer()
    await consumer.run()

if __name__ == "__main__":
    asyncio.run(main())
```

### Custom Configuration

```python
from note_service.nats_integration import NATSConsumer, NATSConsumerConfig

config = NATSConsumerConfig(
    servers=["nats://localhost:4222"],
    stream_name="ACADEMIC_EVENTS",
    durable_name="graphrag-consumer",
    batch_size=20,
    enable_auto_embeddings=True,
    enable_idempotency=True,
)

consumer = NATSConsumer(config=config)
await consumer.run()
```

### Environment Configuration

Create a `.env` file:

```bash
# NATS Connection
NATS_SERVERS=["nats://localhost:4222"]
NATS_CLIENT_NAME=graphrag-note-service
NATS_MAX_RECONNECT_ATTEMPTS=10
NATS_RECONNECT_WAIT_SECONDS=2

# Authentication (optional)
NATS_USERNAME=myuser
NATS_PASSWORD=mypassword

# JetStream
NATS_STREAM_NAME=ACADEMIC_EVENTS
NATS_DURABLE_NAME=graphrag-note-service-consumer
NATS_BATCH_SIZE=10
NATS_ACK_WAIT_SECONDS=60
NATS_MAX_DELIVER=3

# Processing
NATS_ENABLE_AUTO_EMBEDDINGS=true
NATS_ENABLE_IDEMPOTENCY=true
NATS_IDEMPOTENCY_CACHE_SIZE=10000

# Monitoring
NATS_ENABLE_METRICS=true
NATS_METRICS_PORT=9090
```

## Event Processing Flow

### 1. Course Created Event

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "event_type": "academic.course.created",
  "event_version": "1.0",
  "timestamp": "2025-01-15T10:30:00Z",
  "metadata": {
    "source_service": "academic-system",
    "correlation_id": "abc-123",
    "user_id": "student-001"
  },
  "course_id": "CS230-Fall2025",
  "title": "Deep Learning",
  "code": "CS",
  "number": "230",
  "term": "Fall 2025",
  "credits": 4,
  "description": "Introduction to deep learning...",
  "instructor_name": "Andrew Ng",
  "instructor_email": "ang@cs.stanford.edu"
}
```

**Processing Steps:**
1. Consumer receives event from NATS
2. Idempotency check (skip if already processed)
3. Extract entity data (remove event metadata)
4. Call `NATSDataAdapter.load_entity_with_embeddings()`
5. DataLoader creates Course node in Neo4j
6. Auto-generate embedding from title + description
7. Store embedding in `embedding_vector` property
8. Acknowledge message to NATS
9. Update Prometheus metrics

### 2. Assignment Updated Event

```json
{
  "event_id": "660e8400-e29b-41d4-a716-446655440001",
  "event_type": "academic.assignment.updated",
  "event_version": "1.0",
  "timestamp": "2025-01-15T11:00:00Z",
  "metadata": {
    "source_service": "academic-system"
  },
  "assignment_id": "CS230-A1",
  "changes": {
    "due_date": "2025-02-01T23:59:59Z",
    "points_possible": 120
  },
  "previous_values": {
    "due_date": "2025-01-31T23:59:59Z",
    "points_possible": 100
  }
}
```

**Processing Steps:**
1. Consumer receives event
2. Extract assignment_id and changes
3. Call `NATSDataAdapter.update_entity()`
4. Update Assignment node properties
5. If text fields changed, regenerate embedding
6. Acknowledge and update metrics

### 3. Exam Deleted Event

```json
{
  "event_id": "770e8400-e29b-41d4-a716-446655440002",
  "event_type": "academic.exam.deleted",
  "event_version": "1.0",
  "timestamp": "2025-01-15T12:00:00Z",
  "metadata": {
    "source_service": "academic-system"
  },
  "exam_id": "CS230-MIDTERM",
  "soft_delete": true,
  "deletion_reason": "Course cancelled"
}
```

**Processing Steps:**
1. Consumer receives event
2. Extract exam_id and soft_delete flag
3. If soft_delete, call `soft_delete_entity()` (sets deleted=true)
4. If hard delete, call `delete_entity()` (DETACH DELETE)
5. Acknowledge and update metrics

## Idempotency

The consumer implements idempotency using `event_id` to prevent duplicate processing:

- Each event has a unique `event_id` (UUID)
- Consumer maintains an in-memory cache of processed event IDs
- Before processing, checks if event_id exists in cache
- If found, skips processing and acknowledges immediately
- Cache size is configurable (default: 10,000 events)
- Automatic cache eviction to prevent memory leaks

## Error Handling

### Retry Logic

- Failed messages are negative-acknowledged (`nak()`)
- NATS automatically redelivers failed messages
- Maximum delivery attempts: configurable (default: 3)
- After max attempts, message moves to dead-letter queue

### Error Types

1. **Transient Errors** (retried):
   - Network connectivity issues
   - Temporary Neo4j unavailability
   - Embedding generation timeouts

2. **Permanent Errors** (not retried):
   - Invalid event schema
   - Unknown event type
   - Invalid entity data

### Error Metrics

Track failures by error type:
```python
EVENTS_FAILED.labels(
    event_type='academic.course.created',
    error_type='ConnectionError'
).inc()
```

## Monitoring

### Prometheus Metrics

Available metrics:

```python
# Events received
graphrag_nats_events_received_total{event_type="academic.course.created", status="new"}

# Events processed successfully
graphrag_nats_events_processed_total{event_type="academic.course.created"}

# Events failed
graphrag_nats_events_failed_total{event_type="academic.course.created", error_type="ValidationError"}

# Processing time histogram
graphrag_nats_event_processing_seconds{event_type="academic.course.created"}

# Consumer lag
graphrag_nats_consumer_lag
```

### Metrics Endpoint

Expose metrics on port 9090 (configurable):
```bash
curl http://localhost:9090/metrics
```

## Deployment

### Running as Standalone Service

```bash
# Run consumer
python -m note_service.nats_integration.consumer
```

### Running with Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

CMD ["python", "-m", "note_service.nats_integration.consumer"]
```

### Running with Systemd

```ini
[Unit]
Description=GraphRAG NATS Consumer
After=network.target nats.service neo4j.service

[Service]
Type=simple
User=graphrag
WorkingDirectory=/opt/graphrag
ExecStart=/usr/bin/python3 -m note_service.nats_integration.consumer
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Testing

### Unit Tests

```bash
pytest tests/nats_integration/test_consumer.py
pytest tests/nats_integration/test_data_adapter.py
```

### Integration Tests

```bash
# Start dependencies
docker-compose up -d nats neo4j

# Run integration tests
pytest tests/nats_integration/test_integration.py
```

### Manual Testing

```python
import asyncio
from note_service.nats_integration import NATSConsumer

async def test():
    # Publish test event to NATS
    # Consumer should process it and create node in Neo4j
    consumer = NATSConsumer()
    await consumer.run()

asyncio.run(test())
```

## Troubleshooting

### Consumer Not Receiving Events

1. Check NATS connection:
   ```bash
   nats stream info ACADEMIC_EVENTS
   ```

2. Check consumer subscription:
   ```bash
   nats consumer info ACADEMIC_EVENTS graphrag-note-service-consumer
   ```

3. Check filter subjects match event types

### Events Not Creating Nodes

1. Check Neo4j connectivity
2. Check DataLoader logs
3. Verify entity data schema matches Neo4j constraints
4. Check for duplicate `event_id` (idempotency)

### High Consumer Lag

1. Increase `batch_size`
2. Increase number of consumer instances
3. Disable auto-embeddings temporarily
4. Check Neo4j performance

### Memory Issues

1. Reduce `idempotency_cache_size`
2. Reduce `batch_size`
3. Increase memory limits

## Performance Tuning

### Batch Size

- Default: 10 messages/batch
- Increase for higher throughput
- Decrease for lower latency
- Balance with Neo4j write capacity

### Embedding Generation

- Enable for searchable entities (Course, Assignment, etc.)
- Disable for non-searchable entities (Schedule)
- Use GPU for faster embedding generation

### Connection Pooling

Configure Neo4j connection pool:
```python
connection = Neo4jConnection(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="password",
    max_connection_pool_size=50
)
```

## Related Documentation

- [NATS Schema Migration Guide](/Users/en_tetteh/Documents/graphrag/docs/NATS_SCHEMA_MIGRATION.md)
- [GraphRAG Event Models](/Users/en_tetteh/Documents/graphrag/src/note_service/nats_integration/graphrag_aligned_events.py)
- [vertector-nats-jetstream Project](/Users/en_tetteh/Documents/vertector-nats-jetstream)
