// ============================================================================
// ACADEMIC NOTE-TAKING GRAPHRAG SYSTEM - NODE DEFINITIONS
// ============================================================================
// Neo4j Version: 5.26 (2025.09.0-community-bullseye)
// Purpose: Define node creation patterns with all researched properties
// Pattern: MERGE ... ON CREATE SET ... ON MATCH SET for idempotency
// ============================================================================

// ============================================================================
// PROFILE NODE
// ============================================================================
// Represents a student's academic profile
// Source: Stanford/Harvard transcript systems, academic requirements
// ============================================================================

MERGE (p:Profile {student_id: $student_id})
ON CREATE SET
    p.first_name = $first_name,
    p.last_name = $last_name,
    p.email = $email,
    p.major = $major,
    p.minor = $minor,  // Array of strings
    p.year = $year,  // 'Freshman', 'Sophomore', 'Junior', 'Senior'
    p.cumulative_gpa = $cumulative_gpa,  // Float
    p.total_credits_earned = $total_credits_earned,  // Integer
    p.degree_program = $degree_program,  // 'BA', 'BS'
    p.enrollment_date = datetime($enrollment_date),
    p.expected_graduation = date($expected_graduation),
    p.academic_standing = $academic_standing,  // 'Good Standing', 'Probation'
    p.preferences = $preferences,  // Map: {study_style, notification_settings, ai_assistance_level}
    p.timezone = $timezone,
    p.created_at = datetime(),
    p.updated_at = datetime()
ON MATCH SET
    p.first_name = $first_name,
    p.last_name = $last_name,
    p.email = $email,
    p.major = $major,
    p.minor = $minor,
    p.year = $year,
    p.cumulative_gpa = $cumulative_gpa,
    p.total_credits_earned = $total_credits_earned,
    p.degree_program = $degree_program,
    p.enrollment_date = datetime($enrollment_date),
    p.expected_graduation = date($expected_graduation),
    p.academic_standing = $academic_standing,
    p.preferences = $preferences,
    p.timezone = $timezone,
    p.updated_at = datetime()
RETURN p;

// Example parameters:
// {
//   "student_id": "STU-2024-001234",
//   "first_name": "Alice",
//   "last_name": "Chen",
//   "email": "alice.chen@stanford.edu",
//   "major": "Computer Science",
//   "minor": ["Mathematics", "Cognitive Science"],
//   "year": "Junior",
//   "cumulative_gpa": 3.87,
//   "total_credits_earned": 96,
//   "degree_program": "BS",
//   "enrollment_date": "2022-09-15T00:00:00",
//   "expected_graduation": "2026-06-15",
//   "academic_standing": "Good Standing",
//   "preferences": {
//     "study_style": "visual",
//     "notification_settings": {"email": true, "push": true, "quiet_hours": "22:00-08:00"},
//     "ai_assistance_level": "high"
//   },
//   "timezone": "America/Los_Angeles"
// }


// ============================================================================
// COURSE NODE
// ============================================================================
// Represents an academic course
// Source: Stanford ExploreCourses, Harvard my.harvard catalog
// ============================================================================

MERGE (c:Course {course_id: $course_id})
ON CREATE SET
    c.title = $title,
    c.code = $code,  // Department code (e.g., 'CS')
    c.number = $number,  // Course number (e.g., '230')
    c.term = $term,  // 'Fall 2024', 'Spring 2025'
    c.credits = $credits,  // Integer (typically 3-5)
    c.description = $description,
    c.instructor_name = $instructor_name,
    c.instructor_email = $instructor_email,
    c.component_type = $component_type,  // Array: ['LEC', 'LAB', 'DIS']
    c.prerequisites = $prerequisites,  // Array of course_ids
    c.grading_options = $grading_options,  // Array: ['Letter', 'S/NC']
    c.syllabus_url = $syllabus_url,
    c.learning_objectives = $learning_objectives,  // Array of strings
    c.final_exam_date = datetime($final_exam_date),
    c.created_at = datetime(),
    c.updated_at = datetime()
ON MATCH SET
    c.title = $title,
    c.code = $code,
    c.number = $number,
    c.term = $term,
    c.credits = $credits,
    c.description = $description,
    c.instructor_name = $instructor_name,
    c.instructor_email = $instructor_email,
    c.component_type = $component_type,
    c.prerequisites = $prerequisites,
    c.grading_options = $grading_options,
    c.syllabus_url = $syllabus_url,
    c.learning_objectives = $learning_objectives,
    c.final_exam_date = datetime($final_exam_date),
    c.updated_at = datetime()
RETURN c;

// Example parameters:
// {
//   "course_id": "CS230-Fall2024",
//   "title": "Deep Learning",
//   "code": "CS",
//   "number": "230",
//   "term": "Fall 2024",
//   "credits": 4,
//   "description": "Introduction to deep learning with focus on neural networks, CNNs, RNNs, and transformers.",
//   "instructor_name": "Andrew Ng",
//   "instructor_email": "ang@cs.stanford.edu",
//   "component_type": ["LEC", "DIS"],
//   "prerequisites": ["CS229-Spring2024", "MATH51-Winter2024"],
//   "grading_options": ["Letter", "S/NC"],
//   "syllabus_url": "https://cs230.stanford.edu/syllabus/",
//   "learning_objectives": [
//     "Understand neural network architectures",
//     "Implement CNNs for computer vision",
//     "Build sequence models with RNNs and transformers"
//   ],
//   "final_exam_date": "2024-12-13T18:00:00"
// }


// ============================================================================
// ASSIGNMENT NODE
// ============================================================================
// Represents course assignments
// Source: CS230/CS50 syllabi, Stanford syllabus templates
// ============================================================================

MERGE (a:Assignment {assignment_id: $assignment_id})
ON CREATE SET
    a.title = $title,
    a.type = $type,  // 'Problem Set', 'Essay', 'Project', 'Programming'
    a.description = $description,
    a.due_date = datetime($due_date),
    a.points_possible = $points_possible,
    a.points_earned = $points_earned,  // Nullable
    a.percentage_grade = $percentage_grade,  // Nullable float
    a.submission_status = $submission_status,  // 'Not Started', 'In Progress', 'Submitted', 'Graded'
    a.submission_url = $submission_url,  // Nullable
    a.instructions_url = $instructions_url,
    a.weight = $weight,  // Float: contribution to course grade
    a.estimated_hours = $estimated_hours,
    a.late_penalty = $late_penalty,
    a.rubric = $rubric,  // Array of objects: [{criterion, points}]
    a.created_at = datetime(),
    a.updated_at = datetime()
ON MATCH SET
    a.title = $title,
    a.type = $type,
    a.description = $description,
    a.due_date = datetime($due_date),
    a.points_possible = $points_possible,
    a.points_earned = $points_earned,
    a.percentage_grade = $percentage_grade,
    a.submission_status = $submission_status,
    a.submission_url = $submission_url,
    a.instructions_url = $instructions_url,
    a.weight = $weight,
    a.estimated_hours = $estimated_hours,
    a.late_penalty = $late_penalty,
    a.rubric = $rubric,
    a.updated_at = datetime()
RETURN a;

// Example parameters:
// {
//   "assignment_id": "CS230-Fall2024-PS3",
//   "title": "Programming Assignment 3: Neural Style Transfer",
//   "type": "Programming",
//   "description": "Implement neural style transfer using pre-trained VGG networks.",
//   "due_date": "2024-11-05T23:00:00",
//   "points_possible": 100,
//   "points_earned": 95,
//   "percentage_grade": 95.0,
//   "submission_status": "Graded",
//   "submission_url": "https://coursera.org/submissions/abc123",
//   "instructions_url": "https://cs230.stanford.edu/assignments/ps3",
//   "weight": 0.15,
//   "estimated_hours": 12,
//   "late_penalty": "10% per day, maximum 3 days",
//   "rubric": [
//     {"criterion": "Correct implementation of content loss", "points": 30},
//     {"criterion": "Correct implementation of style loss", "points": 30},
//     {"criterion": "Training loop optimization", "points": 20},
//     {"criterion": "Code quality and documentation", "points": 20}
//   ]
// }


// ============================================================================
// EXAM NODE
// ============================================================================
// Represents course exams
// Source: CS230 midterm structure, Stanford exam scheduling
// ============================================================================

MERGE (e:Exam {exam_id: $exam_id})
ON CREATE SET
    e.title = $title,
    e.exam_type = $exam_type,  // 'Midterm', 'Final', 'Cumulative'
    e.date = datetime($date),
    e.duration_minutes = $duration_minutes,
    e.location = $location,  // Building + room
    e.points_possible = $points_possible,
    e.points_earned = $points_earned,  // Nullable
    e.percentage_grade = $percentage_grade,  // Nullable
    e.topics_covered = $topics_covered,  // Array of strings
    e.format = $format,  // 'Multiple Choice', 'Essay', 'Mixed'
    e.open_book = $open_book,  // Boolean
    e.allowed_materials = $allowed_materials,  // Array of strings
    e.weight = $weight,  // Float: contribution to course grade
    e.preparation_notes = $preparation_notes,
    e.created_at = datetime(),
    e.updated_at = datetime()
ON MATCH SET
    e.title = $title,
    e.exam_type = $exam_type,
    e.date = datetime($date),
    e.duration_minutes = $duration_minutes,
    e.location = $location,
    e.points_possible = $points_possible,
    e.points_earned = $points_earned,
    e.percentage_grade = $percentage_grade,
    e.topics_covered = $topics_covered,
    e.format = $format,
    e.open_book = $open_book,
    e.allowed_materials = $allowed_materials,
    e.weight = $weight,
    e.preparation_notes = $preparation_notes,
    e.updated_at = datetime()
RETURN e;

// Example parameters:
// {
//   "exam_id": "CS230-Fall2024-Midterm",
//   "title": "Midterm Examination",
//   "exam_type": "Midterm",
//   "date": "2024-11-06T18:00:00",
//   "duration_minutes": 180,
//   "location": "Memorial Auditorium",
//   "points_possible": 100,
//   "points_earned": 87,
//   "percentage_grade": 87.0,
//   "topics_covered": [
//     "Neural Network Fundamentals",
//     "Convolutional Neural Networks",
//     "Optimization Techniques",
//     "Regularization Methods"
//   ],
//   "format": "Mixed",
//   "open_book": false,
//   "allowed_materials": ["One 8.5x11 formula sheet (both sides)", "Calculator"],
//   "weight": 0.25,
//   "preparation_notes": "Focus on lectures 1-12, problem sets 1-4"
// }


// ============================================================================
// QUIZ NODE
// ============================================================================
// Represents course quizzes
// Source: CS230 weekly quizzes, Harvard CS50 auto-graded quizzes
// ============================================================================

MERGE (q:Quiz {quiz_id: $quiz_id})
ON CREATE SET
    q.title = $title,
    q.quiz_number = $quiz_number,
    q.date = datetime($date),
    q.duration_minutes = $duration_minutes,
    q.points_possible = $points_possible,
    q.points_earned = $points_earned,  // Nullable
    q.percentage_grade = $percentage_grade,  // Nullable
    q.topics_covered = $topics_covered,  // Array of strings
    q.format = $format,  // 'Online', 'In-Class'
    q.attempts_allowed = $attempts_allowed,
    q.weight = $weight,
    q.auto_graded = $auto_graded,  // Boolean
    q.created_at = datetime(),
    q.updated_at = datetime()
ON MATCH SET
    q.title = $title,
    q.quiz_number = $quiz_number,
    q.date = datetime($date),
    q.duration_minutes = $duration_minutes,
    q.points_possible = $points_possible,
    q.points_earned = $points_earned,
    q.percentage_grade = $percentage_grade,
    q.topics_covered = $topics_covered,
    q.format = $format,
    q.attempts_allowed = $attempts_allowed,
    q.weight = $weight,
    q.auto_graded = $auto_graded,
    q.updated_at = datetime()
RETURN q;

// Example parameters:
// {
//   "quiz_id": "CS230-Fall2024-Quiz5",
//   "title": "Week 5 Quiz: RNNs and LSTMs",
//   "quiz_number": 5,
//   "date": "2024-10-15T11:00:00",
//   "duration_minutes": 30,
//   "points_possible": 10,
//   "points_earned": 8,
//   "percentage_grade": 80.0,
//   "topics_covered": ["Recurrent Neural Networks", "LSTM Architecture", "Vanishing Gradients"],
//   "format": "Online",
//   "attempts_allowed": 1,
//   "weight": 0.02,
//   "auto_graded": true
// }


// ============================================================================
// LAB_SESSION NODE
// ============================================================================
// Represents laboratory sessions
// Source: University lab structures (2-6 hour sessions)
// ============================================================================

MERGE (l:Lab_Session {lab_id: $lab_id})
ON CREATE SET
    l.title = $title,
    l.session_number = $session_number,
    l.date = datetime($date),
    l.duration_minutes = $duration_minutes,  // Typically 120-360
    l.location = $location,  // Lab building + room
    l.instructor_name = $instructor_name,  // TA or lab instructor
    l.experiment_title = $experiment_title,
    l.objectives = $objectives,  // Array of strings
    l.pre_lab_reading = $pre_lab_reading,
    l.pre_lab_assignment_due = datetime($pre_lab_assignment_due),
    l.equipment_needed = $equipment_needed,  // Array of strings
    l.safety_requirements = $safety_requirements,  // Array: ['Lab Coat', 'Goggles']
    l.submission_deadline = datetime($submission_deadline),
    l.points_possible = $points_possible,
    l.points_earned = $points_earned,  // Nullable
    l.created_at = datetime(),
    l.updated_at = datetime()
ON MATCH SET
    l.title = $title,
    l.session_number = $session_number,
    l.date = datetime($date),
    l.duration_minutes = $duration_minutes,
    l.location = $location,
    l.instructor_name = $instructor_name,
    l.experiment_title = $experiment_title,
    l.objectives = $objectives,
    l.pre_lab_reading = $pre_lab_reading,
    l.pre_lab_assignment_due = datetime($pre_lab_assignment_due),
    l.equipment_needed = $equipment_needed,
    l.safety_requirements = $safety_requirements,
    l.submission_deadline = datetime($submission_deadline),
    l.points_possible = $points_possible,
    l.points_earned = $points_earned,
    l.updated_at = datetime()
RETURN l;

// Example parameters:
// {
//   "lab_id": "CHEM31A-Fall2024-Lab3",
//   "title": "Acid-Base Titration",
//   "session_number": 3,
//   "date": "2024-10-18T14:00:00",
//   "duration_minutes": 240,
//   "location": "Keck Science Building, Lab 102",
//   "instructor_name": "Dr. Sarah Martinez",
//   "experiment_title": "Determination of Acetic Acid Concentration in Vinegar",
//   "objectives": [
//     "Practice proper pipetting techniques",
//     "Determine equivalence point using pH indicator",
//     "Calculate molarity of acetic acid solution"
//   ],
//   "pre_lab_reading": "Lab Manual Chapter 5: Acid-Base Equilibria",
//   "pre_lab_assignment_due": "2024-10-18T13:00:00",
//   "equipment_needed": ["Burette", "Pipette", "Erlenmeyer flask", "pH meter"],
//   "safety_requirements": ["Lab Coat", "Goggles", "Closed-toe shoes"],
//   "submission_deadline": "2024-10-25T23:59:00",
//   "points_possible": 50,
//   "points_earned": 47
// }


// ============================================================================
// STUDY_TODO NODE
// ============================================================================
// Represents study tasks following GTD methodology
// Source: GTD best practices, academic productivity research
// ============================================================================

MERGE (t:Study_Todo {todo_id: $todo_id})
ON CREATE SET
    t.title = $title,
    t.description = $description,
    t.priority = $priority,  // 'High', 'Medium', 'Low'
    t.status = $status,  // 'Next Action', 'Waiting For', 'Someday/Maybe', 'Completed'
    t.due_date = datetime($due_date),  // Nullable
    t.estimated_minutes = $estimated_minutes,
    t.actual_minutes = $actual_minutes,  // Nullable
    t.context = $context,  // Array: ['@Library', '@Home', '@Computer']
    t.energy_required = $energy_required,  // 'High', 'Medium', 'Low'
    t.created_date = datetime($created_date),
    t.completed_date = datetime($completed_date),  // Nullable
    t.recurrence = $recurrence,  // 'Daily', 'Weekly', 'None'
    t.ai_generated = $ai_generated,  // Boolean
    t.source = $source,  // 'User', 'AI-Assignment', 'AI-Challenge'
    t.created_at = datetime(),
    t.updated_at = datetime()
ON MATCH SET
    t.title = $title,
    t.description = $description,
    t.priority = $priority,
    t.status = $status,
    t.due_date = datetime($due_date),
    t.estimated_minutes = $estimated_minutes,
    t.actual_minutes = $actual_minutes,
    t.context = $context,
    t.energy_required = $energy_required,
    t.created_date = datetime($created_date),
    t.completed_date = datetime($completed_date),
    t.recurrence = $recurrence,
    t.ai_generated = $ai_generated,
    t.source = $source,
    t.updated_at = datetime()
RETURN t;

// Example parameters:
// {
//   "todo_id": "TODO-2024-10-001",
//   "title": "Review lecture notes on CNNs before midterm",
//   "description": "Review lectures 8-10 focusing on convolutional layer mechanics and pooling operations",
//   "priority": "High",
//   "status": "Next Action",
//   "due_date": "2024-11-05T23:59:00",
//   "estimated_minutes": 90,
//   "actual_minutes": null,
//   "context": ["@Library", "@Computer"],
//   "energy_required": "Medium",
//   "created_date": "2024-10-20T10:30:00",
//   "completed_date": null,
//   "recurrence": "None",
//   "ai_generated": true,
//   "source": "AI-Challenge"
// }


// ============================================================================
// CHALLENGE_AREA NODE
// ============================================================================
// Represents academic difficulties requiring intervention
// Source: Academic support systems, IEP concepts, progress monitoring
// ============================================================================

MERGE (ca:Challenge_Area {challenge_id: $challenge_id})
ON CREATE SET
    ca.title = $title,
    ca.description = $description,
    ca.severity = $severity,  // 'Critical', 'Moderate', 'Minor'
    ca.identified_date = datetime($identified_date),
    ca.detection_method = $detection_method,  // 'AI-Performance', 'Self-Reported', 'Instructor-Flagged'
    ca.status = $status,  // 'Active', 'Improving', 'Resolved'
    ca.resolution_date = datetime($resolution_date),  // Nullable
    ca.performance_trend = $performance_trend,  // Array of floats (recent grades)
    ca.related_topics = $related_topics,  // Array of strings
    ca.improvement_notes = $improvement_notes,
    ca.confidence_level = $confidence_level,  // Integer 1-10
    ca.embedding_vector = $embedding_vector,  // Vector for similarity search (896 dims)
    ca.created_at = datetime(),
    ca.updated_at = datetime()
ON MATCH SET
    ca.title = $title,
    ca.description = $description,
    ca.severity = $severity,
    ca.identified_date = datetime($identified_date),
    ca.detection_method = $detection_method,
    ca.status = $status,
    ca.resolution_date = datetime($resolution_date),
    ca.performance_trend = $performance_trend,
    ca.related_topics = $related_topics,
    ca.improvement_notes = $improvement_notes,
    ca.confidence_level = $confidence_level,
    ca.embedding_vector = $embedding_vector,
    ca.updated_at = datetime()
RETURN ca;

// Example parameters:
// {
//   "challenge_id": "CHALLENGE-CS230-Integration",
//   "title": "Calculus - Integration Techniques",
//   "description": "Struggling with integration by parts and substitution methods in calculus problems",
//   "severity": "Moderate",
//   "identified_date": "2024-10-15T00:00:00",
//   "detection_method": "AI-Performance",
//   "status": "Active",
//   "resolution_date": null,
//   "performance_trend": [65.0, 58.0, 62.0, 55.0],
//   "related_topics": ["Integration by Parts", "U-Substitution", "Trigonometric Substitution"],
//   "improvement_notes": "Needs more practice with pattern recognition",
//   "confidence_level": 4,
//   "embedding_vector": [0.234, -0.123, ...]  // 896 dimensions from Qwen3-Embedding-0.6B
// }


// ============================================================================
// CLASS_SCHEDULE NODE
// ============================================================================
// Represents class meeting schedules
// Source: College schedule formats, Stanford quarter system
// ============================================================================

MERGE (cs:Class_Schedule {schedule_id: $schedule_id})
ON CREATE SET
    cs.days_of_week = $days_of_week,  // Array: ['Monday', 'Wednesday', 'Friday']
    cs.start_time = localtime($start_time),
    cs.end_time = localtime($end_time),
    cs.building = $building,
    cs.room = $room,
    cs.campus = $campus,
    cs.format = $format,  // 'F2F', 'Online', 'Hybrid'
    cs.meeting_url = $meeting_url,  // Nullable (Zoom link)
    cs.instructor_office_hours = $instructor_office_hours,  // Array of objects
    cs.section_number = $section_number,
    cs.enrollment_capacity = $enrollment_capacity,
    cs.term_start_date = date($term_start_date),
    cs.term_end_date = date($term_end_date),
    cs.created_at = datetime(),
    cs.updated_at = datetime()
ON MATCH SET
    cs.days_of_week = $days_of_week,
    cs.start_time = localtime($start_time),
    cs.end_time = localtime($end_time),
    cs.building = $building,
    cs.room = $room,
    cs.campus = $campus,
    cs.format = $format,
    cs.meeting_url = $meeting_url,
    cs.instructor_office_hours = $instructor_office_hours,
    cs.section_number = $section_number,
    cs.enrollment_capacity = $enrollment_capacity,
    cs.term_start_date = date($term_start_date),
    cs.term_end_date = date($term_end_date),
    cs.updated_at = datetime()
RETURN cs;

// Example parameters:
// {
//   "schedule_id": "CS230-Fall2024-LEC-01",
//   "days_of_week": ["Tuesday", "Thursday"],
//   "start_time": "11:30:00",
//   "end_time": "13:00:00",
//   "building": "NVIDIA Auditorium",
//   "room": "Main Hall",
//   "campus": "Main Campus",
//   "format": "F2F",
//   "meeting_url": null,
//   "instructor_office_hours": [
//     {"day": "Wednesday", "time": "14:00-16:00", "location": "Gates 288"},
//     {"day": "Friday", "time": "10:00-11:00", "location": "Gates 288"}
//   ],
//   "section_number": "01",
//   "enrollment_capacity": 180,
//   "term_start_date": "2024-09-24",
//   "term_end_date": "2024-12-06"
// }


// ============================================================================
// NOTE NODE
// ============================================================================
// Represents student notes with vector embeddings
// Source: Obsidian/Roam structures, academic note-taking best practices
// ============================================================================

MERGE (n:Note {note_id: $note_id})
ON CREATE SET
    n.title = $title,
    n.content = $content,  // Markdown/rich text
    n.created_date = datetime($created_date),
    n.last_modified = datetime($last_modified),
    n.note_type = $note_type,  // 'Lecture', 'Reading', 'Lab', 'Personal Insight'
    n.tags = $tags,  // Array of strings
    n.embedding_vector = $embedding_vector,  // Vector (896 dimensions for Qwen3-Embedding-0.6B)
    n.word_count = $word_count,
    n.quality_score = $quality_score,  // Float (completeness metric)
    n.linked_resources = $linked_resources,  // Array of URLs
    n.review_count = $review_count,  // Spaced repetition counter
    n.last_reviewed = datetime($last_reviewed),
    n.created_at = datetime(),
    n.updated_at = datetime()
ON MATCH SET
    n.title = $title,
    n.content = $content,
    n.last_modified = datetime($last_modified),
    n.note_type = $note_type,
    n.tags = $tags,
    n.embedding_vector = $embedding_vector,
    n.word_count = $word_count,
    n.quality_score = $quality_score,
    n.linked_resources = $linked_resources,
    n.review_count = $review_count,
    n.last_reviewed = datetime($last_reviewed),
    n.updated_at = datetime()
RETURN n;

// Example parameters:
// {
//   "note_id": "NOTE-2024-10-20-001",
//   "title": "Lecture 8: Convolutional Neural Networks",
//   "content": "# CNN Architecture\n\n## Key Concepts\n- Convolutional layers extract spatial features...",
//   "created_date": "2024-10-20T11:45:00",
//   "last_modified": "2024-10-20T14:30:00",
//   "note_type": "Lecture",
//   "tags": ["CNN", "Computer Vision", "Deep Learning"],
//   "embedding_vector": [0.123, -0.456, ...],  // 896 dimensions from Qwen3-Embedding-0.6B
//   "word_count": 1247,
//   "quality_score": 8.5,
//   "linked_resources": ["https://cs230.stanford.edu/slides/lecture8.pdf"],
//   "review_count": 2,
//   "last_reviewed": "2024-10-22T16:00:00"
// }


// ============================================================================
// LECTURE NODE
// ============================================================================
// Represents individual lecture sessions
// Source: Academic lecture formats, recording systems
// ============================================================================

MERGE (lec:Lecture {lecture_id: $lecture_id})
ON CREATE SET
    lec.title = $title,
    lec.lecture_number = $lecture_number,
    lec.date = datetime($date),
    lec.duration_minutes = $duration_minutes,
    lec.recording_url = $recording_url,  // Nullable
    lec.slides_url = $slides_url,  // Nullable
    lec.transcript = $transcript,  // Nullable (auto-generated)
    lec.key_concepts = $key_concepts,  // Array: AI-extracted
    lec.attendance_required = $attendance_required,
    lec.reading_due = $reading_due,  // Array of chapters/articles
    lec.embedding_vector = $embedding_vector,  // Vector for transcript search (896 dims)
    lec.created_at = datetime(),
    lec.updated_at = datetime()
ON MATCH SET
    lec.title = $title,
    lec.lecture_number = $lecture_number,
    lec.date = datetime($date),
    lec.duration_minutes = $duration_minutes,
    lec.recording_url = $recording_url,
    lec.slides_url = $slides_url,
    lec.transcript = $transcript,
    lec.key_concepts = $key_concepts,
    lec.attendance_required = $attendance_required,
    lec.reading_due = $reading_due,
    lec.embedding_vector = $embedding_vector,
    lec.updated_at = datetime()
RETURN lec;

// Example parameters:
// {
//   "lecture_id": "CS230-Fall2024-LEC8",
//   "title": "Convolutional Neural Networks",
//   "lecture_number": 8,
//   "date": "2024-10-20T11:30:00",
//   "duration_minutes": 90,
//   "recording_url": "https://canvas.stanford.edu/recordings/lec8",
//   "slides_url": "https://cs230.stanford.edu/slides/lecture8.pdf",
//   "transcript": "Today we'll discuss convolutional neural networks...",
//   "key_concepts": ["Convolutional Layers", "Pooling", "Stride", "Padding"],
//   "attendance_required": true,
//   "reading_due": ["Deep Learning Book Chapter 9", "CS231n Notes on CNNs"],
//   "embedding_vector": [0.345, -0.234, ...]  // 896 dimensions
// }


// ============================================================================
// TOPIC NODE
// ============================================================================
// Represents knowledge topics/concepts
// Source: Knowledge graph structures, curriculum design
// ============================================================================

MERGE (t:Topic {topic_id: $topic_id})
ON CREATE SET
    t.name = $name,
    t.description = $description,
    t.parent_topic_id = $parent_topic_id,  // Nullable (hierarchical)
    t.difficulty_level = $difficulty_level,  // 'Introductory', 'Intermediate', 'Advanced'
    t.estimated_study_hours = $estimated_study_hours,
    t.prerequisite_topics = $prerequisite_topics,  // Array of topic_ids
    t.keywords = $keywords,  // Array for search
    t.embedding_vector = $embedding_vector,  // Vector for topic similarity (896 dims)
    t.created_at = datetime(),
    t.updated_at = datetime()
ON MATCH SET
    t.name = $name,
    t.description = $description,
    t.parent_topic_id = $parent_topic_id,
    t.difficulty_level = $difficulty_level,
    t.estimated_study_hours = $estimated_study_hours,
    t.prerequisite_topics = $prerequisite_topics,
    t.keywords = $keywords,
    t.embedding_vector = $embedding_vector,
    t.updated_at = datetime()
RETURN t;

// Example parameters:
// {
//   "topic_id": "TOPIC-CNN",
//   "name": "Convolutional Neural Networks",
//   "description": "Neural network architecture designed for processing grid-like data such as images",
//   "parent_topic_id": "TOPIC-DeepLearning",
//   "difficulty_level": "Intermediate",
//   "estimated_study_hours": 20,
//   "prerequisite_topics": ["TOPIC-NeuralNetworks", "TOPIC-LinearAlgebra"],
//   "keywords": ["CNN", "convolution", "computer vision", "image processing"],
//   "embedding_vector": [0.567, -0.123, ...]  // 896 dimensions
// }


// ============================================================================
// RESOURCE NODE
// ============================================================================
// Represents learning resources
// Source: Harvard syllabus reading lists, academic resource management
// ============================================================================

MERGE (r:Resource {resource_id: $resource_id})
ON CREATE SET
    r.title = $title,
    r.type = $type,  // 'Textbook', 'Article', 'Video', 'Website', 'Tool'
    r.url = $url,  // Nullable
    r.author = $author,
    r.publication_date = date($publication_date),  // Nullable
    r.isbn = $isbn,  // Nullable (for books)
    r.description = $description,
    r.access_method = $access_method,  // 'Library', 'Online', 'Purchase'
    r.relevance_score = $relevance_score,  // Float: AI-rated importance
    r.embedding_vector = $embedding_vector,  // Vector for resource recommendation (896 dims)
    r.created_at = datetime(),
    r.updated_at = datetime()
ON MATCH SET
    r.title = $title,
    r.type = $type,
    r.url = $url,
    r.author = $author,
    r.publication_date = date($publication_date),
    r.isbn = $isbn,
    r.description = $description,
    r.access_method = $access_method,
    r.relevance_score = $relevance_score,
    r.embedding_vector = $embedding_vector,
    r.updated_at = datetime()
RETURN r;

// Example parameters:
// {
//   "resource_id": "RES-DeepLearningBook",
//   "title": "Deep Learning",
//   "type": "Textbook",
//   "url": "https://www.deeplearningbook.org/",
//   "author": "Ian Goodfellow, Yoshua Bengio, Aaron Courville",
//   "publication_date": "2016-11-18",
//   "isbn": "978-0262035613",
//   "description": "Comprehensive textbook on deep learning covering mathematical foundations and modern architectures",
//   "access_method": "Online",
//   "relevance_score": 9.5,
//   "embedding_vector": [0.789, -0.234, ...]  // 896 dimensions
// }


// ============================================================================
// BULK LOADING NOTES
// ============================================================================
// For production data loads with thousands of nodes, use:
// 1. LOAD CSV WITH HEADERS for batch imports
// 2. neo4j-admin import for initial database population
// 3. APOC procedures for complex transformations
// 4. CALL { ... } IN TRANSACTIONS for large updates
//
// Example bulk load:
// LOAD CSV WITH HEADERS FROM 'file:///courses.csv' AS row
// CALL {
//   WITH row
//   MERGE (c:Course {course_id: row.course_id})
//   ON CREATE SET c.title = row.title, c.credits = toInteger(row.credits), ...
//   ON MATCH SET c.title = row.title, c.credits = toInteger(row.credits), ...
// } IN TRANSACTIONS OF 1000 ROWS
// ============================================================================
