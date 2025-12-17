"""
MVP Demo: Create Lecture Notes for Investor/School Owner Presentation

This script creates comprehensive lecture notes for all courses with automatic:
- Summary generation using LLM (Gemini 2.5 Flash Lite)
- Tag/topic extraction using LLM
- 1024-dimension embedding generation
- Chunk creation for paragraph-level retrieval
- Relationship creation to Course nodes

All lecture notes will be stored in Neo4j and demonstrate semantic search capabilities.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from note_service.config import Settings
from note_service.db.connection import Neo4jConnection
from note_service.ingestion.data_loader import DataLoader
from note_service.ingestion.id_generator import IDGenerator


# Course-specific lecture notes
# Students provide course_code (e.g., "CS301"), NOT course_id
# The system auto-generates course_id based on current term
LECTURE_NOTES = [
    # CS301 - Advanced Algorithms
    {
        "course_code": "CS301",  # What student provides (code + number)
        "title": "Graph Algorithms: BFS and DFS Traversal",
        "content": """
Breadth-First Search (BFS) and Depth-First Search (DFS) are fundamental graph traversal algorithms essential for solving many graph-related problems.

BFS explores the graph level by level, visiting all neighbors of a node before moving to the next level. It uses a queue data structure and is ideal for finding shortest paths in unweighted graphs. The algorithm starts at the source node, marks it as visited, and enqueues it. Then it dequeues a node, processes it, and enqueues all unvisited neighbors. Time complexity is O(V + E) where V is vertices and E is edges. Space complexity is O(V) for the queue and visited set.

DFS explores as far as possible along each branch before backtracking. It uses a stack or recursion and is useful for topological sorting, cycle detection, and path finding. The algorithm marks the current node as visited, then recursively visits unvisited neighbors. Time complexity is also O(V + E). Space complexity is O(V) for the recursion stack.

Key differences: BFS uses a queue while DFS uses a stack. BFS finds shortest paths while DFS explores depth. BFS is better for finding nearest solutions while DFS is better for exploring all paths.

Applications include social network analysis and web crawling for BFS, and maze solving and topological sorting for DFS. Understanding when to use each algorithm is crucial for efficient problem-solving.
        """,
        "date": "2025-12-10",
        "professor": "Prof. Michael Zhang"
    },
    {
        "course_code": "CS301",
        "title": "Dynamic Programming: Optimal Substructure and Memoization",
        "content": """
Dynamic Programming (DP) is a powerful algorithmic technique for solving optimization problems by breaking them down into simpler subproblems.

Two key properties must exist for DP: Optimal Substructure means an optimal solution contains optimal solutions to subproblems. Overlapping Subproblems means the same subproblems are solved multiple times during recursion.

DP stores solutions in a table through memoization to avoid redundant calculations. There are two approaches: Top-Down uses recursion with caching, while Bottom-Up uses iteration building from base cases.

Classic DP problems include the Fibonacci sequence where F(n) equals F(n-1) plus F(n-2), the 0/1 Knapsack problem for maximizing value with weight constraints, Longest Common Subsequence for finding the longest subsequence in two strings, and Matrix Chain Multiplication for minimizing scalar multiplications.

Time complexity typically reduces exponential O(2^n) to polynomial O(n²) or O(n*m). Space complexity is O(n) for 1D DP and O(n*m) for 2D DP.

Common mistakes include not identifying the optimal substructure, incorrect base cases, off-by-one errors in array indexing, and not considering all possible transitions. Mastering DP requires practice and pattern recognition.
        """,
        "date": "2025-12-11",
        "professor": "Prof. Michael Zhang"
    },
    {
        "course_code": "CS301",
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
        "date": "2025-12-12",
        "professor": "Prof. Michael Zhang"
    },

    # BUS202 - Financial Accounting
    {
        "course_code": "BUS202",
        "title": "Introduction to Double-Entry Accounting",
        "content": """
Double-entry accounting is the foundation of modern financial accounting. Every transaction affects at least two accounts, maintaining the accounting equation: Assets = Liabilities + Equity.

The five account types are Assets (resources owned), Liabilities (obligations owed), Equity (owner's residual interest), Revenue (income earned), and Expenses (costs incurred).

Debits and credits are the recording mechanism. For assets and expenses, debits increase and credits decrease. For liabilities, equity, and revenue, credits increase and debits decrease.

A journal entry records each transaction with debits on the left and credits on the right. The general ledger contains all accounts with their running balances. The trial balance verifies that total debits equal total credits.

Common transactions include purchasing inventory (debit Inventory, credit Cash or Accounts Payable), recording sales (debit Cash or Accounts Receivable, credit Revenue), and paying salaries (debit Salaries Expense, credit Cash).

Understanding T-accounts helps visualize debits and credits. Each account is drawn as a T, with debits on the left side and credits on the right side.
        """,
        "date": "2025-12-10",
        "professor": "Prof. Sarah Williams"
    },

    # ME401 - Thermodynamics
    {
        "course_code": "ME401",
        "title": "First Law of Thermodynamics and Energy Conservation",
        "content": """
The First Law of Thermodynamics states that energy cannot be created or destroyed, only transformed from one form to another. This is the principle of energy conservation.

For a closed system, the change in internal energy equals the heat added to the system minus the work done by the system: ΔU = Q - W.

Heat transfer occurs through three mechanisms: conduction (through direct contact), convection (through fluid motion), and radiation (through electromagnetic waves).

Work in thermodynamics can be boundary work (moving a piston), shaft work (rotating machinery), or flow work (pushing fluid through a system).

Specific heat capacity determines how much energy is needed to raise the temperature of a substance. For gases, we distinguish between constant pressure (Cp) and constant volume (Cv) specific heats.

Applications include analyzing heat engines, refrigeration cycles, and power generation systems. Understanding energy flow is crucial for designing efficient thermal systems.
        """,
        "date": "2025-12-10",
        "professor": "Prof. David Kim"
    },

    # BIO101 - General Biology
    {
        "course_code": "BIO101",
        "title": "Cell Structure and Function",
        "content": """
The cell is the basic unit of life. All living organisms are composed of one or more cells. Cells can be prokaryotic (no nucleus) or eukaryotic (with nucleus).

Prokaryotic cells include bacteria and archaea. They have a cell membrane, cytoplasm, ribosomes, and genetic material (DNA) in a nucleoid region. They lack membrane-bound organelles.

Eukaryotic cells include animal, plant, and fungal cells. They have a nucleus containing DNA, surrounded by a nuclear envelope. The cytoplasm contains organelles including mitochondria (energy production), endoplasmic reticulum (protein and lipid synthesis), Golgi apparatus (protein modification and packaging), and lysosomes (digestion).

Plant cells have additional structures: cell wall (structural support), chloroplasts (photosynthesis), and a large central vacuole (storage and turgor pressure).

The cell membrane is a phospholipid bilayer with embedded proteins. It controls what enters and exits the cell through passive transport (diffusion, osmosis) and active transport (requires energy).

Cellular respiration occurs in mitochondria, converting glucose and oxygen into ATP, carbon dioxide, and water. Photosynthesis occurs in chloroplasts, converting light energy, carbon dioxide, and water into glucose and oxygen.
        """,
        "date": "2025-12-10",
        "professor": "Prof. Emily Thompson"
    },

    # PSY301 - Cognitive Psychology
    {
        "course_code": "PSY301",
        "title": "Memory Systems and Processes",
        "content": """
Human memory is divided into three main systems: sensory memory, short-term memory, and long-term memory.

Sensory memory holds information from our senses for a very brief period (less than a second for visual, a few seconds for auditory). It acts as a buffer for incoming sensory information.

Short-term memory (also called working memory) holds a limited amount of information (7±2 items) for a short duration (15-30 seconds without rehearsal). The phonological loop processes verbal information, the visuospatial sketchpad processes visual information, and the central executive coordinates these systems.

Long-term memory has theoretically unlimited capacity and duration. It's divided into explicit memory (conscious recall) and implicit memory (unconscious recall).

Explicit memory includes episodic memory (personal experiences) and semantic memory (facts and general knowledge). Implicit memory includes procedural memory (skills and habits) and priming (unconscious influence of prior exposure).

Encoding is the process of getting information into memory through attention and elaboration. Storage maintains information over time. Retrieval accesses stored information through recall (generating information) or recognition (identifying previously learned information).

Forgetting occurs due to decay (fading over time), interference (other memories disrupting retrieval), and retrieval failure (information is stored but inaccessible).
        """,
        "date": "2025-12-10",
        "professor": "Prof. Lisa Anderson"
    },

    # EE250 - Circuit Analysis
    {
        "course_code": "EE250",
        "title": "Ohm's Law and Kirchhoff's Laws",
        "content": """
Ohm's Law states that voltage (V) equals current (I) times resistance (R): V = IR. This fundamental relationship governs the behavior of resistive circuits.

Kirchhoff's Current Law (KCL) states that the sum of currents entering a node equals the sum of currents leaving that node. This follows from charge conservation.

Kirchhoff's Voltage Law (KVL) states that the sum of voltages around any closed loop equals zero. This follows from energy conservation.

Series circuits have components connected end-to-end. Current is the same through all components. Total resistance equals the sum of individual resistances. Voltage divides among components proportionally to their resistance.

Parallel circuits have components connected across the same two nodes. Voltage is the same across all components. The reciprocal of total resistance equals the sum of reciprocals of individual resistances. Current divides among components inversely proportional to their resistance.

Common circuit analysis techniques include nodal analysis (applying KCL at nodes), mesh analysis (applying KVL to loops), and Thevenin/Norton equivalent circuits for simplification.
        """,
        "date": "2025-12-10",
        "professor": "Prof. Jennifer Lee"
    },

    # DS501 - Machine Learning
    {
        "course_code": "DS501",
        "title": "Supervised Learning: Linear Regression and Classification",
        "content": """
Supervised learning trains models on labeled data to predict outputs for new inputs. The two main types are regression (predicting continuous values) and classification (predicting discrete categories).

Linear regression models the relationship between input features and a continuous output. The model learns weights that minimize the mean squared error between predictions and actual values. Gradient descent is commonly used for optimization.

Multiple linear regression extends this to multiple input features. The model becomes y = w₀ + w₁x₁ + w₂x₂ + ... + wₙxₙ where wᵢ are weights and xᵢ are features.

Logistic regression is used for binary classification despite its name. It applies a sigmoid function to linear combination of features, outputting probabilities between 0 and 1. The decision boundary is where the probability equals 0.5.

Model evaluation for regression uses metrics like Mean Squared Error (MSE), Root Mean Squared Error (RMSE), and R² score. Classification uses accuracy, precision, recall, F1-score, and ROC-AUC.

Overfitting occurs when the model learns noise in the training data and performs poorly on new data. Regularization techniques like L1 (Lasso) and L2 (Ridge) add penalty terms to prevent overfitting.

Cross-validation splits data into training and validation sets multiple times to get robust performance estimates. K-fold cross-validation is commonly used.
        """,
        "date": "2025-12-10",
        "professor": "Prof. Alan Turing"
    },

    # CHEM302 - Organic Chemistry
    {
        "course_code": "CHEM302",
        "title": "Nucleophilic Substitution Reactions: SN1 and SN2",
        "content": """
Nucleophilic substitution reactions involve a nucleophile (electron-rich species) replacing a leaving group in a molecule. The two main mechanisms are SN1 and SN2.

SN2 (Substitution Nucleophilic Bimolecular) is a one-step mechanism. The nucleophile attacks the carbon bearing the leaving group from the backside, causing inversion of configuration (Walden inversion). The rate depends on both nucleophile and substrate concentrations: Rate = k[Nu][RX].

SN2 is favored by strong nucleophiles, polar aprotic solvents, primary and secondary substrates, and good leaving groups. Steric hindrance slows SN2 reactions.

SN1 (Substitution Nucleophilic Unimolecular) is a two-step mechanism. First, the leaving group departs forming a carbocation intermediate. Then, the nucleophile attacks the carbocation. The rate depends only on substrate concentration: Rate = k[RX].

SN1 is favored by weak nucleophiles, polar protic solvents, tertiary substrates, and good leaving groups. Carbocation stability (tertiary > secondary > primary) determines reactivity.

SN1 reactions lead to racemization because the nucleophile can attack the planar carbocation from either side, producing both stereoisomers.

Factors affecting substitution reactions include substrate structure (methyl, primary, secondary, tertiary), nucleophile strength, solvent polarity, and leaving group ability.
        """,
        "date": "2025-12-10",
        "professor": "Prof. Marie Curie"
    },

    # MATH201 - Calculus III
    {
        "course_code": "MATH201",
        "title": "Partial Derivatives and Gradient",
        "content": """
Partial derivatives extend the concept of derivatives to functions of multiple variables. For a function f(x,y), the partial derivative with respect to x treats y as constant and vice versa.

Notation includes ∂f/∂x, fₓ, or ∂ₓf for the partial derivative with respect to x. Geometric interpretation: ∂f/∂x represents the slope of the tangent line in the direction of the x-axis.

Higher-order partial derivatives include second derivatives (fₓₓ, fᵧᵧ) and mixed derivatives (fₓᵧ, fᵧₓ). Clairaut's theorem states that if mixed partial derivatives are continuous, they are equal: fₓᵧ = fᵧₓ.

The gradient of a function f is a vector containing all partial derivatives: ∇f = (∂f/∂x, ∂f/∂y, ∂f/∂z). The gradient points in the direction of steepest ascent, and its magnitude is the rate of change in that direction.

The directional derivative measures the rate of change of a function in a specified direction. It equals the dot product of the gradient and the unit direction vector: Dᵤf = ∇f · u.

Level curves (2D) and level surfaces (3D) are sets of points where the function has the same value. The gradient is perpendicular to level curves and surfaces.

Applications include optimization, finding tangent planes to surfaces, and analyzing multivariable functions in physics and engineering.
        """,
        "date": "2025-12-10",
        "professor": "Prof. Alan Turing"
    }
]


def create_lecture_notes():
    """Create lecture notes for all courses with automatic features."""

    print("=" * 100)
    print("MVP DEMO: CREATING LECTURE NOTES FOR INVESTOR PRESENTATION")
    print("=" * 100)
    print()
    print("This script creates comprehensive lecture notes for all courses with automatic:")
    print("  • LLM-generated summaries (Gemini 2.5 Flash Lite)")
    print("  • LLM-extracted tags and topics")
    print("  • 1024-dimension embeddings (Qwen3-Embedding)")
    print("  • Chunk creation for paragraph-level retrieval")
    print("  • Relationships to Course nodes")
    print()
    print("All lecture notes will be stored in Neo4j for semantic search.")
    print()

    # Initialize connection and data loader
    settings = Settings()
    connection = Neo4jConnection(settings=settings)
    data_loader = DataLoader(connection=connection, settings=settings)

    print(f"✓ Connected to Neo4j at {settings.neo4j.uri}")
    print()

    # Get current term
    current_term = IDGenerator.get_current_term()
    print(f"Current academic term: {current_term}")
    print()

    # Create lecture notes for all students enrolled in each course
    # Get student enrollments from Neo4j
    student_enrollments = {}
    with connection.session() as session:
        result = session.run("""
            MATCH (p:Profile)-[:ENROLLED_IN]->(c:Course)
            RETURN p.student_id as student_id, c.course_id as course_id
        """)

        for record in result:
            student_id = record['student_id']
            course_id = record['course_id']
            if course_id not in student_enrollments:
                student_enrollments[course_id] = []
            student_enrollments[course_id].append(student_id)

    print(f"Found {len(student_enrollments)} courses with enrolled students")
    print()

    # Create lecture notes
    created_count = 0
    total_count = 0

    for note_idx, note_template in enumerate(LECTURE_NOTES, start=1):
        # Student provides course_code (e.g., "CS301")
        # System generates course_id with current term (e.g., "CS301-Fall2025")
        course_code = note_template['course_code']
        course_id = IDGenerator.generate_course_id(course_code, current_term)

        students = student_enrollments.get(course_id, [])

        if not students:
            print(f"⚠️  No students enrolled in {course_id}, skipping lecture notes")
            continue

        print(f"Creating lecture note: '{note_template['title']}'")
        print(f"  Course: {course_id}")
        print(f"  Students: {len(students)}")
        print("-" * 100)

        for student_id in students:
            total_count += 1

            # Create note data for this student
            # CRITICAL: Each student gets their own personalized lecture note
            # This enables student-specific RAG queries and personalized learning
            note_data = note_template.copy()
            note_data['student_id'] = student_id
            note_data['course_id'] = course_id  # Add generated course_id
            note_data['lecture_note_id'] = f"{course_id}-{student_id}-lecture-{note_idx}"

            try:
                # Create lecture note with automatic features
                created_node = data_loader.create_node(
                    label="LectureNote",
                    properties=note_data,
                    id_field="lecture_note_id",
                    auto_embed=True,
                    create_relationships=True
                )

                # Log automatic features
                if created_count < 3:  # Show details for first few
                    summary = created_node.get('summary', 'N/A')
                    if summary and summary != 'N/A' and len(summary) > 0:
                        print(f"    ✓ {student_id}: Summary: {summary[:100]}...")

                    tags = created_node.get('tagged_topics', [])
                    if tags:
                        print(f"    ✓ {student_id}: Tags: {', '.join(tags[:5])}")

                    embedding = created_node.get('embedding_vector', [])
                    if embedding:
                        print(f"    ✓ {student_id}: Embedding: {len(embedding)} dimensions")

                created_count += 1

            except Exception as e:
                print(f"    ✗ {student_id}: Failed - {e}")

        print()

    # Summary
    print("=" * 100)
    print(f"LECTURE NOTES CREATED: {created_count}/{total_count}")
    print("=" * 100)
    print()
    print("Features automatically applied:")
    print("  ✓ 1024-dimension embeddings for semantic search")
    print("  ✓ LLM-generated summaries (Gemini 2.5 Flash Lite)")
    print("  ✓ LLM-extracted tags/topics")
    print("  ✓ Chunk creation for paragraph-level retrieval")
    print("  ✓ Course relationships (BELONGS_TO)")
    print()
    print("Verify lecture notes in Neo4j:")
    print('  docker exec neo4j-graphrag cypher-shell -u neo4j -p graphrag_secure_password_2025 \\')
    print('    "MATCH (l:LectureNote) RETURN l.lecture_note_id, l.title, l.course_id LIMIT 10;"')
    print()
    print("Check chunks created:")
    print('  docker exec neo4j-graphrag cypher-shell -u neo4j -p graphrag_secure_password_2025 \\')
    print('    "MATCH (l:LectureNote)-[:HAS_CHUNK]->(c:Chunk) RETURN l.title, count(c) as chunk_count;"')
    print()
    print("Test semantic search:")
    print('  cd /Users/en_tetteh/Documents/graphrag && uv run python test_semantic_search.py')
    print()
    print("=" * 100)

    # Cleanup
    connection.close()


if __name__ == "__main__":
    create_lecture_notes()
