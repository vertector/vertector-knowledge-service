"""
Test to demonstrate chunk skipping issues.
"""

from note_service.config import Settings
from note_service.db.connection import Neo4jConnection
from note_service.ingestion.chunk_generator import ChunkGenerator

settings = Settings()
connection = Neo4jConnection(settings)

# Test content with some small sections
test_content = """
## Large Section 1
This is a large section with plenty of content that will definitely exceed the minimum token threshold.
Variables in Python are dynamic containers for data values. They are created when you assign a value.
Python supports multiple data types including integers, floats, strings, and booleans.

## Tiny
Small

## Large Section 2
This section also has substantial content that exceeds the minimum threshold.
Functions are reusable blocks of code that perform specific tasks.
They help organize code and follow the DRY principle.
Lambda functions provide a concise way to define small anonymous functions.

## Mini
X

## Large Section 3
Another large section with plenty of text content.
Integration by parts is a technique for integrating products of functions.
The LIATE rule helps determine which function to choose for u and dv.
"""

chunk_gen = ChunkGenerator(
    driver=connection.driver,
    max_chunk_tokens=512,
    overlap_tokens=50,
    min_chunk_tokens=25  # This will cause "Tiny" and "Mini" to be skipped
)

chunks = chunk_gen.generate_chunks(
    lecture_note_id="TEST-001",
    content=test_content,
    title="Test"
)

print("\n" + "="*80)
print("CHUNK SKIPPING DEMONSTRATION")
print("="*80 + "\n")

print(f"Content has 5 markdown sections, but generated {len(chunks)} chunks\n")

print("Generated Chunks:")
print("-" * 80)
for chunk in chunks:
    print(f"\nChunk ID: {chunk.chunk_id}")
    print(f"  Index: {chunk.chunk_index}  ← NOTICE THE GAPS!")
    print(f"  Heading: {chunk.heading}")
    print(f"  Tokens: {chunk.token_count}")
    print(f"  Content preview: {chunk.content[:60]}...")

print("\n" + "="*80)
print("PROBLEMS IDENTIFIED:")
print("="*80)
print("1. LOST CONTENT: 'Tiny' and 'Mini' sections are completely discarded")
print("   - Users lose data they wrote")
print("   - No way to recover this content from chunks")
print("\n2. INDEX GAPS: chunk_index has gaps (0, 2, 4 instead of 0, 1, 2)")
print("   - NEXT_CHUNK relationships will have gaps")
print("   - chunk_index doesn't match array position")
print("\n3. MISLEADING IDs: CHUNK-TEST-001-002 is actually the 2nd chunk, not 3rd")
print("   - Confusing for debugging")
print("   - Doesn't match actual sequence")

print("\n" + "="*80)
print("EXPECTED BEHAVIOR:")
print("="*80)
print("Option 1: Merge small chunks into adjacent chunks")
print("  - No data loss")
print("  - Sequential indexes")
print("  - Example: Merge 'Tiny' into 'Large Section 1'")
print("\nOption 2: Keep all chunks, remove min_chunk_tokens filter")
print("  - All content preserved")
print("  - Sequential indexes")
print("  - Some chunks will be very small")
print("\nOption 3: Use a separate actual_index counter")
print("  - No data loss if we merge")
print("  - chunk_index stays sequential")
print("  - Use enumerate on filtered list, not original")

connection.close()
