# Entity Ownership Analysis: Which Entities Need student_id?

## Guiding Principle

**The Question**: "Can multiple students have different versions of this entity, or do all students share the same instance?"

- ✅ **Student-Specific (HAS student_id)**: Each student has their own version with their own data
- ❌ **Shared Entity (NO student_id)**: All students share the same instance

---

## Entity Classification

### 1. Profile
- **Type**: Student-Specific (BY DEFINITION)
- **student_id**: ✅ YES (it IS the student_id)
- **Reasoning**: Profile represents the student itself
- **Access Pattern**: Direct access (no enrollment needed)

---

### 2. Course
- **Type**: SHARED
- **student_id**: ❌ NO
- **Reasoning**:
  - Courses are shared academic offerings (e.g., CS301-Fall2025)
  - Multiple students enroll in the same course
  - Course properties (title, description, instructor) are identical for all students
- **Example**: CS301 "Graph Algorithms" taught by Prof. Smith - same for all enrolled students
- **Access Pattern**: `Profile → ENROLLED_IN → Course`
- **Status**: ✅ FIXED (removed student_id, consolidated duplicates)

---

### 3. Class_Schedule
- **Type**: SHARED
- **student_id**: ❌ NO
- **Reasoning**:
  - Represents when/where a course meets (Monday/Wednesday 2-3:30pm, Room 301)
  - All students in the course attend at the same time and location
  - Schedule properties are identical for all enrolled students
- **Example**: CS301 meets MWF 10-11am in Room 301 - same for all students
- **Access Pattern**: `Profile → ENROLLED_IN → Course → SCHEDULED_AS → Class_Schedule`
- **Status**: ✅ FIXED (removed student_id, consolidated duplicates)

---

### 4. Assignment
- **Type**: Student-Specific
- **student_id**: ✅ YES
- **Reasoning**:
  - Each student has their own submission, grade, and completion status
  - Student A's Assignment 1 grade ≠ Student B's Assignment 1 grade
  - Contains student-specific data: submission_date, grade_received, status, feedback
- **Example**: Assignment "HW1" - each student submits their own work and gets their own grade
- **Access Pattern**: `Profile → ENROLLED_IN → Course → HAS_ASSIGNMENT → Assignment`
- **Why Not Shared**: Although assignment instructions are the same, each student's work and grade is different

---

### 5. Exam
- **Type**: Student-Specific
- **student_id**: ✅ YES
- **Reasoning**:
  - Each student has their own exam performance, grade, and score
  - Student A's midterm score ≠ Student B's midterm score
  - Contains student-specific data: score_received, grade, performance_notes
- **Example**: Midterm Exam - each student takes it and receives their own score
- **Access Pattern**: `Profile → ENROLLED_IN → Course → HAS_EXAM → Exam`
- **Why Not Shared**: Although exam questions may be the same, each student's performance is different

---

### 6. Quiz
- **Type**: Student-Specific
- **student_id**: ✅ YES
- **Reasoning**:
  - Each student has their own quiz score and completion status
  - Contains student-specific data: score_received, completion_status, attempts
- **Example**: Quiz 1 on Chapter 3 - each student takes it and gets their own score
- **Access Pattern**: `Profile → ENROLLED_IN → Course → HAS_QUIZ → Quiz`

---

### 7. Lab_Session
- **Type**: Student-Specific
- **student_id**: ✅ YES
- **Reasoning**:
  - Each student has their own lab completion, submission, and feedback
  - Contains student-specific data: completion_status, lab_report, grade, feedback
- **Example**: Lab 5 "Sorting Algorithms" - each student completes the lab and submits their report
- **Access Pattern**: `Profile → ENROLLED_IN → Course → HAS_LAB → Lab_Session`
- **Why Not Shared**: Although lab instructions are the same, each student's work and results are different

---

### 8. Study_Todo
- **Type**: Student-Specific
- **student_id**: ✅ YES
- **Reasoning**:
  - Personal study tasks specific to each student's learning needs
  - Contains student-specific data: completion_status, priority, due_date
- **Example**: "Review Chapter 5 for midterm" - Student A may have this todo, Student B may not
- **Access Pattern**: `Profile → owns → Study_Todo` or via `Course → FOR_COURSE → Study_Todo`

---

### 9. Challenge_Area
- **Type**: Student-Specific
- **student_id**: ✅ YES
- **Reasoning**:
  - Identifies topics where a specific student struggles
  - Different students have different challenge areas
  - Contains student-specific data: difficulty_level, improvement_progress, identified_date
- **Example**: Student A struggles with "Dynamic Programming", Student B struggles with "Graph Theory"
- **Access Pattern**: `Profile → has → Challenge_Area` or via `Course → IDENTIFIED_IN_COURSE → Challenge_Area`

---

### 10. LectureNote
- **Type**: Student-Specific
- **student_id**: ✅ YES
- **Reasoning**:
  - Personal notes created by each student during lectures
  - Different students take different notes for the same lecture
  - Contains student-specific content, highlights, and summaries
- **Example**: Lecture on "BFS Algorithm" - each student writes their own notes
- **Access Pattern**: `Profile → ENROLLED_IN → Course ← BELONGS_TO ← LectureNote`

---

### 11. Topic
- **Type**: SHARED
- **student_id**: ❌ NO
- **Reasoning**:
  - Topics are universal academic concepts (e.g., "Dynamic Programming", "Machine Learning")
  - Topics are not course-specific or student-specific
  - Same topic can be referenced across multiple courses and students
- **Example**: Topic "Graph Traversal" - same concept for all students across all courses
- **Access Pattern**: Via relationships (COVERS_TOPIC, APPLIES_TOPIC, etc.)
- **Status**: Already correct (no student_id)

---

### 12. Resource
- **Type**: SHARED (with consideration)
- **student_id**: ❌ NO
- **Reasoning**:
  - Resources like textbooks, videos, articles are shared references
  - Same YouTube video URL, same textbook chapter - identical for all students
  - Resource metadata (title, URL, type) is universal
- **Example**: "Introduction to Algorithms" textbook - same for all students
- **Access Pattern**: Via relationships (REFERENCES_RESOURCE, COVERED_IN_RESOURCE, etc.)
- **Exception**: If we add personal annotations or bookmarks, those would be student-specific but stored separately

---

## Summary Table

| Entity | Has student_id? | Type | Reasoning |
|--------|----------------|------|-----------|
| **Profile** | ✅ YES | Student Identity | Is the student |
| **Course** | ❌ NO | Shared | Same course for all students |
| **Class_Schedule** | ❌ NO | Shared | Same schedule for all students in course |
| **Assignment** | ✅ YES | Student-Specific | Each student's work/grade is different |
| **Exam** | ✅ YES | Student-Specific | Each student's score is different |
| **Quiz** | ✅ YES | Student-Specific | Each student's score is different |
| **Lab_Session** | ✅ YES | Student-Specific | Each student's lab work is different |
| **Study_Todo** | ✅ YES | Student-Specific | Personal study tasks |
| **Challenge_Area** | ✅ YES | Student-Specific | Personal learning challenges |
| **LectureNote** | ✅ YES | Student-Specific | Personal notes |
| **Topic** | ❌ NO | Shared | Universal concepts |
| **Resource** | ❌ NO | Shared | Universal references |

---

## NATS Consumer Implementation

Based on this analysis, the NATS consumer should exclude these entities from receiving student_id:

```python
SHARED_ENTITIES = {
    "Course",           # Shared course offering
    "Class_Schedule",   # Shared schedule for course
    "Topic",            # Universal academic concepts
    "Resource",         # Shared references (books, videos, etc.)
}
```

All other entities should receive student_id for proper data isolation.

---

## Access Patterns

### Shared Entity Access
```
Profile → ENROLLED_IN → Course → SCHEDULED_AS → Class_Schedule
Profile → ENROLLED_IN → Course → COVERS_TOPIC → Topic
```

### Student-Specific Entity Access
```
Profile → ENROLLED_IN → Course → HAS_ASSIGNMENT → Assignment (student_id filter)
Profile → ENROLLED_IN → Course → HAS_EXAM → Exam (student_id filter)
Profile → owns → Study_Todo (direct via student_id)
Profile → owns → Challenge_Area (direct via student_id)
Profile → ENROLLED_IN → Course ← BELONGS_TO ← LectureNote (student_id filter)
```

---

## Data Isolation Principle

**Shared Entities**: Accessed via enrollment relationship, no student_id filtering needed
**Student-Specific Entities**: Accessed via enrollment + student_id filtering for security

This ensures:
- Students can only see their own grades, assignments, notes
- Students share the same course information, schedules, topics
- Proper multi-tenancy and data privacy
