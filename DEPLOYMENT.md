# GraphRAG Note Service - Deployment Guide

## Overview

The GraphRAG Note Service is a standalone microservice that:
- **Automatically consumes** academic events from NATS JetStream
- **Generates vector embeddings** (1024 dimensions) for semantic search
- **Stores data** in Neo4j graph database with hybrid indexing
- **Provides** production-ready event-driven architecture

## Architecture

```
┌─────────────────────┐
│ vertector-nats      │
│ (NATS JetStream)    │──┐
└─────────────────────┘  │
                         │ Events
                         ↓
                   ┌─────────────────┐
                   │  Note Service   │
                   │ (This Service)  │
                   └─────────────────┘
                         │
                         │ Graph + Embeddings
                         ↓
                   ┌─────────────────┐
                   │     Neo4j       │
                   └─────────────────┘
```

## Prerequisites

- Docker & Docker Compose
- NATS JetStream running (via vertector-nats-jetstream)
- 4GB+ RAM available
- 10GB+ disk space (for embeddings cache)

## Quick Start

### 1. Start NATS (from vertector-nats-jetstream)

```bash
cd /path/to/vertector-nats-jetstream
docker-compose up -d
```

### 2. Start GraphRAG Note Service

```bash
cd /path/to/graphrag
docker-compose up -d
```

This will:
- ✓ Start Neo4j database
- ✓ Start Note Service
- ✓ Download embedding model (first time only, ~1.5GB)
- ✓ Create database indices
- ✓ Begin consuming NATS events automatically

### 3. Verify Services

```bash
# Check running containers
docker-compose ps

# View Note Service logs
docker-compose logs -f note-service

# View Neo4j logs
docker-compose logs neo4j
```

### 4. Access Services

- **Neo4j Browser**: http://localhost:7474
  - Username: `neo4j`
  - Password: `graphrag_secure_password_2025`

- **NATS Monitoring**: http://localhost:8222

## Running Locally (Without Docker)

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file:

```bash
# Neo4j Configuration
NEO4J__URI=bolt://localhost:7687
NEO4J__USERNAME=neo4j
NEO4J__PASSWORD=graphrag_secure_password_2025
NEO4J__DATABASE=neo4j

# NATS Configuration
NATS__SERVERS=["nats://localhost:4222"]
NATS__STREAM_NAME=ACADEMIC_EVENTS
NATS__DURABLE_NAME=graphrag-note-service-consumer-v2

# Embedding Configuration
EMBEDDING__MODEL_NAME=Qwen/Qwen3-Embedding-0.6B
EMBEDDING__DEVICE=cpu
EMBEDDING__NORMALIZE_EMBEDDINGS=true
EMBEDDING__BATCH_SIZE=32
EMBEDDING__DIMENSIONS=1024
```

### 3. Start Service

```bash
# Option 1: Using startup script
./start.sh

# Option 2: Direct Python
export PYTHONPATH=src:${PYTHONPATH}
python3 -m note_service.main
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEO4J__URI` | Neo4j connection URI | `bolt://localhost:7687` |
| `NEO4J__USERNAME` | Neo4j username | `neo4j` |
| `NEO4J__PASSWORD` | Neo4j password | (required) |
| `NATS__SERVERS` | NATS server URLs | `["nats://localhost:4222"]` |
| `NATS__STREAM_NAME` | JetStream stream name | `ACADEMIC_EVENTS` |
| `NATS__DURABLE_NAME` | Consumer durable name | `graphrag-note-service-consumer-v2` |
| `EMBEDDING__MODEL_NAME` | HuggingFace model | `Qwen/Qwen3-Embedding-0.6B` |
| `EMBEDDING__DEVICE` | Computation device | `cpu` (or `cuda`) |
| `EMBEDDING__DIMENSIONS` | Embedding dimensions | `1024` |

## Monitoring

### Health Checks

```bash
# Check if Note Service is healthy
docker exec graphrag-note-service python -c "import sys; sys.exit(0)"

# Check Neo4j connectivity
docker exec graphrag-note-service python -c "
from note_service.db.connection import Neo4jConnection
from note_service.config import Settings
conn = Neo4jConnection(settings=Settings())
conn.close()
print('✓ Neo4j connection successful')
"
```

### Logs

```bash
# Follow all logs
docker-compose logs -f

# Note Service only
docker-compose logs -f note-service

# Check for errors
docker-compose logs note-service | grep ERROR
```

### Metrics

The service exposes Prometheus metrics:
- `graphrag_nats_events_received_total` - Events received
- `graphrag_nats_events_processed_total` - Events processed successfully
- `graphrag_nats_events_failed_total` - Failed events
- `graphrag_nats_event_processing_seconds` - Processing time histogram
- `graphrag_nats_consumer_lag` - Consumer lag

## Troubleshooting

### Service won't start

```bash
# Check logs
docker-compose logs note-service

# Common issues:
# 1. Neo4j not ready - wait 30s and retry
# 2. NATS not running - start vertector-nats-jetstream first
# 3. Port conflicts - check ports 7474, 7687, 4222
```

### No events being processed

```bash
# 1. Verify NATS is running
docker ps | grep nats

# 2. Check NATS stream exists
docker exec graphrag-nats nats stream ls

# 3. Check consumer is registered
docker logs graphrag-note-service | grep "consumer started"

# 4. Publish test event (from vertector-nats-jetstream)
cd /path/to/vertector-nats-jetstream
python3 examples/publisher_example.py
```

### Embeddings not generated

```bash
# Check logs for embedding generation
docker logs graphrag-note-service | grep "Generated embedding"

# Should see:
# "Auto-embedding enabled for Course"
# "Generated embedding for Course: 1024 dimensions"

# Verify in Neo4j Browser:
MATCH (c:Course)
RETURN c.course_id, c.embedding_vector IS NOT NULL as has_embedding,
       size(c.embedding_vector) as dimensions
```

### Out of memory

```bash
# Reduce batch size in docker-compose.yml
EMBEDDING__BATCH_SIZE=16  # Default is 32

# Or allocate more memory to Docker
# Docker Desktop → Settings → Resources → Memory: 6GB+
```

## Updating

### Pull latest changes

```bash
git pull origin main

# Rebuild and restart
docker-compose build --no-cache note-service
docker-compose up -d note-service
```

### Update dependencies

```bash
# Edit requirements.txt
# Then rebuild
docker-compose build note-service
docker-compose up -d note-service
```

## Production Recommendations

### 1. Security

- Change default Neo4j password
- Use secrets management (Docker secrets, Vault)
- Enable NATS authentication
- Use TLS/SSL for connections

### 2. Persistence

```yaml
# Add named volumes for production
volumes:
  neo4j_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /mnt/data/neo4j
```

### 3. Scaling

- Use GPU for embeddings (`EMBEDDING__DEVICE=cuda`)
- Increase batch size (`EMBEDDING__BATCH_SIZE=64`)
- Run multiple consumer instances with different durable names
- Use Neo4j Enterprise for clustering

### 4. Monitoring

- Set up Prometheus + Grafana
- Configure alerting (PagerDuty, Slack)
- Monitor disk space (embeddings cache grows)
- Track consumer lag

## Backup & Recovery

### Backup Neo4j

```bash
# Stop service
docker-compose stop note-service

# Backup Neo4j data
docker exec graphrag-neo4j neo4j-admin database dump neo4j \
  --to-path=/backups/neo4j-$(date +%Y%m%d).dump

# Copy from container
docker cp graphrag-neo4j:/backups ./backups/

# Restart service
docker-compose start note-service
```

### Restore Neo4j

```bash
# Stop services
docker-compose down

# Restore dump
docker run --rm -v $(pwd)/backups:/backups \
  -v $(pwd)/neo4j/data:/data \
  neo4j:2025.09.0-community-bullseye \
  neo4j-admin database load neo4j --from-path=/backups/neo4j-20250125.dump

# Start services
docker-compose up -d
```

## Support

- Documentation: `/docs` directory
- Issues: GitHub Issues
- Logs: `docker-compose logs`
- Neo4j Browser: http://localhost:7474

## License

[Your License]
