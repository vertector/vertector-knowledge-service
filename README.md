# Vertector Knowledge Service

GraphRAG-powered knowledge service for Vertector's academic productivity platform. Consumes academic events via NATS JetStream, builds Neo4j knowledge graphs with semantic embeddings, and enables contextual queries for exam prep, assignment help, and personalized study recommendations.

## Overview

The Knowledge Service is a core component of the Vertector microservices architecture, responsible for:

- **Real-time Event Processing**: Consumes academic events (courses, assignments, exams, quizzes, labs, profiles) from NATS JetStream
- **Knowledge Graph Construction**: Builds course-centric Neo4j graphs with semantically meaningful relationships
- **Semantic Search**: Generates embeddings for contextual note retrieval and intelligent recommendations
- **Profile Integration**: Links student profiles with their enrolled courses and academic activities
- **Challenge Detection**: Identifies learning difficulties and suggests targeted interventions

## Architecture

### Technology Stack

- **Graph Database**: Neo4j 5.x with semantic embeddings
- **Message Broker**: NATS JetStream for event-driven architecture
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **Language**: Python 3.12+ with async/await
- **Container**: Docker with hot-reload for development

### Integration Points

- **Profile Service**: Receives student profile and enrollment events
- **Academic Service** (planned): Will receive course, assignment, and grade data
- **Study Planning Service** (planned): Will consume knowledge graph insights
- **Exam Prep Service** (planned): Will use challenge areas and recommendations

## Features

### Knowledge Graph Model

The service implements a **course-centric** knowledge graph with descriptive relationships:

```
Profile --[ENROLLED_IN]--> Course
Assignment --[ASSIGNED_IN]--> Course
Exam --[SCHEDULED_IN]--> Course
Quiz --[GIVEN_IN]--> Course
Lab_Session --[PART_OF]--> Course
Study_Todo --[FOR_COURSE]--> Course
Challenge_Area --[IDENTIFIED_IN_COURSE]--> Course
```

### Event Types

Processes events from NATS subjects:
- `academic.profile.created` - New student profiles
- `academic.profile.updated` - Profile changes
- `academic.profile.enrolled` - Course enrollments
- `academic.course.*` - Course lifecycle events
- `academic.assignment.*` - Assignment events
- `academic.exam.*` - Exam scheduling and results
- `academic.quiz.*` - Quiz events
- `academic.lab.*` - Lab session tracking
- `academic.study.*` - Study todos and plans
- `academic.challenge.*` - Identified learning challenges

### Semantic Capabilities

- **Automatic Embedding Generation**: Creates vector embeddings for all text content
- **Contextual Retrieval**: Query notes by upcoming exams, assignments, or topics
- **Challenge Area Detection**: Identifies topics where students struggle
- **Intelligent Recommendations**: Suggests resources based on performance patterns

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.12+
- NATS Server (or use Docker Compose)
- Neo4j (or use Docker Compose)

### Installation

1. **Clone the repository**:
```bash
git clone https://github.com/vertector/vertector-knowledge-service.git
cd vertector-knowledge-service
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start services**:
```bash
docker-compose up -d
```

4. **Verify deployment**:
```bash
docker-compose logs -f note-service
```

### Configuration

Key environment variables in `.env`:

```bash
# Neo4j Configuration
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_secure_password

# NATS Configuration
NATS_SERVERS=["nats://localhost:4222"]
NATS_STREAM_NAME=ACADEMIC_EVENTS
NATS_DURABLE_NAME=graphrag-knowledge-consumer

# Service Configuration
LOG_LEVEL=INFO
ENABLE_AUTO_EMBEDDINGS=true
ENABLE_IDEMPOTENCY=true
```

## Development

### Project Structure

```
vertector-knowledge-service/
├── src/note_service/           # Main application code
│   ├── config.py               # Configuration management
│   ├── main.py                 # Service entry point
│   ├── db/                     # Neo4j connection and queries
│   ├── ingestion/              # Knowledge graph construction
│   │   ├── data_loader.py      # Data loading and transformation
│   │   └── relationships.py    # Relationship rules engine
│   ├── models/                 # Pydantic data models
│   ├── nats_integration/       # NATS event processing
│   │   ├── consumer.py         # Event consumer with routing
│   │   ├── data_adapter.py     # NATS → Neo4j adapter
│   │   └── config.py           # NATS configuration
│   └── retrieval/              # Semantic search and retrieval
├── schema/                     # Neo4j schema definitions
├── scripts/                    # Utility scripts
├── tests/                      # Integration and unit tests
├── docker-compose.yml          # Multi-container orchestration
├── Dockerfile                  # Service container definition
└── pyproject.toml              # Python dependencies
```

### Running Tests

```bash
# Integration tests
python tests/integration/test_comprehensive_academic_profile.py

# NATS pipeline test
python tests/integration/test_nats_pipeline.py
```

### Local Development

```bash
# Install dependencies
uv pip install -e .

# Run service locally
python src/note_service/main.py
```

## API & Querying

### Neo4j Cypher Queries

**Find all courses for a student**:
```cypher
MATCH (p:Profile {student_id: 'S2025001'})-[:ENROLLED_IN]->(c:Course)
RETURN p, c
```

**Get upcoming assignments**:
```cypher
MATCH (p:Profile {student_id: 'S2025001'})-[:ENROLLED_IN]->(c:Course)
MATCH (a:Assignment)-[:ASSIGNED_IN]->(c)
WHERE a.due_date > datetime()
RETURN a, c
ORDER BY a.due_date
```

**Identify challenge areas**:
```cypher
MATCH (p:Profile {student_id: 'S2025001'})-[:ENROLLED_IN]->(c:Course)
MATCH (ch:Challenge_Area)-[:IDENTIFIED_IN_COURSE]->(c)
WHERE ch.difficulty = 'Hard'
RETURN ch, c
```

## Monitoring

### Prometheus Metrics

Exposed on port `9090`:
- Event processing rates
- Neo4j query performance
- Embedding generation times
- Error rates and types

### Logging

Structured JSON logging with correlation IDs for request tracing across services.

## Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for production deployment guidelines.

## Roadmap

- [ ] Academic Service integration (ScyllaDB + Qdrant)
- [ ] Study plan generation service
- [ ] Exam and quiz preparation recommendations
- [ ] Performance analytics and insights
- [ ] Multi-tenancy support
- [ ] GraphQL API layer

## Contributing

This is a private repository. For Vertector team members:

1. Create a feature branch
2. Make your changes
3. Run tests
4. Submit a pull request

## License

Proprietary - Vertector Platform

## Support

For questions or issues, contact the Vertector development team.
