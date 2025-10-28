"""
Comprehensive Academic Profile Test

This script creates a complete academic profile demonstrating all features:
- Student Profile with personal information
- Course enrollments (multiple courses)
- Assignments with due dates
- Exams and preparation
- Quizzes
- Lab sessions
- Study todos
- Challenge areas
- All relationships between entities

This provides a realistic example of a student's complete academic graph.
"""

import asyncio
import sys
from datetime import datetime, timedelta

# Add vertector-nats to path
sys.path.insert(0, '/Users/en_tetteh/Documents/vertector-nats-jetstream/src')

from vertector_nats import (
    NATSClient,
    NATSConfig,
    EventPublisher,
    ProfileCreatedEvent,
    ProfileEnrolledEvent,
    CourseCreatedEvent,
    AssignmentCreatedEvent,
    ExamCreatedEvent,
    QuizCreatedEvent,
    LabSessionCreatedEvent,
    StudyTodoCreatedEvent,
    ChallengeAreaCreatedEvent,
    EventMetadata,
)


class ComprehensiveAcademicProfileTest:
    """Creates a complete academic profile with all related entities."""

    def __init__(self):
        self.nats_config = NATSConfig(
            servers=["nats://localhost:4222"],
            client_name="comprehensive-academic-test"
        )
        self.nats_client = None
        self.publisher = None

        # Student information
        self.student_id = "S2025001"
        self.student_email = "alice.johnson@university.edu"
        self.student_first_name = "Alice"
        self.student_last_name = "Johnson"

        # Course IDs
        self.courses = {
            "CS101": "Introduction to Computer Science",
            "CS201": "Data Structures and Algorithms",
            "MATH301": "Linear Algebra",
        }

    async def setup(self):
        """Setup NATS connection."""
        print("🔧 Setting up NATS connection...")
        self.nats_client = NATSClient(self.nats_config)
        await self.nats_client.connect()
        self.publisher = EventPublisher(self.nats_client)
        print("✅ NATS connection established\n")

    async def cleanup(self):
        """Cleanup connections."""
        if self.nats_client:
            await self.nats_client.close()
        print("\n🧹 Cleanup complete")

    async def create_student_profile(self):
        """Create the student profile."""
        print("=" * 80)
        print("STEP 1: Creating Student Profile")
        print("=" * 80)

        profile_event = ProfileCreatedEvent(
            student_id=self.student_id,
            email=self.student_email,
            first_name=self.student_first_name,
            last_name=self.student_last_name,
            major="Computer Science",
            minor="Mathematics",
            year=3,
            student_type="Undergraduate",
            enrollment_status="Active",
            matriculation_date=datetime(2023, 9, 1),
            expected_graduation=datetime(2027, 5, 15),
            cumulative_gpa=3.85,
            phone="+1-555-0199",
            emergency_contact="+1-555-0200",
            academic_advisor="Dr. Sarah Mitchell",
            profile_picture_url="https://example.com/profiles/alice.jpg",
            metadata=EventMetadata(
                source_service="comprehensive-academic-test",
                correlation_id="profile-001",
            )
        )

        await self.publisher.publish(profile_event)
        print(f"✅ Created profile for {self.student_first_name} {self.student_last_name}")
        print(f"   Student ID: {self.student_id}")
        print(f"   Major: Computer Science, Minor: Mathematics")
        print(f"   Year: 3rd year, GPA: 3.85")
        await asyncio.sleep(2)

    async def create_courses_and_enrollments(self):
        """Create courses and enroll the student."""
        print("\n" + "=" * 80)
        print("STEP 2: Creating Courses and Enrollments")
        print("=" * 80)

        course_details = {
            "CS101": {
                "code": "CS",
                "number": "101",
                "term": "Spring 2025",
                "title": "Introduction to Computer Science",
                "description": "Fundamentals of programming, algorithms, and computational thinking",
                "credits": 4,
                "instructor": "Dr. Emily Chen",
                "instructor_email": "emily.chen@university.edu",
                "schedule": "MWF 10:00-11:00",
            },
            "CS201": {
                "code": "CS",
                "number": "201",
                "term": "Spring 2025",
                "title": "Data Structures and Algorithms",
                "description": "Advanced data structures, algorithm design and analysis, complexity theory",
                "credits": 4,
                "instructor": "Dr. Robert Kumar",
                "instructor_email": "robert.kumar@university.edu",
                "schedule": "TTh 14:00-16:00",
            },
            "MATH301": {
                "code": "MATH",
                "number": "301",
                "term": "Spring 2025",
                "title": "Linear Algebra",
                "description": "Vector spaces, linear transformations, eigenvalues and applications",
                "credits": 3,
                "instructor": "Dr. Maria Rodriguez",
                "instructor_email": "maria.rodriguez@university.edu",
                "schedule": "MWF 13:00-14:00",
            },
        }

        for course_id, details in course_details.items():
            # Create course
            course_event = CourseCreatedEvent(
                course_id=course_id,
                code=details["code"],
                number=details["number"],
                term=details["term"],
                title=details["title"],
                description=details["description"],
                credits=details["credits"],
                instructor_name=details["instructor"],
                instructor_email=details["instructor_email"],
                metadata=EventMetadata(
                    source_service="comprehensive-academic-test",
                    correlation_id=f"course-{course_id}",
                )
            )
            await self.publisher.publish(course_event)
            print(f"✅ Created course: {course_id} - {details['title']}")

            # Enroll student in course
            enrollment_event = ProfileEnrolledEvent(
                student_id=self.student_id,
                course_id=course_id,
                enrollment_date=datetime(2025, 1, 10),
                grading_basis="Letter",
                enrollment_status="Active",
                metadata=EventMetadata(
                    source_service="comprehensive-academic-test",
                    correlation_id=f"enrollment-{course_id}",
                )
            )
            await self.publisher.publish(enrollment_event)
            print(f"   └─ Enrolled {self.student_first_name} in {course_id}")

        await asyncio.sleep(3)

    async def create_assignments(self):
        """Create assignments for courses."""
        print("\n" + "=" * 80)
        print("STEP 3: Creating Assignments")
        print("=" * 80)

        assignments = [
            {
                "course_id": "CS101",
                "title": "Programming Fundamentals - Hello World",
                "description": "Write a program that prints 'Hello World' and demonstrates basic I/O",
                "type": "Homework",
                "due_date": datetime.now() + timedelta(days=7),
                "points": 10.0,
                "weight": 0.05,
            },
            {
                "course_id": "CS201",
                "title": "Implement Binary Search Tree",
                "description": "Design and implement a balanced BST with insert, delete, and search operations",
                "type": "Programming Assignment",
                "due_date": datetime.now() + timedelta(days=14),
                "points": 100.0,
                "weight": 0.15,
            },
            {
                "course_id": "CS201",
                "title": "Algorithm Analysis Report",
                "description": "Analyze time and space complexity of sorting algorithms",
                "type": "Written Assignment",
                "due_date": datetime.now() + timedelta(days=10),
                "points": 50.0,
                "weight": 0.10,
            },
            {
                "course_id": "MATH301",
                "title": "Matrix Operations Problem Set",
                "description": "Solve problems on matrix multiplication, determinants, and inverses",
                "type": "Homework",
                "due_date": datetime.now() + timedelta(days=5),
                "points": 30.0,
                "weight": 0.08,
            },
        ]

        for idx, assignment in enumerate(assignments):
            assignment_event = AssignmentCreatedEvent(
                assignment_id=f"A{datetime.now().strftime('%Y%m%d')}{idx+1:03d}",
                course_id=assignment["course_id"],
                student_id=self.student_id,
                title=assignment["title"],
                description=assignment["description"],
                type=assignment["type"],
                due_date=assignment["due_date"],
                points_possible=assignment["points"],
                weight=assignment["weight"],
                submission_types=["online_text_entry", "online_upload"],
                metadata=EventMetadata(
                    source_service="comprehensive-academic-test",
                    correlation_id=f"assignment-{idx+1:03d}",
                )
            )
            await self.publisher.publish(assignment_event)
            print(f"✅ Assignment: {assignment['title']} ({assignment['course_id']})")
            print(f"   Due: {assignment['due_date'].strftime('%Y-%m-%d')}, Points: {assignment['points']}")

        await asyncio.sleep(3)

    async def create_exams(self):
        """Create exams for courses."""
        print("\n" + "=" * 80)
        print("STEP 4: Creating Exams")
        print("=" * 80)

        exams = [
            {
                "course_id": "CS101",
                "title": "Midterm Exam",
                "type": "Midterm",
                "exam_date": datetime.now() + timedelta(days=30),
                "duration": 120,
                "points": 100.0,
                "weight": 0.25,
                "location": "Building A, Room 101",
                "topics": ["Variables and Data Types", "Control Structures", "Functions", "Arrays"],
            },
            {
                "course_id": "CS201",
                "title": "Final Exam",
                "type": "Final",
                "exam_date": datetime.now() + timedelta(days=90),
                "duration": 180,
                "points": 200.0,
                "weight": 0.35,
                "location": "Building B, Room 205",
                "topics": ["Trees", "Graphs", "Sorting Algorithms", "Dynamic Programming", "Complexity Analysis"],
            },
            {
                "course_id": "MATH301",
                "title": "Midterm Examination",
                "type": "Midterm",
                "exam_date": datetime.now() + timedelta(days=35),
                "duration": 90,
                "points": 100.0,
                "weight": 0.30,
                "location": "Math Building, Room 303",
                "topics": ["Vector Spaces", "Linear Transformations", "Matrix Theory"],
            },
        ]

        for idx, exam in enumerate(exams):
            exam_event = ExamCreatedEvent(
                exam_id=f"E{datetime.now().strftime('%Y%m%d')}{idx+1:03d}",
                course_id=exam["course_id"],
                student_id=self.student_id,
                title=exam["title"],
                date=exam["exam_date"],
                duration_minutes=exam["duration"],
                points_possible=int(exam["points"]),
                weight=exam["weight"],
                exam_type=exam["type"],
                location=exam["location"],
                topics_covered=exam["topics"],
                format="Mixed",
                preparation_notes=f"Review all lecture notes and complete practice problems for: {', '.join(exam['topics'])}",
                metadata=EventMetadata(
                    source_service="comprehensive-academic-test",
                    correlation_id=f"exam-{idx+1:03d}",
                )
            )
            await self.publisher.publish(exam_event)
            print(f"✅ Exam: {exam['title']} ({exam['course_id']})")
            print(f"   Date: {exam['exam_date'].strftime('%Y-%m-%d %H:%M')}, Duration: {exam['duration']} min")
            print(f"   Topics: {', '.join(exam['topics'][:3])}...")

        await asyncio.sleep(3)

    async def create_quizzes(self):
        """Create quizzes for courses."""
        print("\n" + "=" * 80)
        print("STEP 5: Creating Quizzes")
        print("=" * 80)

        quizzes = [
            {
                "course_id": "CS101",
                "title": "Week 3 Quiz: Control Structures",
                "quiz_date": datetime.now() + timedelta(days=3),
                "duration": 30,
                "points": 20.0,
                "weight": 0.05,
            },
            {
                "course_id": "CS201",
                "title": "Data Structures Quiz",
                "quiz_date": datetime.now() + timedelta(days=8),
                "duration": 45,
                "points": 25.0,
                "weight": 0.08,
            },
            {
                "course_id": "MATH301",
                "title": "Vector Spaces Quick Check",
                "quiz_date": datetime.now() + timedelta(days=4),
                "duration": 20,
                "points": 15.0,
                "weight": 0.05,
            },
        ]

        for idx, quiz in enumerate(quizzes):
            quiz_event = QuizCreatedEvent(
                quiz_id=f"Q{datetime.now().strftime('%Y%m%d')}{idx+1:03d}",
                course_id=quiz["course_id"],
                student_id=self.student_id,
                title=quiz["title"],
                quiz_number=idx + 1,
                date=quiz["quiz_date"],
                duration_minutes=quiz["duration"],
                points_possible=int(quiz["points"]),
                weight=quiz["weight"],
                format="Online",
                metadata=EventMetadata(
                    source_service="comprehensive-academic-test",
                    correlation_id=f"quiz-{idx+1:03d}",
                )
            )
            await self.publisher.publish(quiz_event)
            print(f"✅ Quiz: {quiz['title']}")
            print(f"   Date: {quiz['quiz_date'].strftime('%Y-%m-%d')}, Points: {quiz['points']}")

        await asyncio.sleep(2)

    async def create_labs(self):
        """Create lab sessions."""
        print("\n" + "=" * 80)
        print("STEP 6: Creating Lab Sessions")
        print("=" * 80)

        labs = [
            {
                "course_id": "CS101",
                "title": "Python Programming Lab",
                "experiment": "Introduction to Python REPL and Basic Syntax",
                "lab_date": datetime.now() + timedelta(days=2),
                "duration": 120,
                "location": "Computer Lab A",
            },
            {
                "course_id": "CS201",
                "title": "Algorithm Implementation Lab",
                "experiment": "Implementing QuickSort and MergeSort",
                "lab_date": datetime.now() + timedelta(days=9),
                "duration": 180,
                "location": "Computer Lab B",
            },
        ]

        for idx, lab in enumerate(labs):
            lab_event = LabSessionCreatedEvent(
                lab_id=f"L{datetime.now().strftime('%Y%m%d')}{idx+1:03d}",
                course_id=lab["course_id"],
                student_id=self.student_id,
                title=lab["title"],
                session_number=idx + 1,
                date=lab["lab_date"],
                duration_minutes=lab["duration"],
                location=lab["location"],
                instructor_name="Lab TA",
                experiment_title=lab["experiment"],
                objectives=[f"Complete hands-on exercises for {lab['experiment']}"],
                metadata=EventMetadata(
                    source_service="comprehensive-academic-test",
                    correlation_id=f"lab-{idx+1:03d}",
                )
            )
            await self.publisher.publish(lab_event)
            print(f"✅ Lab: {lab['title']} ({lab['course_id']})")
            print(f"   Experiment: {lab['experiment']}")
            print(f"   Date: {lab['lab_date'].strftime('%Y-%m-%d')}, Location: {lab['location']}")

        await asyncio.sleep(2)

    async def create_study_todos(self):
        """Create study todos."""
        print("\n" + "=" * 80)
        print("STEP 7: Creating Study Todos")
        print("=" * 80)

        todos = [
            {
                "course_id": "CS101",
                "title": "Review Python Basics",
                "description": "Go through chapters 1-3 and complete practice exercises",
                "priority": "High",
                "due_date": datetime.now() + timedelta(days=2),
            },
            {
                "course_id": "CS201",
                "title": "Practice Binary Tree Problems",
                "description": "Solve 10 BST problems on LeetCode",
                "priority": "Medium",
                "due_date": datetime.now() + timedelta(days=5),
            },
            {
                "course_id": "MATH301",
                "title": "Linear Transformation Exercises",
                "description": "Complete problem set 3.1-3.3 from textbook",
                "priority": "High",
                "due_date": datetime.now() + timedelta(days=3),
            },
            {
                "course_id": "CS201",
                "title": "Watch Algorithm Visualization Videos",
                "description": "Study sorting algorithm animations and understand time complexity",
                "priority": "Low",
                "due_date": datetime.now() + timedelta(days=7),
            },
        ]

        for idx, todo in enumerate(todos):
            todo_event = StudyTodoCreatedEvent(
                todo_id=f"T{datetime.now().strftime('%Y%m%d')}{idx+1:03d}",
                course_id=todo["course_id"],
                student_id=self.student_id,
                title=todo["title"],
                description=todo["description"],
                priority=todo["priority"],
                due_date=todo["due_date"],
                estimated_minutes=60,
                metadata=EventMetadata(
                    source_service="comprehensive-academic-test",
                    correlation_id=f"todo-{idx+1:03d}",
                )
            )
            await self.publisher.publish(todo_event)
            print(f"✅ Study Todo: {todo['title']} ({todo['course_id']})")
            print(f"   Priority: {todo['priority']}, Due: {todo['due_date'].strftime('%Y-%m-%d')}")

        await asyncio.sleep(2)

    async def create_challenge_areas(self):
        """Create challenge areas."""
        print("\n" + "=" * 80)
        print("STEP 8: Creating Challenge Areas")
        print("=" * 80)

        challenges = [
            {
                "course_id": "CS201",
                "title": "Graph Algorithms",
                "description": "Struggling with DFS/BFS traversal and shortest path algorithms",
                "difficulty": "Hard",
                "resources": ["Graph Theory Textbook Ch. 5", "YouTube: Graph Algorithms Playlist"],
            },
            {
                "course_id": "MATH301",
                "title": "Eigenvalues and Eigenvectors",
                "description": "Need more practice with eigenvalue decomposition and applications",
                "difficulty": "Medium",
                "resources": ["Linear Algebra Done Right - Chapter 8", "Khan Academy: Eigenvalues"],
            },
            {
                "course_id": "CS101",
                "title": "Recursion Concepts",
                "description": "Understanding recursive function calls and base cases",
                "difficulty": "Medium",
                "resources": ["SICP Chapter 1.2", "Recursion Practice Problems"],
            },
        ]

        for idx, challenge in enumerate(challenges):
            challenge_event = ChallengeAreaCreatedEvent(
                challenge_id=f"C{datetime.now().strftime('%Y%m%d')}{idx+1:03d}",
                course_id=challenge["course_id"],
                student_id=self.student_id,
                title=challenge["title"],
                description=challenge["description"],
                severity=challenge["difficulty"],
                detection_method="Self-Reported",
                confidence_level=7,
                metadata=EventMetadata(
                    source_service="comprehensive-academic-test",
                    correlation_id=f"challenge-{idx+1:03d}",
                )
            )
            await self.publisher.publish(challenge_event)
            print(f"✅ Challenge: {challenge['title']} ({challenge['course_id']})")
            print(f"   Difficulty: {challenge['difficulty']}")
            print(f"   Resources: {', '.join(challenge['resources'][:2])}")

        await asyncio.sleep(2)

    async def run_comprehensive_test(self):
        """Run the complete academic profile creation."""
        print("\n" + "=" * 80)
        print("COMPREHENSIVE ACADEMIC PROFILE TEST")
        print("=" * 80)
        print(f"\nCreating complete academic profile for {self.student_first_name} {self.student_last_name}")
        print(f"Student ID: {self.student_id}")
        print("=" * 80 + "\n")

        try:
            await self.setup()

            # Create all academic entities
            await self.create_student_profile()
            await self.create_courses_and_enrollments()
            await self.create_assignments()
            await self.create_exams()
            await self.create_quizzes()
            await self.create_labs()
            await self.create_study_todos()
            await self.create_challenge_areas()

            # Summary
            print("\n" + "=" * 80)
            print("SUMMARY - Academic Profile Created Successfully!")
            print("=" * 80)
            print(f"✅ Student Profile: {self.student_first_name} {self.student_last_name} ({self.student_id})")
            print(f"✅ Courses Enrolled: 3 (CS101, CS201, MATH301)")
            print(f"✅ Assignments: 4")
            print(f"✅ Exams: 3")
            print(f"✅ Quizzes: 3")
            print(f"✅ Lab Sessions: 2")
            print(f"✅ Study Todos: 4")
            print(f"✅ Challenge Areas: 3")
            print("=" * 80)
            print("\n⏳ Waiting 10 seconds for all events to be processed by GraphRAG...")
            await asyncio.sleep(10)

            print("\n✅ All events published successfully!")
            print("\nYou can now query the GraphRAG Neo4j database to see:")
            print("  • Profile node with all student information")
            print("  • Course nodes with details")
            print("  • Assignment, Exam, Quiz, Lab, Study_Todo, Challenge_Area nodes")
            print("  • ENROLLED_IN relationships (Profile → Course)")
            print("  • BELONGS_TO relationships (Academic entities → Course)")
            print("  • ASSIGNED_TO relationships (Assignments → Profile)")
            print("\nExample Cypher queries:")
            print("  1. MATCH (p:Profile {student_id: 'S2025001'}) RETURN p")
            print("  2. MATCH (p:Profile {student_id: 'S2025001'})-[:ENROLLED_IN]->(c:Course) RETURN p, c")
            print("  3. MATCH (a:Assignment)-[:ASSIGNED_TO]->(p:Profile {student_id: 'S2025001'}) RETURN a, p")
            print("  4. MATCH (p:Profile {student_id: 'S2025001'})-[:ENROLLED_IN]->(c:Course)<-[:BELONGS_TO]-(e) RETURN p, c, e")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.cleanup()


async def main():
    """Main entry point."""
    tester = ComprehensiveAcademicProfileTest()
    await tester.run_comprehensive_test()


if __name__ == "__main__":
    asyncio.run(main())
