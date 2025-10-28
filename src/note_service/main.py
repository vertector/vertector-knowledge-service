"""
GraphRAG Note Service - Main Application Entry Point

Standalone microservice that:
1. Connects to Neo4j graph database
2. Automatically consumes academic events from NATS JetStream
3. Generates vector embeddings for semantic search
4. Provides hybrid retrieval (vector + fulltext + graph)
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

from note_service.config import Settings
from note_service.db.connection import Neo4jConnection
from note_service.nats_integration.consumer import NATSConsumer
from note_service.ingestion.data_loader import DataLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('note_service.log')
    ]
)

logger = logging.getLogger(__name__)


class NoteServiceApplication:
    """Main application orchestrator for the GraphRAG Note Service."""

    def __init__(self):
        """Initialize the note service application."""
        self.settings = Settings()
        self.neo4j_connection = None
        self.nats_consumer = None
        self.running = False

    async def startup(self):
        """Initialize all service components."""
        logger.info("=" * 80)
        logger.info("GraphRAG Note Service - Starting Up")
        logger.info("=" * 80)

        # 1. Connect to Neo4j
        logger.info("Connecting to Neo4j...")
        self.neo4j_connection = Neo4jConnection(settings=self.settings)
        logger.info(f"✓ Connected to Neo4j at {self.settings.neo4j.uri}")

        # 2. Ensure database schema (indices)
        logger.info("Ensuring database indices...")
        data_loader = DataLoader(
            connection=self.neo4j_connection,
            settings=self.settings
        )
        data_loader.ensure_indices_exist()
        logger.info("✓ Database indices verified")

        # 3. Initialize NATS consumer
        logger.info("Initializing NATS consumer...")
        self.nats_consumer = NATSConsumer()
        logger.info("✓ NATS consumer initialized")

        logger.info("=" * 80)
        logger.info("GraphRAG Note Service - Ready")
        logger.info("=" * 80)
        logger.info("")
        logger.info("Services:")
        logger.info(f"  • Neo4j:     {self.settings.neo4j.uri}")
        logger.info(f"  • NATS:      {', '.join(self.nats_consumer.config.servers)}")
        logger.info(f"  • Stream:    {self.nats_consumer.config.stream_name}")
        logger.info(f"  • Consumer:  {self.nats_consumer.config.durable_name}")
        logger.info("")
        logger.info("Automatic Features:")
        logger.info("  ✓ Embedding generation (1024 dimensions)")
        logger.info("  ✓ Vector indexing")
        logger.info("  ✓ Fulltext indexing")
        logger.info("  ✓ Idempotent event processing")
        logger.info("")
        logger.info("=" * 80)

    async def run(self):
        """Run the note service (NATS consumer)."""
        self.running = True

        try:
            # Start up services
            await self.startup()

            # Run NATS consumer (this blocks)
            logger.info("Starting NATS event consumption...")
            logger.info("Press Ctrl+C to stop")
            logger.info("=" * 80)
            logger.info("")

            await self.nats_consumer.run()

        except KeyboardInterrupt:
            logger.info("\n\nReceived shutdown signal...")
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
            raise
        finally:
            await self.shutdown()

    async def shutdown(self):
        """Gracefully shutdown all service components."""
        logger.info("=" * 80)
        logger.info("GraphRAG Note Service - Shutting Down")
        logger.info("=" * 80)

        if self.nats_consumer:
            logger.info("Disconnecting from NATS...")
            try:
                await self.nats_consumer.disconnect()
                logger.info("✓ NATS disconnected")
            except Exception as e:
                logger.warning(f"Error disconnecting NATS: {e}")

        if self.neo4j_connection:
            logger.info("Closing Neo4j connection...")
            try:
                self.neo4j_connection.close()
                logger.info("✓ Neo4j connection closed")
            except Exception as e:
                logger.warning(f"Error closing Neo4j: {e}")

        logger.info("=" * 80)
        logger.info("GraphRAG Note Service - Stopped")
        logger.info("=" * 80)

    def handle_signal(self, sig, frame):
        """Handle shutdown signals."""
        logger.info(f"\nReceived signal {sig}")
        self.running = False
        sys.exit(0)


async def main():
    """Main entry point."""
    app = NoteServiceApplication()

    # Register signal handlers
    signal.signal(signal.SIGINT, app.handle_signal)
    signal.signal(signal.SIGTERM, app.handle_signal)

    # Run the application
    await app.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nShutdown complete")
    except Exception as e:
        logger.error(f"Application failed: {e}", exc_info=True)
        sys.exit(1)
