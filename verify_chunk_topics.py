"""
Verify that chunks are only linked to topics from their actual content.
"""

from note_service.config import Settings
from note_service.db.connection import Neo4jConnection

settings = Settings()
connection = Neo4jConnection(settings)

print("\n" + "=" * 80)
print("CHUNK TOPIC VERIFICATION")
print("=" * 80 + "\n")

with connection.driver.session() as session:
    # Get all chunks with their topics and content preview
    result = session.run("""
        MATCH (c:Chunk)-[:PART_OF]->(ln:LectureNote)
        OPTIONAL MATCH (c)-[:COVERS_TOPIC]->(t:Topic)
        WITH ln, c, collect(t.name) as chunk_topics
        ORDER BY ln.lecture_note_id, c.chunk_index
        RETURN ln.title as note_title,
               c.chunk_index as chunk_index,
               c.heading as chunk_heading,
               substring(c.content, 0, 200) as content_preview,
               chunk_topics
    """)

    for record in result:
        print(f"Note: {record['note_title']}")
        print(f"  Chunk #{record['chunk_index']}: {record['chunk_heading']}")
        print(f"  Content: {record['content_preview']}...")
        print(f"  Topics: {record['chunk_topics']}")
        print()

print("=" * 80)
print("DOCUMENT vs CHUNK TOPIC COMPARISON")
print("=" * 80 + "\n")

with connection.driver.session() as session:
    # Compare document-level vs chunk-level topics
    result = session.run("""
        MATCH (ln:LectureNote)
        OPTIONAL MATCH (ln)-[:COVERS_TOPIC]->(dt:Topic)
        WITH ln, collect(DISTINCT dt.name) as doc_topics
        OPTIONAL MATCH (c:Chunk)-[:PART_OF]->(ln)
        OPTIONAL MATCH (c)-[:COVERS_TOPIC]->(ct:Topic)
        WITH ln, doc_topics, collect(DISTINCT ct.name) as chunk_topics
        RETURN ln.title as note_title,
               doc_topics,
               chunk_topics,
               size(doc_topics) as doc_topic_count,
               size(chunk_topics) as chunk_topic_count
        ORDER BY ln.title
    """)

    for record in result:
        print(f"{record['note_title']}:")
        print(f"  Document topics ({record['doc_topic_count']}): {record['doc_topics']}")
        print(f"  Chunk topics ({record['chunk_topic_count']}): {record['chunk_topics']}")
        print()

connection.close()
