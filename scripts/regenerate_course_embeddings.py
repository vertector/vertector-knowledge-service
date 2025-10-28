"""
Regenerate embeddings for existing Course nodes without embeddings.
"""

import logging
from note_service.db.connection import Neo4jConnection
from note_service.config import Settings
from note_service.ingestion.data_loader import DataLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    settings = Settings()
    conn = Neo4jConnection(settings=settings)
    loader = DataLoader(connection=conn, settings=settings)

    logger.info("Regenerating embeddings for existing Course nodes...")
    loader.generate_embeddings_for_existing_nodes(label="Course")

    # Verify
    with conn.session() as session:
        result = session.run("""
            MATCH (c:Course)
            RETURN c.course_id as id,
                   c.title as title,
                   c.embedding_vector IS NOT NULL as has_embedding,
                   size(c.embedding_vector) as embedding_size
            ORDER BY c.course_id
        """)

        logger.info("\nCourse nodes after regeneration:")
        for record in result:
            logger.info(f"  {record['id']}: {record['title']}")
            logger.info(f"    Has embedding: {record['has_embedding']}")
            if record['has_embedding']:
                logger.info(f"    Embedding size: {record['embedding_size']}")

    conn.close()

if __name__ == "__main__":
    main()
