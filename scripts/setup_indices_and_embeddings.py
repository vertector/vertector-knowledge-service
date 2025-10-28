"""
============================================================================
Setup Indices and Generate Embeddings
============================================================================
Ensures all required indices exist and generates embeddings for existing data
============================================================================
"""

import logging
from dotenv import load_dotenv

from note_service.config import Settings
from note_service.db.connection import Neo4jConnection
from note_service.ingestion.data_loader import DataLoader

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Setup indices and generate embeddings for existing data."""
    logger.info("\n" + "=" * 80)
    logger.info("Academic GraphRAG System - Setup Indices & Embeddings")
    logger.info("=" * 80 + "\n")

    settings = Settings()

    logger.info("Connecting to Neo4j...")
    connection = Neo4jConnection(settings)

    try:
        logger.info("Initializing data loader...")
        loader = DataLoader(connection, settings)

        # Step 1: Ensure all indices exist
        logger.info("\n" + "=" * 80)
        logger.info("Step 1: Ensuring Indices Exist")
        logger.info("=" * 80)
        loader.ensure_indices_exist()

        # Step 2: Generate embeddings for existing nodes
        logger.info("\n" + "=" * 80)
        logger.info("Step 2: Generating Embeddings for Existing Nodes")
        logger.info("=" * 80 + "\n")
        loader.generate_embeddings_for_existing_nodes()

        logger.info("=" * 80)
        logger.info("✓ Setup completed successfully!")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"Error during setup: {e}")
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    main()
