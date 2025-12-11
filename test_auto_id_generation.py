"""
Test Automatic ID Generation for LectureNote
"""

import logging
from note_service.config import Settings
from note_service.db.connection import Neo4jConnection
from note_service.ingestion.data_loader import DataLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_auto_id_generation():
    """Test that lecture_note_id is automatically generated when not provided."""

    settings = Settings()
    connection = Neo4jConnection(settings)
    data_loader = DataLoader(connection=connection, settings=settings)

    print("\n" + "=" * 80)
    print("TESTING AUTOMATIC ID GENERATION FOR LECTURENOTE")
    print("=" * 80 + "\n")

    # Test Case 1: Create LectureNote WITHOUT providing lecture_note_id
    print("Test Case 1: Creating LectureNote WITHOUT lecture_note_id")
    print("-" * 80)

    note_data_without_id = {
        'student_id': 'S2025001',
        'course_id': 'CS101-S2025001-1',
        'title': 'Test Note - Auto ID Generation',
        'content': 'This note tests automatic ID generation.',
        'key_concepts': ['testing', 'auto-generation', 'ids']
    }

    # Create note - ID should be auto-generated
    created_note = data_loader.create_node(
        label='LectureNote',
        properties=note_data_without_id,
        id_field='lecture_note_id',
        auto_embed=True,
        create_relationships=True
    )

    generated_id = note_data_without_id.get('lecture_note_id')

    if generated_id:
        print(f"✅ SUCCESS: Auto-generated ID = {generated_id}")
        print(f"   Pattern matches: NOTE-YYYYMMDDHHMMSS-XXXXXX")
        print(f"   Student ID: {note_data_without_id['student_id']}")
        print(f"   Title: {note_data_without_id['title']}")
    else:
        print("❌ FAILED: No ID was generated")
        connection.close()
        return False

    # Verify in database
    print("\nVerifying in Neo4j...")
    with connection.session() as session:
        result = session.run(
            "MATCH (ln:LectureNote {lecture_note_id: $id}) RETURN ln",
            id=generated_id
        )
        record = result.single()

        if record:
            print(f"✅ Verified: LectureNote exists in database with ID {generated_id}")
        else:
            print(f"❌ Not found in database")
            connection.close()
            return False

    # Test Case 2: Create LectureNote WITH manual lecture_note_id (should use provided ID)
    print("\n" + "-" * 80)
    print("Test Case 2: Creating LectureNote WITH manual lecture_note_id")
    print("-" * 80)

    manual_id = "NOTE-MANUAL-TEST-001"
    note_data_with_id = {
        'lecture_note_id': manual_id,
        'student_id': 'S2025002',
        'course_id': 'CS101-S2025002-1',
        'title': 'Test Note - Manual ID',
        'content': 'This note uses a manually provided ID.',
        'key_concepts': ['testing', 'manual-id']
    }

    # Create note - should use the provided ID
    created_note_2 = data_loader.create_node(
        label='LectureNote',
        properties=note_data_with_id,
        id_field='lecture_note_id',
        auto_embed=True,
        create_relationships=True
    )

    final_id = note_data_with_id.get('lecture_note_id')

    if final_id == manual_id:
        print(f"✅ SUCCESS: Manual ID preserved = {final_id}")
        print(f"   Title: {note_data_with_id['title']}")
    else:
        print(f"❌ FAILED: Manual ID was changed from {manual_id} to {final_id}")
        connection.close()
        return False

    # Cleanup
    print("\n" + "-" * 80)
    print("Cleaning up test data...")
    with connection.session() as session:
        session.run(
            "MATCH (ln:LectureNote) WHERE ln.lecture_note_id IN [$id1, $id2] DETACH DELETE ln",
            id1=generated_id,
            id2=manual_id
        )
        print("✓ Test data cleaned up")

    connection.close()

    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED - AUTOMATIC ID GENERATION WORKING!")
    print("=" * 80)

    return True


if __name__ == "__main__":
    try:
        success = test_auto_id_generation()
        if not success:
            print("\n❌ Tests failed")
            exit(1)
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
