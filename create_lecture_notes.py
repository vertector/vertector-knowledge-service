"""
Create Lecture Notes using GraphRAG Note Service

This script demonstrates creating lecture notes with automatic:
- Summary generation using LLM (Gemini 2.5 Flash Lite)
- Tag/topic extraction using LLM
- 1024-dimension embedding generation
- Chunk creation for paragraph-level retrieval
- Relationship creation to Course nodes
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from note_service.config import Settings
from note_service.db.connection import Neo4jConnection
from note_service.ingestion.data_loader import DataLoader

def create_lecture_notes():
    """Create comprehensive lecture notes for the CS301 course."""

    print("=" * 100)
    print("CREATING LECTURE NOTES WITH GRAPHRAG NOTE SERVICE")
    print("=" * 100)
    print()

    # Initialize connection and data loader
    settings = Settings()
    connection = Neo4jConnection(settings=settings)
    data_loader = DataLoader(connection=connection, settings=settings)

    print(f"✓ Connected to Neo4j at {settings.neo4j.uri}")
    print()

    # Lecture notes to create
    lecture_notes = [
        {
            "title": "Graph Algorithms: BFS and DFS Traversal",
            "content": """
Breadth-First Search (BFS) and Depth-First Search (DFS) are fundamental graph traversal algorithms.

BFS explores the graph level by level, visiting all neighbors of a node before moving to the next level. It uses a queue data structure and is ideal for finding shortest paths in unweighted graphs. Time complexity is O(V + E) where V is vertices and E is edges.

DFS explores as far as possible along each branch before backtracking. It uses a stack or recursion and is useful for topological sorting, cycle detection, and path finding. Time complexity is also O(V + E).

Key differences: BFS uses a queue while DFS uses a stack. BFS finds shortest paths while DFS explores depth. BFS is better for finding nearest solutions while DFS is better for exploring all paths.

Applications include social network analysis and web crawling for BFS, and maze solving and topological sorting for DFS.
            """,
            "course_id": "CS301-Fall2025",
            "student_id": "STU001",
            "date": "2025-12-10",
            "professor": "Prof. Michael Zhang",
            "lecture_number": 1
        },
        {
            "title": "Dynamic Programming: Optimal Substructure and Memoization",
            "content": """
Dynamic Programming (DP) is a powerful algorithmic technique for solving optimization problems by breaking them down into simpler subproblems.

Two key properties must exist for DP: Optimal Substructure means an optimal solution contains optimal solutions to subproblems. Overlapping Subproblems means the same subproblems are solved multiple times during recursion.

DP stores solutions in a table through memoization to avoid redundant calculations. There are two approaches: Top-Down uses recursion with caching, while Bottom-Up uses iteration building from base cases.

Classic DP problems include the Fibonacci sequence where F(n) equals F(n-1) plus F(n-2), the 0/1 Knapsack problem for maximizing value with weight constraints, Longest Common Subsequence for finding the longest subsequence in two strings, and Matrix Chain Multiplication for minimizing scalar multiplications.

Time complexity typically reduces exponential O(2^n) to polynomial O(n²) or O(n*m). Space complexity is O(n) for 1D DP and O(n*m) for 2D DP.

Common mistakes include not identifying the optimal substructure, incorrect base cases, off-by-one errors in array indexing, and not considering all possible transitions.
            """,
            "course_id": "CS301-Fall2025",
            "student_id": "STU001",
            "date": "2025-12-11",
            "professor": "Prof. Michael Zhang",
            "lecture_number": 2
        },
        {
            "title": "Greedy Algorithms: Making Locally Optimal Choices",
            "content": """
Greedy algorithms make locally optimal choices at each step hoping to find a global optimum. Unlike dynamic programming, greedy algorithms never reconsider past choices.

The Greedy Choice Property states that a global optimum can be arrived at by selecting local optima.

Classic greedy algorithms include Activity Selection for selecting maximum non-overlapping activities with O(n log n) time for sorting. Huffman Coding builds optimal prefix-free binary codes for data compression using a priority queue with O(n log n) time.

Dijkstra's Shortest Path finds shortest paths from source to all vertices by greedily selecting the vertex with minimum distance, running in O(E log V) time with a binary heap.

Kruskal's Minimum Spanning Tree sorts edges by weight and adds them if no cycle forms, using Union-Find data structure with O(E log E) time. Prim's MST grows the tree one vertex at a time, always adding the minimum weight edge connecting to the tree in O(E log V) time.

Greedy algorithms fail for some problems like the 0/1 Knapsack problem, shortest paths with negative weights, and the Traveling Salesman Problem.

To prove greedy correctness, show the greedy choice is safe using an exchange argument, prove optimal substructure exists, and show the greedy choice leads to an optimal solution.
            """,
            "course_id": "CS301-Fall2025",
            "student_id": "STU001",
            "date": "2025-12-11",
            "professor": "Prof. Michael Zhang",
            "lecture_number": 3
        }
    ]

    # Create lecture notes
    created_notes = []
    for i, note_data in enumerate(lecture_notes, 1):
        print(f"{i}. Creating Lecture Note: '{note_data['title']}'")
        print("-" * 100)

        try:
            # Create lecture note with automatic:
            # - Embedding generation (1024 dimensions)
            # - Summary generation using LLM
            # - Tag extraction using LLM
            # - Chunk creation for paragraph-level retrieval
            # - Relationship creation to Course
            created_node = data_loader.create_node(
                label="LectureNote",
                properties=note_data,
                id_field="lecture_note_id",
                auto_embed=True,
                create_relationships=True
            )

            print(f"   ✓ Lecture Note ID: {created_node.get('lecture_note_id')}")

            summary = created_node.get('summary', 'N/A')
            if summary and summary != 'N/A':
                print(f"   ✓ Auto-generated summary: {summary[:150]}...")

            tags = created_node.get('tagged_topics', [])
            if tags:
                print(f"   ✓ Auto-generated tags: {', '.join(tags)}")

            embedding = created_node.get('embedding_vector', [])
            if embedding:
                print(f"   ✓ Embedding dimensions: {len(embedding)}")

            print()

            created_notes.append(created_node)

        except Exception as e:
            print(f"   ✗ Failed to create lecture note: {e}")
            import traceback
            traceback.print_exc()
            print()

    # Summary
    print("=" * 100)
    print(f"LECTURE NOTES CREATED: {len(created_notes)}/{len(lecture_notes)}")
    print("=" * 100)
    print()
    print("Features automatically applied:")
    print("  ✓ 1024-dimension embeddings for semantic search")
    print("  ✓ LLM-generated summaries (Gemini 2.5 Flash Lite)")
    print("  ✓ LLM-extracted tags/topics")
    print("  ✓ Chunk creation for paragraph-level retrieval")
    print("  ✓ Course relationships (linked to CS301-Fall2025)")
    print()
    print("Query lecture notes in Neo4j:")
    print('  docker exec neo4j-graphrag cypher-shell -u neo4j -p graphrag_secure_password_2025 \\')
    print('    "MATCH (l:LectureNote) RETURN l.lecture_note_id, l.title, l.summary LIMIT 5;"')
    print()
    print("Check chunks created:")
    print('  docker exec neo4j-graphrag cypher-shell -u neo4j -p graphrag_secure_password_2025 \\')
    print('    "MATCH (l:LectureNote)-[:HAS_CHUNK]->(c:Chunk) RETURN l.title, count(c) as chunk_count;"')
    print()
    print("=" * 100)

    # Cleanup
    connection.close()


if __name__ == "__main__":
    create_lecture_notes()
