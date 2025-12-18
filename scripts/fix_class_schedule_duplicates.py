#!/usr/bin/env python3
"""
Migration script to consolidate duplicate Class_Schedule nodes.

Class_Schedule nodes are shared entities and should NOT have student_id property.
Currently, there are duplicate Class_Schedule nodes (one per student per course).

This script:
1. Identifies duplicate Class_Schedule nodes for each course
2. Keeps one canonical Class_Schedule per course
3. Removes student_id property from remaining schedules
4. Deletes duplicate schedules
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


def fix_class_schedule_duplicates():
    """Consolidate duplicate Class_Schedule nodes into one per course."""

    settings = Settings()
    connection = Neo4jConnection(settings)

    try:
        with connection.session() as session:
            # Step 1: Find all courses and their associated schedules
            logger.info("Finding courses with multiple Class_Schedule nodes...")
            result = session.run("""
                MATCH (cs:Class_Schedule)-[:SCHEDULED_FOR]->(c:Course)
                WITH c.course_id AS course_id,
                     collect({schedule_id: cs.schedule_id, student_id: cs.student_id}) AS schedules
                WHERE size(schedules) > 1
                RETURN course_id, schedules
            """)

            courses_with_duplicates = list(result)

            if not courses_with_duplicates:
                logger.info("✅ No duplicate Class_Schedule nodes found!")

                # Still need to remove student_id from all Class_Schedule nodes
                logger.info("\nChecking for Class_Schedule nodes with student_id property...")
                result = session.run("""
                    MATCH (cs:Class_Schedule)
                    WHERE cs.student_id IS NOT NULL
                    RETURN count(cs) AS count
                """)

                count = result.single()['count']
                if count > 0:
                    logger.info(f"Found {count} Class_Schedule nodes with student_id property")
                    logger.info("Removing student_id property...")

                    result = session.run("""
                        MATCH (cs:Class_Schedule)
                        WHERE cs.student_id IS NOT NULL
                        REMOVE cs.student_id
                        RETURN count(cs) AS count
                    """)

                    cleaned = result.single()['count']
                    logger.info(f"✅ Removed student_id from {cleaned} Class_Schedule nodes")

                return

            logger.info(f"Found {len(courses_with_duplicates)} courses with duplicate schedules\n")

            # Step 2: For each course, keep first schedule and delete duplicates
            for record in courses_with_duplicates:
                course_id = record['course_id']
                schedules = record['schedules']

                logger.info(f"Course {course_id} has {len(schedules)} schedules:")
                for sched in schedules:
                    logger.info(f"  - {sched['schedule_id']} (student_id: {sched['student_id']})")

                # Keep the first schedule, delete the rest
                canonical_schedule_id = schedules[0]['schedule_id']
                duplicate_schedule_ids = [s['schedule_id'] for s in schedules[1:]]

                logger.info(f"  ✓ Keeping: {canonical_schedule_id}")
                logger.info(f"  ✗ Deleting: {duplicate_schedule_ids}")

                # Delete duplicate schedules
                for dup_id in duplicate_schedule_ids:
                    result = session.run("""
                        MATCH (cs:Class_Schedule {schedule_id: $schedule_id})
                        DETACH DELETE cs
                    """, schedule_id=dup_id)
                    logger.info(f"    Deleted {dup_id}")

            # Step 3: Remove student_id property from all remaining Class_Schedule nodes
            logger.info("\nRemoving student_id property from Class_Schedule nodes...")
            result = session.run("""
                MATCH (cs:Class_Schedule)
                WHERE cs.student_id IS NOT NULL
                REMOVE cs.student_id
                RETURN count(cs) AS count
            """)

            count = result.single()['count']
            logger.info(f"✅ Removed student_id property from {count} Class_Schedule nodes")

            # Step 4: Verify cleanup
            logger.info("\nVerifying cleanup...")
            result = session.run("""
                MATCH (cs:Class_Schedule)
                WHERE cs.student_id IS NOT NULL
                RETURN count(cs) AS count
            """)

            remaining_with_student_id = result.single()['count']

            result = session.run("""
                MATCH (cs:Class_Schedule)-[:SCHEDULED_FOR]->(c:Course)
                WITH c.course_id AS course_id, count(cs) AS schedule_count
                WHERE schedule_count > 1
                RETURN count(*) AS courses_with_duplicates
            """)

            remaining_duplicates = result.single()['courses_with_duplicates']

            if remaining_with_student_id == 0 and remaining_duplicates == 0:
                logger.info("✅ Successfully cleaned up all Class_Schedule nodes!")
                logger.info("✅ Class_Schedule nodes are now shared entities without student_id property")
                logger.info("✅ Each course has exactly one Class_Schedule")
            else:
                if remaining_with_student_id > 0:
                    logger.error(f"❌ Still {remaining_with_student_id} Class_Schedule nodes with student_id!")
                if remaining_duplicates > 0:
                    logger.error(f"❌ Still {remaining_duplicates} courses with duplicate schedules!")

    finally:
        connection.close()


if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info("Class_Schedule Duplicate Cleanup Migration")
    logger.info("=" * 70)
    logger.info("")
    logger.info("This script consolidates duplicate Class_Schedule nodes.")
    logger.info("Class_Schedule nodes are shared entities - one schedule per course.")
    logger.info("")

    fix_class_schedule_duplicates()

    logger.info("")
    logger.info("=" * 70)
    logger.info("Migration Complete")
    logger.info("=" * 70)
