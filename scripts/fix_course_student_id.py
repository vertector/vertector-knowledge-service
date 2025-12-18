#!/usr/bin/env python3
"""
Migration script to remove student_id property from Course nodes.

Course nodes are shared entities and should NOT have a student_id property.
Student enrollment is represented via ENROLLED_IN relationships, not properties.

This script:
1. Finds all Course nodes with student_id property
2. Removes the student_id property from Course nodes
3. Verifies ENROLLED_IN relationships exist for those students
"""

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from note_service.config import Settings
from note_service.db.connection import Neo4jConnection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fix_course_student_id():
    """Remove student_id property from all Course nodes."""

    settings = Settings()
    connection = Neo4jConnection(settings)

    try:
        with connection.session() as session:
            # Step 1: Find all Course nodes with student_id
            logger.info("Finding Course nodes with student_id property...")
            result = session.run("""
                MATCH (c:Course)
                WHERE c.student_id IS NOT NULL
                RETURN c.course_id AS course_id, c.student_id AS student_id
            """)

            courses_with_student_id = list(result)

            if not courses_with_student_id:
                logger.info("✅ No Course nodes have student_id property. Database is clean!")
                return

            logger.info(f"Found {len(courses_with_student_id)} Course nodes with student_id property")

            # Step 2: For each Course, verify ENROLLED_IN relationship exists
            for record in courses_with_student_id:
                course_id = record['course_id']
                student_id = record['student_id']

                logger.info(f"Processing Course {course_id} with student_id {student_id}")

                # Check if ENROLLED_IN relationship exists
                check_result = session.run("""
                    MATCH (p:Profile {student_id: $student_id})-[r:ENROLLED_IN]->(c:Course {course_id: $course_id})
                    RETURN r
                """, student_id=student_id, course_id=course_id)

                if check_result.single():
                    logger.info(f"  ✓ ENROLLED_IN relationship exists: {student_id} → {course_id}")
                else:
                    logger.warning(f"  ⚠ ENROLLED_IN relationship missing: {student_id} → {course_id}")
                    logger.warning(f"    This should have been created by the NATS consumer.")

            # Step 3: Remove student_id property from all Course nodes
            logger.info("\nRemoving student_id property from Course nodes...")
            result = session.run("""
                MATCH (c:Course)
                WHERE c.student_id IS NOT NULL
                REMOVE c.student_id
                RETURN count(c) AS count
            """)

            count = result.single()['count']
            logger.info(f"✅ Removed student_id property from {count} Course nodes")

            # Step 4: Verify cleanup
            logger.info("\nVerifying cleanup...")
            result = session.run("""
                MATCH (c:Course)
                WHERE c.student_id IS NOT NULL
                RETURN count(c) AS count
            """)

            remaining = result.single()['count']

            if remaining == 0:
                logger.info("✅ Successfully cleaned up all Course nodes!")
                logger.info("✅ Course nodes are now shared entities without student_id property")
            else:
                logger.error(f"❌ Still {remaining} Course nodes with student_id property!")

    finally:
        connection.close()


if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info("Course student_id Property Cleanup Migration")
    logger.info("=" * 70)
    logger.info("")
    logger.info("This script removes student_id property from Course nodes.")
    logger.info("Course nodes are shared entities - enrollment is via relationships.")
    logger.info("")

    fix_course_student_id()

    logger.info("")
    logger.info("=" * 70)
    logger.info("Migration Complete")
    logger.info("=" * 70)
