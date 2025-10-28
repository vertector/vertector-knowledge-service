"""
============================================================================
Academic Note-Taking GraphRAG System - Pydantic Models
============================================================================
Type-safe data models for all graph entities
============================================================================
"""

from .profile import Profile, ProfileCreate, ProfileUpdate
from .course import Course, CourseCreate, CourseUpdate
from .note import Note, NoteCreate, NoteUpdate
from .topic import Topic, TopicCreate, TopicUpdate
from .assignment import Assignment, AssignmentCreate, AssignmentUpdate
from .exam import Exam, ExamCreate, ExamUpdate
from .quiz import Quiz, QuizCreate, QuizUpdate
from .lab_session import LabSession, LabSessionCreate, LabSessionUpdate
from .study_todo import StudyTodo, StudyTodoCreate, StudyTodoUpdate
from .challenge_area import ChallengeArea, ChallengeAreaCreate, ChallengeAreaUpdate
from .class_schedule import ClassSchedule, ClassScheduleCreate, ClassScheduleUpdate
from .lecture import Lecture, LectureCreate, LectureUpdate
from .resource import Resource, ResourceCreate, ResourceUpdate

__all__ = [
    # Profile
    "Profile",
    "ProfileCreate",
    "ProfileUpdate",
    # Course
    "Course",
    "CourseCreate",
    "CourseUpdate",
    # Note
    "Note",
    "NoteCreate",
    "NoteUpdate",
    # Topic
    "Topic",
    "TopicCreate",
    "TopicUpdate",
    # Assignment
    "Assignment",
    "AssignmentCreate",
    "AssignmentUpdate",
    # Exam
    "Exam",
    "ExamCreate",
    "ExamUpdate",
    # Quiz
    "Quiz",
    "QuizCreate",
    "QuizUpdate",
    # Lab Session
    "LabSession",
    "LabSessionCreate",
    "LabSessionUpdate",
    # Study Todo
    "StudyTodo",
    "StudyTodoCreate",
    "StudyTodoUpdate",
    # Challenge Area
    "ChallengeArea",
    "ChallengeAreaCreate",
    "ChallengeAreaUpdate",
    # Class Schedule
    "ClassSchedule",
    "ClassScheduleCreate",
    "ClassScheduleUpdate",
    # Lecture
    "Lecture",
    "LectureCreate",
    "LectureUpdate",
    # Resource
    "Resource",
    "ResourceCreate",
    "ResourceUpdate",
]
