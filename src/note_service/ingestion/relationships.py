"""
============================================================================
Relationship Configuration and Management for GraphRAG Knowledge Graph
============================================================================
Implements all 32 relationship types from schema/04_relationships.cypher

Provides declarative configuration and automatic relationship creation
based on entity properties, foreign keys, and semantic connections.
============================================================================
"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class RelationshipRule:
    """
    Defines a rule for creating relationships between entities.

    Attributes:
        source_label: Source node label (e.g., "Assignment")
        target_label: Target node label (e.g., "Course")
        relationship_type: Type of relationship (e.g., "BELONGS_TO")
        source_ref_field: Field in source containing target ID (e.g., "course_id")
        target_id_field: ID field in target node (e.g., "course_id")
        properties_mapping: Map source fields to relationship properties
        static_properties: Static relationship properties
        required: Whether the target must exist (default: False)
        bidirectional: Whether to create reverse relationship
        reverse_type: Type for reverse relationship if bidirectional
    """
    source_label: str
    target_label: str
    relationship_type: str
    source_ref_field: str
    target_id_field: str
    properties_mapping: Optional[Dict[str, str]] = None  # source_field -> rel_property
    static_properties: Optional[Dict[str, Any]] = None
    required: bool = False
    bidirectional: bool = False
    reverse_type: Optional[str] = None


class RelationshipManager:
    """
    Manages relationship creation in the knowledge graph.

    Implements all 32 relationship types from the schema with:
    - Automatic foreign key detection
    - Rich relationship properties
    - Bidirectional relationships
    - Multi-target relationships (arrays)
    """

    # ========================================================================
    # RELATIONSHIP RULES CONFIGURATION
    # ========================================================================

    RELATIONSHIP_RULES: Dict[str, List[RelationshipRule]] = {

        # ====================================================================
        # PROFILE RELATIONSHIPS (8 - Course + Student Work Tracking)
        # ====================================================================
        "Profile": [
            # Profile → Course (ENROLLED_IN)
            RelationshipRule(
                source_label="Profile",
                target_label="Course",
                relationship_type="ENROLLED_IN",
                source_ref_field="enrolled_courses",  # Array field
                target_id_field="course_id",
                properties_mapping={
                    "enrollment_date": "enrollment_date",
                    "status": "status",
                    "final_grade": "final_grade",
                    "letter_grade": "letter_grade",
                    "grading_basis": "grading_basis",
                },
                required=False
            ),
            # Profile → Assignment (HAS_SUBMISSION)
            RelationshipRule(
                source_label="Profile",
                target_label="Assignment",
                relationship_type="HAS_SUBMISSION",
                source_ref_field="student_id",
                target_id_field="student_id",
                properties_mapping={
                    "submission_date": "submission_date",
                    "status": "status",
                    "grade": "grade",
                    "feedback": "feedback",
                },
                required=False
            ),
            # Profile → Exam (TOOK_EXAM)
            RelationshipRule(
                source_label="Profile",
                target_label="Exam",
                relationship_type="TOOK_EXAM",
                source_ref_field="student_id",
                target_id_field="student_id",
                properties_mapping={
                    "exam_date": "exam_date",
                    "score": "score",
                    "grade": "grade",
                    "completion_time": "completion_time",
                },
                required=False
            ),
            # Profile → Quiz (TOOK_QUIZ)
            RelationshipRule(
                source_label="Profile",
                target_label="Quiz",
                relationship_type="TOOK_QUIZ",
                source_ref_field="student_id",
                target_id_field="student_id",
                properties_mapping={
                    "quiz_date": "quiz_date",
                    "score": "score",
                    "time_taken": "time_taken",
                },
                required=False
            ),
            # Profile → Lab_Session (ATTENDED_LAB)
            RelationshipRule(
                source_label="Profile",
                target_label="Lab_Session",
                relationship_type="ATTENDED_LAB",
                source_ref_field="student_id",
                target_id_field="lab_id",
                properties_mapping={
                    "attendance_date": "attendance_date",
                    "participation_score": "participation_score",
                    "completed": "completed",
                },
                required=False
            ),
            # Profile → Study_Todo (HAS_TODO)
            RelationshipRule(
                source_label="Profile",
                target_label="Study_Todo",
                relationship_type="HAS_TODO",
                source_ref_field="student_id",
                target_id_field="student_id",
                required=False
            ),
            # Profile → Challenge_Area (FACES_CHALLENGE)
            RelationshipRule(
                source_label="Profile",
                target_label="Challenge_Area",
                relationship_type="FACES_CHALLENGE",
                source_ref_field="student_id",
                target_id_field="student_id",
                properties_mapping={
                    "first_detected": "first_detected",
                    "current_severity": "current_severity",
                    "intervention_count": "intervention_count",
                },
                required=False
            ),
            # Profile → Note (CREATED_NOTE)
            RelationshipRule(
                source_label="Profile",
                target_label="Note",
                relationship_type="CREATED_NOTE",
                source_ref_field="student_id",
                target_id_field="student_id",
                required=False
            ),
        ],

        # ====================================================================
        # COURSE RELATIONSHIPS (7)
        # ====================================================================
        "Course": [
            # Note: Profile → Course (ENROLLED_IN) relationship is created implicitly
            # in the NATS consumer when a Course with student_id is created.
            # No RelationshipRule needed here.

            # Course → Assignment (HAS_ASSIGNMENT)
            RelationshipRule(
                source_label="Course",
                target_label="Assignment",
                relationship_type="HAS_ASSIGNMENT",
                source_ref_field="course_id",
                target_id_field="course_id",
                properties_mapping={
                    "sequence_number": "sequence_number",
                },
                required=False
            ),
            # Course → Exam (HAS_EXAM)
            RelationshipRule(
                source_label="Course",
                target_label="Exam",
                relationship_type="HAS_EXAM",
                source_ref_field="course_id",
                target_id_field="course_id",
                required=False
            ),
            # Course → Quiz (HAS_QUIZ)
            RelationshipRule(
                source_label="Course",
                target_label="Quiz",
                relationship_type="HAS_QUIZ",
                source_ref_field="course_id",
                target_id_field="course_id",
                required=False
            ),
            # Course → Lab_Session (HAS_LAB)
            RelationshipRule(
                source_label="Course",
                target_label="Lab_Session",
                relationship_type="HAS_LAB",
                source_ref_field="course_id",
                target_id_field="course_id",
                required=False
            ),
            # Course → Class_Schedule (SCHEDULED_AS)
            RelationshipRule(
                source_label="Course",
                target_label="Class_Schedule",
                relationship_type="SCHEDULED_AS",
                source_ref_field="course_id",
                target_id_field="course_id",
                required=False
            ),
            # Course → Lecture (INCLUDES_LECTURE)
            RelationshipRule(
                source_label="Course",
                target_label="Lecture",
                relationship_type="INCLUDES_LECTURE",
                source_ref_field="course_id",
                target_id_field="course_id",
                required=False
            ),
            # Course → Topic (COVERS_TOPIC)
            RelationshipRule(
                source_label="Course",
                target_label="Topic",
                relationship_type="COVERS_TOPIC",
                source_ref_field="topics_covered",  # Array field
                target_id_field="topic_id",
                properties_mapping={
                    "coverage_depth": "coverage_depth",
                    "week_introduced": "week_introduced",
                },
                required=False
            ),
        ],

        # ====================================================================
        # ASSIGNMENT RELATIONSHIPS (4 - Course-Centric Model)
        # ====================================================================
        "Assignment": [
            # Assignment → Course (ASSIGNED_IN)
            RelationshipRule(
                source_label="Assignment",
                target_label="Course",
                relationship_type="ASSIGNED_IN",
                source_ref_field="course_id",
                target_id_field="course_id",
                required=True
            ),
            # Assignment → Topic (COVERS_TOPIC)
            RelationshipRule(
                source_label="Assignment",
                target_label="Topic",
                relationship_type="COVERS_TOPIC",
                source_ref_field="topics_covered",  # Array field
                target_id_field="topic_id",
                properties_mapping={
                    "coverage_percentage": "coverage_percentage",
                },
                required=False
            ),
            # Assignment → Study_Todo (TRIGGERED_TODO)
            RelationshipRule(
                source_label="Assignment",
                target_label="Study_Todo",
                relationship_type="TRIGGERED_TODO",
                source_ref_field="assignment_id",
                target_id_field="related_assignment_id",
                properties_mapping={
                    "auto_generated": "auto_generated",
                    "trigger_type": "trigger_type",
                },
                required=False
            ),
            # Assignment → Note (RELATED_TO_NOTE)
            RelationshipRule(
                source_label="Assignment",
                target_label="Note",
                relationship_type="RELATED_TO_NOTE",
                source_ref_field="related_notes",  # Array field
                target_id_field="note_id",
                properties_mapping={
                    "relevance_score": "relevance_score",
                    "linked_by": "linked_by",
                },
                required=False
            ),
        ],

        # ====================================================================
        # EXAM RELATIONSHIPS (3 - Course-Centric Model)
        # ====================================================================
        "Exam": [
            # Exam → Course (SCHEDULED_IN)
            RelationshipRule(
                source_label="Exam",
                target_label="Course",
                relationship_type="SCHEDULED_IN",
                source_ref_field="course_id",
                target_id_field="course_id",
                required=True
            ),
            # Exam → Topic (COVERS_TOPIC)
            RelationshipRule(
                source_label="Exam",
                target_label="Topic",
                relationship_type="COVERS_TOPIC",
                source_ref_field="topics_covered",  # Array field
                target_id_field="topic_id",
                properties_mapping={
                    "weight": "weight",
                    "difficulty": "difficulty",
                },
                required=False
            ),
            # Exam → Challenge_Area (REVEALED_CHALLENGE)
            RelationshipRule(
                source_label="Exam",
                target_label="Challenge_Area",
                relationship_type="REVEALED_CHALLENGE",
                source_ref_field="exam_id",
                target_id_field="revealed_by_exam_id",
                properties_mapping={
                    "detection_date": "detection_date",
                    "score": "score",
                    "threshold": "threshold",
                },
                required=False
            ),
        ],

        # ====================================================================
        # QUIZ RELATIONSHIPS (3 - Course-Centric Model)
        # ====================================================================
        "Quiz": [
            # Quiz → Course (GIVEN_IN)
            RelationshipRule(
                source_label="Quiz",
                target_label="Course",
                relationship_type="GIVEN_IN",
                source_ref_field="course_id",
                target_id_field="course_id",
                required=True
            ),
            # Quiz → Topic (COVERS_TOPIC)
            RelationshipRule(
                source_label="Quiz",
                target_label="Topic",
                relationship_type="COVERS_TOPIC",
                source_ref_field="topics_covered",  # Array field
                target_id_field="topic_id",
                properties_mapping={
                    "question_count": "question_count",
                },
                required=False
            ),
            # Quiz → Challenge_Area (REVEALED_CHALLENGE)
            RelationshipRule(
                source_label="Quiz",
                target_label="Challenge_Area",
                relationship_type="REVEALED_CHALLENGE",
                source_ref_field="quiz_id",
                target_id_field="revealed_by_quiz_id",
                properties_mapping={
                    "detection_date": "detection_date",
                    "score": "score",
                    "threshold": "threshold",
                },
                required=False
            ),
        ],

        # ====================================================================
        # LAB_SESSION RELATIONSHIPS (3 - Course-Centric Model)
        # ====================================================================
        "Lab_Session": [
            # Lab_Session → Course (PART_OF)
            RelationshipRule(
                source_label="Lab_Session",
                target_label="Course",
                relationship_type="PART_OF",
                source_ref_field="course_id",
                target_id_field="course_id",
                required=True
            ),
            # Lab_Session → Topic (APPLIES_TOPIC)
            RelationshipRule(
                source_label="Lab_Session",
                target_label="Topic",
                relationship_type="APPLIES_TOPIC",
                source_ref_field="topics_applied",  # Array field
                target_id_field="topic_id",
                properties_mapping={
                    "application_type": "application_type",
                },
                required=False
            ),
            # Lab_Session → Note (DOCUMENTED_IN_NOTE)
            RelationshipRule(
                source_label="Lab_Session",
                target_label="Note",
                relationship_type="DOCUMENTED_IN_NOTE",
                source_ref_field="lab_id",
                target_id_field="related_lab_id",
                properties_mapping={
                    "documentation_type": "documentation_type",
                },
                required=False
            ),
        ],

        # ====================================================================
        # STUDY_TODO RELATIONSHIPS (4)
        # ====================================================================
        "Study_Todo": [
            # Study_Todo → Course (FOR_COURSE)
            RelationshipRule(
                source_label="Study_Todo",
                target_label="Course",
                relationship_type="FOR_COURSE",
                source_ref_field="course_id",
                target_id_field="course_id",
                required=False
            ),
            # Study_Todo → Challenge_Area (ADDRESSES_CHALLENGE)
            RelationshipRule(
                source_label="Study_Todo",
                target_label="Challenge_Area",
                relationship_type="ADDRESSES_CHALLENGE",
                source_ref_field="addresses_challenges",  # Array field
                target_id_field="challenge_id",
                properties_mapping={
                    "intervention_strategy": "intervention_strategy",
                },
                required=False
            ),
            # Study_Todo → Note (REFERENCES_NOTE)
            RelationshipRule(
                source_label="Study_Todo",
                target_label="Note",
                relationship_type="REFERENCES_NOTE",
                source_ref_field="referenced_notes",  # Array field
                target_id_field="note_id",
                properties_mapping={
                    "reference_type": "reference_type",
                },
                required=False
            ),
            # Study_Todo → Exam (PREPARES_FOR_EXAM)
            RelationshipRule(
                source_label="Study_Todo",
                target_label="Exam",
                relationship_type="PREPARES_FOR_EXAM",
                source_ref_field="prepares_for_exam_id",
                target_id_field="exam_id",
                properties_mapping={
                    "preparation_phase": "preparation_phase",
                    "days_before_exam": "days_before_exam",
                },
                required=False
            ),
        ],

        # ====================================================================
        # CHALLENGE_AREA RELATIONSHIPS (4)
        # ====================================================================
        "Challenge_Area": [
            # Challenge_Area → Course (IDENTIFIED_IN_COURSE)
            RelationshipRule(
                source_label="Challenge_Area",
                target_label="Course",
                relationship_type="IDENTIFIED_IN_COURSE",
                source_ref_field="course_id",
                target_id_field="course_id",
                required=False
            ),
            # Challenge_Area → Topic (RELATED_TO_TOPIC)
            RelationshipRule(
                source_label="Challenge_Area",
                target_label="Topic",
                relationship_type="RELATED_TO_TOPIC",
                source_ref_field="related_topics",  # Array field
                target_id_field="topic_id",
                properties_mapping={
                    "relevance_strength": "relevance_strength",
                    "is_root_cause": "is_root_cause",
                },
                required=False
            ),
            # Challenge_Area → Note (IMPROVED_BY_NOTE)
            RelationshipRule(
                source_label="Challenge_Area",
                target_label="Note",
                relationship_type="IMPROVED_BY_NOTE",
                source_ref_field="helpful_notes",  # Array field
                target_id_field="note_id",
                properties_mapping={
                    "improvement_contribution": "improvement_contribution",
                    "student_rating": "student_rating",
                },
                required=False
            ),
        ],

        # ====================================================================
        # LECTURE RELATIONSHIPS (3)
        # ====================================================================
        "Lecture": [
            # Lecture → Course (BELONGS_TO)
            RelationshipRule(
                source_label="Lecture",
                target_label="Course",
                relationship_type="BELONGS_TO",
                source_ref_field="course_id",
                target_id_field="course_id",
                required=True
            ),
            # Lecture → Topic (COVERED_TOPIC)
            RelationshipRule(
                source_label="Lecture",
                target_label="Topic",
                relationship_type="COVERED_TOPIC",
                source_ref_field="topics_covered",  # Array field
                target_id_field="topic_id",
                properties_mapping={
                    "coverage_duration_minutes": "coverage_duration_minutes",
                    "depth": "depth",
                },
                required=False
            ),
            # Lecture → Note (HAS_NOTE)
            RelationshipRule(
                source_label="Lecture",
                target_label="Note",
                relationship_type="HAS_NOTE",
                source_ref_field="lecture_id",
                target_id_field="related_lecture_id",
                properties_mapping={
                    "note_completeness": "note_completeness",
                },
                required=False
            ),
        ],

        # ====================================================================
        # NOTE RELATIONSHIPS (3)
        # ====================================================================
        "Note": [
            # Note → Topic (TAGGED_WITH_TOPIC)
            RelationshipRule(
                source_label="Note",
                target_label="Topic",
                relationship_type="TAGGED_WITH_TOPIC",
                source_ref_field="tagged_topics",  # Array field
                target_id_field="topic_id",
                properties_mapping={
                    "tag_source": "tag_source",
                    "confidence": "confidence",
                },
                required=False
            ),
            # Note → Note (LINKS_TO_NOTE) - bidirectional
            RelationshipRule(
                source_label="Note",
                target_label="Note",
                relationship_type="LINKS_TO_NOTE",
                source_ref_field="linked_notes",  # Array field
                target_id_field="note_id",
                properties_mapping={
                    "link_type": "link_type",
                    "link_strength": "link_strength",
                    "context": "context",
                },
                required=False,
                bidirectional=False  # User controls directionality
            ),
            # Note → Resource (CITES_RESOURCE)
            RelationshipRule(
                source_label="Note",
                target_label="Resource",
                relationship_type="CITES_RESOURCE",
                source_ref_field="cited_resources",  # Array field
                target_id_field="resource_id",
                properties_mapping={
                    "citation_type": "citation_type",
                    "page_numbers": "page_numbers",
                },
                required=False
            ),
        ],

        # ====================================================================
        # TOPIC RELATIONSHIPS (2)
        # ====================================================================
        "Topic": [
            # Topic → Topic (PREREQUISITE_FOR)
            RelationshipRule(
                source_label="Topic",
                target_label="Topic",
                relationship_type="PREREQUISITE_FOR",
                source_ref_field="prerequisite_for",  # Array field
                target_id_field="topic_id",
                properties_mapping={
                    "strength": "strength",
                    "estimated_gap_hours": "estimated_gap_hours",
                },
                required=False
            ),
            # Topic → Resource (COVERED_IN_RESOURCE)
            RelationshipRule(
                source_label="Topic",
                target_label="Resource",
                relationship_type="COVERED_IN_RESOURCE",
                source_ref_field="covered_in_resources",  # Array field
                target_id_field="resource_id",
                properties_mapping={
                    "chapter_section": "chapter_section",
                    "coverage_quality": "coverage_quality",
                    "difficulty_match": "difficulty_match",
                },
                required=False
            ),
        ],

        # ====================================================================
        # CLASS_SCHEDULE RELATIONSHIPS (1)
        # ====================================================================
        "Class_Schedule": [
            # Class_Schedule → Course (SCHEDULED_FOR)
            RelationshipRule(
                source_label="Class_Schedule",
                target_label="Course",
                relationship_type="SCHEDULED_FOR",
                source_ref_field="course_id",
                target_id_field="course_id",
                required=True
            ),
        ],
    }

    def __init__(self, session):
        """
        Initialize relationship manager.

        Args:
            session: Neo4j session for executing queries
        """
        self.session = session

    def create_relationships_for_node(
        self,
        label: str,
        node_id: str,
        id_field: str,
        properties: Dict[str, Any]
    ) -> List[Tuple[str, str]]:
        """
        Create all applicable relationships for a node.

        Args:
            label: Node label (e.g., "Assignment")
            node_id: Node identifier value
            id_field: ID field name (e.g., "assignment_id")
            properties: Node properties containing foreign key references

        Returns:
            List of created relationships as (relationship_type, target_label) tuples
        """
        if label not in self.RELATIONSHIP_RULES:
            logger.debug(f"No relationship rules defined for {label}")
            return []

        rules = self.RELATIONSHIP_RULES[label]
        created_relationships = []

        for rule in rules:
            # Check if the source has the reference field
            ref_value = properties.get(rule.source_ref_field)

            if not ref_value:
                if rule.required:
                    logger.warning(
                        f"Required relationship field '{rule.source_ref_field}' "
                        f"missing for {label} {node_id}"
                    )
                continue

            # Handle array fields (multiple targets)
            if isinstance(ref_value, list):
                for target_id in ref_value:
                    success = self._create_single_relationship(
                        rule=rule,
                        source_id_field=id_field,
                        source_id_value=node_id,
                        target_id_value=target_id,
                        properties=properties
                    )
                    if success:
                        created_relationships.append((rule.relationship_type, rule.target_label))
            else:
                # Single target
                success = self._create_single_relationship(
                    rule=rule,
                    source_id_field=id_field,
                    source_id_value=node_id,
                    target_id_value=ref_value,
                    properties=properties
                )
                if success:
                    created_relationships.append((rule.relationship_type, rule.target_label))
                elif rule.required:
                    logger.warning(
                        f"Failed to create required relationship {rule.relationship_type} "
                        f"from {label} {node_id} to {rule.target_label} {ref_value}"
                    )

        return created_relationships

    def _create_single_relationship(
        self,
        rule: RelationshipRule,
        source_id_field: str,
        source_id_value: str,
        target_id_value: str,
        properties: Dict[str, Any]
    ) -> bool:
        """
        Create a single relationship based on a rule.

        Args:
            rule: RelationshipRule defining the relationship
            source_id_field: Source node ID field name
            source_id_value: Source node ID value
            target_id_value: Target node ID value
            properties: Source node properties for extracting relationship properties

        Returns:
            True if relationship was created, False otherwise
        """
        # Build relationship properties from mapping
        rel_properties = {}

        if rule.properties_mapping:
            for source_field, rel_prop in rule.properties_mapping.items():
                if source_field in properties and properties[source_field] is not None:
                    rel_properties[rel_prop] = properties[source_field]

        if rule.static_properties:
            rel_properties.update(rule.static_properties)

        # Create the relationship
        return self._create_relationship(
            source_label=rule.source_label,
            source_id_field=source_id_field,
            source_id_value=source_id_value,
            target_label=rule.target_label,
            target_id_field=rule.target_id_field,
            target_id_value=target_id_value,
            relationship_type=rule.relationship_type,
            relationship_properties=rel_properties
        )

    def _create_relationship(
        self,
        source_label: str,
        source_id_field: str,
        source_id_value: str,
        target_label: str,
        target_id_field: str,
        target_id_value: str,
        relationship_type: str,
        relationship_properties: Dict[str, Any]
    ) -> bool:
        """
        Create a single relationship between two nodes.

        Args:
            source_label: Source node label
            source_id_field: Source node ID field name
            source_id_value: Source node ID value
            target_label: Target node label
            target_id_field: Target node ID field name
            target_id_value: Target node ID value
            relationship_type: Type of relationship to create
            relationship_properties: Properties to set on the relationship

        Returns:
            True if relationship was created, False if target not found
        """
        # Build relationship properties clause with ON CREATE SET
        set_clause = ""
        if relationship_properties:
            set_parts = []
            for key in relationship_properties.keys():
                set_parts.append(f"r.{key} = ${key}")
            set_parts.append("r.created_at = datetime()")
            set_clause = "ON CREATE SET " + ", ".join(set_parts)

        query = f"""
            MATCH (source:{source_label} {{ {source_id_field}: $source_id }})
            MATCH (target:{target_label} {{ {target_id_field}: $target_id }})
            MERGE (source)-[r:{relationship_type}]->(target)
            {set_clause}
            RETURN r
        """

        try:
            result = self.session.run(
                query,
                source_id=source_id_value,
                target_id=target_id_value,
                **relationship_properties
            )

            record = result.single()

            if record:
                logger.info(
                    f"Created relationship: ({source_label})-[:{relationship_type}]->({target_label})"
                )
                return True
            else:
                logger.debug(
                    f"Target {target_label} with {target_id_field}={target_id_value} not found"
                )
                return False

        except Exception as e:
            logger.error(
                f"Error creating relationship {relationship_type}: {e}",
                exc_info=True
            )
            return False

    def rebuild_all_relationships(self) -> Dict[str, int]:
        """
        Rebuild all relationships for existing nodes in the graph.

        Useful for backfilling relationships after adding relationship rules
        or for fixing broken relationships.

        Returns:
            Dictionary mapping relationship types to count created
        """
        logger.info("Rebuilding all relationships in the knowledge graph...")

        relationship_counts = {}

        for source_label, rules in self.RELATIONSHIP_RULES.items():
            # Get all nodes of this type
            result = self.session.run(f"MATCH (n:{source_label}) RETURN n")
            nodes = list(result)

            if not nodes:
                logger.debug(f"No {source_label} nodes found")
                continue

            logger.info(f"Processing {len(nodes)} {source_label} nodes...")

            for record in nodes:
                node = record['n']
                node_props = dict(node)

                # Get the ID field for this node type
                id_field = self._infer_id_field(source_label, node_props)
                if not id_field:
                    logger.warning(f"Could not determine ID field for {source_label}")
                    continue

                node_id = node_props[id_field]

                # Create relationships
                created = self.create_relationships_for_node(
                    label=source_label,
                    node_id=node_id,
                    id_field=id_field,
                    properties=node_props
                )

                # Count created relationships
                for rel_type, _ in created:
                    relationship_counts[rel_type] = relationship_counts.get(rel_type, 0) + 1

        logger.info(f"Relationship rebuild complete: {relationship_counts}")
        return relationship_counts

    def _infer_id_field(self, label: str, properties: Dict[str, Any]) -> Optional[str]:
        """
        Infer the ID field for a node based on label and properties.

        Args:
            label: Node label
            properties: Node properties

        Returns:
            ID field name or None
        """
        # Common ID field patterns
        id_field_map = {
            "Profile": "student_id",
            "Course": "course_id",
            "Assignment": "assignment_id",
            "Exam": "exam_id",
            "Quiz": "quiz_id",
            "Lab_Session": "lab_id",
            "Study_Todo": "todo_id",
            "Challenge_Area": "challenge_id",
            "Class_Schedule": "schedule_id",
            "Lecture": "lecture_id",
            "Note": "note_id",
            "Topic": "topic_id",
            "Resource": "resource_id",
        }

        expected_field = id_field_map.get(label)
        if expected_field and expected_field in properties:
            return expected_field

        # Fallback: look for any field ending with "_id"
        for field in properties:
            if field.endswith("_id") and not field.startswith("related_") and not field.startswith("course_"):
                return field

        return None
