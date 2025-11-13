"""
============================================================================
Chunk-Based Retrieval Examples
============================================================================
Demonstrates precise, paragraph-level retrieval using the ChunkGenerator
and enhanced RetrievalService
============================================================================
"""

import logging
import os
from pprint import pprint

from dotenv import load_dotenv

from note_service.config import Settings
from note_service.db.connection import Neo4jConnection
from note_service.ingestion.chunk_generator import ChunkGenerator
from note_service.retrieval.embedder import EmbeddingService
from note_service.retrieval.service import RetrievalService

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Main example demonstrating chunk-based retrieval."""

    settings = Settings()

    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        raise ValueError(
            "GOOGLE_API_KEY environment variable required for LLM query generation"
        )

    logger.info("Connecting to Neo4j...")
    connection = Neo4jConnection(settings)
    driver = connection.driver

    print("\n" + "=" * 80)
    print("Chunk-Based Retrieval Examples")
    print("=" * 80 + "\n")

    # Initialize services
    chunk_generator = ChunkGenerator(driver=driver)
    retrieval_service = RetrievalService(
        driver=driver, settings=settings, google_api_key=google_api_key
    )

    # Example 1: Generate chunks from existing LectureNote
    example_1_generate_chunks(chunk_generator, retrieval_service)

    # Example 2: Chunk-level hybrid search
    example_2_chunk_search(retrieval_service)

    # Example 3: Chunk search with parent context
    example_3_chunk_with_context(retrieval_service)

    # Example 4: Chunk search with surrounding chunks
    example_4_chunk_with_surrounding(retrieval_service)

    # Example 5: Compare document vs chunk retrieval
    example_5_compare_retrieval(retrieval_service)

    connection.close()
    logger.info("Examples completed successfully")


def example_1_generate_chunks(
    chunk_generator: ChunkGenerator, retrieval_service: RetrievalService
):
    """Example 1: Generate chunks from an existing LectureNote."""

    print("\n" + "-" * 80)
    print("Example 1: Generate Chunks from LectureNote")
    print("-" * 80 + "\n")

    # Fetch a sample LectureNote
    query = """
    MATCH (ln:LectureNote)
    WHERE ln.content IS NOT NULL
    RETURN ln.lecture_note_id AS lecture_note_id,
           ln.title AS title,
           ln.content AS content
    LIMIT 1
    """

    with chunk_generator.driver.session() as session:
        result = session.run(query)
        record = result.single()

    if not record:
        print("⚠️  No LectureNotes found in database. Please create some first.")
        return

    lecture_note_id = record["lecture_note_id"]
    title = record["title"]
    content = record["content"]

    print(f"LectureNote: {title}")
    print(f"ID: {lecture_note_id}")
    print(f"Content length: {len(content)} characters\n")

    # Generate chunks
    chunks = chunk_generator.generate_chunks(
        lecture_note_id=lecture_note_id,
        content=content,
        title=title,
    )

    print(f"✅ Generated {len(chunks)} chunks\n")

    # Display first few chunks
    for i, chunk in enumerate(chunks[:3], 1):
        print(f"Chunk {i}:")
        print(f"  ID: {chunk.chunk_id}")
        print(f"  Heading: {chunk.heading or 'N/A'}")
        print(f"  Type: {chunk.chunk_type}")
        print(f"  Tokens: {chunk.token_count}")
        print(f"  Content preview: {chunk.content[:150]}...")
        print()

    # Generate embeddings for chunks
    print("Generating embeddings for chunks...")
    embedding_service = retrieval_service.embedding_service
    chunk_texts = [chunk.content for chunk in chunks]
    embeddings = embedding_service.embed_documents(chunk_texts, prompt_name="document")

    # Create mapping
    embedding_vectors = {
        chunks[i].chunk_id: embeddings[i].tolist() if hasattr(embeddings[i], 'tolist') else embeddings[i]
        for i in range(len(chunks))
    }
    print(f"✅ Generated {len(embedding_vectors)} embeddings\n")

    # Save chunks to Neo4j with embeddings
    print("Saving chunks to Neo4j...")
    saved_count = chunk_generator.save_chunks_to_neo4j(chunks, embedding_vectors)
    print(f"✅ Saved {saved_count} chunks with embeddings\n")


def example_2_chunk_search(service: RetrievalService):
    """Example 2: Basic chunk-level hybrid search."""

    print("\n" + "-" * 80)
    print("Example 2: Chunk-Level Hybrid Search")
    print("-" * 80 + "\n")

    query = "How do I declare a variable in Python?"

    logger.info(f"Query: {query}")

    result = service.search(
        query_text=query,
        granularity="chunk",
        top_k=5,
        search_type="hybrid",
        return_parent_context=False,
        return_surrounding_chunks=False,
    )

    print(f"\nQuery: {query}")
    print(f"Results: {result.num_results} chunks\n")

    for i, item in enumerate(result.results[:3], 1):
        print(f"Chunk {i} (Score: {item.get('score', 'N/A'):.3f}):")
        print(f"  Heading: {item.get('heading', 'N/A')}")
        print(f"  Content: {item.get('content', '')[:200]}...")
        print()


def example_3_chunk_with_context(service: RetrievalService):
    """Example 3: Chunk search with parent document context."""

    print("\n" + "-" * 80)
    print("Example 3: Chunk Search + Parent Context")
    print("-" * 80 + "\n")

    query = "Explain control flow and conditionals"

    logger.info(f"Query: {query}")

    result = service.search(
        query_text=query,
        granularity="chunk",
        top_k=3,
        search_type="hybrid",
        return_parent_context=True,  # ← Include parent info
        return_surrounding_chunks=False,
    )

    print(f"\nQuery: {query}")
    print(f"Results: {result.num_results} chunks\n")

    for i, item in enumerate(result.results, 1):
        print(f"Chunk {i}:")
        print(f"  Content: {item.get('content', '')[:150]}...")
        print(f"  Heading: {item.get('heading', 'N/A')}")
        print(f"\n  Parent Document:")
        print(f"    Title: {item.get('parent_title', 'N/A')}")
        print(f"    Course: {item.get('course_title', 'N/A')}")
        print(f"    Author: {item.get('author', 'N/A')}")
        print(f"    Topics: {item.get('topics', [])}")
        print()


def example_4_chunk_with_surrounding(service: RetrievalService):
    """Example 4: Chunk search with surrounding chunks for context."""

    print("\n" + "-" * 80)
    print("Example 4: Chunk Search + Surrounding Chunks")
    print("-" * 80 + "\n")

    query = "What are loops?"

    logger.info(f"Query: {query}")

    result = service.search(
        query_text=query,
        granularity="chunk",
        top_k=2,
        search_type="hybrid",
        return_parent_context=True,
        return_surrounding_chunks=True,  # ← Include prev/next chunks
    )

    print(f"\nQuery: {query}")
    print(f"Results: {result.num_results} chunks\n")

    for i, item in enumerate(result.results, 1):
        print(f"Chunk {i}:")
        print(f"  Current chunk: {item.get('content', '')[:100]}...")

        prev_chunk = item.get('previous_chunk')
        if prev_chunk:
            print(f"  Previous chunk: {prev_chunk[:80]}...")

        next_chunk = item.get('next_chunk')
        if next_chunk:
            print(f"  Next chunk: {next_chunk[:80]}...")

        print()


def example_5_compare_retrieval(service: RetrievalService):
    """Example 5: Compare document-level vs chunk-level retrieval."""

    print("\n" + "-" * 80)
    print("Example 5: Document vs Chunk Retrieval Comparison")
    print("-" * 80 + "\n")

    query = "Python type conversion"

    # Document-level retrieval
    print("📄 DOCUMENT-LEVEL RETRIEVAL:")
    print("-" * 40)

    doc_result = service.search(
        query_text=query,
        granularity="document",
        top_k=2,
        search_type="hybrid",
        initial_node_type="LectureNote",
    )

    print(f"Results: {doc_result.num_results} full documents")
    for i, item in enumerate(doc_result.results, 1):
        content = str(item.get('content', ''))
        print(f"\nDocument {i}:")
        print(f"  Length: {len(content)} characters")
        print(f"  Preview: {content[:150]}...")

    # Chunk-level retrieval
    print("\n\n📝 CHUNK-LEVEL RETRIEVAL:")
    print("-" * 40)

    chunk_result = service.search(
        query_text=query,
        granularity="chunk",
        top_k=3,
        search_type="hybrid",
        return_parent_context=True,
    )

    print(f"Results: {chunk_result.num_results} precise chunks")
    for i, item in enumerate(chunk_result.results, 1):
        content = item.get('content', '')
        print(f"\nChunk {i}:")
        print(f"  Parent: {item.get('parent_title', 'N/A')}")
        print(f"  Section: {item.get('heading', 'N/A')}")
        print(f"  Length: {len(content)} characters")
        print(f"  Content: {content[:150]}...")

    print("\n\n💡 Key Difference:")
    print("  Document retrieval: Returns entire lecture notes (verbose)")
    print("  Chunk retrieval: Returns specific paragraphs (precise)")


if __name__ == "__main__":
    main()
