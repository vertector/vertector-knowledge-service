"""
Test NATS pipeline with automatic embedding generation - with automatic exit after processing.
"""

import asyncio
import logging
from note_service.nats_integration.consumer import NATSConsumer
from note_service.db.connection import Neo4jConnection
from note_service.config import Settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def main():
    """Run consumer, process messages, verify embeddings, then exit."""

    logger.info("=" * 80)
    logger.info("Testing NATS → Neo4j Pipeline with Automatic Embedding Generation")
    logger.info("=" * 80)

    consumer = NATSConsumer()

    try:
        await consumer.connect()

        # Manually fetch and process a few messages
        consumer_instance = await consumer.js.pull_subscribe(
            subject="academic.course.*",
            durable="graphrag-note-service-consumer-v2"
        )

        logger.info("Fetching messages...")
        messages = await consumer_instance.fetch(batch=10, timeout=5)

        logger.info(f"Fetched {len(messages)} messages")

        for i, msg in enumerate(messages, 1):
            import json
            event_data = json.loads(msg.data.decode())
            logger.info(f"\nProcessing message {i}/{len(messages)}")
            logger.info(f"  Event type: {event_data.get('event_type')}")

            await consumer.process_event(event_data)
            await msg.ack()
            logger.info(f"  ✓ Message {i} processed and acknowledged")

        await consumer.disconnect()

        # Verify results
        logger.info("\n" + "=" * 80)
        logger.info("Verifying Results in Neo4j")
        logger.info("=" * 80)

        conn = Neo4jConnection(settings=Settings())
        with conn.session() as session:
            result = session.run('''
                MATCH (c:Course)
                RETURN c.course_id as id,
                       c.title as title,
                       c.embedding_vector IS NOT NULL as has_embedding,
                       size(c.embedding_vector) as embedding_size
                ORDER BY c.created_at
            ''')

            records = list(result)
            if records:
                for r in records:
                    logger.info(f"\n✓ Course: {r['title']}")
                    logger.info(f"  ID: {r['id']}")
                    if r['has_embedding']:
                        logger.info(f"  Embedding: YES ({r['embedding_size']} dimensions)")
                        logger.info(f"  ✅ SUCCESS - Automatic embedding generation WORKING!")
                    else:
                        logger.info(f"  Embedding: NO")
                        logger.info(f"  ❌ FAILED - No embedding generated")
            else:
                logger.warning("No Course nodes found in database")

        conn.close()
        logger.info("\n" + "=" * 80)
        logger.info("Test Complete")
        logger.info("=" * 80)

    except asyncio.TimeoutError:
        logger.info("No messages available (timeout)")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(main())
