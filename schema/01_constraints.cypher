// ============================================================================
// ACADEMIC NOTE-TAKING GRAPHRAG SYSTEM - CONSTRAINTS
// ============================================================================
// Neo4j Version: 5.26 (2025.09.0-community-bullseye)
// Edition: Community Edition
// ============================================================================
// COMMUNITY EDITION CAPABILITIES:
//   ✅ UNIQUENESS constraints
//   ❌ PROPERTY TYPE constraints (Enterprise only)
//   ❌ NODE KEY constraints (Enterprise only)
//   ❌ PROPERTY EXISTENCE constraints (Enterprise only)
//
// VALIDATION STRATEGY:
//   1. Database-level: Uniqueness constraints (this file)
//   2. Application-level: Required fields + type validation via DataLoader
//   3. Optional: APOC triggers for advanced validation (see comments)
// ============================================================================

// ============================================================================
// PROFILE CONSTRAINTS
// ============================================================================

CREATE CONSTRAINT profile_student_id_unique IF NOT EXISTS
FOR (p:Profile) REQUIRE p.student_id IS UNIQUE;

CREATE CONSTRAINT profile_email_unique IF NOT EXISTS
FOR (p:Profile) REQUIRE p.email IS UNIQUE;


// ============================================================================
// COURSE CONSTRAINTS
// ============================================================================

CREATE CONSTRAINT course_id_unique IF NOT EXISTS
FOR (c:Course) REQUIRE c.course_id IS UNIQUE;


// ============================================================================
// ASSIGNMENT CONSTRAINTS
// ============================================================================

CREATE CONSTRAINT assignment_id_unique IF NOT EXISTS
FOR (a:Assignment) REQUIRE a.assignment_id IS UNIQUE;


// ============================================================================
// EXAM CONSTRAINTS
// ============================================================================

CREATE CONSTRAINT exam_id_unique IF NOT EXISTS
FOR (e:Exam) REQUIRE e.exam_id IS UNIQUE;


// ============================================================================
// QUIZ CONSTRAINTS
// ============================================================================

CREATE CONSTRAINT quiz_id_unique IF NOT EXISTS
FOR (q:Quiz) REQUIRE q.quiz_id IS UNIQUE;


// ============================================================================
// LAB_SESSION CONSTRAINTS
// ============================================================================

CREATE CONSTRAINT lab_id_unique IF NOT EXISTS
FOR (l:Lab_Session) REQUIRE l.lab_id IS UNIQUE;


// ============================================================================
// STUDY_TODO CONSTRAINTS
// ============================================================================

CREATE CONSTRAINT todo_id_unique IF NOT EXISTS
FOR (t:Study_Todo) REQUIRE t.todo_id IS UNIQUE;


// ============================================================================
// CHALLENGE_AREA CONSTRAINTS
// ============================================================================

CREATE CONSTRAINT challenge_id_unique IF NOT EXISTS
FOR (ca:Challenge_Area) REQUIRE ca.challenge_id IS UNIQUE;


// ============================================================================
// CLASS_SCHEDULE CONSTRAINTS
// ============================================================================

CREATE CONSTRAINT schedule_id_unique IF NOT EXISTS
FOR (cs:Class_Schedule) REQUIRE cs.schedule_id IS UNIQUE;


// ============================================================================
// NOTE CONSTRAINTS
// ============================================================================

CREATE CONSTRAINT note_id_unique IF NOT EXISTS
FOR (n:Note) REQUIRE n.note_id IS UNIQUE;


// ============================================================================
// LECTURE CONSTRAINTS
// ============================================================================

CREATE CONSTRAINT lecture_id_unique IF NOT EXISTS
FOR (lec:Lecture) REQUIRE lec.lecture_id IS UNIQUE;


// ============================================================================
// TOPIC CONSTRAINTS
// ============================================================================

CREATE CONSTRAINT topic_id_unique IF NOT EXISTS
FOR (t:Topic) REQUIRE t.topic_id IS UNIQUE;


// ============================================================================
// RESOURCE CONSTRAINTS
// ============================================================================

CREATE CONSTRAINT resource_id_unique IF NOT EXISTS
FOR (r:Resource) REQUIRE r.resource_id IS UNIQUE;


// ============================================================================
// ADVANCED VALIDATION OPTIONS (OPTIONAL)
// ============================================================================
// For validation beyond uniqueness constraints, consider:
//
// 1. APPLICATION-LEVEL VALIDATION (RECOMMENDED)
//    - Already implemented in DataLoader class
//    - Validates required fields before database insertion
//    - Path: src/note_service/ingestion/data_loader.py
//
// 2. APOC TRIGGERS (OPTIONAL - for direct Cypher access)
//    - Enables database-level validation when bypassing application layer
//    - Requires: dbms.security.procedures.unrestricted=apoc.trigger.*
//
//    Example: Email format validation
//    --------------------------------
//    CALL apoc.trigger.add(
//      'validateEmail',
//      'UNWIND apoc.trigger.nodesByLabel({assignedNodeProperties}, "Profile") AS node
//       WITH node WHERE node.email IS NOT NULL
//       CALL apoc.util.validate(
//         NOT node.email =~ "^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$",
//         "Invalid email format: %s", [node.email]
//       ) RETURN null',
//      {phase: 'before'}
//    );
//
//    Example: Required field validation
//    ----------------------------------
//    CALL apoc.trigger.add(
//      'validateNoteRequiredFields',
//      'UNWIND apoc.trigger.nodesByLabel({createdNodes}, "Note") AS node
//       CALL apoc.util.validate(
//         node.title IS NULL OR node.content IS NULL,
//         "Note requires both title and content", []
//       ) RETURN null',
//      {phase: 'before'}
//    );
//
//    To list active triggers: CALL apoc.trigger.list();
//    To remove a trigger: CALL apoc.trigger.remove('triggerName');
//
// 3. QUERY-LEVEL VALIDATION
//    - Add COALESCE() or CASE for default values in MERGE/CREATE
//
//    Example:
//    -------
//    MERGE (n:Note {note_id: $id})
//    ON CREATE SET
//      n.title = COALESCE($title, "Untitled"),
//      n.content = COALESCE($content, ""),
//      n.created_date = COALESCE($created_date, datetime())
//
// ============================================================================


// ============================================================================
// VERIFICATION QUERIES
// ============================================================================
// Run these to verify constraint creation:
//
// Show all constraints:
// SHOW CONSTRAINTS;
//
// Show uniqueness constraints only:
// SHOW CONSTRAINTS YIELD name, type WHERE type = "UNIQUENESS" RETURN name;
//
// Count constraints:
// SHOW CONSTRAINTS YIELD type RETURN type, count(*) AS count ORDER BY count DESC;
// ============================================================================
