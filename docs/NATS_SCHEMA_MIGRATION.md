# NATS JetStream to GraphRAG Note Service Schema Migration

## Overview

This document provides the complete mapping from current NATS JetStream event schemas to the GraphRAG Note Service schema. Use this as a reference to update the Pydantic models in `/Users/en_tetteh/Documents/vertector-nats-jetstream/src/vertector_nats/events.py`.

---

## 1. Course Events

### Current NATS Schema:
```python
class CourseCreatedEvent(BaseEvent):
    course_code: str              # e.g., "CS230-Fall2025"
    course_name: str              # e.g., "Deep Learning"
    semester: str                 # e.g., "Fall 2025"
    credits: int                  # e.g., 4
    instructor: str               # e.g., "Andrew Ng"
    instructor_email: Optional[str]
    difficulty_level: Optional[int]  # 1-10
    current_grade: Optional[float]
    is_challenging: Optional[bool]
    prerequisites: Optional[List[str]]
    corequisites: Optional[List[str]]
```

### Updated NATS Schema (GraphRAG Aligned):
```python
class CourseCreatedEvent(BaseEvent):
    # PRIMARY IDENTIFIER
    course_id: str                    # e.g., "CS230-Fall2025" (maps to course_code)

    # CORE FIELDS
    title: str                        # e.g., "Deep Learning" (was: course_name)
    code: str                         # e.g., "CS" (department code, extracted from course_id)
    number: str                       # e.g., "230" (course number, extracted from course_id)
    term: str                         # e.g., "Fall 2025" (was: semester)
    credits: int                      # e.g., 4 (unchanged)
    description: str                  # Full course description (NEW - required)

    # INSTRUCTOR INFORMATION
    instructor_name: str              # e.g., "Andrew Ng" (was: instructor)
    instructor_email: str             # e.g., "ang@cs.stanford.edu" (now required)

    # COURSE STRUCTURE
    component_type: List[str]         # e.g., ["LEC", "DIS", "LAB"] (NEW)
    prerequisites: List[str] = []     # e.g., ["CS229-Spring2025", "MATH51-Winter2025"]
    grading_options: List[str]        # e.g., ["Letter", "S/NC"] (NEW)

    # ADDITIONAL INFORMATION
    syllabus_url: Optional[str] = None           # URL to course syllabus (NEW)
    learning_objectives: List[str] = []          # List of learning goals (NEW)
    final_exam_date: Optional[datetime] = None   # Final exam datetime (NEW)
```

**Migration Notes:**
- Remove: `difficulty_level`, `current_grade`, `is_challenging`, `corequisites`
- Rename: `course_code` → `course_id`, `course_name` → `title`, `semester` → `term`, `instructor` → `instructor_name`
- Add: `description`, `code`, `number`, `component_type`, `grading_options`, `syllabus_url`, `learning_objectives`, `final_exam_date`

---

## 2. Assignment Events

### Current NATS Schema:
```python
class AssignmentCreatedEvent(BaseEvent):
    assignment_id: str
    course_code: str
    title: str
    due_date: datetime
    description: Optional[str]
    estimated_hours: Optional[int]
    total_points: Optional[int]
    weight_percentage: Optional[float]
    status: Optional[str]  # "Not Started", "In Progress", "Submitted"
```

### Updated NATS Schema (GraphRAG Aligned):
```python
class AssignmentCreatedEvent(BaseEvent):
    # PRIMARY IDENTIFIER
    assignment_id: str                # e.g., "CS230-Fall2025-PS3" (unchanged)

    # CORE FIELDS
    title: str                        # e.g., "Programming Assignment 3: Neural Style Transfer"
    course_id: str                    # e.g., "CS230-Fall2025" (was: course_code)
    type: str                         # e.g., "Programming", "Problem Set", "Essay", "Project" (NEW)
    description: str                  # Full assignment description (now required)
    due_date: datetime                # e.g., "2025-11-05T23:00:00" (unchanged)

    # GRADING INFORMATION
    points_possible: int              # e.g., 100 (was: total_points)
    points_earned: Optional[float] = None     # e.g., 95 (NEW)
    percentage_grade: Optional[float] = None  # e.g., 95.0 (NEW)
    weight: float                     # e.g., 0.15 (was: weight_percentage as decimal)

    # SUBMISSION TRACKING
    submission_status: str = "Not Started"    # "Not Started", "In Progress", "Submitted", "Graded" (was: status)
    submission_url: Optional[str] = None      # URL to submission (NEW)
    instructions_url: Optional[str] = None    # URL to instructions (NEW)

    # EFFORT ESTIMATION
    estimated_hours: Optional[int] = None     # e.g., 12 (unchanged)

    # GRADING DETAILS
    late_penalty: Optional[str] = None        # e.g., "10% per day, maximum 3 days" (NEW)
    rubric: Optional[List[Dict[str, Any]]] = None  # [{"criterion": "...", "points": 30}] (NEW)
```

**Migration Notes:**
- Rename: `course_code` → `course_id`, `total_points` → `points_possible`, `status` → `submission_status`, `weight_percentage` → `weight` (convert to decimal)
- Add: `type`, `points_earned`, `percentage_grade`, `submission_url`, `instructions_url`, `late_penalty`, `rubric`
- Make `description` required (was optional)

---

## 3. Exam Events

### Current NATS Schema:
```python
class ExamCreatedEvent(BaseEvent):
    exam_id: str
    course_code: str
    exam_name: str
    exam_type: str          # "Midterm", "Final", "Quiz"
    exam_date: datetime
    duration_minutes: Optional[int]
    total_points: Optional[int]
    topics_covered: Optional[List[str]]
    location: Optional[str]
```

### Updated NATS Schema (GraphRAG Aligned):
```python
class ExamCreatedEvent(BaseEvent):
    # PRIMARY IDENTIFIER
    exam_id: str                      # e.g., "CS230-Fall2025-Midterm"

    # CORE FIELDS
    title: str                        # e.g., "Midterm Examination" (was: exam_name)
    course_id: str                    # e.g., "CS230-Fall2025" (was: course_code)
    exam_type: str                    # "Midterm", "Final", "Cumulative" (unchanged)
    date: datetime                    # e.g., "2025-11-06T18:00:00" (was: exam_date)
    duration_minutes: int             # e.g., 180 (now required)
    location: str                     # e.g., "Memorial Auditorium" (now required)

    # GRADING INFORMATION
    points_possible: int              # e.g., 100 (was: total_points, now required)
    points_earned: Optional[float] = None     # e.g., 87 (NEW)
    percentage_grade: Optional[float] = None  # e.g., 87.0 (NEW)
    weight: float                     # e.g., 0.25 (NEW - exam weight in course grade)

    # EXAM CONTENT
    topics_covered: List[str] = []    # e.g., ["Neural Networks", "CNNs"] (unchanged)
    format: str                       # "Multiple Choice", "Essay", "Mixed" (NEW)
    open_book: bool = False           # Whether exam is open book (NEW)
    allowed_materials: List[str] = [] # e.g., ["One formula sheet", "Calculator"] (NEW)
    preparation_notes: Optional[str] = None   # Study guidance (NEW)
```

**Migration Notes:**
- Rename: `exam_name` → `title`, `course_code` → `course_id`, `exam_date` → `date`, `total_points` → `points_possible`
- Make required: `duration_minutes`, `location`, `points_possible`
- Add: `points_earned`, `percentage_grade`, `weight`, `format`, `open_book`, `allowed_materials`, `preparation_notes`

---

## 4. Quiz Events

### Current NATS Schema:
```python
class QuizCreatedEvent(BaseEvent):
    quiz_id: str
    course_code: str
    quiz_date: datetime
    duration_minutes: Optional[int]
    total_points: Optional[int]
    topics: Optional[List[str]]
```

### Updated NATS Schema (GraphRAG Aligned):
```python
class QuizCreatedEvent(BaseEvent):
    # PRIMARY IDENTIFIER
    quiz_id: str                      # e.g., "CS230-Fall2025-Quiz5"

    # CORE FIELDS
    title: str                        # e.g., "Week 5 Quiz: RNNs and LSTMs" (NEW)
    course_id: str                    # e.g., "CS230-Fall2025" (was: course_code)
    quiz_number: int                  # e.g., 5 (NEW)
    date: datetime                    # e.g., "2025-10-15T11:00:00" (was: quiz_date)
    duration_minutes: int             # e.g., 30 (now required)

    # GRADING INFORMATION
    points_possible: int              # e.g., 10 (was: total_points, now required)
    points_earned: Optional[float] = None     # e.g., 8 (NEW)
    percentage_grade: Optional[float] = None  # e.g., 80.0 (NEW)
    weight: float                     # e.g., 0.02 (NEW)

    # QUIZ DETAILS
    topics_covered: List[str] = []    # e.g., ["RNNs", "LSTM"] (was: topics)
    format: str = "Online"            # "Online" or "In-Class" (NEW)
    attempts_allowed: int = 1         # Number of attempts (NEW)
    auto_graded: bool = True          # Whether auto-graded (NEW)
```

**Migration Notes:**
- Rename: `course_code` → `course_id`, `quiz_date` → `date`, `topics` → `topics_covered`, `total_points` → `points_possible`
- Make required: `duration_minutes`, `points_possible`
- Add: `title`, `quiz_number`, `points_earned`, `percentage_grade`, `weight`, `format`, `attempts_allowed`, `auto_graded`

---

## 5. Lab Session Events

### Current NATS Schema:
```python
class LabSessionCreatedEvent(BaseEvent):
    lab_id: str
    course_code: str
    lab_number: int
    lab_date: datetime
    topic: Optional[str]
    objectives: Optional[List[str]]
```

### Updated NATS Schema (GraphRAG Aligned):
```python
class LabSessionCreatedEvent(BaseEvent):
    # PRIMARY IDENTIFIER
    lab_id: str                       # e.g., "CHEM31A-Fall2025-Lab3"

    # CORE FIELDS
    title: str                        # e.g., "Acid-Base Titration" (NEW)
    course_id: str                    # e.g., "CHEM31A-Fall2025" (was: course_code)
    session_number: int               # e.g., 3 (was: lab_number)
    date: datetime                    # e.g., "2025-10-18T14:00:00" (was: lab_date)
    duration_minutes: int             # e.g., 240 (NEW - typically 2-6 hours)
    location: str                     # e.g., "Keck Science Building, Lab 102" (NEW)

    # INSTRUCTOR INFORMATION
    instructor_name: str              # e.g., "Dr. Sarah Martinez" (NEW - TA or lab instructor)

    # LAB CONTENT
    experiment_title: str             # e.g., "Determination of Acetic Acid..." (was: topic)
    objectives: List[str] = []        # e.g., ["Practice pipetting", ...] (unchanged)

    # PREPARATION
    pre_lab_reading: Optional[str] = None           # e.g., "Lab Manual Chapter 5" (NEW)
    pre_lab_assignment_due: Optional[datetime] = None  # Pre-lab deadline (NEW)
    equipment_needed: List[str] = []                # e.g., ["Burette", "Pipette"] (NEW)
    safety_requirements: List[str] = []             # e.g., ["Lab Coat", "Goggles"] (NEW)

    # GRADING INFORMATION
    submission_deadline: Optional[datetime] = None  # Lab report deadline (NEW)
    points_possible: Optional[int] = None           # e.g., 50 (NEW)
    points_earned: Optional[float] = None           # e.g., 47 (NEW)
```

**Migration Notes:**
- Rename: `course_code` → `course_id`, `lab_number` → `session_number`, `lab_date` → `date`, `topic` → `experiment_title`
- Add: `title`, `duration_minutes`, `location`, `instructor_name`, `pre_lab_reading`, `pre_lab_assignment_due`, `equipment_needed`, `safety_requirements`, `submission_deadline`, `points_possible`, `points_earned`

---

## 6. Study Todo Events

### Current NATS Schema:
```python
class StudyTodoCreatedEvent(BaseEvent):
    todo_id: str
    course_code: str
    topic: str
    task: str
    priority: int              # 1-5
    estimated_time: int        # minutes
    materials_needed: Optional[List[str]]
    timeline: Optional[str]
    associated_exam: Optional[str]
```

### Updated NATS Schema (GraphRAG Aligned):
```python
class StudyTodoCreatedEvent(BaseEvent):
    # PRIMARY IDENTIFIER
    todo_id: str                      # e.g., "TODO-2025-10-001"

    # CORE FIELDS
    title: str                        # e.g., "Review lecture notes on CNNs" (was: topic + task combined)
    course_id: str                    # e.g., "CS230-Fall2025" (was: course_code)
    description: str                  # Detailed description (was: task, now more detailed)

    # PRIORITY AND STATUS
    priority: str                     # "High", "Medium", "Low" (was: int 1-5, convert: 1-2=High, 3=Medium, 4-5=Low)
    status: str = "Next Action"       # "Next Action", "Waiting For", "Someday/Maybe", "Completed" (NEW)

    # TIME TRACKING
    due_date: Optional[datetime] = None       # Task deadline (was: timeline, now datetime)
    estimated_minutes: int            # e.g., 90 (was: estimated_time in minutes)
    actual_minutes: Optional[int] = None      # Actual time spent (NEW)

    # GTD METHODOLOGY
    context: List[str] = []           # e.g., ["@Library", "@Computer"] (was: materials_needed, different purpose)
    energy_required: str = "Medium"   # "High", "Medium", "Low" (NEW)

    # METADATA
    created_date: datetime            # When todo was created (NEW)
    completed_date: Optional[datetime] = None  # When completed (NEW)
    recurrence: str = "None"          # "Daily", "Weekly", "None" (NEW)
    ai_generated: bool = False        # Whether AI-created (NEW)
    source: str = "User"              # "User", "AI-Assignment", "AI-Challenge" (NEW)
```

**Migration Notes:**
- Combine `topic` + `task` into `title` and `description`
- Convert `priority` from int (1-5) to string ("High"/"Medium"/"Low"): 1-2 → "High", 3 → "Medium", 4-5 → "Low"
- Rename: `course_code` → `course_id`, `estimated_time` → `estimated_minutes`
- Restructure: `materials_needed` → `context` (different GTD concept), `timeline` → `due_date` (parse to datetime)
- Add: `status`, `actual_minutes`, `energy_required`, `created_date`, `completed_date`, `recurrence`, `ai_generated`, `source`
- Remove: `associated_exam` (handle via relationships instead)

---

## 7. Challenge Area Events

### Current NATS Schema:
```python
class ChallengeAreaCreatedEvent(BaseEvent):
    challenge_id: str
    course_code: str
    subject: str
    topic: str
    difficulty_level: int       # 1-10
    description: Optional[str]
    specific_concepts: Optional[List[str]]
    root_causes: Optional[List[str]]
    recommended_resources: Optional[List[str]]
```

### Updated NATS Schema (GraphRAG Aligned):
```python
class ChallengeAreaCreatedEvent(BaseEvent):
    # PRIMARY IDENTIFIER
    challenge_id: str                 # e.g., "CHALLENGE-CS230-Integration"

    # CORE FIELDS
    title: str                        # e.g., "Calculus - Integration Techniques" (was: subject + topic combined)
    course_id: str                    # e.g., "CS230-Fall2025" (was: course_code)
    description: str                  # Detailed problem description (now required)

    # SEVERITY ASSESSMENT
    severity: str                     # "Critical", "Moderate", "Minor" (was: difficulty_level int)
                                     # Convert: 8-10 → "Critical", 4-7 → "Moderate", 1-3 → "Minor"

    # TRACKING
    identified_date: datetime         # When challenge was identified (NEW)
    detection_method: str             # "AI-Performance", "Self-Reported", "Instructor-Flagged" (NEW)
    status: str = "Active"            # "Active", "Improving", "Resolved" (NEW)
    resolution_date: Optional[datetime] = None  # When resolved (NEW)

    # PERFORMANCE DATA
    performance_trend: List[float] = []    # Recent grades [65.0, 58.0, 62.0, 55.0] (NEW)
    confidence_level: int             # 1-10 scale (was: difficulty_level, repurposed)

    # RELATED INFORMATION
    related_topics: List[str] = []    # e.g., ["Integration by Parts"] (was: specific_concepts)
    improvement_notes: Optional[str] = None  # Guidance notes (was: root_causes + recommended_resources combined)
```

**Migration Notes:**
- Combine `subject` + `topic` into `title`
- Convert `difficulty_level` (1-10 int) to `severity` (string): 8-10 → "Critical", 4-7 → "Moderate", 1-3 → "Minor"
- Repurpose `difficulty_level` as `confidence_level` (how confident about the challenge)
- Rename: `course_code` → `course_id`, `specific_concepts` → `related_topics`
- Combine `root_causes` + `recommended_resources` into `improvement_notes` (string)
- Add: `identified_date`, `detection_method`, `status`, `resolution_date`, `performance_trend`
- **Note**: Embeddings will be auto-generated by DataLoader from title + description

---

## 8. Class Schedule Events

### Current NATS Schema:
```python
class ClassScheduleCreatedEvent(BaseEvent):
    schedule_id: str
    course_code: str
    day_of_week: str          # "Monday", "Tuesday", etc.
    start_time: str           # "10:30"
    end_time: str             # "12:00"
    semester: str             # "Fall 2025"
    location: Optional[str]
    notes: Optional[str]
    recurring: bool = True
```

### Updated NATS Schema (GraphRAG Aligned):
```python
class ClassScheduleCreatedEvent(BaseEvent):
    # PRIMARY IDENTIFIER
    schedule_id: str                  # e.g., "CS230-Fall2025-LEC-01"

    # CORE FIELDS
    course_id: str                    # e.g., "CS230-Fall2025" (was: course_code)
    days_of_week: List[str]           # e.g., ["Tuesday", "Thursday"] (was: day_of_week single)
    start_time: str                   # e.g., "11:30:00" (HH:MM:SS format)
    end_time: str                     # e.g., "13:00:00" (HH:MM:SS format)

    # LOCATION DETAILS
    building: str                     # e.g., "NVIDIA Auditorium" (was: location, now split)
    room: str                         # e.g., "Main Hall" (NEW - extracted from location)
    campus: str = "Main Campus"       # Campus location (NEW)

    # FORMAT
    format: str                       # "F2F", "Online", "Hybrid" (NEW)
    meeting_url: Optional[str] = None # Zoom/Teams URL (was: notes, repurposed)

    # INSTRUCTOR AVAILABILITY
    instructor_office_hours: List[str] = []  # e.g., ["Wednesday 14:00-16:00 Gates 288"] (NEW)

    # SECTION INFORMATION
    section_number: str               # e.g., "01" (NEW)
    enrollment_capacity: int          # e.g., 180 (NEW)

    # TERM DATES
    term_start_date: date             # e.g., "2025-09-24" (NEW)
    term_end_date: date               # e.g., "2025-12-06" (NEW)
```

**Migration Notes:**
- Rename: `course_code` → `course_id`, `day_of_week` → `days_of_week` (now list)
- Change `days_of_week` from single string to list (can have multiple days)
- Split `location` into `building` + `room` + `campus`
- Repurpose `notes` as `meeting_url` for online meetings
- Remove `recurring` and `semester` (handled by term dates)
- Add: `format`, `instructor_office_hours`, `section_number`, `enrollment_capacity`, `term_start_date`, `term_end_date`

---

## Field Type Conversions

### Priority Conversion (Study_Todo)
```python
def convert_priority(nats_priority: int) -> str:
    """Convert NATS priority (1-5) to GraphRAG priority."""
    if nats_priority <= 2:
        return "High"
    elif nats_priority == 3:
        return "Medium"
    else:  # 4-5
        return "Low"
```

### Severity Conversion (Challenge_Area)
```python
def convert_severity(difficulty_level: int) -> str:
    """Convert NATS difficulty (1-10) to GraphRAG severity."""
    if difficulty_level >= 8:
        return "Critical"
    elif difficulty_level >= 4:
        return "Moderate"
    else:  # 1-3
        return "Minor"
```

### Weight Percentage Conversion (Assignment)
```python
def convert_weight(weight_percentage: Optional[float]) -> float:
    """Convert percentage (0-100) to decimal (0-1)."""
    if weight_percentage is None:
        return 0.0
    return weight_percentage / 100.0
```

---

## Implementation Checklist

### In vertector-nats-jetstream project:

- [ ] Update `src/vertector_nats/events.py` with new Pydantic models
- [ ] Add conversion utility functions for priority, severity, weight
- [ ] Update publisher examples to use new schema
- [ ] Update consumer examples to handle new fields
- [ ] Add validation for new required fields
- [ ] Update documentation (README.md, QUICKSTART.md)
- [ ] Update tests to match new schema
- [ ] Add migration guide for existing consumers

### In graphrag project:

- [ ] Create NATS consumer service using updated events
- [ ] Integrate with existing DataLoader for embedding generation
- [ ] Add idempotency tracking for event_id
- [ ] Implement event handlers for create/update/delete
- [ ] Add monitoring and metrics
- [ ] Create end-to-end integration tests

---

## Example: Updated Course Event

```python
# Before (Old NATS Schema)
CourseCreatedEvent(
    event_id="evt_123",
    event_type="academic.course.created",
    timestamp=datetime.utcnow(),
    course_code="CS230-Fall2025",
    course_name="Deep Learning",
    semester="Fall 2025",
    credits=4,
    instructor="Andrew Ng",
    instructor_email="ang@cs.stanford.edu",
    prerequisites=["CS229-Spring2025"],
    metadata=EventMetadata(source_service="schedule-service")
)

# After (GraphRAG-Aligned NATS Schema)
CourseCreatedEvent(
    event_id="evt_123",
    event_type="academic.course.created",
    timestamp=datetime.utcnow(),
    course_id="CS230-Fall2025",
    title="Deep Learning",
    code="CS",
    number="230",
    term="Fall 2025",
    credits=4,
    description="Introduction to deep learning with focus on neural networks, CNNs, RNNs, and transformers. Hands-on implementation using PyTorch.",
    instructor_name="Andrew Ng",
    instructor_email="ang@cs.stanford.edu",
    component_type=["LEC", "DIS"],
    prerequisites=["CS229-Spring2025", "MATH51-Winter2025"],
    grading_options=["Letter", "S/NC"],
    syllabus_url="https://cs230.stanford.edu/syllabus/",
    learning_objectives=[
        "Understand neural network architectures",
        "Implement CNNs for computer vision tasks",
        "Build sequence models with RNNs and transformers",
        "Apply deep learning to real-world projects"
    ],
    final_exam_date=datetime(2025, 12, 13, 18, 0, 0),
    metadata=EventMetadata(source_service="schedule-service")
)
```

---

## Next Steps

1. **Update NATS Event Schemas**: Apply all changes to `/Users/en_tetteh/Documents/vertector-nats-jetstream/src/vertector_nats/events.py`
2. **Test Publishers**: Ensure all publishers can create events with new schema
3. **Update Consumers**: Modify any existing consumers to handle new fields
4. **Create GraphRAG Consumer**: Build the Note Service NATS consumer with direct DataLoader integration
5. **End-to-End Testing**: Verify data flows from NATS → Neo4j with embeddings

---

**Document Version**: 1.0
**Last Updated**: 2025-10-24
**Author**: GraphRAG Integration Team
