#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from note_service.config import Settings
from note_service.db.connection import Neo4jConnection

settings = Settings()
connection = Neo4jConnection(settings)

with connection.session() as session:
    result = session.run('''
        MATCH (c:Course {course_id: "CS301-Fall2025"})
        OPTIONAL MATCH (p:Profile)-[:ENROLLED_IN]->(c)
        WITH c, collect(p.student_id) AS enrolled_students
        RETURN
            c.course_id AS course_id,
            c.student_id AS course_student_id,
            enrolled_students,
            size(enrolled_students) AS enrollment_count
    ''')

    record = result.single()
    if record:
        print('Course ID:', record['course_id'])
        print('Course student_id property:', record['course_student_id'])
        print('Enrolled students (via relationships):', record['enrolled_students'])
        print('Enrollment count:', record['enrollment_count'])
    else:
        print('Course not found')

connection.close()
