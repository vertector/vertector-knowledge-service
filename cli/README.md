# Note Service CLI

Command-line interface for managing lecture notes with full CRUD operations and semantic search.

## Features

- **Create**: Create notes with auto-generated summaries, tags, embeddings, and chunks
- **Read**: Get note details by ID
- **Update**: Update notes with automatic re-processing of embeddings and chunks
- **Delete**: Delete notes and all associated chunks
- **List**: Query notes by student, course, or tags
- **Search**: Semantic and hybrid search across notes

## Installation

The CLI is included in the project. Make sure dependencies are installed:

```bash
uv sync
```

## Usage

Run the CLI using the wrapper script:

```bash
./note-cli [COMMAND] [OPTIONS]
```

Or directly with Python:

```bash
PYTHONPATH=src uv run python src/note_service/cli.py [COMMAND] [OPTIONS]
```

## Commands

### Create a Note

Create a new lecture note with automatic processing:

```bash
./note-cli create \
  --student-id STU001 \
  --title "Graph Algorithms" \
  --content "BFS and DFS are fundamental graph traversal algorithms..." \
  --course-id CS301 \
  --tags "algorithms" --tags "graphs" \
  --key-concepts "BFS" --key-concepts "DFS"
```

**Read content from file:**

```bash
./note-cli create \
  --student-id STU001 \
  --title "Graph Algorithms" \
  --content @lecture-notes.txt \
  --course-id CS301
```

**Options:**
- `--student-id`: Required. Student ID who owns the note
- `--title`: Required. Note title
- `--content`: Required. Note content (use `@filename` to read from file)
- `--course-id`: Optional. Course ID
- `--summary`: Optional. Custom summary (auto-generated if not provided)
- `--key-concepts`: Optional. Key concepts (can specify multiple times)
- `--tags`: Optional. Manual tags (can specify multiple times, merged with LLM-generated)
- `--note-id`: Optional. Custom note ID (auto-generated if not provided)
- `--json-output`: Output as JSON

### Get a Note

Fetch note details by ID:

```bash
./note-cli get CS301-Fall2025-STU001-lecture-1
```

**Options:**
- `--json-output`: Output as JSON

### Update a Note

Update an existing note (only provide fields you want to change):

```bash
./note-cli update CS301-Fall2025-STU001-lecture-1 \
  --title "Updated Title" \
  --tags "algorithms" --tags "graphs" --tags "data-structures"
```

**Update content from file:**

```bash
./note-cli update CS301-Fall2025-STU001-lecture-1 \
  --content @updated-notes.txt
```

**Options:**
- `--title`: New title
- `--content`: New content (use `@filename` to read from file)
- `--summary`: New summary (auto-generated if content changes)
- `--key-concepts`: New key concepts (replaces existing)
- `--tags`: New manual tags (replaces existing, merged with LLM-generated)
- `--course-id`: New course ID
- `--json-output`: Output as JSON

**Note:** If content is updated, the system automatically:
- Regenerates summary (if not provided)
- Regenerates tags (merges manual + LLM-generated)
- Regenerates embeddings
- Regenerates all chunks

### Delete a Note

Delete a note and all its chunks:

```bash
./note-cli delete CS301-Fall2025-STU001-lecture-1
```

**Skip confirmation:**

```bash
./note-cli delete CS301-Fall2025-STU001-lecture-1 --yes
```

**Options:**
- `--yes`: Skip confirmation prompt

### List Notes

List notes with optional filters:

```bash
# List all notes for a student
./note-cli list --student-id STU001

# List notes for a specific course
./note-cli list --student-id STU001 --course-id CS301

# List notes with specific tags
./note-cli list --student-id STU001 --tags "algorithms" --tags "graphs"

# Pagination
./note-cli list --student-id STU001 --limit 5 --skip 10
```

**Options:**
- `--student-id`: Filter by student ID
- `--course-id`: Filter by course ID
- `--tags`: Filter by tags (notes must have at least one matching tag)
- `--limit`: Maximum number of results (default: 10)
- `--skip`: Number of results to skip (default: 0)
- `--json-output`: Output as JSON

### Search Notes

Semantic and hybrid search across notes:

```bash
# Basic search
./note-cli search \
  --query "graph traversal algorithms" \
  --student-id STU001

# Search with options
./note-cli search \
  --query "dynamic programming" \
  --student-id STU001 \
  --granularity chunk \
  --search-type hybrid \
  --top-k 10
```

**Options:**
- `--query`: Required. Search query
- `--student-id`: Required. Student ID for data isolation
- `--granularity`: Search granularity - `document` (default) or `chunk`
- `--search-type`: Search type - `hybrid` (default), `vector`, or `fulltext`
- `--top-k`: Number of results to return (default: 5)
- `--json-output`: Output as JSON

**Granularity:**
- `document`: Returns whole lecture notes (best for broad topics)
- `chunk`: Returns specific chunks/paragraphs (best for precise answers)

**Search Types:**
- `hybrid`: Combines semantic (vector) and keyword (fulltext) search
- `vector`: Semantic search only (good for conceptual queries)
- `fulltext`: Keyword search only (good for exact phrases)

## Examples

### Complete Workflow

```bash
# 1. Create a note
./note-cli create \
  --student-id STU001 \
  --title "Introduction to Graph Theory" \
  --content @graph-theory-notes.txt \
  --course-id MATH301 \
  --tags "mathematics" --tags "graphs"

# Output: Created LectureNote: MATH301-Fall2025-STU001-1

# 2. List student's notes
./note-cli list --student-id STU001 --limit 5

# 3. Get note details
./note-cli get MATH301-Fall2025-STU001-1

# 4. Update the note
./note-cli update MATH301-Fall2025-STU001-1 \
  --title "Advanced Graph Theory" \
  --tags "mathematics" --tags "graphs" --tags "advanced"

# 5. Search notes
./note-cli search \
  --query "shortest path algorithms" \
  --student-id STU001 \
  --top-k 3

# 6. Delete the note (with confirmation)
./note-cli delete MATH301-Fall2025-STU001-1
```

### JSON Output

All commands support `--json-output` for programmatic use:

```bash
./note-cli create \
  --student-id STU001 \
  --title "Test Note" \
  --content "Content here" \
  --json-output | jq .lecture_note_id
```

## Automatic Processing

When creating or updating notes, the CLI automatically:

1. **Generates ID**: Creates unique note ID if not provided
2. **Generates Summary**: Creates 3-sentence summary using LLM
3. **Generates Tags**: Extracts topics using LLM and merges with manual tags
4. **Generates Embeddings**: Creates vector embeddings for semantic search
5. **Generates Chunks**: Splits content into 500-character chunks with 100-character overlap
6. **Creates Relationships**: Links notes to courses if course_id provided

## Performance

- **Create**: ~5-10 seconds (including LLM processing and embedding generation)
- **Update**: ~5-15 seconds (regenerates embeddings/chunks if content changed)
- **Delete**: <1 second
- **List**: <1 second
- **Search**: 1-3 seconds (hybrid search with re-ranking)

## Data Isolation

All operations enforce student-level data isolation. Students can only access their own notes through the `--student-id` parameter.

## Error Handling

The CLI provides clear error messages:

```bash
./note-cli get INVALID-ID
# Error: LectureNote INVALID-ID not found

./note-cli delete INVALID-ID
# Note INVALID-ID not found
```

## Environment Requirements

- Neo4j database running
- Ollama running (for LLM-based tag/summary generation)
- Embedding model downloaded (sentence-transformers)

Check `.env` file for configuration:
```
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
GOOGLE_API_KEY=your-key-here  # For retrieval service
```
