// ============================================================================
// ACADEMIC NOTE-TAKING GRAPHRAG SYSTEM - RELATIONSHIPS
// ============================================================================
// Neo4j Version: 5.26 (2025.09.0-community-bullseye)
// Purpose: Define all relationships between nodes with properties
// Pattern: MERGE nodes, then MERGE relationships with ON CREATE/ON MATCH SET
// Source: Research from Stanford/Harvard structures, GraphRAG best practices
// ============================================================================

// ============================================================================
// PROFILE RELATIONSHIPS
// ============================================================================

// Profile -> Course (ENROLLED_IN)
// Tracks student course enrollments with status and dates
MATCH (p:Profile {student_id: $student_id})
MATCH (c:Course {course_id: $course_id})
MERGE (p)-[r:ENROLLED_IN]->(c)
ON CREATE SET
    r.enrollment_date = datetime($enrollment_date),
    r.status = $status,  // 'Active', 'Completed', 'Dropped', 'Withdrawn'
    r.final_grade = $final_grade,  // Nullable float
    r.letter_grade = $letter_grade,  // Nullable string ('A', 'B+', etc.)
    r.grading_basis = $grading_basis,  // 'Letter', 'S/NC'
    r.created_at = datetime(),
    r.updated_at = datetime()
ON MATCH SET
    r.status = $status,
    r.final_grade = $final_grade,
    r.letter_grade = $letter_grade,
    r.grading_basis = $grading_basis,
    r.updated_at = datetime()
RETURN p, r, c;

// Example parameters:
// {
//   "student_id": "STU-2024-001234",
//   "course_id": "CS230-Fall2024",
//   "enrollment_date": "2024-09-15T10:00:00",
//   "status": "Active",
//   "final_grade": null,
//   "letter_grade": null,
//   "grading_basis": "Letter"
// }


// Profile -> Study_Todo (HAS_TODO)
// Links todos to student profiles
MATCH (p:Profile {student_id: $student_id})
MATCH (t:Study_Todo {todo_id: $todo_id})
MERGE (p)-[r:HAS_TODO]->(t)
ON CREATE SET
    r.created_at = datetime()
RETURN p, r, t;


// Profile -> Challenge_Area (FACES_CHALLENGE)
// Tracks student challenges with detection metadata
MATCH (p:Profile {student_id: $student_id})
MATCH (ca:Challenge_Area {challenge_id: $challenge_id})
MERGE (p)-[r:FACES_CHALLENGE]->(ca)
ON CREATE SET
    r.first_detected = datetime($first_detected),
    r.current_severity = $current_severity,  // Can change over time
    r.intervention_count = $intervention_count,  // Number of interventions attempted
    r.created_at = datetime(),
    r.updated_at = datetime()
ON MATCH SET
    r.current_severity = $current_severity,
    r.intervention_count = $intervention_count,
    r.updated_at = datetime()
RETURN p, r, ca;

// Example parameters:
// {
//   "student_id": "STU-2024-001234",
//   "challenge_id": "CHALLENGE-CS230-Integration",
//   "first_detected": "2024-10-15T00:00:00",
//   "current_severity": "Moderate",
//   "intervention_count": 3
// }


// Profile -> Note (CREATED_NOTE)
// Tracks note authorship
MATCH (p:Profile {student_id: $student_id})
MATCH (n:Note {note_id: $note_id})
MERGE (p)-[r:CREATED_NOTE]->(n)
ON CREATE SET
    r.created_at = datetime()
RETURN p, r, n;


// ============================================================================
// COURSE RELATIONSHIPS
// ============================================================================

// Course -> Assignment (HAS_ASSIGNMENT)
// Links assignments to courses
MATCH (c:Course {course_id: $course_id})
MATCH (a:Assignment {assignment_id: $assignment_id})
MERGE (c)-[r:HAS_ASSIGNMENT]->(a)
ON CREATE SET
    r.sequence_number = $sequence_number,  // Order in course
    r.created_at = datetime()
RETURN c, r, a;

// Example parameters:
// {
//   "course_id": "CS230-Fall2024",
//   "assignment_id": "CS230-Fall2024-PS3",
//   "sequence_number": 3
// }


// Course -> Exam (HAS_EXAM)
// Links exams to courses
MATCH (c:Course {course_id: $course_id})
MATCH (e:Exam {exam_id: $exam_id})
MERGE (c)-[r:HAS_EXAM]->(e)
ON CREATE SET
    r.created_at = datetime()
RETURN c, r, e;


// Course -> Quiz (HAS_QUIZ)
// Links quizzes to courses
MATCH (c:Course {course_id: $course_id})
MATCH (q:Quiz {quiz_id: $quiz_id})
MERGE (c)-[r:HAS_QUIZ]->(q)
ON CREATE SET
    r.created_at = datetime()
RETURN c, r, q;


// Course -> Lab_Session (HAS_LAB)
// Links lab sessions to courses
MATCH (c:Course {course_id: $course_id})
MATCH (l:Lab_Session {lab_id: $lab_id})
MERGE (c)-[r:HAS_LAB]->(l)
ON CREATE SET
    r.created_at = datetime()
RETURN c, r, l;


// Course -> Class_Schedule (SCHEDULED_AS)
// Links courses to their schedules (typically one-to-one, but can have multiple sections)
MATCH (c:Course {course_id: $course_id})
MATCH (cs:Class_Schedule {schedule_id: $schedule_id})
MERGE (c)-[r:SCHEDULED_AS]->(cs)
ON CREATE SET
    r.created_at = datetime()
RETURN c, r, cs;


// Course -> Lecture (INCLUDES_LECTURE)
// Links lectures to courses
MATCH (c:Course {course_id: $course_id})
MATCH (lec:Lecture {lecture_id: $lecture_id})
MERGE (c)-[r:INCLUDES_LECTURE]->(lec)
ON CREATE SET
    r.created_at = datetime()
RETURN c, r, lec;


// Course -> Topic (COVERS_TOPIC)
// Links courses to topics they cover (many-to-many)
MATCH (c:Course {course_id: $course_id})
MATCH (t:Topic {topic_id: $topic_id})
MERGE (c)-[r:COVERS_TOPIC]->(t)
ON CREATE SET
    r.coverage_depth = $coverage_depth,  // 'Brief', 'Moderate', 'Comprehensive'
    r.week_introduced = $week_introduced,  // Integer: which week topic appears
    r.created_at = datetime()
ON MATCH SET
    r.coverage_depth = $coverage_depth,
    r.week_introduced = $week_introduced,
    r.updated_at = datetime()
RETURN c, r, t;

// Example parameters:
// {
//   "course_id": "CS230-Fall2024",
//   "topic_id": "TOPIC-CNN",
//   "coverage_depth": "Comprehensive",
//   "week_introduced": 4
// }


// ============================================================================
// ASSIGNMENT RELATIONSHIPS
// ============================================================================

// Assignment -> Study_Todo (TRIGGERED_TODO)
// AI-generated todos from assignments
MATCH (a:Assignment {assignment_id: $assignment_id})
MATCH (t:Study_Todo {todo_id: $todo_id})
MERGE (a)-[r:TRIGGERED_TODO]->(t)
ON CREATE SET
    r.auto_generated = $auto_generated,  // Boolean
    r.trigger_type = $trigger_type,  // 'Due Date Approaching', 'Assignment Created', 'Grade Posted'
    r.created_at = datetime()
RETURN a, r, t;

// Example parameters:
// {
//   "assignment_id": "CS230-Fall2024-PS3",
//   "todo_id": "TODO-2024-10-001",
//   "auto_generated": true,
//   "trigger_type": "Due Date Approaching"
// }


// Assignment -> Note (RELATED_TO_NOTE)
// Links assignments to related notes (many-to-many)
MATCH (a:Assignment {assignment_id: $assignment_id})
MATCH (n:Note {note_id: $note_id})
MERGE (a)-[r:RELATED_TO_NOTE]->(n)
ON CREATE SET
    r.relevance_score = $relevance_score,  // Float 0-1: how relevant the note is
    r.linked_by = $linked_by,  // 'User', 'AI'
    r.created_at = datetime()
ON MATCH SET
    r.relevance_score = $relevance_score,
    r.updated_at = datetime()
RETURN a, r, n;

// Example parameters:
// {
//   "assignment_id": "CS230-Fall2024-PS3",
//   "note_id": "NOTE-2024-10-20-001",
//   "relevance_score": 0.92,
//   "linked_by": "AI"
// }


// ============================================================================
// EXAM RELATIONSHIPS
// ============================================================================

// Exam -> Topic (COVERS_TOPIC)
// Links exams to topics they assess (many-to-many)
MATCH (e:Exam {exam_id: $exam_id})
MATCH (t:Topic {topic_id: $topic_id})
MERGE (e)-[r:COVERS_TOPIC]->(t)
ON CREATE SET
    r.weight = $weight,  // Float: percentage of exam devoted to this topic
    r.difficulty = $difficulty,  // 'Easy', 'Medium', 'Hard'
    r.created_at = datetime()
ON MATCH SET
    r.weight = $weight,
    r.difficulty = $difficulty,
    r.updated_at = datetime()
RETURN e, r, t;

// Example parameters:
// {
//   "exam_id": "CS230-Fall2024-Midterm",
//   "topic_id": "TOPIC-CNN",
//   "weight": 0.30,
//   "difficulty": "Medium"
// }


// Exam -> Challenge_Area (REVEALED_CHALLENGE)
// Performance-based challenge detection from exams
MATCH (e:Exam {exam_id: $exam_id})
MATCH (ca:Challenge_Area {challenge_id: $challenge_id})
MERGE (e)-[r:REVEALED_CHALLENGE]->(ca)
ON CREATE SET
    r.detection_date = datetime($detection_date),
    r.score = $score,  // Float: student's score on challenged topics
    r.threshold = $threshold,  // Float: threshold below which challenge is flagged
    r.created_at = datetime()
RETURN e, r, ca;

// Example parameters:
// {
//   "exam_id": "CS230-Fall2024-Midterm",
//   "challenge_id": "CHALLENGE-CS230-Integration",
//   "detection_date": "2024-11-10T00:00:00",
//   "score": 55.0,
//   "threshold": 70.0
// }


// ============================================================================
// QUIZ RELATIONSHIPS
// ============================================================================

// Quiz -> Topic (COVERS_TOPIC)
// Links quizzes to topics (many-to-many, granular assessment)
MATCH (q:Quiz {quiz_id: $quiz_id})
MATCH (t:Topic {topic_id: $topic_id})
MERGE (q)-[r:COVERS_TOPIC]->(t)
ON CREATE SET
    r.question_count = $question_count,  // Number of questions on this topic
    r.created_at = datetime()
ON MATCH SET
    r.question_count = $question_count,
    r.updated_at = datetime()
RETURN q, r, t;

// Example parameters:
// {
//   "quiz_id": "CS230-Fall2024-Quiz5",
//   "topic_id": "TOPIC-RNN",
//   "question_count": 5
// }


// Quiz -> Challenge_Area (REVEALED_CHALLENGE)
// Early challenge detection from quiz patterns
MATCH (q:Quiz {quiz_id: $quiz_id})
MATCH (ca:Challenge_Area {challenge_id: $challenge_id})
MERGE (q)-[r:REVEALED_CHALLENGE]->(ca)
ON CREATE SET
    r.detection_date = datetime($detection_date),
    r.score = $score,
    r.threshold = $threshold,
    r.created_at = datetime()
RETURN q, r, ca;


// ============================================================================
// LAB_SESSION RELATIONSHIPS
// ============================================================================

// Lab_Session -> Topic (APPLIES_TOPIC)
// Links lab sessions to topics (theory-practice bridge)
MATCH (l:Lab_Session {lab_id: $lab_id})
MATCH (t:Topic {topic_id: $topic_id})
MERGE (l)-[r:APPLIES_TOPIC]->(t)
ON CREATE SET
    r.application_type = $application_type,  // 'Hands-on Practice', 'Verification', 'Exploration'
    r.created_at = datetime()
ON MATCH SET
    r.application_type = $application_type,
    r.updated_at = datetime()
RETURN l, r, t;

// Example parameters:
// {
//   "lab_id": "CHEM31A-Fall2024-Lab3",
//   "topic_id": "TOPIC-AcidBase",
//   "application_type": "Hands-on Practice"
// }


// Lab_Session -> Note (DOCUMENTED_IN_NOTE)
// Lab reports and observations
MATCH (l:Lab_Session {lab_id: $lab_id})
MATCH (n:Note {note_id: $note_id})
MERGE (l)-[r:DOCUMENTED_IN_NOTE]->(n)
ON CREATE SET
    r.documentation_type = $documentation_type,  // 'Pre-Lab', 'Lab Report', 'Observations'
    r.created_at = datetime()
RETURN l, r, n;

// Example parameters:
// {
//   "lab_id": "CHEM31A-Fall2024-Lab3",
//   "note_id": "NOTE-2024-10-18-Lab3",
//   "documentation_type": "Lab Report"
// }


// ============================================================================
// STUDY_TODO RELATIONSHIPS
// ============================================================================

// Study_Todo -> Challenge_Area (ADDRESSES_CHALLENGE)
// Targeted intervention todos
MATCH (t:Study_Todo {todo_id: $todo_id})
MATCH (ca:Challenge_Area {challenge_id: $challenge_id})
MERGE (t)-[r:ADDRESSES_CHALLENGE]->(ca)
ON CREATE SET
    r.intervention_strategy = $intervention_strategy,  // 'Practice', 'Review', 'Tutoring', 'Office Hours'
    r.created_at = datetime()
RETURN t, r, ca;

// Example parameters:
// {
//   "todo_id": "TODO-2024-10-001",
//   "challenge_id": "CHALLENGE-CS230-Integration",
//   "intervention_strategy": "Practice"
// }


// Study_Todo -> Note (REFERENCES_NOTE)
// Todos reference specific notes for study
MATCH (t:Study_Todo {todo_id: $todo_id})
MATCH (n:Note {note_id: $note_id})
MERGE (t)-[r:REFERENCES_NOTE]->(n)
ON CREATE SET
    r.reference_type = $reference_type,  // 'Primary Resource', 'Supplementary', 'Example'
    r.created_at = datetime()
RETURN t, r, n;

// Example parameters:
// {
//   "todo_id": "TODO-2024-10-001",
//   "note_id": "NOTE-2024-10-20-001",
//   "reference_type": "Primary Resource"
// }


// Study_Todo -> Exam (PREPARES_FOR_EXAM)
// Exam preparation todos
MATCH (t:Study_Todo {todo_id: $todo_id})
MATCH (e:Exam {exam_id: $exam_id})
MERGE (t)-[r:PREPARES_FOR_EXAM]->(e)
ON CREATE SET
    r.preparation_phase = $preparation_phase,  // 'Early Review', 'Intensive Study', 'Final Review'
    r.days_before_exam = $days_before_exam,  // Integer
    r.created_at = datetime()
RETURN t, r, e;

// Example parameters:
// {
//   "todo_id": "TODO-2024-10-001",
//   "exam_id": "CS230-Fall2024-Midterm",
//   "preparation_phase": "Intensive Study",
//   "days_before_exam": 7
// }


// ============================================================================
// CHALLENGE_AREA RELATIONSHIPS
// ============================================================================

// Challenge_Area -> Course (IN_COURSE)
// Links challenges to specific courses
MATCH (ca:Challenge_Area {challenge_id: $challenge_id})
MATCH (c:Course {course_id: $course_id})
MERGE (ca)-[r:IN_COURSE]->(c)
ON CREATE SET
    r.created_at = datetime()
RETURN ca, r, c;


// Challenge_Area -> Topic (RELATED_TO_TOPIC)
// Links challenges to specific topics (many-to-many for root cause analysis)
MATCH (ca:Challenge_Area {challenge_id: $challenge_id})
MATCH (t:Topic {topic_id: $topic_id})
MERGE (ca)-[r:RELATED_TO_TOPIC]->(t)
ON CREATE SET
    r.relevance_strength = $relevance_strength,  // Float 0-1: how strongly related
    r.is_root_cause = $is_root_cause,  // Boolean: identified as root vs symptom
    r.created_at = datetime()
ON MATCH SET
    r.relevance_strength = $relevance_strength,
    r.is_root_cause = $is_root_cause,
    r.updated_at = datetime()
RETURN ca, r, t;

// Example parameters:
// {
//   "challenge_id": "CHALLENGE-CS230-Integration",
//   "topic_id": "TOPIC-Integration",
//   "relevance_strength": 0.95,
//   "is_root_cause": true
// }


// Challenge_Area -> Note (IMPROVED_BY_NOTE)
// Success tracking: which notes helped overcome challenges
MATCH (ca:Challenge_Area {challenge_id: $challenge_id})
MATCH (n:Note {note_id: $note_id})
MERGE (ca)-[r:IMPROVED_BY_NOTE]->(n)
ON CREATE SET
    r.improvement_contribution = $improvement_contribution,  // Float 0-1
    r.student_rating = $student_rating,  // Integer 1-5: how helpful
    r.created_at = datetime()
ON MATCH SET
    r.improvement_contribution = $improvement_contribution,
    r.student_rating = $student_rating,
    r.updated_at = datetime()
RETURN ca, r, n;

// Example parameters:
// {
//   "challenge_id": "CHALLENGE-CS230-Integration",
//   "note_id": "NOTE-2024-10-20-001",
//   "improvement_contribution": 0.75,
//   "student_rating": 5
// }


// ============================================================================
// LECTURE RELATIONSHIPS
// ============================================================================

// Lecture -> Topic (COVERED_TOPIC)
// Topics covered in each lecture (many-to-many)
MATCH (lec:Lecture {lecture_id: $lecture_id})
MATCH (t:Topic {topic_id: $topic_id})
MERGE (lec)-[r:COVERED_TOPIC]->(t)
ON CREATE SET
    r.coverage_duration_minutes = $coverage_duration_minutes,  // Time spent on topic
    r.depth = $depth,  // 'Overview', 'Detailed', 'Advanced'
    r.created_at = datetime()
ON MATCH SET
    r.coverage_duration_minutes = $coverage_duration_minutes,
    r.depth = $depth,
    r.updated_at = datetime()
RETURN lec, r, t;

// Example parameters:
// {
//   "lecture_id": "CS230-Fall2024-LEC8",
//   "topic_id": "TOPIC-CNN",
//   "coverage_duration_minutes": 45,
//   "depth": "Detailed"
// }


// Lecture -> Note (HAS_NOTE)
// Links lectures to notes taken during/about them (one-to-many)
MATCH (lec:Lecture {lecture_id: $lecture_id})
MATCH (n:Note {note_id: $note_id})
MERGE (lec)-[r:HAS_NOTE]->(n)
ON CREATE SET
    r.note_completeness = $note_completeness,  // Float 0-1: how complete the notes are
    r.created_at = datetime()
ON MATCH SET
    r.note_completeness = $note_completeness,
    r.updated_at = datetime()
RETURN lec, r, n;

// Example parameters:
// {
//   "lecture_id": "CS230-Fall2024-LEC8",
//   "note_id": "NOTE-2024-10-20-001",
//   "note_completeness": 0.95
// }


// ============================================================================
// NOTE RELATIONSHIPS
// ============================================================================

// Note -> Topic (TAGGED_WITH_TOPIC)
// Semantic organization of notes by topics (many-to-many)
MATCH (n:Note {note_id: $note_id})
MATCH (t:Topic {topic_id: $topic_id})
MERGE (n)-[r:TAGGED_WITH_TOPIC]->(t)
ON CREATE SET
    r.tag_source = $tag_source,  // 'Manual', 'AI-Extracted', 'Inherited'
    r.confidence = $confidence,  // Float 0-1: AI confidence in tagging
    r.created_at = datetime()
ON MATCH SET
    r.tag_source = $tag_source,
    r.confidence = $confidence,
    r.updated_at = datetime()
RETURN n, r, t;

// Example parameters:
// {
//   "note_id": "NOTE-2024-10-20-001",
//   "topic_id": "TOPIC-CNN",
//   "tag_source": "AI-Extracted",
//   "confidence": 0.95
// }


// Note -> Note (LINKS_TO_NOTE)
// Bidirectional linking (Roam/Obsidian style) - many-to-many
MATCH (n1:Note {note_id: $note_id_1})
MATCH (n2:Note {note_id: $note_id_2})
MERGE (n1)-[r:LINKS_TO_NOTE]->(n2)
ON CREATE SET
    r.link_type = $link_type,  // 'Reference', 'Elaboration', 'Contradiction', 'Example'
    r.link_strength = $link_strength,  // Float 0-1: relationship strength
    r.context = $context,  // Text snippet showing link context
    r.created_at = datetime()
ON MATCH SET
    r.link_type = $link_type,
    r.link_strength = $link_strength,
    r.context = $context,
    r.updated_at = datetime()
RETURN n1, r, n2;

// Example parameters:
// {
//   "note_id_1": "NOTE-2024-10-20-001",
//   "note_id_2": "NOTE-2024-10-15-003",
//   "link_type": "Reference",
//   "link_strength": 0.85,
//   "context": "See [[NOTE-2024-10-15-003]] for foundation on neural networks"
// }


// Note -> Resource (CITES_RESOURCE)
// Source attribution for notes (many-to-many)
MATCH (n:Note {note_id: $note_id})
MATCH (r:Resource {resource_id: $resource_id})
MERGE (n)-[rel:CITES_RESOURCE]->(r)
ON CREATE SET
    rel.citation_type = $citation_type,  // 'Direct Quote', 'Paraphrase', 'Summary', 'Reference'
    rel.page_numbers = $page_numbers,  // String: "45-47" or array
    rel.created_at = datetime()
ON MATCH SET
    rel.citation_type = $citation_type,
    rel.page_numbers = $page_numbers,
    rel.updated_at = datetime()
RETURN n, rel, r;

// Example parameters:
// {
//   "note_id": "NOTE-2024-10-20-001",
//   "resource_id": "RES-DeepLearningBook",
//   "citation_type": "Paraphrase",
//   "page_numbers": "326-330"
// }


// ============================================================================
// TOPIC RELATIONSHIPS
// ============================================================================

// Topic -> Topic (PREREQUISITE_FOR)
// Hierarchical prerequisite relationships (many-to-many, directed graph)
MATCH (t1:Topic {topic_id: $prerequisite_topic_id})
MATCH (t2:Topic {topic_id: $target_topic_id})
MERGE (t1)-[r:PREREQUISITE_FOR]->(t2)
ON CREATE SET
    r.strength = $strength,  // 'Essential', 'Recommended', 'Optional'
    r.estimated_gap_hours = $estimated_gap_hours,  // Study hours needed if missing
    r.created_at = datetime()
ON MATCH SET
    r.strength = $strength,
    r.estimated_gap_hours = $estimated_gap_hours,
    r.updated_at = datetime()
RETURN t1, r, t2;

// Example parameters:
// {
//   "prerequisite_topic_id": "TOPIC-NeuralNetworks",
//   "target_topic_id": "TOPIC-CNN",
//   "strength": "Essential",
//   "estimated_gap_hours": 15
// }


// Topic -> Resource (COVERED_IN_RESOURCE)
// Links topics to learning resources (many-to-many)
MATCH (t:Topic {topic_id: $topic_id})
MATCH (r:Resource {resource_id: $resource_id})
MERGE (t)-[rel:COVERED_IN_RESOURCE]->(r)
ON CREATE SET
    rel.chapter_section = $chapter_section,  // String: "Chapter 9.1-9.3"
    rel.coverage_quality = $coverage_quality,  // Float 0-1: how well resource covers topic
    rel.difficulty_match = $difficulty_match,  // 'Easier', 'Appropriate', 'Advanced'
    rel.created_at = datetime()
ON MATCH SET
    rel.chapter_section = $chapter_section,
    rel.coverage_quality = $coverage_quality,
    rel.difficulty_match = $difficulty_match,
    rel.updated_at = datetime()
RETURN t, rel, r;

// Example parameters:
// {
//   "topic_id": "TOPIC-CNN",
//   "resource_id": "RES-DeepLearningBook",
//   "chapter_section": "Chapter 9",
//   "coverage_quality": 0.95,
//   "difficulty_match": "Appropriate"
// }


// ============================================================================
// ACADEMIC ENTITY TOPIC RELATIONSHIPS (TOPIC-BASED LINKING)
// ============================================================================

// LectureNote -> Topic (COVERS_TOPIC)
// Links lecture notes to topics they cover via TopicExtractor service
// NOTE: These relationships are typically created automatically by TopicExtractor.extract_and_link()
// when processing LectureNotes with tagged_topics field.
MATCH (ln:LectureNote {lecture_note_id: $lecture_note_id})
MATCH (t:Topic {topic_id: $topic_id})
MERGE (ln)-[r:COVERS_TOPIC]->(t)
ON CREATE SET
    r.created_at = datetime($created_at)
RETURN ln, r, t;

// Example parameters:
// {
//   "lecture_note_id": "LN-CS101-S2025001-001",
//   "topic_id": "TOPIC-loops",
//   "created_at": "2025-01-15T10:30:00"
// }


// Assignment -> Topic (COVERS_TOPIC)
// Links assignments to topics they assess
// NOTE: Created automatically by TopicExtractor when related_topics field is present
MATCH (a:Assignment {assignment_id: $assignment_id})
MATCH (t:Topic {topic_id: $topic_id})
MERGE (a)-[r:COVERS_TOPIC]->(t)
ON CREATE SET
    r.coverage_percentage = $coverage_percentage,  // Nullable: how much of assignment focuses on this topic
    r.created_at = datetime($created_at)
ON MATCH SET
    r.coverage_percentage = $coverage_percentage,
    r.updated_at = datetime()
RETURN a, r, t;

// Example parameters:
// {
//   "assignment_id": "A-CS101-S2025-001",
//   "topic_id": "TOPIC-loops",
//   "coverage_percentage": 0.60,
//   "created_at": "2025-01-15T10:30:00"
// }


// Exam -> Topic (COVERS_TOPIC)
// Already defined above (lines 241-262), but included here for completeness
// NOTE: Uses 'weight' and 'difficulty' properties instead of 'coverage_percentage'


// Quiz -> Topic (COVERS_TOPIC)
// Already defined above (lines 291-309), but included here for completeness
// NOTE: Uses 'question_count' property


// ============================================================================
// TOPIC-BASED RETRIEVAL QUERIES
// ============================================================================
// Example: Find relevant lecture notes for an assignment
//
// MATCH (a:Assignment {assignment_id: 'A-CS101-S2025-001'})
// MATCH (a)-[:COVERS_TOPIC]->(t:Topic)<-[:COVERS_TOPIC]-(ln:LectureNote)
// RETURN ln.title, ln.summary, collect(DISTINCT t.name) as shared_topics
// ORDER BY size(shared_topics) DESC
//
// Example: Find all entities linked to a specific topic
//
// MATCH (t:Topic {normalized_name: 'machine-learning'})
// OPTIONAL MATCH (t)<-[:COVERS_TOPIC]-(ln:LectureNote)
// OPTIONAL MATCH (t)<-[:COVERS_TOPIC]-(a:Assignment)
// OPTIONAL MATCH (t)<-[:COVERS_TOPIC]-(e:Exam)
// OPTIONAL MATCH (t)<-[:COVERS_TOPIC]-(q:Quiz)
// RETURN t.name,
//        collect(DISTINCT ln.title) as lecture_notes,
//        collect(DISTINCT a.title) as assignments,
//        collect(DISTINCT e.title) as exams,
//        collect(DISTINCT q.title) as quizzes
// ============================================================================


// ============================================================================
// CHUNK RELATIONSHIPS
// ============================================================================

// Chunk -> LectureNote (PART_OF)
// Links chunks to their parent document for context retrieval
// NOTE: Created automatically by ChunkGenerator.generate_chunks()
MATCH (c:Chunk {chunk_id: $chunk_id})
MATCH (ln:LectureNote {lecture_note_id: $lecture_note_id})
MERGE (c)-[r:PART_OF]->(ln)
ON CREATE SET
    r.created_at = datetime($created_at)
RETURN c, r, ln;

// Example parameters:
// {
//   "chunk_id": "CHUNK-LN-CS101-S2025001-001-003",
//   "lecture_note_id": "LN-CS101-S2025001-001",
//   "created_at": "2025-01-15T10:30:00"
// }


// Chunk -> Chunk (NEXT_CHUNK)
// Sequential ordering of chunks within a document
// NOTE: Enables reconstructing document order and retrieving surrounding context
MATCH (c1:Chunk {chunk_id: $chunk_id})
MATCH (c2:Chunk {chunk_id: $next_chunk_id})
MERGE (c1)-[r:NEXT_CHUNK]->(c2)
ON CREATE SET
    r.created_at = datetime($created_at)
RETURN c1, r, c2;

// Example parameters:
// {
//   "chunk_id": "CHUNK-LN-CS101-S2025001-001-003",
//   "next_chunk_id": "CHUNK-LN-CS101-S2025001-001-004",
//   "created_at": "2025-01-15T10:30:00"
// }


// Chunk -> Topic (COVERS_TOPIC)
// Links chunks to topics they discuss (inherited from parent or chunk-specific)
// NOTE: Can be inherited from parent LectureNote or extracted specifically for chunk
MATCH (c:Chunk {chunk_id: $chunk_id})
MATCH (t:Topic {topic_id: $topic_id})
MERGE (c)-[r:COVERS_TOPIC]->(t)
ON CREATE SET
    r.relevance_score = $relevance_score,  // 0.0-1.0: how relevant this topic is to chunk
    r.inherited = $inherited,  // Boolean: true if inherited from parent, false if chunk-specific
    r.created_at = datetime($created_at)
ON MATCH SET
    r.relevance_score = $relevance_score,
    r.inherited = $inherited,
    r.updated_at = datetime()
RETURN c, r, t;

// Example parameters:
// {
//   "chunk_id": "CHUNK-LN-CS101-S2025001-001-003",
//   "topic_id": "TOPIC-variables",
//   "relevance_score": 0.95,
//   "inherited": false,
//   "created_at": "2025-01-15T10:30:00"
// }


// ============================================================================
// CHUNK-BASED RETRIEVAL QUERIES
// ============================================================================
// Example: Find specific chunks about a topic with parent context
//
// MATCH (c:Chunk)-[:COVERS_TOPIC]->(t:Topic {normalized_name: 'variables'})
// MATCH (c)-[:PART_OF]->(ln:LectureNote)
// OPTIONAL MATCH (c)-[:NEXT_CHUNK]->(next:Chunk)
// OPTIONAL MATCH (prev:Chunk)-[:NEXT_CHUNK]->(c)
// RETURN c.content AS chunk,
//        c.heading AS section,
//        c.chunk_index AS position,
//        ln.title AS parent_title,
//        ln.lecture_note_id AS parent_id,
//        prev.content AS previous_chunk,
//        next.content AS next_chunk
// ORDER BY c.chunk_index
//
// Example: Hybrid chunk + document retrieval
//
// CALL db.index.vector.queryNodes('chunk_content_vector', $embedding, 10)
// YIELD node AS chunk, score
// MATCH (chunk)-[:PART_OF]->(ln:LectureNote)
// MATCH (ln)-[:BELONGS_TO]->(course:Course)
// OPTIONAL MATCH (chunk)-[:COVERS_TOPIC]->(topic:Topic)
// RETURN chunk.content,
//        chunk.heading,
//        chunk.chunk_index,
//        ln.title AS note_title,
//        course.title AS course_title,
//        collect(DISTINCT topic.name) AS topics,
//        score
// ORDER BY score DESC
// LIMIT 5
// ============================================================================


// ============================================================================
// BATCH RELATIONSHIP CREATION
// ============================================================================
// For bulk operations, use UNWIND with CALL { ... } IN TRANSACTIONS
//
// Example:
// UNWIND $relationships AS rel
// CALL {
//   WITH rel
//   MATCH (p:Profile {student_id: rel.student_id})
//   MATCH (c:Course {course_id: rel.course_id})
//   MERGE (p)-[r:ENROLLED_IN]->(c)
//   ON CREATE SET r.enrollment_date = datetime(rel.enrollment_date), ...
//   ON MATCH SET r.updated_at = datetime()
// } IN TRANSACTIONS OF 1000 ROWS
// ============================================================================
