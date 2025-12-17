# Gemini Code Understanding

This document provides a comprehensive overview of the Vertector Knowledge Service, a GraphRAG-powered microservice designed for Vertector's academic productivity platform.

## Project Overview

The Vertector Knowledge Service is a Python-based microservice that processes academic events in real-time, constructs a Neo4j knowledge graph with semantic embeddings, and provides contextual query capabilities. It is a core component of the Vertector microservices architecture and is designed to support features like exam preparation, assignment assistance, and personalized study recommendations.

The service is built with a focus on event-driven architecture, utilizing NATS JetStream for consuming academic events. It leverages sentence transformers to generate embeddings for semantic search and uses Neo4j as its graph database.

### Key Technologies

- **Programming Language:** Python 3.12+
- **Graph Database:** Neo4j 5.x
- **Message Broker:** NATS JetStream
- **Embeddings:** Sentence Transformers (e.g., `all-MiniLM-L6-v2`)
- **Core Libraries:**
    - `neo4j`: Official Neo4j driver for Python.
    - `nats-py`: Python client for NATS.
    - `sentence-transformers`: For generating embeddings.
    - `pydantic`: For data validation and settings management.
- **Development & CI/CD:**
    - `docker`: For containerization.
    - `pytest`: For testing.
    - `black`, `ruff`, `mypy`: For code formatting, linting, and type checking.

### Architecture

The service follows a layered architecture:

1.  **Main Application (`main.py`):** The entry point of the service, responsible for initializing and managing the lifecycle of the other components.
2.  **NATS Integration (`nats_integration/`):**
    -   **Consumer (`consumer.py`):** Subscribes to NATS topics, receives messages, and delegates processing to the data adapter.
    -   **Data Adapter (`data_adapter.py`):** Translates NATS messages into a format suitable for the data loader and orchestrates the ingestion process.
3.  **Ingestion (`ingestion/`):**
    -   **Data Loader (`data_loader.py`):** Handles the direct interaction with the Neo4j database, including node creation, updates, and relationship management.
    -   **Tag and Topic Generation:** Includes services for automatically generating tags and extracting topics from lecture notes using LLMs.
4.  **Database (`db/`):** Manages the connection to the Neo4j database.

## Building and Running

### Prerequisites

-   Docker and Docker Compose
-   Python 3.12+

### Running the Service (Docker)

1.  **Set up the environment:**
    ```bash
    cp .env.example .env
    # Edit .env with your Neo4j and NATS configurations
    ```
2.  **Start the services:**
    ```bash
    docker-compose up -d
    ```
3.  **Monitor the logs:**
    ```bash
    docker-compose logs -f note-service
    ```

### Local Development

1.  **Install dependencies:**
    ```bash
    uv pip install -e .[dev]
    ```
2.  **Run the service:**
    ```bash
    python src/note_service/main.py
    ```

### Running Tests

To run the integration tests, use the following command:

```bash
pytest
```

## Development Conventions

-   **Code Style:** The project uses `black` for code formatting and `ruff` for linting.
-   **Typing:** The codebase uses type hints and is checked with `mypy`.
-   **Testing:** The project has a `tests/` directory with unit and integration tests. `pytest` is the test runner.
-   **Configuration:** Application configuration is managed through environment variables and Pydantic settings.
-   **Asynchronous Code:** The service makes extensive use of `asyncio` for handling concurrent operations, especially for NATS and database interactions.
