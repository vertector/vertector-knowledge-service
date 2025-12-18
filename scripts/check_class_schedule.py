#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from note_service.config import Settings
from note_service.db.connection import Neo4jConnection

settings = Settings()
connection = Neo4jConnection(settings)

with connection.session() as session:
    # Check if any Class_Schedule nodes have student_id
    result = session.run('''
        MATCH (cs:Class_Schedule)
        RETURN cs.schedule_id AS schedule_id,
               cs.student_id AS student_id,
               cs.course_id AS course_id
        LIMIT 10
    ''')

    print('Class_Schedule nodes:')
    records = list(result)
    if not records:
        print('  No Class_Schedule nodes found')
    else:
        for record in records:
            print(f'  Schedule: {record["schedule_id"]}, Course: {record["course_id"]}, student_id: {record["student_id"]}')

    # Count total with student_id
    result = session.run('''
        MATCH (cs:Class_Schedule)
        WHERE cs.student_id IS NOT NULL
        RETURN count(cs) AS count
    ''')

    count = result.single()['count']
    print(f'\nClass_Schedule nodes with student_id: {count}')

connection.close()
