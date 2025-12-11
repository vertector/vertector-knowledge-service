"""
============================================================================
Test Chunk-Aware Document Ranking
============================================================================
Tests the improved precision of document-level search with chunk-aware ranking
============================================================================
"""

import os
from dotenv import load_dotenv
from note_service.config import Settings
from note_service.db.connection import Neo4jConnection
from note_service.retrieval.service import RetrievalService

# Load environment variables
load_dotenv()


def test_chunk_aware_ranking():
    """Test document-level search with and without chunk-aware ranking."""

    settings = Settings()
    connection = Neo4jConnection(settings)

    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        raise ValueError("GOOGLE_API_KEY environment variable required")

    retrieval_service = RetrievalService(
        driver=connection.driver,
        settings=settings,
        google_api_key=google_api_key
    )

    print("\n" + "=" * 80)
    print("TESTING CHUNK-AWARE DOCUMENT RANKING")
    print("=" * 80 + "\n")

    # Test query that previously returned irrelevant results
    query = "What are the different data types in Python?"

    print(f"Query: \"{query}\"\n")
    print("=" * 80)
    print("TEST 1: Document search WITHOUT chunk-aware ranking")
    print("=" * 80)

    result_without_ranking = retrieval_service.search(
        query_text=query,
        top_k=3,
        granularity="document",
        search_type="hybrid",
        use_chunk_ranking=False  # Disable chunk ranking
    )

    print(f"\nFound {result_without_ranking.num_results} results:\n")
    for i, doc in enumerate(result_without_ranking.results, 1):
        print(f"  Result {i}:")
        print(f"    Title: {doc.get('lecture_note_title', 'N/A')}")
        print(f"    Score: {doc.get('score', 'N/A'):.4f}" if isinstance(doc.get('score'), float) else f"    Score: {doc.get('score', 'N/A')}")
        print()

    print("=" * 80)
    print("TEST 2: Document search WITH chunk-aware ranking (default)")
    print("=" * 80)

    result_with_ranking = retrieval_service.search(
        query_text=query,
        top_k=3,
        granularity="document",
        search_type="hybrid",
        use_chunk_ranking=True  # Enable chunk ranking (default)
    )

    print(f"\nFound {result_with_ranking.num_results} results:\n")
    for i, doc in enumerate(result_with_ranking.results, 1):
        print(f"  Result {i}:")
        print(f"    Title: {doc.get('lecture_note_title', 'N/A')}")

        # Show original score vs combined score
        if '_original_score' in doc:
            print(f"    Original Score: {doc['_original_score']:.4f}")
        if '_combined_score' in doc:
            print(f"    Combined Score (chunk-aware): {doc['_combined_score']:.4f}")
        else:
            print(f"    Score: {doc.get('score', 'N/A'):.4f}" if isinstance(doc.get('score'), float) else f"    Score: {doc.get('score', 'N/A')}")

        # Show chunk metrics if available
        if '_chunk_metrics' in doc and doc['_chunk_metrics']:
            metrics = doc['_chunk_metrics']
            print(f"    Chunk Metrics:")
            print(f"      - Max chunk score: {metrics['max_chunk_score']:.4f}")
            print(f"      - Avg top-3 score: {metrics['avg_top3_score']:.4f}")
            print(f"      - Relevant chunks: {metrics['num_relevant_chunks']}")
            print(f"      - Top chunks:")
            for j, chunk in enumerate(metrics['top_chunks'], 1):
                print(f"        {j}. {chunk.get('heading', 'No heading')} (score: {chunk['score']:.4f})")
                print(f"           {chunk['content'][:80]}...")
        print()

    print("=" * 80)
    print("COMPARISON")
    print("=" * 80)

    print("\nWithout chunk ranking:")
    for i, doc in enumerate(result_without_ranking.results, 1):
        print(f"  {i}. {doc.get('lecture_note_title', 'N/A')}")

    print("\nWith chunk ranking (improved precision):")
    for i, doc in enumerate(result_with_ranking.results, 1):
        print(f"  {i}. {doc.get('lecture_note_title', 'N/A')}")

    # Check if ranking improved (Python note should be first)
    if result_with_ranking.results:
        top_result_title = result_with_ranking.results[0].get('lecture_note_title', '')
        if 'Python' in top_result_title and 'Data Types' in top_result_title:
            print("\n✅ SUCCESS: Chunk-aware ranking correctly prioritized Python data types note!")
        else:
            print(f"\n⚠️  WARNING: Top result is '{top_result_title}' - expected Python data types note")

    connection.close()
    print("\n" + "=" * 80)
    print("✅ Test complete!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    test_chunk_aware_ranking()
