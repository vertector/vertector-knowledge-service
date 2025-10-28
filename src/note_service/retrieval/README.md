# Dynamic Retrieval Service

Production-ready retrieval service for the Academic Note-Taking GraphRAG system. Dynamically generates custom Cypher queries on-demand using LLM + graph schema introspection.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     RetrievalService                             │
│  (Main orchestrator - coordinates all components)                │
└────────────┬────────────────────────────────────────────────────┘
             │
    ┌────────┴────────┬──────────────┬──────────────────┐
    │                 │              │                  │
┌───▼───────────┐ ┌──▼────────┐ ┌──▼──────────┐ ┌────▼─────────┐
│ Schema        │ │ Dynamic    │ │ Embedding   │ │ Neo4j        │
│ Introspector  │ │ Query      │ │ Service     │ │ GraphRAG     │
│               │ │ Builder    │ │             │ │ Retrievers   │
└───┬───────────┘ └──┬─────────┘ └──┬──────────┘ └────┬─────────┘
    │                │              │                  │
    │ APOC           │ Google       │ Sentence         │ Hybrid/
    │ Meta Schema    │ Gemini LLM   │ Transformers     │ Vector/
    │                │              │ (Qwen3)          │ Cypher
    │                │              │                  │
┌───▼────────────────▼──────────────▼──────────────────▼─────────┐
│                        Neo4j Database                           │
│  (Vector indexes, Full-text indexes, Graph relationships)       │
└─────────────────────────────────────────────────────────────────┘
```

## Key Features

### 1. **Dynamic Query Generation**
- Queries are built on-demand using LLM (Google Gemini)
- No static, pre-defined query templates
- Adapts automatically to schema changes

### 2. **Schema-Aware**
- Uses APOC `apoc.meta.schema()` to introspect graph structure
- Caches schema with configurable TTL (default 5 minutes)
- Provides schema context to LLM for accurate query generation

### 3. **Self-Healing Queries**
- Validates generated Cypher syntax using `EXPLAIN`
- Automatically retries with error feedback (max 3 attempts)
- Learns from syntax errors to fix queries

### 4. **Hybrid Search**
- Combines vector similarity (semantic) + full-text (lexical)
- Graph traversal enrichment via custom Cypher queries
- Uses `HybridCypherRetriever` from neo4j-graphrag

### 5. **Multiple Search Modes**
- **hybrid**: Vector + fulltext + graph traversal (recommended)
- **vector**: Semantic search only
- **fulltext**: Keyword/phrase search only
- **standalone**: Direct LLM-to-Cypher without hybrid components

## Components

### SchemaIntrospector
Extracts and caches Neo4j graph schema.

**Key Methods:**
- `get_schema(use_cache=True)` - Get complete graph schema
- `format_schema_for_llm()` - Format schema for LLM prompts
- `invalidate_cache()` - Force schema refresh

**Example:**
```python
introspector = SchemaIntrospector(driver, cache_ttl_seconds=300)
schema = introspector.get_schema()
print(introspector.format_schema_for_llm(schema))
```

### DynamicQueryBuilder
Generates Cypher queries using LLM + schema context.

**Key Methods:**
- `build_standalone_query(question)` - Generate complete query
- `build_hybrid_retrieval_query(question, node_type)` - Generate traversal query
- Self-healing with validation and retry logic

**Example:**
```python
builder = DynamicQueryBuilder(driver, introspector, llm_model="gemini-2.0-flash-exp")

# Standalone query
result = builder.build_standalone_query("What assignments are due this week?")
print(result.query)

# Hybrid retrieval query
result = builder.build_hybrid_retrieval_query(
    "Explain neural networks",
    initial_node_type="Note"
)
print(result.query)
```

### EmbeddingService
Generates embeddings using SentenceTransformers (Qwen3-Embedding-0.6B).

**Key Methods:**
- `embed_query(text)` - Single query embedding
- `embed_documents(texts)` - Batch document embeddings
- `similarity(emb1, emb2)` - Cosine similarity

**Example:**
```python
embedder = EmbeddingService(model_name="Qwen/Qwen3-Embedding-0.6B")
query_emb = embedder.embed_query("neural networks")
doc_embs = embedder.embed_documents(["doc1", "doc2"])
similarity_score = embedder.similarity(query_emb, doc_embs[0])
```

### RetrievalService
Main orchestrator that coordinates all components.

**Key Methods:**
- `search(query_text, top_k, search_type, initial_node_type)`
- `refresh_schema()` - Manually refresh schema cache
- `get_schema_summary()` - Get formatted schema for debugging

## Usage

### Basic Setup

```python
from neo4j import GraphDatabase
from config import Settings
from retrieval.service import RetrievalService

# Initialize
settings = Settings()
driver = GraphDatabase.driver(
    settings.neo4j.uri,
    auth=(settings.neo4j.username, settings.neo4j.password.get_secret_value())
)

# Create retrieval service
retrieval_service = RetrievalService(
    driver=driver,
    settings=settings,
    google_api_key="your-google-api-key"  # or set GOOGLE_API_KEY env var
)
```

### Example 1: Hybrid Search

```python
result = retrieval_service.search(
    query_text="Explain backpropagation in neural networks",
    top_k=5,
    search_type="hybrid",
    initial_node_type="Note"
)

print(f"Generated Query:\n{result.query}\n")
print(f"Found {result.num_results} results:")
for item in result.results:
    print(item)
```

### Example 2: Standalone Query

```python
result = retrieval_service.search(
    query_text="What assignments are due this week?",
    search_type="standalone"
)

print(f"Query:\n{result.query}\n")
for assignment in result.results:
    print(f"- {assignment['assignment']}: {assignment['due_date']}")
```

### Example 3: Vector-Only Search

```python
result = retrieval_service.search(
    query_text="machine learning optimization",
    top_k=3,
    search_type="vector",
    initial_node_type="Topic"
)

for topic in result.results:
    print(topic['content'])
```

## Configuration

### Environment Variables

```bash
# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=graphrag_secure_password_2025
NEO4J_DATABASE=neo4j

# Embedding Model
EMBEDDING_MODEL_NAME=Qwen/Qwen3-Embedding-0.6B
EMBEDDING_DIMENSIONS=896
EMBEDDING_DEVICE=cpu
EMBEDDING_BATCH_SIZE=32

# LLM (Google Gemini)
LLM_MODEL_NAME=gemini-2.0-flash-exp
LLM_TEMPERATURE=0.0
GOOGLE_API_KEY=your-api-key-here

# Application
APP_ENVIRONMENT=development
APP_LOG_LEVEL=INFO
```

### Settings in Code

```python
from config import Settings

settings = Settings(
    neo4j=Neo4jSettings(
        uri="bolt://localhost:7687",
        password=SecretStr("your-password")
    ),
    llm=LLMSettings(
        model_name="gemini-2.0-flash-exp",
        temperature=0.0
    )
)
```

## How It Works

### 1. Schema Introspection

```python
# Automatically called on initialization
schema = introspector.get_schema()
# Returns: GraphSchema with nodes, relationships, indexes, constraints
```

### 2. Query Generation

**For Hybrid Search:**
```
User Question
     ↓
Schema Context + Few-Shot Examples
     ↓
LLM (Google Gemini)
     ↓
Cypher Traversal Query
     ↓
Validation (EXPLAIN)
     ↓
Self-Healing (if errors)
     ↓
Final Query
```

**For Standalone Search:**
```
User Question
     ↓
Schema Context + Few-Shot Examples
     ↓
LLM (Google Gemini)
     ↓
Complete Cypher Query
     ↓
Validation + Self-Healing
     ↓
Execute Directly
```

### 3. Hybrid Retrieval Execution

```
User Query
     ↓
Hybrid Search (Vector + Fulltext)
     ↓
Initial Nodes Matched
     ↓
Dynamic Cypher Traversal
     ↓
Graph Context Enrichment
     ↓
Aggregated Results
```

## Advanced Features

### Custom Result Formatting

```python
from neo4j_graphrag.types import RetrieverResultItem

def custom_formatter(record) -> RetrieverResultItem:
    content = f"""
    Title: {record.get('note_title')}
    Topics: {', '.join(record.get('topics', []))}
    """
    return RetrieverResultItem(
        content=content,
        metadata={"score": record.get("score")}
    )

# Use in HybridCypherRetriever initialization
```

### Schema Cache Management

```python
# Manual refresh
retrieval_service.refresh_schema()

# Configure TTL
introspector = SchemaIntrospector(driver, cache_ttl_seconds=600)  # 10 minutes

# Disable cache
schema = introspector.get_schema(use_cache=False)
```

### Query Validation

```python
result = builder.build_standalone_query("your question", validate=True)

if not result.is_valid:
    print(f"Query failed validation: {result.error_message}")
    print(f"Attempts: {result.attempts}")
else:
    print(f"Valid query generated in {result.attempts} attempt(s)")
```

## Performance Considerations

1. **Schema Caching**: Default 5-minute TTL balances freshness vs. performance
2. **LLM Calls**: Temperature=0 for deterministic query generation
3. **Batch Embeddings**: Configurable batch size (default 32)
4. **Self-Healing**: Max 3 attempts to fix syntax errors
5. **Connection Pooling**: Uses Neo4j driver's connection pool (max 50)

## Error Handling

All components include comprehensive error handling:

```python
try:
    result = retrieval_service.search("your query")
    if result.num_results == 0:
        print("No results found")
    elif result.query_generation and not result.query_generation.is_valid:
        print(f"Query generation failed: {result.query_generation.error_message}")
except Exception as e:
    logger.error(f"Retrieval failed: {e}")
```

## Logging

Configure logging level:

```python
import logging

logging.basicConfig(level=logging.DEBUG)  # See all debug messages
logging.getLogger("retrieval").setLevel(logging.INFO)  # Specific component
```

## Testing

See `tests/test_retrieval_service.py` for comprehensive test examples.

```bash
pytest tests/test_retrieval_service.py -v
```

## See Also

- [Neo4j GraphRAG Documentation](https://neo4j.com/docs/neo4j-graphrag-python/)
- [SentenceTransformers](https://www.sbert.net/)
- [Google Gemini API](https://ai.google.dev/)
