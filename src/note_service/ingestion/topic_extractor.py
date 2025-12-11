"""
============================================================================
Topic Extraction Service
============================================================================
Extracts and manages topics from academic entities for knowledge graph linking.
Uses both existing tags and LLM-powered extraction for intelligent topic discovery.
============================================================================
"""

import logging
from typing import Dict, List, Set
from datetime import datetime

from neo4j import Session
from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger(__name__)


class TopicExtractor:
    """
    Intelligent topic extraction and management service.

    Combines rule-based extraction from existing tags with LLM-powered
    topic discovery for comprehensive knowledge graph linking.
    """

    def __init__(self, llm_api_key: str | None = None):
        """
        Initialize topic extractor.

        Args:
            llm_api_key: Google API key for LLM-powered extraction (optional)
        """
        self.llm = None
        if llm_api_key:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                temperature=0.0,
                google_api_key=llm_api_key,
                max_tokens=512,
                timeout=30.0,
            )
            logger.info("LLM-powered topic extraction enabled")

    def normalize_topic(self, topic: str) -> str:
        """
        Normalize topic string to consistent format.

        Args:
            topic: Raw topic string

        Returns:
            Normalized topic string (lowercase, hyphenated)
        """
        return topic.lower().strip().replace(" ", "-").replace("_", "-")

    def extract_from_tags(self, tagged_topics: List[str]) -> Set[str]:
        """
        Extract normalized topics from existing tags.

        Args:
            tagged_topics: List of topic strings

        Returns:
            Set of normalized topic strings
        """
        if not tagged_topics:
            return set()

        topics = set()
        for topic in tagged_topics:
            if topic and isinstance(topic, str):
                normalized = self.normalize_topic(topic)
                if normalized:
                    topics.add(normalized)

        return topics

    def extract_from_text(self, text: str, max_topics: int = 5) -> Set[str]:
        """
        Extract topics from text using LLM.

        Args:
            text: Text content to analyze
            max_topics: Maximum number of topics to extract

        Returns:
            Set of normalized topic strings
        """
        if not self.llm or not text:
            return set()

        try:
            prompt = f"""Extract {max_topics} key academic topics/concepts from this text.
Return ONLY a comma-separated list of topics, no explanations.
Use lowercase, hyphenate multi-word topics (e.g., "machine-learning", "data-structures").

Text: {text[:500]}

Topics:"""

            response = self.llm.invoke(prompt)
            topics_str = response.content.strip()

            # Parse comma-separated topics
            topics = set()
            for topic in topics_str.split(","):
                normalized = self.normalize_topic(topic)
                if normalized and len(normalized) > 2:
                    topics.add(normalized)

            logger.debug(f"Extracted {len(topics)} topics from text: {topics}")
            return topics

        except Exception as e:
            logger.error(f"LLM topic extraction failed: {e}")
            return set()

    def create_topic_nodes(
        self,
        session: Session,
        topics: Set[str],
        course_id: str | None = None
    ) -> Dict[str, str]:
        """
        Create or retrieve Topic nodes in Neo4j.

        Args:
            session: Neo4j session
            topics: Set of normalized topic strings
            course_id: Optional course context

        Returns:
            Dict mapping topic strings to topic_ids
        """
        topic_map = {}

        for topic in topics:
            # Generate topic_id from normalized name
            topic_id = f"TOPIC-{topic}"

            # Create or merge Topic node
            result = session.run("""
                MERGE (t:Topic {topic_id: $topic_id})
                ON CREATE SET
                    t.name = $name,
                    t.normalized_name = $normalized_name,
                    t.created_at = datetime(),
                    t.usage_count = 1
                ON MATCH SET
                    t.usage_count = t.usage_count + 1,
                    t.last_used = datetime()
                RETURN t.topic_id as topic_id
            """, topic_id=topic_id, name=topic.replace("-", " ").title(),
                 normalized_name=topic)

            record = result.single()
            if record:
                topic_map[topic] = record["topic_id"]

        logger.info(f"Created/updated {len(topic_map)} Topic nodes")
        return topic_map

    def link_entity_to_topics(
        self,
        session: Session,
        entity_label: str,
        entity_id: str,
        topics: Set[str],
        relationship_type: str = "COVERS_TOPIC",
        properties: Dict | None = None
    ) -> int:
        """
        Create relationships from entity to Topic nodes.

        Args:
            session: Neo4j session
            entity_label: Label of source entity (e.g., "LectureNote")
            entity_id: ID of source entity
            topics: Set of normalized topic strings
            relationship_type: Type of relationship to create
            properties: Optional relationship properties

        Returns:
            Number of relationships created
        """
        if not topics:
            return 0

        # First create/get topic nodes
        topic_map = self.create_topic_nodes(session, topics)

        # Create relationships
        rel_properties = properties or {}
        rel_properties["created_at"] = datetime.utcnow().isoformat()

        result = session.run(f"""
            MATCH (entity:{entity_label})
            WHERE entity.{self._get_id_field(entity_label)} = $entity_id
            UNWIND $topic_ids as topic_id
            MATCH (t:Topic {{topic_id: topic_id}})
            MERGE (entity)-[r:{relationship_type}]->(t)
            ON CREATE SET r += $properties
            RETURN count(r) as count
        """, entity_id=entity_id, topic_ids=list(topic_map.values()),
             properties=rel_properties)

        record = result.single()
        count = record["count"] if record else 0

        logger.info(f"Linked {entity_label} {entity_id} to {count} topics")
        return count

    def _get_id_field(self, label: str) -> str:
        """Get ID field name for entity label."""
        id_fields = {
            "LectureNote": "lecture_note_id",
            "Assignment": "assignment_id",
            "Exam": "exam_id",
            "Quiz": "quiz_id",
            "Challenge_Area": "challenge_id",
            "Topic": "topic_id",
        }
        return id_fields.get(label, f"{label.lower()}_id")

    def extract_and_link(
        self,
        session: Session,
        entity_label: str,
        entity_id: str,
        tagged_topics: List[str] | None = None,
        text_content: str | None = None,
        course_id: str | None = None
    ) -> Set[str]:
        """
        Extract topics and link entity in one operation.

        Args:
            session: Neo4j session
            entity_label: Label of entity
            entity_id: ID of entity
            tagged_topics: Pre-existing topic tags
            text_content: Text to extract topics from (if LLM enabled)
            course_id: Optional course context

        Returns:
            Set of topics extracted and linked
        """
        all_topics = set()

        # Extract from existing tags
        if tagged_topics:
            tag_topics = self.extract_from_tags(tagged_topics)
            all_topics.update(tag_topics)
            logger.debug(f"Extracted {len(tag_topics)} topics from tags")

        # Extract from text if LLM available
        if text_content and self.llm:
            text_topics = self.extract_from_text(text_content, max_topics=5)
            all_topics.update(text_topics)
            logger.debug(f"Extracted {len(text_topics)} topics from text")

        # Link to topics with specificity property
        if all_topics:
            # Automatically determine specificity based on entity type
            specificity = "chunk" if entity_label == "Chunk" else "document"

            self.link_entity_to_topics(
                session=session,
                entity_label=entity_label,
                entity_id=entity_id,
                topics=all_topics,
                properties={"specificity": specificity}
            )

        return all_topics
