"""
Test Natural Language Search with RetrievalService.search() method
"""

import os
from dotenv import load_dotenv
from note_service.config import Settings
from note_service.db.connection import Neo4jConnection
from note_service.retrieval.service import RetrievalService

# Load environment variables
load_dotenv()

def test_natural_language_queries():
    """Test various natural language search queries using the main search endpoint."""

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
    print("NATURAL LANGUAGE SEARCH TEST - Using search() with granularity")
    print("=" * 80 + "\n")

    # Test queries with different granularities
    test_cases = [
        {
            "query": "How do I define functions in Python?",
            "granularity": "chunk",
            "description": "Chunk-level search for Python functions"
        },
        {
            "query": "What are the different data types in Python?",
            "granularity": "document",
            "description": "Document-level search for data types"
        },
        {
            "query": "Explain integration by parts formula",
            "granularity": "chunk",
            "description": "Chunk-level search for calculus concept"
        },
        {
            "query": "lambda expressions and anonymous functions",
            "granularity": "auto",
            "description": "Auto-granularity for specific Python concept"
        },
        {
            "query": "LIATE rule for integration",
            "granularity": "chunk",
            "description": "Chunk-level search for specific math technique"
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"Query {i}: \"{test['query']}\"")
        print(f"Granularity: {test['granularity']}")
        print(f"Description: {test['description']}")
        print('='*80)

        # Perform search using the main search endpoint
        result = retrieval_service.search(
            query_text=test['query'],
            top_k=3,
            granularity=test['granularity'],
            search_type="hybrid"
        )

        print(f"\nFound {result.num_results} results:\n")

        for j, item in enumerate(result.results, 1):
            print(f"  Result {j}:")
            print(f"    Score: {item.get('score', 'N/A')}")

            # Handle different response formats
            if 'content' in item:
                # Chunk-level result
                print(f"    Type: Chunk")
                print(f"    Content: {item['content'][:200]}...")
            elif 'title' in item:
                # Document-level result
                print(f"    Type: Document")
                print(f"    Title: {item['title']}")
                if 'summary' in item:
                    print(f"    Summary: {item.get('summary', 'N/A')[:150]}...")

            print()

    connection.close()
    print("\n" + "=" * 80)
    print("✅ Natural language search test complete!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    test_natural_language_queries()
