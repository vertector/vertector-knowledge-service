# Chunk Generation Flow

## Complete Process Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    User Creates LectureNote                              │
│                   (title, content, key_concepts)                         │
└─────────────────────────┬───────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  data_loader.create_node()                               │
│  1. Auto-generate summary (if missing)                                  │
│  2. Auto-generate tags                                                   │
│  3. Generate embedding for LectureNote                                   │
│  4. Save LectureNote to Neo4j                                            │
│  5. Create relationships (BELONGS_TO Course, CREATED_BY Profile)         │
└─────────────────────────┬───────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│          data_loader._generate_chunks_for_lecture_note()                 │
│                                                                          │
│  Triggered automatically after LectureNote creation                      │
└─────────────────────────┬───────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│             chunk_generator.generate_chunks()                            │
│                                                                          │
│  Step 1: Semantic Chunking                                              │
│  ┌────────────────────────────────────────────────────┐                │
│  │ _semantic_chunking(content)                        │                │
│  │                                                    │                │
│  │ 1. Split content by lines                         │                │
│  │ 2. Detect markdown headings (##, ###, etc.)       │                │
│  │ 3. Detect code blocks (```)                       │                │
│  │ 4. Group content under each heading               │                │
│  │                                                    │                │
│  │ Example:                                           │                │
│  │   Input:                                           │                │
│  │     ## Introduction                                │                │
│  │     Variables store data...                        │                │
│  │     ## Data Types                                  │                │
│  │     Python has several types...                    │                │
│  │                                                    │                │
│  │   Output:                                          │                │
│  │     Chunk 0: (content, "Introduction", "heading") │                │
│  │     Chunk 1: (content, "Data Types", "heading")   │                │
│  └────────────────────────────────────────────────────┘                │
│                                                                          │
│  Step 2: Fallback to Fixed-Size (if needed)                             │
│  ┌────────────────────────────────────────────────────┐                │
│  │ If content has no markdown structure AND            │                │
│  │ is larger than max_chunk_tokens * 4:               │                │
│  │                                                    │                │
│  │ _fixed_size_chunking(content)                     │                │
│  │ 1. Split by words                                 │                │
│  │ 2. Group into max_chunk_tokens (512) chunks       │                │
│  │ 3. Add overlap_tokens (50) between chunks         │                │
│  └────────────────────────────────────────────────────┘                │
│                                                                          │
│  Step 3: Create Chunk Objects                                           │
│  ┌────────────────────────────────────────────────────┐                │
│  │ For each chunk:                                     │                │
│  │ - Filter out small chunks (< min_chunk_tokens=25)  │                │
│  │ - Generate unique ID: CHUNK-NOTE-001-000          │                │
│  │ - Estimate token count (~len/4)                    │                │
│  │ - Track char positions (start, end)               │                │
│  │                                                    │                │
│  │ Chunk Properties:                                  │                │
│  │   chunk_id: "CHUNK-NOTE-001-000"                  │                │
│  │   lecture_note_id: "NOTE-001"                     │                │
│  │   content: "## Introduction\nVariables..."        │                │
│  │   chunk_index: 0                                   │                │
│  │   heading: "Introduction"                          │                │
│  │   chunk_type: "heading"                            │                │
│  │   token_count: 45                                  │                │
│  │   char_start: 0                                    │                │
│  │   char_end: 180                                    │                │
│  └────────────────────────────────────────────────────┘                │
└─────────────────────────┬───────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│            Generate Embeddings for All Chunks                            │
│                                                                          │
│  embedder.embed_documents(chunk_texts)                                   │
│                                                                          │
│  1. Extract text from each chunk                                        │
│  2. Batch process through Qwen3-Embedding-0.6B model                    │
│  3. Generate 1024-dimensional vectors                                    │
│                                                                          │
│  Output: {                                                               │
│    "CHUNK-NOTE-001-000": [0.023, -0.145, 0.089, ...],  # 1024 dims     │
│    "CHUNK-NOTE-001-001": [0.112, -0.034, 0.156, ...],                  │
│    ...                                                                   │
│  }                                                                       │
└─────────────────────────┬───────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│          chunk_generator.save_chunks_to_neo4j()                          │
│                                                                          │
│  Step 1: Create Chunk Nodes                                             │
│  ┌────────────────────────────────────────────────────┐                │
│  │ For each chunk:                                     │                │
│  │                                                    │                │
│  │ MERGE (c:Chunk {chunk_id: $chunk_id})             │                │
│  │ SET c.content = ...                               │                │
│  │     c.heading = ...                               │                │
│  │     c.chunk_index = ...                           │                │
│  │     c.embedding_vector = [...]                    │                │
│  │     c.token_count = ...                           │                │
│  │     c.char_start = ...                            │                │
│  │     c.char_end = ...                              │                │
│  └────────────────────────────────────────────────────┘                │
│                                                                          │
│  Step 2: Create PART_OF Relationships                                   │
│  ┌────────────────────────────────────────────────────┐                │
│  │ Link each Chunk to parent LectureNote:             │                │
│  │                                                    │                │
│  │ (Chunk)-[:PART_OF]->(LectureNote)                 │                │
│  │                                                    │                │
│  │ Example:                                           │                │
│  │   (CHUNK-NOTE-001-000)-[:PART_OF]->(NOTE-001)    │                │
│  │   (CHUNK-NOTE-001-001)-[:PART_OF]->(NOTE-001)    │                │
│  └────────────────────────────────────────────────────┘                │
│                                                                          │
│  Step 3: Create NEXT_CHUNK Relationships                                │
│  ┌────────────────────────────────────────────────────┐                │
│  │ Link sequential chunks:                            │                │
│  │                                                    │                │
│  │ (Chunk[i])-[:NEXT_CHUNK]->(Chunk[i+1])           │                │
│  │                                                    │                │
│  │ Example:                                           │                │
│  │   (CHUNK-000)-[:NEXT_CHUNK]->(CHUNK-001)         │                │
│  │   (CHUNK-001)-[:NEXT_CHUNK]->(CHUNK-002)         │                │
│  │                                                    │                │
│  │ This enables sequential reading and context       │                │
│  └────────────────────────────────────────────────────┘                │
└─────────────────────────┬───────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Final Graph Structure                                 │
│                                                                          │
│   (Profile)                                                              │
│       ↑                                                                  │
│       │ CREATED_BY                                                       │
│       │                                                                  │
│   (LectureNote) ────BELONGS_TO───→ (Course)                             │
│       ↑                                                                  │
│       │ PART_OF                                                          │
│       │                                                                  │
│   (Chunk[0])─NEXT_CHUNK→(Chunk[1])─NEXT_CHUNK→(Chunk[2])               │
│       │                      │                     │                     │
│       │ Properties:          │                     │                     │
│       │ - content            │                     │                     │
│       │ - heading            │                     │                     │
│       │ - embedding_vector   │                     │                     │
│       │ - token_count        │                     │                     │
│       │ - chunk_index        │                     │                     │
│       │ - char_start/end     │                     │                     │
└─────────────────────────────────────────────────────────────────────────┘
```

## Configuration Parameters

From `data_loader.py:97-101`:
```python
self.chunk_generator = ChunkGenerator(
    driver=self.connection.driver,
    max_chunk_tokens=512,      # Maximum tokens per chunk
    overlap_tokens=50,          # Overlap for context preservation
    min_chunk_tokens=25         # Filter out tiny chunks
)
```

## Real Example

**Input LectureNote:**
```markdown
Title: Python Variables and Data Types

## Introduction to Variables
Variables in Python are used to store data values...

### Variable Naming Rules
1. Variable names must start with a letter...
2. Variable names can only contain letters...

## Data Types
Python has several built-in data types...

### Numeric Types
- **int**: Integer numbers...
- **float**: Decimal numbers...
```

**Generated Chunks:**

| Chunk ID | Heading | Type | Content Preview | Tokens |
|----------|---------|------|-----------------|--------|
| CHUNK-NOTE-001-000 | Introduction to Variables | heading | ## Introduction to Variables\nVariables in Python... | 45 |
| CHUNK-NOTE-001-001 | Variable Naming Rules | heading | ### Variable Naming Rules\n1. Variable names... | 38 |
| CHUNK-NOTE-001-003 | Data Types | heading | ## Data Types\nPython has several built-in... | 52 |
| CHUNK-NOTE-001-006 | Numeric Types | heading | ### Numeric Types\n- **int**: Integer numbers... | 41 |

**Graph Relationships:**
```
(NOTE-001)
    ↑
    │ PART_OF
    │
(CHUNK-000) → (CHUNK-001) → (CHUNK-003) → (CHUNK-006)
  NEXT_CHUNK    NEXT_CHUNK    NEXT_CHUNK
```

## Key Features

1. **Semantic Chunking** - Respects markdown structure
2. **Code Block Preservation** - Keeps code together
3. **Minimum Size Filtering** - Skips chunks < 25 tokens
4. **Sequential Linking** - NEXT_CHUNK relationships
5. **Embedding Generation** - 1024-dim vectors per chunk
6. **Position Tracking** - char_start/char_end for highlighting

## Usage in Retrieval

Chunks enable **precise retrieval**:

```cypher
// Vector search returns specific chunks, not entire documents
CALL db.index.vector.queryNodes(
  'chunk_embedding_index',
  5,
  $query_vector
) YIELD node, score
RETURN node.content, node.heading, score
```

This is much more precise than returning entire LectureNotes!
