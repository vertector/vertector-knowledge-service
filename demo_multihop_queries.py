"""
============================================================================
Multi-Hop Query Demo
============================================================================
Demonstrates the power of dual-level topic linking (Document + Chunk)
for advanced GraphRAG retrieval and multi-hop reasoning
============================================================================
"""

from note_service.config import Settings
from note_service.db.connection import Neo4jConnection

settings = Settings()
connection = Neo4jConnection(settings)


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80 + "\n")


def run_query(session, title, query, description=""):
    """Run a Cypher query and display results."""
    print(f"Query: {title}")
    if description:
        print(f"Description: {description}")
    print(f"Cypher: {query[:100]}...")
    print()

    result = session.run(query)
    records = list(result)

    if not records:
        print("  No results found")
    else:
        for i, record in enumerate(records, 1):
            print(f"  Result {i}:")
            for key, value in record.items():
                if isinstance(value, list) and len(value) > 5:
                    print(f"    {key}: {value[:5]}... ({len(value)} total)")
                else:
                    print(f"    {key}: {value}")
    print()


print_section("MULTI-HOP QUERY DEMONSTRATIONS")

with connection.driver.session() as session:

    # Query 1: Document-level broad search
    print_section("Query 1: Document-Level Search (Broad)")
    run_query(
        session,
        "Find all Python notes",
        """
        MATCH (ln:LectureNote)-[r:COVERS_TOPIC {specificity: 'document'}]->(t:Topic)
        WHERE t.name CONTAINS 'Python'
        WITH ln, collect(t.name) as topics
        RETURN ln.lecture_note_id as note_id,
               ln.title as note_title,
               topics
        ORDER BY note_id
        """,
        "Uses document-level topics for broad discovery"
    )

    # Query 2: Chunk-level precise search
    print_section("Query 2: Chunk-Level Search (Precise)")
    run_query(
        session,
        "Find specific content about 'Type Conversion'",
        """
        MATCH (c:Chunk)-[r:COVERS_TOPIC {specificity: 'chunk'}]->(t:Topic {name: 'Type Conversion'})
        MATCH (c)-[:PART_OF]->(ln:LectureNote)
        RETURN ln.title as note_title,
               c.heading as chunk_heading,
               substring(c.content, 0, 150) + '...' as content_preview
        """,
        "Uses chunk-level topics for precise retrieval"
    )

    # Query 3: Topic co-occurrence (multi-hop)
    print_section("Query 3: Topic Co-occurrence Analysis (Multi-Hop)")
    run_query(
        session,
        "Find topics that appear together with 'Variables'",
        """
        MATCH (c1:Chunk)-[:COVERS_TOPIC]->(t1:Topic)
        WHERE t1.name CONTAINS 'Variables'
        MATCH (c1)-[:PART_OF]->(ln:LectureNote)
        MATCH (c2:Chunk)-[:PART_OF]->(ln)
        MATCH (c2)-[:COVERS_TOPIC]->(t2:Topic)
        WHERE t2 <> t1
        WITH t2, collect(DISTINCT ln) as notes
        RETURN t2.name as related_topic,
               size(notes) as note_count,
               [n IN notes | n.title][0..2] as sample_notes
        ORDER BY note_count DESC
        LIMIT 5
        """,
        "Multi-hop: Find topics that co-occur with Variables in the same document"
    )

    # Query 4: Prerequisite detection
    print_section("Query 4: Prerequisite Topic Detection (Multi-Hop)")
    run_query(
        session,
        "Find topics that appear before 'Lambda Functions'",
        """
        MATCH (c1:Chunk)-[:COVERS_TOPIC]->(t1:Topic)
        WHERE t1.name = 'Lambda Functions'
        MATCH (c1)-[:PART_OF]->(ln:LectureNote)
        MATCH (c2:Chunk)-[:PART_OF]->(ln)
        MATCH (c2)-[:COVERS_TOPIC]->(t2:Topic)
        WHERE c2.chunk_index < c1.chunk_index
        RETURN DISTINCT t2.name as prerequisite_topic,
               c2.heading as in_chunk,
               c2.chunk_index as chunk_position
        ORDER BY chunk_position
        """,
        "Multi-hop: Identify topics discussed earlier in the same note"
    )

    # Query 5: Hybrid retrieval (combining document + chunk topics)
    print_section("Query 5: Hybrid Retrieval (Document + Chunk)")
    run_query(
        session,
        "Find Python notes that specifically discuss Functions",
        """
        MATCH (ln:LectureNote)-[:COVERS_TOPIC {specificity: 'document'}]->(dt:Topic)
        WHERE dt.name CONTAINS 'Python'
        MATCH (c:Chunk)-[:PART_OF]->(ln)
        MATCH (c)-[:COVERS_TOPIC {specificity: 'chunk'}]->(ct:Topic)
        WHERE ct.name CONTAINS 'Function'
        RETURN ln.title as note_title,
               c.heading as relevant_section,
               substring(c.content, 0, 100) + '...' as preview
        """,
        "Combines document-level filtering with chunk-level precision"
    )

    # Query 6: Topic difficulty progression
    print_section("Query 6: Topic Learning Progression")
    run_query(
        session,
        "Track how 'Variables' topic is introduced across documents",
        """
        MATCH (c:Chunk)-[:COVERS_TOPIC]->(t:Topic)
        WHERE t.name CONTAINS 'Variables'
        MATCH (c)-[:PART_OF]->(ln:LectureNote)
        RETURN ln.title as note_title,
               c.chunk_index as position_in_note,
               c.heading as section_heading,
               c.token_count as content_length
        ORDER BY ln.created_at, c.chunk_index
        """,
        "Multi-hop: Analyze topic introduction patterns"
    )

    # Query 7: Find chunks bridging two topics
    print_section("Query 7: Find Content Bridging Two Topics")
    run_query(
        session,
        "Find chunks discussing both Variables AND Type Conversion",
        """
        MATCH (ln:LectureNote)-[:COVERS_TOPIC {specificity: 'document'}]->(t1:Topic)
        WHERE t1.name CONTAINS 'Variables'
        MATCH (c:Chunk)-[:PART_OF]->(ln)
        MATCH (c)-[:COVERS_TOPIC {specificity: 'chunk'}]->(t2:Topic)
        WHERE t2.name = 'Type Conversion'
        RETURN ln.title as note_title,
               c.heading as bridging_section,
               substring(c.content, 0, 120) + '...' as content
        """,
        "Multi-hop: Find specific content connecting two concepts"
    )

    # Query 8: Statistics
    print_section("Query 8: Topic Linking Statistics")
    run_query(
        session,
        "Summary of dual-level topic structure",
        """
        MATCH (ln:LectureNote)-[dr:COVERS_TOPIC {specificity: 'document'}]->(dt:Topic)
        WITH count(DISTINCT ln) as total_notes,
             count(DISTINCT dt) as doc_topics,
             count(dr) as doc_relationships
        MATCH (c:Chunk)-[cr:COVERS_TOPIC {specificity: 'chunk'}]->(ct:Topic)
        WITH total_notes, doc_topics, doc_relationships,
             count(DISTINCT c) as total_chunks,
             count(DISTINCT ct) as chunk_topics,
             count(cr) as chunk_relationships
        RETURN total_notes,
               total_chunks,
               doc_topics,
               chunk_topics,
               doc_relationships,
               chunk_relationships,
               doc_relationships + chunk_relationships as total_relationships
        """,
        "Overview of the dual-level topic graph structure"
    )

connection.close()

print()
print("=" * 80)
print("✅ Multi-hop query demonstrations complete!")
print("=" * 80)
print()
print("Key Insights:")
print("  1. Document-level topics enable broad discovery")
print("  2. Chunk-level topics enable precise retrieval")
print("  3. Multi-hop queries reveal relationships between topics")
print("  4. Hybrid queries combine the best of both approaches")
print("  5. Topic co-occurrence helps identify related concepts")
print()
