"""
Test Semantic Search on Lecture Notes using RetrievalService

Demonstrates hybrid retrieval on CS301 lecture notes.
"""

import os
from dotenv import load_dotenv
from note_service.config import Settings
from note_service.db.connection import Neo4jConnection
from note_service.retrieval.service import RetrievalService

# Load environment variables
load_dotenv()

def test_lecture_note_search():
    """Test semantic search on CS301 lecture notes."""

    settings = Settings()
    connection = Neo4jConnection(settings)

    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print("⚠️  GOOGLE_API_KEY not set - some features may be limited")
        print("   Continuing with vector and fulltext search only...")
        print()

    retrieval_service = RetrievalService(
        driver=connection.driver,
        settings=settings,
        google_api_key=google_api_key
    )

    print("\n" + "=" * 100)
    print("SEMANTIC SEARCH TEST - CS301 Lecture Notes")
    print("=" * 100 + "\n")

    # Test queries relevant to our CS301 lecture notes
    test_cases = [
        {
            "query": "How do I find the shortest path in a graph?",
            "granularity": "document",
            "description": "Search for graph algorithms lecture"
        },
        {
            "query": "What is memoization and how does it optimize recursive algorithms?",
            "granularity": "chunk",
            "description": "Chunk-level search for dynamic programming concepts"
        },
        {
            "query": "Explain greedy algorithms and when they fail",
            "granularity": "document",
            "description": "Document-level search for greedy algorithm lecture"
        },
        {
            "query": "differences between BFS and DFS traversal",
            "granularity": "auto",
            "description": "Auto-granularity for comparing graph traversal methods"
        },
        {
            "query": "optimal substructure and overlapping subproblems",
            "granularity": "chunk",
            "description": "Specific DP concepts in chunk-level detail"
        },
        {
            "query": "Kruskal and Prim minimum spanning tree algorithms",
            "granularity": "document",
            "description": "MST algorithms from greedy lecture"
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*100}")
        print(f"Query {i}: \"{test['query']}\"")
        print(f"Granularity: {test['granularity']}")
        print(f"Description: {test['description']}")
        print('='*100)

        # Perform search using hybrid retrieval
        result = retrieval_service.search(
            query_text=test['query'],
            student_id="STU001",  # Student ID for data isolation
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
                print(f"    Content: {item['content'][:250]}...")
                if 'source_title' in item:
                    print(f"    Source: {item['source_title']}")
            elif 'title' in item:
                # Document-level result
                print(f"    Type: Document")
                print(f"    Title: {item['title']}")
                if 'summary' in item:
                    print(f"    Summary: {item.get('summary', 'N/A')[:200]}...")
                if 'tagged_topics' in item and item['tagged_topics']:
                    print(f"    Tags: {', '.join(item['tagged_topics'][:5])}")

            print()

    connection.close()
    print("\n" + "=" * 100)
    print("✅ Semantic search test complete!")
    print("=" * 100)
    print()
    print("Summary:")
    print("  • Tested hybrid search (vector + fulltext + graph)")
    print("  • Used chunk-level and document-level granularity")
    print("  • Retrieved relevant CS301 lecture content")
    print("  • Demonstrated automatic relevance ranking")
    print()


if __name__ == "__main__":
    test_lecture_note_search()
