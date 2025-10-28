"""
============================================================================
Retrieval Service Usage Examples
============================================================================
Demonstrates how to use the dynamic retrieval service
============================================================================
"""

import logging
import os
from pprint import pprint

from dotenv import load_dotenv
from neo4j import GraphDatabase

from note_service.config import Settings
from note_service.db.connection import Neo4jConnection
from note_service.retrieval.service import RetrievalService

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Main example demonstrating retrieval service usage."""

    settings = Settings()

    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        raise ValueError(
            "GOOGLE_API_KEY environment variable required for LLM query generation"
        )

    logger.info("Connecting to Neo4j...")
    connection = Neo4jConnection(settings)

    driver = connection.driver

    logger.info("Initializing RetrievalService...")
    retrieval_service = RetrievalService(
        driver=driver, settings=settings, google_api_key=google_api_key
    )

    print("\n" + "=" * 80)
    print("Academic Note-Taking System - Retrieval Service Examples")
    print("=" * 80 + "\n")

    example_1_hybrid_search(retrieval_service)
    example_2_standalone_search(retrieval_service)
    example_3_vector_only_search(retrieval_service)
    example_4_schema_inspection(retrieval_service)

    connection.close()
    logger.info("Examples completed successfully")


def example_1_hybrid_search(service: RetrievalService):
    """Example 1: Hybrid search (vector + fulltext) with dynamic graph traversal."""

    print("\n" + "-" * 80)
    print("Example 1: Hybrid Search with Dynamic Traversal")
    print("-" * 80 + "\n")

    query = "Explain convolutional neural networks and pooling"

    logger.info(f"Query: {query}")

    result = service.search(
        query_text=query,
        top_k=5,
        search_type="hybrid",
        initial_node_type="Note",
    )

    print(f"\nGenerated Retrieval Query:\n{'-' * 40}")
    print(result.query)

    print(f"\n\nQuery Generation Info:")
    if result.query_generation:
        print(f"  Valid: {result.query_generation.is_valid}")
        print(f"  Attempts: {result.query_generation.attempts}")
        if result.query_generation.error_message:
            print(f"  Error: {result.query_generation.error_message}")

    print(f"\n\nResults: {result.num_results} items\n{'-' * 40}")
    for i, item in enumerate(result.results[:3], 1):
        print(f"\nResult {i}:")
        pprint(item, depth=2)


def example_2_standalone_search(service: RetrievalService):
    """Example 2: Standalone query generation without hybrid search."""

    print("\n\n" + "-" * 80)
    print("Example 2: Standalone Query Generation")
    print("-" * 80 + "\n")

    query = "Show me all courses and their assignments"

    logger.info(f"Query: {query}")

    result = service.search(query_text=query, search_type="standalone")

    print(f"\nGenerated Query:\n{'-' * 40}")
    print(result.query)

    print(f"\n\nResults: {result.num_results} items\n{'-' * 40}")
    for i, item in enumerate(result.results, 1):
        print(f"\nResult {i}:")
        pprint(item, depth=2)


def example_3_vector_only_search(service: RetrievalService):
    """Example 3: Vector-only semantic search."""

    print("\n\n" + "-" * 80)
    print("Example 3: Vector-Only Semantic Search")
    print("-" * 80 + "\n")

    query = "deep learning architectures for computer vision"

    logger.info(f"Query: {query}")

    result = service.search(
        query_text=query, top_k=3, search_type="vector", initial_node_type="Topic"
    )

    print(f"\nGenerated Retrieval Query:\n{'-' * 40}")
    print(result.query)

    print(f"\n\nResults: {result.num_results} items\n{'-' * 40}")
    for i, item in enumerate(result.results, 1):
        print(f"\nResult {i}:")
        pprint(item, depth=2)


def example_4_schema_inspection(service: RetrievalService):
    """Example 4: Inspect graph schema."""

    print("\n\n" + "-" * 80)
    print("Example 4: Graph Schema Inspection")
    print("-" * 80 + "\n")

    schema_summary = service.get_schema_summary()

    print("Current Graph Schema:")
    print("-" * 40)
    print(schema_summary)


if __name__ == "__main__":
    main()
