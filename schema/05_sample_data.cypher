MERGE (p:Profile {student_id: "STU-2024-001234"})
ON CREATE SET
    p.first_name = "Alice",
    p.last_name = "Chen",
    p.email = "alice.chen@stanford.edu",
    p.major = "Computer Science",
    p.minor = ["Mathematics", "Cognitive Science"],
    p.year = "Junior",
    p.cumulative_gpa = 3.87,
    p.total_credits_earned = 96,
    p.degree_program = "BS",
    p.enrollment_date = datetime("2022-09-15T00:00:00"),
    p.expected_graduation = date("2026-06-15"),
    p.academic_standing = "Good Standing",
    p.preference_study_style = "visual",
    p.preference_notification_email = true,
    p.preference_notification_push = true,
    p.preference_quiet_hours = "22:00-08:00",
    p.preference_ai_assistance_level = "high",
    p.timezone = "America/Los_Angeles",
    p.created_at = datetime(),
    p.updated_at = datetime();
MERGE (c1:Course {course_id: "CS230-Fall2025"})
ON CREATE SET
    c1.title = "Deep Learning",
    c1.code = "CS",
    c1.number = "230",
    c1.term = "Fall 2025",
    c1.credits = 4,
    c1.description = "Introduction to deep learning with focus on neural networks, CNNs, RNNs, and transformers. Hands-on implementation using PyTorch.",
    c1.instructor_name = "Andrew Ng",
    c1.instructor_email = "ang@cs.stanford.edu",
    c1.component_type = ["LEC", "DIS"],
    c1.prerequisites = ["CS229-Spring2025", "MATH51-Winter2025"],
    c1.grading_options = ["Letter", "S/NC"],
    c1.syllabus_url = "https://cs230.stanford.edu/syllabus/",
    c1.learning_objectives = [
        "Understand neural network architectures",
        "Implement CNNs for computer vision tasks",
        "Build sequence models with RNNs and transformers",
        "Apply deep learning to real-world projects"
    ],
    c1.final_exam_date = datetime("2025-12-13T18:00:00"),
    c1.created_at = datetime(),
    c1.updated_at = datetime();
MERGE (c2:Course {course_id: "MATH51-Winter2025"})
ON CREATE SET
    c2.title = "Linear Algebra, Multivariable Calculus, and Modern Applications",
    c2.code = "MATH",
    c2.number = "51",
    c2.term = "Winter 2025",
    c2.credits = 5,
    c2.description = "Matrices, determinants, eigenvalues, eigenvectors. Applications to data science and machine learning.",
    c2.instructor_name = "Dr. Sarah Johnson",
    c2.instructor_email = "sjohnson@math.stanford.edu",
    c2.component_type = ["LEC", "DIS"],
    c2.prerequisites = [],
    c2.grading_options = ["Letter"],
    c2.syllabus_url = "https://example.edu/syllabus",
    c2.learning_objectives = [
        "Master matrix operations and vector spaces",
        "Understand eigenvalue decomposition",
        "Apply linear algebra to ML problems"
    ],
    c2.final_exam_date = datetime("2025-03-15T14:00:00"),
    c2.created_at = datetime(),
    c2.updated_at = datetime();
MERGE (t1:Topic {topic_id: "TOPIC-NeuralNetworks"})
ON CREATE SET
    t1.name = "Neural Networks",
    t1.description = "Foundational architecture for deep learning with layers, activations, and backpropagation",
    t1.parent_topic_id = NULL,
    t1.difficulty_level = "Intermediate",
    t1.estimated_study_hours = 15,
    t1.prerequisite_topics = ["TOPIC-LinearAlgebra", "TOPIC-Calculus"],
    t1.keywords = ["neural net", "backprop", "activation functions", "forward pass"],
    t1.embedding_vector = NULL,
    t1.created_at = datetime(),
    t1.updated_at = datetime();
MERGE (t2:Topic {topic_id: "TOPIC-CNN"})
ON CREATE SET
    t2.name = "Convolutional Neural Networks",
    t2.description = "Neural network architecture designed for processing grid-like data such as images",
    t2.parent_topic_id = "TOPIC-NeuralNetworks",
    t2.difficulty_level = "Intermediate",
    t2.estimated_study_hours = 20,
    t2.prerequisite_topics = ["TOPIC-NeuralNetworks"],
    t2.keywords = ["CNN", "convolution", "computer vision", "image processing", "filters"],
    t2.embedding_vector = NULL,
    t2.created_at = datetime(),
    t2.updated_at = datetime();
MERGE (t3:Topic {topic_id: "TOPIC-RNN"})
ON CREATE SET
    t3.name = "Recurrent Neural Networks",
    t3.description = "Neural networks for sequential data with hidden state and temporal dependencies",
    t3.parent_topic_id = "TOPIC-NeuralNetworks",
    t3.difficulty_level = "Advanced",
    t3.estimated_study_hours = 18,
    t3.prerequisite_topics = ["TOPIC-NeuralNetworks"],
    t3.keywords = ["RNN", "LSTM", "GRU", "sequence modeling", "time series"],
    t3.embedding_vector = NULL,
    t3.created_at = datetime(),
    t3.updated_at = datetime();
MERGE (sch1:Class_Schedule {schedule_id: "CS230-Fall2025-LEC-01"})
ON CREATE SET
    sch1.days_of_week = ["Tuesday", "Thursday"],
    sch1.start_time = localtime("11:30:00"),
    sch1.end_time = localtime("13:00:00"),
    sch1.building = "NVIDIA Auditorium",
    sch1.room = "Main Hall",
    sch1.campus = "Main Campus",
    sch1.format = "F2F",
    sch1.meeting_url = NULL,
    sch1.instructor_office_hours = [
        "Wednesday 14:00-16:00 Gates 288",
        "Friday 10:00-11:00 Gates 288"
    ],
    sch1.section_number = "01",
    sch1.enrollment_capacity = 180,
    sch1.term_start_date = date("2025-09-24"),
    sch1.term_end_date = date("2025-12-06"),
    sch1.created_at = datetime(),
    sch1.updated_at = datetime();
MERGE (lec1:Lecture {lecture_id: "CS230-Fall2025-LEC8"})
ON CREATE SET
    lec1.title = "Convolutional Neural Networks",
    lec1.lecture_number = 8,
    lec1.date = datetime("2025-10-20T11:30:00"),
    lec1.duration_minutes = 90,
    lec1.recording_url = "https://example.edu/recording",
    lec1.slides_url = "https://example.edu/slides",
    lec1.transcript = "Today we will discuss convolutional neural networks, which are the cornerstone of modern computer vision...",
    lec1.key_concepts = ["Convolutional Layers", "Pooling", "Stride", "Padding", "Feature Maps"],
    lec1.attendance_required = true,
    lec1.reading_due = ["Deep Learning Book Chapter 9", "CS231n Notes on CNNs"],
    lec1.embedding_vector = NULL,
    lec1.created_at = datetime(),
    lec1.updated_at = datetime();
MERGE (n1:Note {note_id: "NOTE-2025-10-20-001"})
ON CREATE SET
    n1.title = "Lecture 8: Convolutional Neural Networks",
    n1.content = "# CNN Architecture\n\n## Key Concepts\n\n### Convolutional Layers\n- Extract spatial features from input\n- Use filters/kernels (e.g., 3x3, 5x5)\n- Parameters shared across spatial locations\n- Output: feature maps\n\n### Pooling Layers\n- Reduce spatial dimensions\n- Max pooling: take maximum value in window\n- Average pooling: take average\n- Provides translation invariance\n\n### Example Architecture\nInput (224x224x3) → Conv (3x3, 64) → ReLU → MaxPool (2x2) → Conv (3x3, 128) → ReLU → MaxPool → FC → Softmax\n\n## Applications\n- Image classification\n- Object detection\n- Semantic segmentation",
    n1.created_date = datetime("2025-10-20T11:45:00"),
    n1.last_modified = datetime("2025-10-20T14:30:00"),
    n1.note_type = "Lecture",
    n1.tags = ["CNN", "Computer Vision", "Deep Learning"],
    n1.embedding_vector = NULL,
    n1.word_count = 247,
    n1.quality_score = 8.5,
    n1.linked_resources = ["https://example.edu/resources"],
    n1.review_count = 2,
    n1.last_reviewed = datetime("2025-10-22T16:00:00"),
    n1.created_at = datetime(),
    n1.updated_at = datetime();
MERGE (a1:Assignment {assignment_id: "CS230-Fall2025-PS3"})
ON CREATE SET
    a1.title = "Programming Assignment 3: Neural Style Transfer",
    a1.type = "Programming",
    a1.description = "Implement neural style transfer using pre-trained VGG networks. Apply artistic styles to content images.",
    a1.due_date = datetime("2025-10-31T23:00:00"),
    a1.points_possible = 100,
    a1.points_earned = NULL,
    a1.percentage_grade = NULL,
    a1.submission_status = "Not Started",
    a1.submission_url = "https://example.edu/submit",
    a1.instructions_url = "https://example.edu/instructions",
    a1.weight = 0.15,
    a1.estimated_hours = 12,
    a1.late_penalty = "10% per day, maximum 3 days",
    a1.rubric = [
        "Correct implementation of content loss (30pts)",
        "Correct implementation of style loss (30pts)",
        "Training loop optimization (20pts)",
        "Code quality and documentation (20pts)"
    ],
    a1.created_at = datetime(),
    a1.updated_at = datetime();
MERGE (q1:Quiz {quiz_id: "CS230-Fall2025-Quiz5"})
ON CREATE SET
    q1.title = "Week 5 Quiz: RNNs and LSTMs",
    q1.quiz_number = 5,
    q1.date = datetime("2025-10-15T11:00:00"),
    q1.duration_minutes = 30,
    q1.points_possible = 10,
    q1.points_earned = 8,
    q1.percentage_grade = 80.0,
    q1.topics_covered = ["Recurrent Neural Networks", "LSTM Architecture", "Vanishing Gradients"],
    q1.format = "Online",
    q1.attempts_allowed = 1,
    q1.weight = 0.02,
    q1.auto_graded = true,
    q1.created_at = datetime(),
    q1.updated_at = datetime();
MERGE (q2:Quiz {quiz_id: "CS230-Fall2025-Quiz6"})
ON CREATE SET
    q2.title = "Week 6 Quiz: Convolutional Networks",
    q2.quiz_number = 6,
    q2.date = datetime("2025-10-22T11:00:00"),
    q2.duration_minutes = 30,
    q2.points_possible = 10,
    q2.points_earned = 6,
    q2.percentage_grade = 60.0,
    q2.topics_covered = ["CNN Architecture", "Convolutional Layers", "Pooling"],
    q2.format = "Online",
    q2.attempts_allowed = 1,
    q2.weight = 0.02,
    q2.auto_graded = true,
    q2.created_at = datetime(),
    q2.updated_at = datetime();
MERGE (e1:Exam {exam_id: "CS230-Fall2025-Midterm"})
ON CREATE SET
    e1.title = "Midterm Examination",
    e1.exam_type = "Midterm",
    e1.date = datetime("2025-11-06T18:00:00"),
    e1.duration_minutes = 180,
    e1.location = "Memorial Auditorium",
    e1.points_possible = 100,
    e1.points_earned = NULL,
    e1.percentage_grade = NULL,
    e1.topics_covered = [
        "Neural Network Fundamentals",
        "Convolutional Neural Networks",
        "Optimization Techniques",
        "Regularization Methods"
    ],
    e1.format = "Mixed",
    e1.open_book = false,
    e1.allowed_materials = ["One 8.5x11 formula sheet (both sides)", "Calculator"],
    e1.weight = 0.25,
    e1.preparation_notes = "Focus on lectures 1-12, problem sets 1-4",
    e1.created_at = datetime(),
    e1.updated_at = datetime();
MERGE (ch1:Challenge_Area {challenge_id: "CHALLENGE-CNN-Pooling"})
ON CREATE SET
    ch1.title = "CNN - Pooling Operations",
    ch1.description = "Difficulty understanding pooling layer mechanics and when to use max vs average pooling",
    ch1.severity = "Moderate",
    ch1.identified_date = datetime("2025-10-23T00:00:00"),
    ch1.detection_method = "AI-Performance",
    ch1.status = "Active",
    ch1.resolution_date = NULL,
    ch1.performance_trend = [80.0, 75.0, 60.0],
    ch1.related_topics = ["Pooling", "Max Pooling", "Average Pooling", "Downsampling"],
    ch1.improvement_notes = "Student needs more practice with pooling visualization and implementation",
    ch1.confidence_level = 4,
    ch1.embedding_vector = NULL,
    ch1.created_at = datetime(),
    ch1.updated_at = datetime();
MERGE (td1:Study_Todo {todo_id: "TODO-2025-10-23-001"})
ON CREATE SET
    td1.title = "Review CNN pooling layer concepts",
    td1.description = "Review lecture 8 notes focusing on pooling operations. Practice visualizing feature map dimensions before/after pooling.",
    td1.priority = "High",
    td1.status = "Next Action",
    td1.due_date = datetime("2025-10-28T23:59:00"),
    td1.estimated_minutes = 90,
    td1.actual_minutes = NULL,
    td1.context = ["@Library", "@Computer"],
    td1.energy_required = "Medium",
    td1.created_date = datetime("2025-10-23T10:00:00"),
    td1.completed_date = NULL,
    td1.recurrence = "None",
    td1.ai_generated = true,
    td1.source = "AI-Challenge",
    td1.created_at = datetime(),
    td1.updated_at = datetime();
MERGE (td2:Study_Todo {todo_id: "TODO-2025-10-23-002"})
ON CREATE SET
    td2.title = "Complete 10 CNN pooling practice problems",
    td2.description = "Work through practice problems calculating output dimensions for various pooling configurations",
    td2.priority = "High",
    td2.status = "Waiting For",
    td2.due_date = datetime("2025-10-30T23:59:00"),
    td2.estimated_minutes = 120,
    td2.actual_minutes = NULL,
    td2.context = ["@Computer"],
    td2.energy_required = "High",
    td2.created_date = datetime("2025-10-23T10:00:00"),
    td2.completed_date = NULL,
    td2.recurrence = "None",
    td2.ai_generated = true,
    td2.source = "AI-Challenge",
    td2.created_at = datetime(),
    td2.updated_at = datetime();
MERGE (r1:Resource {resource_id: "RES-DeepLearningBook"})
ON CREATE SET
    r1.title = "Deep Learning",
    r1.type = "Textbook",
    r1.url = "https://example.edu/resource",
    r1.author = "Ian Goodfellow, Yoshua Bengio, Aaron Courville",
    r1.publication_date = date("2016-11-18"),
    r1.isbn = "978-0262035613",
    r1.description = "Comprehensive textbook on deep learning covering mathematical foundations and modern architectures",
    r1.access_method = "Online",
    r1.relevance_score = 9.5,
    r1.embedding_vector = NULL,
    r1.created_at = datetime(),
    r1.updated_at = datetime();
MATCH (p:Profile {student_id: "STU-2024-001234"})
MATCH (c1:Course {course_id: "CS230-Fall2025"})
MERGE (p)-[r1:ENROLLED_IN]->(c1)
ON CREATE SET
    r1.enrollment_date = datetime("2025-09-15T10:00:00"),
    r1.status = "Active",
    r1.final_grade = NULL,
    r1.letter_grade = NULL,
    r1.grading_basis = "Letter",
    r1.created_at = datetime(),
    r1.updated_at = datetime();
MATCH (p:Profile {student_id: "STU-2024-001234"})
MATCH (c2:Course {course_id: "MATH51-Winter2025"})
MERGE (p)-[r1a:ENROLLED_IN]->(c2)
ON CREATE SET
    r1a.enrollment_date = datetime("2025-01-05T10:00:00"),
    r1a.status = "Completed",
    r1a.final_grade = 94.5,
    r1a.letter_grade = "A",
    r1a.grading_basis = "Letter",
    r1a.created_at = datetime(),
    r1a.updated_at = datetime();
MATCH (p:Profile {student_id: "STU-2024-001234"})
MATCH (n1:Note {note_id: "NOTE-2025-10-20-001"})
MERGE (p)-[r2:CREATED_NOTE]->(n1)
ON CREATE SET r2.created_at = datetime();
MATCH (p:Profile {student_id: "STU-2024-001234"})
MATCH (ch1:Challenge_Area {challenge_id: "CHALLENGE-CNN-Pooling"})
MERGE (p)-[r3:FACES_CHALLENGE]->(ch1)
ON CREATE SET
    r3.first_detected = datetime("2025-10-23T00:00:00"),
    r3.current_severity = "Moderate",
    r3.intervention_count = 2,
    r3.created_at = datetime(),
    r3.updated_at = datetime();
MATCH (p:Profile {student_id: "STU-2024-001234"})
MATCH (td1:Study_Todo {todo_id: "TODO-2025-10-23-001"})
MERGE (p)-[r4:HAS_TODO]->(td1)
ON CREATE SET r4.created_at = datetime();
MATCH (p:Profile {student_id: "STU-2024-001234"})
MATCH (td2:Study_Todo {todo_id: "TODO-2025-10-23-002"})
MERGE (p)-[r5:HAS_TODO]->(td2)
ON CREATE SET r5.created_at = datetime();
MATCH (c1:Course {course_id: "CS230-Fall2025"})
MATCH (sch1:Class_Schedule {schedule_id: "CS230-Fall2025-LEC-01"})
MERGE (c1)-[r6:SCHEDULED_AS]->(sch1)
ON CREATE SET r6.created_at = datetime();
MATCH (c1:Course {course_id: "CS230-Fall2025"})
MATCH (lec1:Lecture {lecture_id: "CS230-Fall2025-LEC8"})
MERGE (c1)-[r7:INCLUDES_LECTURE]->(lec1)
ON CREATE SET r7.created_at = datetime();
MATCH (c1:Course {course_id: "CS230-Fall2025"})
MATCH (a1:Assignment {assignment_id: "CS230-Fall2025-PS3"})
MERGE (c1)-[r8:HAS_ASSIGNMENT]->(a1)
ON CREATE SET r8.sequence_number = 3, r8.created_at = datetime();
MATCH (c1:Course {course_id: "CS230-Fall2025"})
MATCH (q1:Quiz {quiz_id: "CS230-Fall2025-Quiz5"})
MERGE (c1)-[r9:HAS_QUIZ]->(q1)
ON CREATE SET r9.created_at = datetime();
MATCH (c1:Course {course_id: "CS230-Fall2025"})
MATCH (q2:Quiz {quiz_id: "CS230-Fall2025-Quiz6"})
MERGE (c1)-[r10:HAS_QUIZ]->(q2)
ON CREATE SET r10.created_at = datetime();
MATCH (c1:Course {course_id: "CS230-Fall2025"})
MATCH (e1:Exam {exam_id: "CS230-Fall2025-Midterm"})
MERGE (c1)-[r11:HAS_EXAM]->(e1)
ON CREATE SET r11.created_at = datetime();
MATCH (c1:Course {course_id: "CS230-Fall2025"})
MATCH (t2:Topic {topic_id: "TOPIC-CNN"})
MERGE (c1)-[r12:COVERS_TOPIC]->(t2)
ON CREATE SET
    r12.coverage_depth = "Comprehensive",
    r12.week_introduced = 4,
    r12.created_at = datetime();
MATCH (c1:Course {course_id: "CS230-Fall2025"})
MATCH (t3:Topic {topic_id: "TOPIC-RNN"})
MERGE (c1)-[r13:COVERS_TOPIC]->(t3)
ON CREATE SET
    r13.coverage_depth = "Comprehensive",
    r13.week_introduced = 5,
    r13.created_at = datetime();
MATCH (lec1:Lecture {lecture_id: "CS230-Fall2025-LEC8"})
MATCH (t2:Topic {topic_id: "TOPIC-CNN"})
MERGE (lec1)-[r14:COVERED_TOPIC]->(t2)
ON CREATE SET
    r14.coverage_duration_minutes = 75,
    r14.depth = "Detailed",
    r14.created_at = datetime();
MATCH (lec1:Lecture {lecture_id: "CS230-Fall2025-LEC8"})
MATCH (n1:Note {note_id: "NOTE-2025-10-20-001"})
MERGE (lec1)-[r15:HAS_NOTE]->(n1)
ON CREATE SET r15.note_completeness = 0.95, r15.created_at = datetime();
MATCH (n1:Note {note_id: "NOTE-2025-10-20-001"})
MATCH (t2:Topic {topic_id: "TOPIC-CNN"})
MERGE (n1)-[r16:TAGGED_WITH_TOPIC]->(t2)
ON CREATE SET
    r16.tag_source = "Manual",
    r16.confidence = 1.0,
    r16.created_at = datetime();
MATCH (n1:Note {note_id: "NOTE-2025-10-20-001"})
MATCH (r1:Resource {resource_id: "RES-DeepLearningBook"})
MERGE (n1)-[rel1:CITES_RESOURCE]->(r1)
ON CREATE SET
    rel1.citation_type = "Reference",
    rel1.page_numbers = "326-350",
    rel1.created_at = datetime();
MATCH (q2:Quiz {quiz_id: "CS230-Fall2025-Quiz6"})
MATCH (ch1:Challenge_Area {challenge_id: "CHALLENGE-CNN-Pooling"})
MERGE (q2)-[r17:REVEALED_CHALLENGE]->(ch1)
ON CREATE SET
    r17.detection_date = datetime("2025-10-23T00:00:00"),
    r17.score = 60.0,
    r17.threshold = 70.0,
    r17.created_at = datetime();
MATCH (ch1:Challenge_Area {challenge_id: "CHALLENGE-CNN-Pooling"})
MATCH (c1:Course {course_id: "CS230-Fall2025"})
MERGE (ch1)-[r18:IN_COURSE]->(c1)
ON CREATE SET r18.created_at = datetime();
MATCH (ch1:Challenge_Area {challenge_id: "CHALLENGE-CNN-Pooling"})
MATCH (t2:Topic {topic_id: "TOPIC-CNN"})
MERGE (ch1)-[r19:RELATED_TO_TOPIC]->(t2)
ON CREATE SET
    r19.relevance_strength = 0.95,
    r19.is_root_cause = true,
    r19.created_at = datetime();
MATCH (td1:Study_Todo {todo_id: "TODO-2025-10-23-001"})
MATCH (ch1:Challenge_Area {challenge_id: "CHALLENGE-CNN-Pooling"})
MERGE (td1)-[r20:ADDRESSES_CHALLENGE]->(ch1)
ON CREATE SET
    r20.intervention_strategy = "Review",
    r20.created_at = datetime();
MATCH (td1:Study_Todo {todo_id: "TODO-2025-10-23-001"})
MATCH (n1:Note {note_id: "NOTE-2025-10-20-001"})
MERGE (td1)-[r21:REFERENCES_NOTE]->(n1)
ON CREATE SET
    r21.reference_type = "Primary Resource",
    r21.created_at = datetime();
MATCH (td2:Study_Todo {todo_id: "TODO-2025-10-23-002"})
MATCH (ch1:Challenge_Area {challenge_id: "CHALLENGE-CNN-Pooling"})
MERGE (td2)-[r22:ADDRESSES_CHALLENGE]->(ch1)
ON CREATE SET
    r22.intervention_strategy = "Practice",
    r22.created_at = datetime();
MATCH (t1:Topic {topic_id: "TOPIC-NeuralNetworks"})
MATCH (t2:Topic {topic_id: "TOPIC-CNN"})
MERGE (t1)-[r23:PREREQUISITE_FOR]->(t2)
ON CREATE SET
    r23.strength = "Essential",
    r23.estimated_gap_hours = 15,
    r23.created_at = datetime();
MATCH (t1:Topic {topic_id: "TOPIC-NeuralNetworks"})
MATCH (t3:Topic {topic_id: "TOPIC-RNN"})
MERGE (t1)-[r24:PREREQUISITE_FOR]->(t3)
ON CREATE SET
    r24.strength = "Essential",
    r24.estimated_gap_hours = 12,
    r24.created_at = datetime();
MATCH (t2:Topic {topic_id: "TOPIC-CNN"})
MATCH (r1:Resource {resource_id: "RES-DeepLearningBook"})
MERGE (t2)-[rel2:COVERED_IN_RESOURCE]->(r1)
ON CREATE SET
    rel2.chapter_section = "Chapter 9",
    rel2.coverage_quality = 0.95,
    rel2.difficulty_match = "Appropriate",
    rel2.created_at = datetime();
