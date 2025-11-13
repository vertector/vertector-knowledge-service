CREATE INDEX profile_email_range IF NOT EXISTS
FOR (p:Profile)
ON (p.email);
CREATE INDEX profile_major_range IF NOT EXISTS
FOR (p:Profile)
ON (p.major);
CREATE INDEX profile_year_range IF NOT EXISTS
FOR (p:Profile)
ON (p.year);
CREATE INDEX profile_gpa_range IF NOT EXISTS
FOR (p:Profile)
ON (p.cumulative_gpa);
CREATE INDEX profile_graduation_range IF NOT EXISTS
FOR (p:Profile)
ON (p.expected_graduation);
CREATE INDEX course_code_range IF NOT EXISTS
FOR (c:Course)
ON (c.code);
CREATE INDEX course_term_range IF NOT EXISTS
FOR (c:Course)
ON (c.term);
CREATE INDEX course_instructor_range IF NOT EXISTS
FOR (c:Course)
ON (c.instructor_name);
CREATE INDEX course_code_term_composite IF NOT EXISTS
FOR (c:Course)
ON (c.code, c.term);
CREATE INDEX assignment_due_date_range IF NOT EXISTS
FOR (a:Assignment)
ON (a.due_date);
CREATE INDEX assignment_type_range IF NOT EXISTS
FOR (a:Assignment)
ON (a.type);
CREATE INDEX assignment_status_range IF NOT EXISTS
FOR (a:Assignment)
ON (a.submission_status);
CREATE INDEX assignment_grade_range IF NOT EXISTS
FOR (a:Assignment)
ON (a.percentage_grade);
CREATE INDEX exam_date_range IF NOT EXISTS
FOR (e:Exam)
ON (e.date);
CREATE INDEX exam_type_range IF NOT EXISTS
FOR (e:Exam)
ON (e.exam_type);
CREATE INDEX exam_grade_range IF NOT EXISTS
FOR (e:Exam)
ON (e.percentage_grade);
CREATE INDEX quiz_date_range IF NOT EXISTS
FOR (q:Quiz)
ON (q.date);
CREATE INDEX quiz_grade_range IF NOT EXISTS
FOR (q:Quiz)
ON (q.percentage_grade);
CREATE INDEX quiz_number_range IF NOT EXISTS
FOR (q:Quiz)
ON (q.quiz_number);
CREATE INDEX lab_date_range IF NOT EXISTS
FOR (l:Lab_Session)
ON (l.date);
CREATE INDEX lab_submission_deadline_range IF NOT EXISTS
FOR (l:Lab_Session)
ON (l.submission_deadline);
CREATE INDEX todo_status_range IF NOT EXISTS
FOR (t:Study_Todo)
ON (t.status);
CREATE INDEX todo_priority_range IF NOT EXISTS
FOR (t:Study_Todo)
ON (t.priority);
CREATE INDEX todo_due_date_range IF NOT EXISTS
FOR (t:Study_Todo)
ON (t.due_date);
CREATE INDEX todo_created_date_range IF NOT EXISTS
FOR (t:Study_Todo)
ON (t.created_date);
CREATE INDEX todo_ai_generated_range IF NOT EXISTS
FOR (t:Study_Todo)
ON (t.ai_generated);
CREATE INDEX todo_status_priority_composite IF NOT EXISTS
FOR (t:Study_Todo)
ON (t.status, t.priority);
CREATE INDEX challenge_severity_range IF NOT EXISTS
FOR (ca:Challenge_Area)
ON (ca.severity);
CREATE INDEX challenge_status_range IF NOT EXISTS
FOR (ca:Challenge_Area)
ON (ca.status);
CREATE INDEX challenge_identified_date_range IF NOT EXISTS
FOR (ca:Challenge_Area)
ON (ca.identified_date);
CREATE INDEX challenge_detection_method_range IF NOT EXISTS
FOR (ca:Challenge_Area)
ON (ca.detection_method);
CREATE INDEX schedule_start_time_range IF NOT EXISTS
FOR (cs:Class_Schedule)
ON (cs.start_time);
CREATE INDEX schedule_format_range IF NOT EXISTS
FOR (cs:Class_Schedule)
ON (cs.format);
CREATE INDEX schedule_term_dates_composite IF NOT EXISTS
FOR (cs:Class_Schedule)
ON (cs.term_start_date, cs.term_end_date);
CREATE INDEX lecture_note_created_date_range IF NOT EXISTS
FOR (ln:LectureNote)
ON (ln.created_date);
CREATE INDEX lecture_note_last_modified_range IF NOT EXISTS
FOR (ln:LectureNote)
ON (ln.last_modified);
CREATE INDEX topic_name_range IF NOT EXISTS
FOR (t:Topic)
ON (t.name);
CREATE INDEX topic_difficulty_range IF NOT EXISTS
FOR (t:Topic)
ON (t.difficulty_level);
CREATE INDEX topic_normalized_name_range IF NOT EXISTS
FOR (t:Topic)
ON (t.normalized_name);
CREATE INDEX resource_type_range IF NOT EXISTS
FOR (r:Resource)
ON (r.type);
CREATE INDEX resource_publication_date_range IF NOT EXISTS
FOR (r:Resource)
ON (r.publication_date);
CREATE TEXT INDEX course_title_text IF NOT EXISTS
FOR (c:Course)
ON (c.title);
CREATE TEXT INDEX course_description_text IF NOT EXISTS
FOR (c:Course)
ON (c.description);
CREATE TEXT INDEX lecture_note_title_text IF NOT EXISTS
FOR (ln:LectureNote)
ON (ln.title);
CREATE TEXT INDEX lecture_note_content_text IF NOT EXISTS
FOR (ln:LectureNote)
ON (ln.content);
CREATE TEXT INDEX lecture_note_summary_text IF NOT EXISTS
FOR (ln:LectureNote)
ON (ln.summary);
CREATE TEXT INDEX assignment_title_text IF NOT EXISTS
FOR (a:Assignment)
ON (a.title);
CREATE TEXT INDEX assignment_description_text IF NOT EXISTS
FOR (a:Assignment)
ON (a.description);
CREATE TEXT INDEX topic_name_text IF NOT EXISTS
FOR (t:Topic)
ON (t.name);
CREATE TEXT INDEX topic_description_text IF NOT EXISTS
FOR (t:Topic)
ON (t.description);
CREATE TEXT INDEX resource_title_text IF NOT EXISTS
FOR (r:Resource)
ON (r.title);
CREATE TEXT INDEX resource_description_text IF NOT EXISTS
FOR (r:Resource)
ON (r.description);
CREATE FULLTEXT INDEX lecture_note_fulltext IF NOT EXISTS
FOR (ln:LectureNote)
ON EACH [ln.title, ln.content, ln.summary];
CREATE TEXT INDEX chunk_content_text IF NOT EXISTS
FOR (c:Chunk)
ON (c.content);
CREATE TEXT INDEX chunk_heading_text IF NOT EXISTS
FOR (c:Chunk)
ON (c.heading);
CREATE FULLTEXT INDEX chunk_fulltext IF NOT EXISTS
FOR (c:Chunk)
ON EACH [c.content, c.heading, c.summary];
CREATE INDEX chunk_lecture_note_id_range IF NOT EXISTS
FOR (c:Chunk)
ON (c.lecture_note_id);
CREATE INDEX chunk_index_range IF NOT EXISTS
FOR (c:Chunk)
ON (c.chunk_index);
CREATE INDEX chunk_type_range IF NOT EXISTS
FOR (c:Chunk)
ON (c.chunk_type);
CREATE VECTOR INDEX chunk_content_vector IF NOT EXISTS
FOR (c:Chunk)
ON c.embedding_vector
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 1024,
    `vector.similarity_function`: 'cosine'
  }
};
CREATE VECTOR INDEX lecture_note_content_vector IF NOT EXISTS
FOR (ln:LectureNote)
ON ln.embedding_vector
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 1024,
    `vector.similarity_function`: 'cosine'
  }
};
CREATE VECTOR INDEX topic_description_vector IF NOT EXISTS
FOR (t:Topic)
ON t.embedding_vector
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 1024,
    `vector.similarity_function`: 'cosine'
  }
};
CREATE VECTOR INDEX resource_description_vector IF NOT EXISTS
FOR (r:Resource)
ON r.embedding_vector
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 1024,
    `vector.similarity_function`: 'cosine'
  }
};
CREATE VECTOR INDEX challenge_description_vector IF NOT EXISTS
FOR (ca:Challenge_Area)
ON ca.embedding_vector
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 1024,
    `vector.similarity_function`: 'cosine'
  }
};
CREATE INDEX enrolled_in_enrollment_date IF NOT EXISTS
FOR ()-[r:ENROLLED_IN]-()
ON (r.enrollment_date);
CREATE INDEX enrolled_in_status IF NOT EXISTS
FOR ()-[r:ENROLLED_IN]-()
ON (r.status);
CREATE INDEX revealed_challenge_detection_date IF NOT EXISTS
FOR ()-[r:REVEALED_CHALLENGE]-()
ON (r.detection_date);
CREATE INDEX revealed_challenge_score IF NOT EXISTS
FOR ()-[r:REVEALED_CHALLENGE]-()
ON (r.score);
CREATE INDEX links_to_note_created_date IF NOT EXISTS
FOR ()-[r:LINKS_TO_NOTE]-()
ON (r.created_date);
CREATE INDEX links_to_note_link_strength IF NOT EXISTS
FOR ()-[r:LINKS_TO_NOTE]-()
ON (r.link_strength);
