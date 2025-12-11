"""
============================================================================
Test Data Management Script
============================================================================
Reusable script for deleting and populating test LectureNote data
============================================================================
"""

import logging
import sys
from dotenv import load_dotenv

from note_service.config import Settings
from note_service.db.connection import Neo4jConnection
from note_service.ingestion.data_loader import DataLoader

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def delete_all_lecture_notes(connection: Neo4jConnection):
    """Delete all LectureNotes and Chunks."""
    print("\n" + "=" * 80)
    print("DELETING ALL LECTURE NOTES")
    print("=" * 80 + "\n")

    with connection.driver.session() as session:
        # Delete all chunks
        result = session.run('MATCH (c:Chunk) DETACH DELETE c RETURN count(c) as deleted_count')
        chunk_count = result.single()['deleted_count']
        print(f'✓ Deleted {chunk_count} chunks')

        # Delete all lecture notes
        result = session.run('MATCH (ln:LectureNote) DETACH DELETE ln RETURN count(ln) as deleted_count')
        note_count = result.single()['deleted_count']
        print(f'✓ Deleted {note_count} lecture notes')

    print(f'\n✅ Cleanup complete!')


def create_sample_lecture_notes(data_loader: DataLoader, connection: Neo4jConnection):
    """Create sample LectureNotes with automatic tag generation and chunking."""
    print("\n" + "=" * 80)
    print("CREATING SAMPLE LECTURE NOTES")
    print("=" * 80 + "\n")

    sample_notes = [
        {
            # lecture_note_id will be auto-generated
            'student_id': 'S2025001',
            'course_id': 'CS101-S2025001-1',
            'title': 'Python Variables and Data Types',
            'content': '''
## Introduction to Variables

Variables in Python are used to store data values. Unlike other programming languages, Python has no command for declaring a variable.

### Variable Naming Rules

1. Variable names must start with a letter or underscore
2. Variable names can only contain letters, numbers, and underscores
3. Variable names are case-sensitive

## Data Types

Python has several built-in data types:

### Numeric Types
- **int**: Integer numbers (e.g., 5, -3, 100)
- **float**: Decimal numbers (e.g., 3.14, -0.5)
- **complex**: Complex numbers (e.g., 3+4j)

### Text Type
- **str**: String values (e.g., "hello", 'Python')

### Boolean Type
- **bool**: True or False values

## Type Conversion

You can convert from one type to another using constructor functions like `int()`, `float()`, and `str()`.

```python
x = 5        # int
y = 3.14     # float
z = "Hello"  # str
```
            '''.strip(),
            # 'summary': will be auto-generated
            'key_concepts': ['variables', 'data types', 'type conversion', 'integers', 'floats', 'strings', 'booleans']
        },
        {
            # lecture_note_id will be auto-generated
            'student_id': 'S2025002',
            'course_id': 'CS101-S2025002-1',
            'title': 'Python Functions and Modularity',
            'content': '''
## Functions in Python

Functions are reusable blocks of code that perform specific tasks. They help organize code and follow the DRY (Don't Repeat Yourself) principle.

### Defining Functions

Use the `def` keyword to define a function:

```python
def greet(name):
    return f"Hello, {name}!"
```

### Function Parameters

Functions can accept parameters (inputs):
- **Positional parameters**: Order matters
- **Keyword parameters**: Named arguments
- **Default parameters**: Optional with default values

### Return Values

Functions can return values using the `return` statement.

## Lambda Functions

Lambda functions are small anonymous functions defined with the `lambda` keyword:

```python
square = lambda x: x ** 2
```

## Scope

Variables defined inside a function have local scope and cannot be accessed outside the function.
            '''.strip(),
            # 'summary': will be auto-generated
            'key_concepts': ['functions', 'parameters', 'return values', 'lambda expressions', 'scope', 'DRY principle']
        },
        {
            # lecture_note_id will be auto-generated
            'student_id': 'S2025001',
            'course_id': 'MATH201-S2025001-2',
            'title': 'Integration Techniques - Integration by Parts',
            'content': '''
## Integration by Parts

Integration by parts is a technique used to integrate products of functions. It's based on the product rule for differentiation.

### The Formula

The integration by parts formula is:

∫ u dv = uv - ∫ v du

### LIATE Rule

Choose u and dv using the LIATE priority:
1. **L**ogarithmic functions
2. **I**nverse trigonometric functions
3. **A**lgebraic functions
4. **T**rigonometric functions
5. **E**xponential functions

### Example

Integrate ∫ x·e^x dx

Let u = x, dv = e^x dx
Then du = dx, v = e^x

∫ x·e^x dx = x·e^x - ∫ e^x dx = x·e^x - e^x + C

## When to Use

Integration by parts is particularly useful when:
- Integrating products of polynomial and exponential/trig functions
- Integrating logarithmic functions
- Reducing the complexity of integrals
            '''.strip(),
            # 'summary': will be auto-generated
            'key_concepts': ['integration by parts', 'LIATE rule', 'u-substitution', 'calculus techniques', 'antiderivatives']
        }
    ]

    created_count = 0
    for note_data in sample_notes:
        print(f"\nCreating: {note_data['title']}")
        print(f"  Course: {note_data['course_id']}")
        print(f"  Student: {note_data['student_id']}")

        try:
            # Create the note (automatic: tag generation, topic extraction, chunking)
            data_loader.create_node(
                label='LectureNote',
                properties=note_data,
                id_field='lecture_note_id',
                auto_embed=True,
                create_relationships=True
            )
            created_count += 1
            print(f"  ✓ Created successfully")
        except Exception as e:
            logger.error(f"Failed to create {note_data['title']}: {e}", exc_info=True)

    print(f"\n✅ Created {created_count}/{len(sample_notes)} lecture notes")


def verify_data(connection: Neo4jConnection):
    """Verify the created data."""
    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80 + "\n")

    with connection.driver.session() as session:
        # Count LectureNotes
        result = session.run('MATCH (ln:LectureNote) RETURN count(ln) as count')
        lecture_note_count = result.single()['count']
        print(f"LectureNotes: {lecture_note_count}")

        # Count Chunks
        result = session.run('MATCH (c:Chunk) RETURN count(c) as count')
        chunk_count = result.single()['count']
        print(f"Chunks: {chunk_count}")

        # Show LectureNote details
        print("\nLectureNote Details:")
        result = session.run('''
            MATCH (ln:LectureNote)
            OPTIONAL MATCH (c:Chunk)-[:PART_OF]->(ln)
            WITH ln,
                 count(DISTINCT c) as chunk_count
            RETURN ln.lecture_note_id as note_id,
                   ln.title as title,
                   ln.tagged_topics as tags,
                   chunk_count
            ORDER BY note_id
        ''')

        for record in result:
            print(f"\n  {record['title']}")
            print(f"    Tags: {record['tags']}")
            print(f"    Chunks: {record['chunk_count']}")


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python manage_test_data.py [delete|populate|reset]")
        print("  delete   - Delete all lecture notes and chunks")
        print("  populate - Create sample lecture notes")
        print("  reset    - Delete all data and create fresh sample lecture notes")
        sys.exit(1)

    command = sys.argv[1].lower()

    settings = Settings()
    connection = Neo4jConnection(settings)

    try:
        if command == 'delete':
            delete_all_lecture_notes(connection)

        elif command == 'populate':
            data_loader = DataLoader(connection=connection, settings=settings)
            # Ensure all indices exist before populating data
            print("\n" + "=" * 80)
            print("ENSURING INDICES EXIST")
            print("=" * 80 + "\n")
            data_loader.ensure_indices_exist()
            create_sample_lecture_notes(data_loader, connection)
            verify_data(connection)

        elif command == 'reset':
            delete_all_lecture_notes(connection)
            data_loader = DataLoader(connection=connection, settings=settings)
            # Ensure all indices exist before populating data
            print("\n" + "=" * 80)
            print("ENSURING INDICES EXIST")
            print("=" * 80 + "\n")
            data_loader.ensure_indices_exist()
            create_sample_lecture_notes(data_loader, connection)
            verify_data(connection)

        else:
            print(f"Unknown command: {command}")
            print("Valid commands: delete, populate, reset")
            sys.exit(1)

    finally:
        connection.close()

    print("\n✅ Done!")


if __name__ == "__main__":
    main()
