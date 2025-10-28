"""
Direct test of NATSDataAdapter to verify automatic embedding generation.
"""

import asyncio
import logging
from datetime import datetime
from note_service.nats_integration.data_adapter import NATSDataAdapter
from note_service.db.connection import Neo4jConnection
from note_service.config import Settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_adapter():
    """Test that data adapter creates nodes with embeddings."""

    settings = Settings()
    conn = Neo4jConnection(settings=settings)
    adapter = NATSDataAdapter(connection=conn, settings=settings)

    # Create a test course
    course_data = {
        "course_id": "ADAPTER-TEST-001",
        "title": "Advanced Algorithms",
        "code": "CS",
        "number": "161",
        "term": "Spring 2025",
        "credits": 4,
        "description": "Design and analysis of algorithms, including greedy algorithms, divide and conquer, dynamic programming, and graph algorithms",
        "instructor_name": "Dr. Tim Roughgarden",
        "instructor_email": "tim@stanford.edu",
        "component_type": ["LEC"],
        "prerequisites": ["CS106B"],
        "grading_options": ["Letter"],
        "learning_objectives": [
            "Master algorithm design paradigms",
            "Analyze algorithm complexity",
            "Implement efficient solutions"
        ],
    }

    logger.info("Creating Course via NATSDataAdapter with auto_embed=True...")
    await adapter.load_entity_with_embeddings("Course", course_data)

    # Verify
    with conn.session() as session:
        result = session.run("""
            MATCH (c:Course {course_id: $course_id})
            RETURN c.title as title,
                   c.embedding_vector IS NOT NULL as has_embedding,
                   size(c.embedding_vector) as embedding_size
        """, course_id="ADAPTER-TEST-001")

        record = result.single()

        if record:
            print()
            print("=" * 80)
            print("DIRECT DATA ADAPTER TEST RESULTS")
            print("=" * 80)
            print(f"Course: {record['title']}")
            print(f"Has Embedding: {record['has_embedding']}")
            if record['has_embedding']:
                print(f"Embedding Dimensions: {record['embedding_size']}")
                print()
                print("✅ SUCCESS! Data Adapter is generating embeddings automatically!")
                print("=" * 80)
            else:
                print()
                print("❌ FAILED! No embedding was generated")
                print("=" * 80)

    # Cleanup
    with conn.session() as session:
        session.run("MATCH (c:Course {course_id: $course_id}) DELETE c",
                   course_id="ADAPTER-TEST-001")
        logger.info("✓ Test course deleted")

    conn.close()

if __name__ == "__main__":
    asyncio.run(test_adapter())
