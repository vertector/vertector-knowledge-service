"""
Test script to verify automatic embedding generation for academic entities.
"""

import logging
from note_service.db.connection import Neo4jConnection
from note_service.config import Settings
from note_service.ingestion.data_loader import DataLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_course_embedding():
    """Test that Course nodes get embeddings automatically."""
    settings = Settings()
    conn = Neo4jConnection(settings=settings)
    loader = DataLoader(connection=conn, settings=settings)

    # Create a test course
    course_data = {
        "course_id": "EMBEDDING-TEST-001",
        "title": "Advanced Machine Learning",
        "code": "CS",
        "number": "229",
        "term": "Spring 2025",
        "credits": 3,
        "description": "Deep dive into neural networks, reinforcement learning, and advanced ML techniques",
        "instructor_name": "Dr. Andrew Ng",
        "instructor_email": "ang@stanford.edu",
        "component_type": ["LEC", "LAB"],
        "prerequisites": ["CS221"],
        "grading_options": ["Letter"],
        "learning_objectives": [
            "Understand deep learning architectures",
            "Implement reinforcement learning algorithms",
            "Apply ML to real-world problems"
        ],
    }

    logger.info("Creating Course with auto_embed=True...")
    created_node = loader.create_node(
        label="Course",
        properties=course_data,
        id_field="course_id",
        auto_embed=True
    )

    # Verify embedding was created
    with conn.session() as session:
        result = session.run("""
            MATCH (c:Course {course_id: $course_id})
            RETURN c.embedding_vector IS NOT NULL as has_embedding,
                   size(c.embedding_vector) as embedding_size
        """, course_id="EMBEDDING-TEST-001")

        record = result.single()
        if record:
            has_embedding = record["has_embedding"]
            embedding_size = record["embedding_size"] if has_embedding else None

            logger.info(f"✓ Course created")
            logger.info(f"  Has embedding: {has_embedding}")
            if has_embedding:
                logger.info(f"  Embedding dimension: {embedding_size}")
                logger.info("✅ AUTOMATIC EMBEDDING GENERATION IS WORKING!")
            else:
                logger.error("❌ EMBEDDING WAS NOT GENERATED!")
        else:
            logger.error("❌ Course node not found!")

    # Clean up
    with conn.session() as session:
        session.run("MATCH (c:Course {course_id: $course_id}) DELETE c",
                   course_id="EMBEDDING-TEST-001")
        logger.info("✓ Test course deleted")

    conn.close()

if __name__ == "__main__":
    test_course_embedding()
