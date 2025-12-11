"""
Check if Topics are creating unwanted links between different students.
"""

from note_service.config import Settings
from note_service.db.connection import Neo4jConnection

settings = Settings()
connection = Neo4jConnection(settings)

print("\n" + "=" * 80)
print("STUDENT DATA ISOLATION CHECK")
print("=" * 80 + "\n")

with connection.driver.session() as session:
    # Find topics that link multiple students
    result = session.run("""
        MATCH (s1:Profile)<-[:CREATED_BY]-(ln1:LectureNote)-[:COVERS_TOPIC]->(t:Topic)
        MATCH (s2:Profile)<-[:CREATED_BY]-(ln2:LectureNote)-[:COVERS_TOPIC]->(t)
        WHERE s1.student_id <> s2.student_id
        WITH t,
             collect(DISTINCT s1.student_id) + collect(DISTINCT s2.student_id) as student_ids,
             collect(DISTINCT ln1.title) + collect(DISTINCT ln2.title) as note_titles
        RETURN t.name as topic_name,
               student_ids,
               note_titles
        ORDER BY size(student_ids) DESC
    """)

    cross_student_topics = list(result)

    if cross_student_topics:
        print(f"⚠️  PRIVACY ISSUE: Found {len(cross_student_topics)} topics linking multiple students!\n")
        for record in cross_student_topics[:10]:
            print(f"Topic: {record['topic_name']}")
            print(f"  Links students: {record['student_ids']}")
            print(f"  Through notes: {record['note_titles']}")
            print()
    else:
        print("✅ No cross-student topic links found\n")

print("=" * 80)
print("CHUNK-LEVEL CROSS-STUDENT LINKS")
print("=" * 80 + "\n")

with connection.driver.session() as session:
    # Find topics linking chunks from different students
    result = session.run("""
        MATCH (c1:Chunk)-[:COVERS_TOPIC]->(t:Topic)<-[:COVERS_TOPIC]-(c2:Chunk)
        MATCH (c1)-[:PART_OF]->(ln1:LectureNote)-[:CREATED_BY]->(s1:Profile)
        MATCH (c2)-[:PART_OF]->(ln2:LectureNote)-[:CREATED_BY]->(s2:Profile)
        WHERE s1.student_id <> s2.student_id
        WITH t,
             collect(DISTINCT s1.student_id) as student1,
             collect(DISTINCT s2.student_id) as student2,
             count(*) as link_count
        RETURN t.name as topic_name,
               student1 + student2 as students,
               link_count
        ORDER BY link_count DESC
        LIMIT 10
    """)

    chunk_links = list(result)

    if chunk_links:
        print(f"⚠️  PRIVACY ISSUE: Found {len(chunk_links)} topics linking chunks across students!\n")
        for record in chunk_links:
            print(f"Topic: {record['topic_name']}")
            print(f"  Linking students: {record['students']}")
            print(f"  Number of cross-student chunk links: {record['link_count']}")
            print()
    else:
        print("✅ No cross-student chunk links found\n")

connection.close()

print("\n" + "=" * 80)
print("RECOMMENDATION")
print("=" * 80)
print("""
The Topic node should be student-scoped or course-scoped, not global.

Option 1: Student-scoped Topics
  - Topic ID: TOPIC-{student_id}-{topic_name}
  - Ensures complete isolation between students
  - Topics are private to each student

Option 2: Course-scoped Topics
  - Topic ID: TOPIC-{course_id}-{topic_name}
  - Topics shared within a course context
  - Enables cross-student insights within same course

Option 3: Remove Topics entirely
  - Use tags/embeddings only for retrieval
  - Avoid the privacy complexity
""")
