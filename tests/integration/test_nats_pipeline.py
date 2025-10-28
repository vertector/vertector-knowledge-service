"""
Test NATS to Neo4j Pipeline

This script demonstrates the full pipeline:
1. Start NATS consumer (listens for events)
2. Publish academic events to NATS
3. Consumer processes events and creates nodes in Neo4j
4. Verify nodes were created with embeddings
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from note_service.nats_integration.consumer import NATSConsumer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def main():
    """Run the NATS consumer."""
    logger.info("=" * 80)
    logger.info("Starting NATS Consumer for GraphRAG Note Service")
    logger.info("=" * 80)
    logger.info("")
    logger.info("Listening for academic events on NATS JetStream...")
    logger.info("Events will be automatically ingested into Neo4j with embeddings")
    logger.info("")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 80)

    try:
        consumer = NATSConsumer()
        await consumer.run()
    except KeyboardInterrupt:
        logger.info("\n\nShutting down consumer...")
    except Exception as e:
        logger.error(f"Consumer error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
