"""
============================================================================
Dynamic Query Builder
============================================================================
Generates custom Cypher retrieval queries on-demand using LLM + schema
============================================================================
"""

import logging
import re
from dataclasses import dataclass
from typing import Literal

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from neo4j import Driver

from note_service.retrieval.schema_introspector import GraphSchema, SchemaIntrospector

logger = logging.getLogger(__name__)


@dataclass
class QueryGenerationResult:
    """Result of LLM query generation."""

    query: str
    is_valid: bool
    error_message: str | None = None
    attempts: int = 1


class DynamicQueryBuilder:
    """
    Dynamically builds Cypher retrieval queries using LLM and graph schema.
    Supports both standalone queries and HybridCypherRetriever traversal queries.
    """

    def __init__(
        self,
        driver: Driver,
        schema_introspector: SchemaIntrospector,
        llm_model: str = "gemini-2.5-flash",
        llm_temperature: float = 0.0,
        llm_api_key: str | None = None,
        max_self_heal_attempts: int = 3,
    ):
        """
        Initialize dynamic query builder.

        Args:
            driver: Neo4j driver for query validation
            schema_introspector: Schema introspection service
            llm_model: Google Gemini model name
            llm_temperature: LLM temperature (0 for deterministic)
            llm_api_key: Google API key (or use GOOGLE_API_KEY env var)
            max_self_heal_attempts: Max attempts to fix syntax errors
        """
        self.driver = driver
        self.schema_introspector = schema_introspector
        self.max_self_heal_attempts = max_self_heal_attempts

        self.llm = ChatGoogleGenerativeAI(
            model=llm_model,
            temperature=llm_temperature,
            google_api_key=llm_api_key,
            max_tokens=2048,
            timeout=30.0,
        )

        logger.info(f"Initialized DynamicQueryBuilder with model: {llm_model}")

    def build_standalone_query(
        self,
        user_question: str,
        validate: bool = True,
    ) -> QueryGenerationResult:
        """
        Build standalone Cypher query from natural language question.

        Args:
            user_question: User's natural language question
            validate: Whether to validate and self-heal the query

        Returns:
            QueryGenerationResult with generated query
        """
        schema = self.schema_introspector.get_schema()
        prompt = self._build_standalone_query_prompt(user_question, schema)

        logger.info(f"Generating standalone query for: {user_question}")
        query = self._invoke_llm(prompt)

        if validate:
            return self._self_heal_query(query, user_question, schema)

        return QueryGenerationResult(query=query, is_valid=True)

    def build_hybrid_retrieval_query(
        self,
        user_question: str,
        initial_node_type: str = "LectureNote",
        validate: bool = True,
        filter_topics: list[str] | None = None,
        filter_tags: list[str] | None = None,
        require_all: bool = False,
        student_id: str = "",
    ) -> QueryGenerationResult:
        """
        Build retrieval_query for HybridCypherRetriever.

        This generates a graph traversal query that starts from the 'node' variable
        (provided by hybrid search) and enriches it with related information.

        Args:
            user_question: User's question to determine what context to retrieve
            initial_node_type: Type of node from hybrid search (default: "LectureNote")
            validate: Whether to validate and self-heal the query
            filter_topics: Optional list of Topic names to filter by
            filter_tags: Optional list of tags to filter by (from tagged_topics field)
            require_all: If True, require ALL topics/tags; if False, require ANY
            student_id: Filter results to only include notes created by this student (optional)

        Returns:
            QueryGenerationResult with traversal query
        """
        schema = self.schema_introspector.get_schema()
        prompt = self._build_hybrid_retrieval_prompt(
            user_question, initial_node_type, schema, filter_topics, filter_tags, require_all, student_id
        )

        logger.info(
            f"Generating hybrid retrieval query for '{user_question}' "
            f"starting from {initial_node_type}"
        )
        query = self._invoke_llm(prompt)

        if validate:
            return self._self_heal_query(query, user_question, schema, is_hybrid=True)

        return QueryGenerationResult(query=query, is_valid=True)

    def _build_standalone_query_prompt(
        self, user_question: str, schema: GraphSchema
    ) -> str:
        """Build prompt for standalone query generation."""
        schema_text = self.schema_introspector.format_schema_for_llm(schema)
        vector_indexes = ", ".join(self.schema_introspector.get_vector_index_names(schema))
        fulltext_indexes = ", ".join(
            self.schema_introspector.get_fulltext_index_names(schema)
        )

        few_shot_examples = self._get_few_shot_examples()

        return f"""You are an expert Neo4j Cypher query generator for an academic note-taking system.

{schema_text}

## Available Vector Indexes
{vector_indexes}

## Available Full-Text Indexes
{fulltext_indexes}

## Instructions
1. Generate syntactically correct Cypher queries ONLY
2. Use ONLY the node labels, relationships, and properties defined in the schema above
3. For semantic search, use vector indexes (db.index.vector.queryNodes)
4. For keyword/phrase search, use full-text indexes (db.index.fulltext.queryNodes)
5. Use case-insensitive matching: WHERE prop =~ '(?i)pattern'
6. Always include LIMIT clause (default 10, max 50)
7. Return relevant properties and context
8. Return ONLY the Cypher query without explanations, markdown, or code blocks

## Example Queries

{few_shot_examples}

## User Question
{user_question}

Generate the Cypher query:"""

    def _build_hybrid_retrieval_prompt(
        self,
        user_question: str,
        initial_node_type: str,
        schema: GraphSchema,
        filter_topics: list[str] | None = None,
        filter_tags: list[str] | None = None,
        require_all: bool = False,
        student_id: str = "",
    ) -> str:
        """Build prompt for hybrid retrieval query generation with optional topic/tag filtering."""
        schema_text = self.schema_introspector.format_schema_for_llm(schema)

        # Build filter instructions
        filter_instructions = ""
        if filter_topics or filter_tags or student_id:
            filter_instructions = "\n## FILTERING REQUIREMENTS\n"
            if student_id:
                filter_instructions += f"""- CRITICAL: MUST filter by student ownership using student_id: '{student_id}'
- Only return notes created by this student
- Use CREATED_NOTE relationship: WHERE EXISTS {{ (p:Profile)-[:CREATED_NOTE]->(node) WHERE p.student_id = '{student_id}' }}
- This filter is MANDATORY for user data privacy
"""
            if filter_topics:
                match_logic = "ALL" if require_all else "ANY"
                topics_str = ", ".join(f"'{t}'" for t in filter_topics)
                filter_instructions += f"""- MUST filter by topics: {topics_str}
- Match logic: {match_logic} of the specified topics
- Use COVERS_TOPIC relationships to filter by Topic nodes
- Filter pattern: WHERE EXISTS {{ (node)-[:COVERS_TOPIC]->(t:Topic) WHERE t.name IN [{topics_str}] }}
"""
            if filter_tags:
                match_logic = "ALL" if require_all else "ANY"
                tags_str = ", ".join(f"'{t}'" for t in filter_tags)
                filter_instructions += f"""- MUST filter by tags from tagged_topics array: {tags_str}
- Match logic: {match_logic} of the specified tags
- Use {'ALL' if require_all else 'ANY'} predicate for array filtering
- Filter pattern: WHERE {'ALL' if require_all else 'ANY'}(tag IN [{tags_str}] WHERE tag IN node.tagged_topics)
"""

        return f"""You are an expert at building Neo4j graph traversal queries for retrieval augmentation.

{schema_text}

## Task
Build a Cypher query that traverses from a '{initial_node_type}' node to gather contextually relevant information.
{filter_instructions}
## CRITICAL Instructions
1. The variable 'node' contains a matched {initial_node_type} from hybrid search
2. The variable 'score' contains the relevance score from hybrid search
3. You MUST start with WHERE clause for filtering, then OPTIONAL MATCH for traversal
4. Traverse relationships from 'node' to gather related entities
5. Use collect(DISTINCT ...) to aggregate related data
6. ALWAYS end with a RETURN statement - never end with WITH
7. Return node properties and related context as named fields
8. Include 'score' in the RETURN clause
9. MUST include the node's primary ID field in RETURN (e.g., node.lecture_note_id, node.course_id, node.profile_id)
10. Return ONLY the Cypher query without explanations, markdown, or code blocks

## Example for LectureNote node
```
OPTIONAL MATCH (node)-[:CREATED_BY]->(profile:Profile)
OPTIONAL MATCH (node)-[:BELONGS_TO]->(course:Course)
OPTIONAL MATCH (node)<-[:PART_OF]-(chunk:Chunk)
RETURN node.lecture_note_id AS lecture_note_id,
       node.title AS lecture_note_title,
       node.content AS lecture_note_content,
       node.summary AS lecture_note_summary,
       node.key_concepts AS key_concepts,
       node.tagged_topics AS tagged_topics,
       collect(DISTINCT profile.first_name + ' ' + profile.last_name) AS created_by_student,
       collect(DISTINCT course.title) AS belongs_to_courses,
       collect(DISTINCT chunk.content) AS related_chunks_content,
       score
```

## Example for Course node
```
OPTIONAL MATCH (node)<-[:BELONGS_TO]-(note:LectureNote)
OPTIONAL MATCH (node)<-[:ENROLLED_IN]-(student:Profile)
RETURN node.course_id AS course_id,
       node.title AS course_title,
       node.description AS course_description,
       collect(DISTINCT note.title) AS lecture_notes,
       collect(DISTINCT student.email) AS enrolled_students,
       score
```

## User Question Context
{user_question}

## Starting Node Type
{initial_node_type}

IMPORTANT: If you cannot determine relevant traversals, return a minimal query:
```
RETURN node, score
```

Generate the traversal query:"""

    def _get_few_shot_examples(self) -> str:
        """Get few-shot examples for query generation."""
        examples = [
            {
                "question": "Find notes about neural networks",
                "query": """CALL db.index.fulltext.queryNodes('note_content_text', 'neural networks')
YIELD node, score
MATCH (node:Note)-[:TAGGED_WITH_TOPIC]->(topic:Topic)
OPTIONAL MATCH (topic)<-[:COVERS_TOPIC]-(course:Course)
RETURN node.title AS note_title,
       node.content AS content,
       collect(DISTINCT topic.name) AS topics,
       collect(DISTINCT course.title) AS courses,
       score
ORDER BY score DESC
LIMIT 10""",
            },
            {
                "question": "What assignments are due this week?",
                "query": """MATCH (a:Assignment)
WHERE a.due_date >= datetime()
  AND a.due_date <= datetime() + duration('P7D')
MATCH (a)-[:IN_COURSE]->(c:Course)
RETURN a.title AS assignment,
       a.due_date AS due_date,
       a.type AS assignment_type,
       c.title AS course,
       a.percentage_grade AS current_grade
ORDER BY a.due_date ASC
LIMIT 20""",
            },
            {
                "question": "Show topics where I'm struggling",
                "query": """MATCH (ch:Challenge_Area)
WHERE ch.severity IN ['high', 'critical']
  AND ch.status = 'active'
MATCH (ch)-[:RELATED_TO_TOPIC]->(t:Topic)
OPTIONAL MATCH (t)<-[:COVERS_TOPIC]-(c:Course)
RETURN t.name AS topic,
       ch.description AS challenge,
       ch.severity AS severity,
       collect(DISTINCT c.title) AS courses
ORDER BY
  CASE ch.severity
    WHEN 'critical' THEN 1
    WHEN 'high' THEN 2
    ELSE 3
  END,
  ch.identified_date DESC
LIMIT 15""",
            },
            {
                "question": "Find notes that reference each other about machine learning",
                "query": """CALL db.index.fulltext.queryNodes('note_title_text', 'machine learning')
YIELD node AS n1, score
MATCH (n1)-[:REFERENCES_NOTE]->(n2:Note)
RETURN n1.title AS main_note,
       n2.title AS referenced_note,
       n1.created_date AS created,
       score
ORDER BY score DESC
LIMIT 10""",
            },
            {
                "question": "Find notes tagged with 'Neural Networks' or 'Deep Learning'",
                "query": """CALL db.index.vector.queryNodes('lecture_note_content_vector', $embedding, 20)
YIELD node, score
WHERE ANY(tag IN ['neural-networks', 'deep-learning'] WHERE tag IN node.tagged_topics)
OPTIONAL MATCH (node)-[:COVERS_TOPIC]->(topic:Topic)
OPTIONAL MATCH (node)-[:BELONGS_TO]->(course:Course)
RETURN node.title AS note_title,
       node.summary AS summary,
       node.tagged_topics AS tags,
       collect(DISTINCT topic.name) AS topics,
       collect(DISTINCT course.title) AS courses,
       score
ORDER BY score DESC
LIMIT 10""",
            },
            {
                "question": "Get notes covering BOTH 'CNNs' and 'Computer Vision' topics",
                "query": """CALL db.index.vector.queryNodes('lecture_note_content_vector', $embedding, 30)
YIELD node, score
WHERE EXISTS { (node)-[:COVERS_TOPIC]->(t1:Topic) WHERE t1.name = 'CNNs' }
  AND EXISTS { (node)-[:COVERS_TOPIC]->(t2:Topic) WHERE t2.name = 'Computer Vision' }
OPTIONAL MATCH (node)-[:COVERS_TOPIC]->(topic:Topic)
OPTIONAL MATCH (node)-[:CREATED_BY]->(student:Profile)
RETURN node.title AS note_title,
       node.content AS content,
       node.created_date AS created,
       collect(DISTINCT topic.name) AS all_topics,
       student.student_id AS author,
       score
ORDER BY score DESC
LIMIT 10""",
            },
        ]

        formatted = []
        for ex in examples:
            formatted.append(f"Question: {ex['question']}\n\n{ex['query']}\n")

        return "\n---\n\n".join(formatted)

    def _invoke_llm(self, prompt: str) -> str:
        """Invoke LLM with prompt and extract Cypher query."""
        response = self.llm.invoke([HumanMessage(content=prompt)])
        query = response.content.strip()

        query = self._clean_query_response(query)

        # Safety check: ensure query is not empty
        if not query or len(query.strip()) == 0:
            logger.warning("LLM returned empty query, using fallback")
            query = "RETURN node, score"

        logger.debug(f"LLM generated query: {query[:200]}...")
        return query

    def _clean_query_response(self, query: str) -> str:
        """Clean LLM response to extract pure Cypher query."""
        query = re.sub(r"^```cypher\s*", "", query, flags=re.IGNORECASE)
        query = re.sub(r"^```\s*", "", query)
        query = re.sub(r"\s*```$", "", query)

        query = query.strip()

        return query

    def _self_heal_query(
        self,
        query: str,
        user_question: str,
        schema: GraphSchema,
        is_hybrid: bool = False,
    ) -> QueryGenerationResult:
        """
        Validate query and attempt to fix syntax errors.

        Args:
            query: Generated Cypher query
            user_question: Original user question
            schema: Graph schema
            is_hybrid: Whether this is a hybrid retrieval query

        Returns:
            QueryGenerationResult with validation status
        """
        for attempt in range(1, self.max_self_heal_attempts + 1):
            is_valid, error = self._validate_query(query, is_hybrid)

            if is_valid:
                logger.info(f"Query validated successfully after {attempt} attempt(s)")
                return QueryGenerationResult(
                    query=query, is_valid=True, attempts=attempt
                )

            logger.warning(f"Query validation failed (attempt {attempt}): {error}")

            if attempt < self.max_self_heal_attempts:
                query = self._heal_query(query, error, user_question, schema, is_hybrid)

        return QueryGenerationResult(
            query=query,
            is_valid=False,
            error_message=error,
            attempts=self.max_self_heal_attempts,
        )

    def _validate_query(
        self, query: str, is_hybrid: bool = False
    ) -> tuple[bool, str | None]:
        """
        Validate Cypher query syntax.

        Args:
            query: Cypher query to validate
            is_hybrid: If True, validate assuming node and score variables exist

        Returns:
            Tuple of (is_valid, error_message)
        """
        if is_hybrid:
            # Simulate the actual HybridCypherRetriever environment
            # It performs vector + fulltext search, normalizes scores, and provides
            # 'node' and 'score' variables to the retrieval_query
            test_query = f"""
            CALL {{
                CALL db.index.vector.queryNodes($vector_index_name, 1, $query_vector)
                YIELD node, score
                WITH collect({{node:node, score:score}}) AS nodes, max(score) AS vector_index_max_score
                UNWIND nodes AS n
                RETURN n.node AS node, (n.score / vector_index_max_score) AS score
                UNION
                CALL db.index.fulltext.queryNodes($fulltext_index_name, $query_text)
                YIELD node, score
                WITH collect({{node:node, score:score}}) AS nodes, max(score) AS ft_index_max_score
                UNWIND nodes AS n
                RETURN n.node AS node, (n.score / ft_index_max_score) AS score
            }}
            WITH node, max(score) AS score ORDER BY score DESC LIMIT 1
            {query}
            """
        else:
            test_query = query

        try:
            with self.driver.session() as session:
                session.run(f"EXPLAIN {test_query}")
            return True, None
        except Exception as e:
            error_msg = str(e)
            return False, error_msg

    def _heal_query(
        self,
        query: str,
        error: str,
        user_question: str,
        schema: GraphSchema,
        is_hybrid: bool,
    ) -> str:
        """Attempt to fix query by re-prompting LLM with error details."""
        schema_text = self.schema_introspector.format_schema_for_llm(schema)

        heal_prompt = f"""The following Cypher query has a syntax error:

```cypher
{query}
```

Error: {error}

## Graph Schema
{schema_text}

## Original Question
{user_question}

## Query Type
{"Hybrid retrieval traversal query (starting from variable 'node')" if is_hybrid else "Standalone query"}

Please fix the query to be syntactically correct.
Return ONLY the corrected Cypher query without explanations or markdown."""

        logger.info("Attempting to heal query with LLM")
        return self._invoke_llm(heal_prompt)
