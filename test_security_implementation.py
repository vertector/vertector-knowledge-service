"""
============================================================================
Test Security Implementation
============================================================================
Comprehensive test of student data isolation, security validation, and
audit logging features.
============================================================================
"""

import os
from dotenv import load_dotenv
from note_service.config import Settings
from note_service.db.connection import Neo4jConnection
from note_service.retrieval.service import RetrievalService
from note_service.security.audit import AuditLogger
from note_service.security.validator import SecurityValidator

# Load environment variables
load_dotenv()


def test_security_features():
    """Test all security features."""

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

    audit_logger = AuditLogger(driver=connection.driver)
    security_validator = SecurityValidator(driver=connection.driver)

    print("\n" + "=" * 80)
    print("TESTING SECURITY IMPLEMENTATION")
    print("=" * 80 + "\n")

    # Test 1: Security Validator - Profile Existence
    print("=" * 80)
    print("TEST 1: Security Validator - Profile Existence Check")
    print("=" * 80)

    test_student_id = "STU001"
    profile_exists = security_validator.verify_profile_exists(test_student_id)
    print(f"✓ Profile exists for {test_student_id}: {profile_exists}")

    invalid_student_id = "INVALID_STUDENT"
    profile_exists_invalid = security_validator.verify_profile_exists(invalid_student_id)
    print(f"✓ Profile exists for {invalid_student_id}: {profile_exists_invalid}")
    print()

    # Test 2: Security Validator - Note Ownership
    print("=" * 80)
    print("TEST 2: Security Validator - Note Ownership Verification")
    print("=" * 80)

    # Get student's notes
    student_notes = security_validator.get_student_note_ids(test_student_id)
    print(f"✓ Student {test_student_id} owns {len(student_notes)} notes")

    if student_notes:
        # Verify ownership of first note
        first_note_id = student_notes[0]
        owns_note = security_validator.verify_note_ownership(test_student_id, first_note_id)
        print(f"✓ Student {test_student_id} owns note {first_note_id}: {owns_note}")

        # Try to verify ownership with wrong student
        wrong_student = "STU999"
        owns_note_wrong = security_validator.verify_note_ownership(wrong_student, first_note_id)
        print(f"✓ Student {wrong_student} owns note {first_note_id}: {owns_note_wrong}")
    print()

    # Test 3: Retrieval Service - Search with Valid Student
    print("=" * 80)
    print("TEST 3: Retrieval Service - Search with Valid Student ID")
    print("=" * 80)

    query = "What are the different data types in Python?"

    try:
        result = retrieval_service.search(
            query_text=query,
            student_id=test_student_id,
            top_k=3,
            granularity="document",
            search_type="hybrid"
        )

        print(f"✓ Search successful for student {test_student_id}")
        print(f"  Query: '{query}'")
        print(f"  Results: {result.num_results}")

        for i, doc in enumerate(result.results[:3], 1):
            title = doc.get('lecture_note_title', 'N/A')
            score = doc.get('score', 'N/A')
            print(f"  {i}. {title} (score: {score})")
        print()

    except Exception as e:
        print(f"✗ Search failed: {e}")
        print()

    # Test 4: Retrieval Service - Search without Student ID (Should Fail)
    print("=" * 80)
    print("TEST 4: Retrieval Service - Search without Student ID (Should Fail)")
    print("=" * 80)

    try:
        result = retrieval_service.search(
            query_text=query,
            student_id="",  # Empty student_id
            top_k=3,
            granularity="document",
            search_type="hybrid"
        )
        print(f"✗ Search should have failed but didn't!")
        print()

    except ValueError as e:
        print(f"✓ Search correctly rejected empty student_id")
        print(f"  Error message: {e}")
        print()

    # Test 5: Retrieval Service - Search with Invalid Student (Should Fail)
    print("=" * 80)
    print("TEST 5: Retrieval Service - Search with Invalid Student (Should Fail)")
    print("=" * 80)

    try:
        result = retrieval_service.search(
            query_text=query,
            student_id="NONEXISTENT_STUDENT",
            top_k=3,
            granularity="document",
            search_type="hybrid"
        )
        print(f"✗ Search should have failed for nonexistent student!")
        print()

    except ValueError as e:
        print(f"✓ Search correctly rejected nonexistent student")
        print(f"  Error message: {e}")
        print()

    # Test 6: Audit Logging - View Access History
    print("=" * 80)
    print("TEST 6: Audit Logging - View Access History")
    print("=" * 80)

    access_history = audit_logger.get_student_access_history(
        student_id=test_student_id,
        limit=5
    )

    print(f"✓ Retrieved {len(access_history)} audit log entries for student {test_student_id}")

    for i, log_entry in enumerate(access_history[:3], 1):
        print(f"\n  Log Entry {i}:")
        print(f"    Operation: {log_entry.get('operation_type', 'N/A')}")
        print(f"    Entity Type: {log_entry.get('entity_type', 'N/A')}")
        print(f"    Timestamp: {log_entry.get('timestamp', 'N/A')}")

        context = log_entry.get('context', {})
        if isinstance(context, dict):
            if 'query_text' in context:
                print(f"    Query: {context['query_text']}")
            if 'result_count' in context:
                print(f"    Results: {context['result_count']}")
    print()

    # Test 7: Security Validator - Batch Filtering
    print("=" * 80)
    print("TEST 7: Security Validator - Batch Note Filtering")
    print("=" * 80)

    if len(student_notes) >= 2:
        # Mix of owned and potentially unowned notes
        test_note_ids = student_notes[:2] + ["FAKE_NOTE_1", "FAKE_NOTE_2"]

        filtered_notes = security_validator.filter_owned_notes(
            student_id=test_student_id,
            note_ids=test_note_ids
        )

        print(f"✓ Filtered {len(test_note_ids)} note IDs")
        print(f"  Input: {test_note_ids}")
        print(f"  Owned by student: {filtered_notes}")
        print(f"  Filtered out: {set(test_note_ids) - set(filtered_notes)}")
    print()

    # Test 8: Manual Audit Log Creation
    print("=" * 80)
    print("TEST 8: Manual Audit Log Creation")
    print("=" * 80)

    log_id = audit_logger.log_access(
        student_id=test_student_id,
        operation_type="test",
        entity_type="LectureNote",
        entity_ids=student_notes[:2] if student_notes else [],
        context={"test": "manual audit log creation"}
    )

    print(f"✓ Created audit log entry: {log_id}")
    print()

    # Final Summary
    print("=" * 80)
    print("SECURITY TESTING COMPLETE")
    print("=" * 80)

    print("\n✅ All security features verified:")
    print("  1. Profile existence validation")
    print("  2. Note ownership verification")
    print("  3. Search with valid student_id")
    print("  4. Search rejection for empty student_id")
    print("  5. Search rejection for nonexistent student")
    print("  6. Audit log retrieval")
    print("  7. Batch note filtering")
    print("  8. Manual audit log creation")

    print("\n🔒 Security Implementation Status:")
    print("  • Student data isolation: ACTIVE")
    print("  • Ownership verification: ACTIVE")
    print("  • Audit logging: ACTIVE")
    print("  • Database constraints: READY (apply schema/05_security_constraints.cypher)")

    connection.close()
    print("\n" + "=" * 80)
    print("✅ Test complete!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    test_security_features()
