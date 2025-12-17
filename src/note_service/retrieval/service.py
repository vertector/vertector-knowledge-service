"""
============================================================================
Retrieval Service Orchestrator
============================================================================
Main service that coordinates dynamic query building and hybrid retrieval
============================================================================
"""

import logging
from dataclasses import dataclass
from typing import Any, Literal

from neo4j import Driver
from neo4j_graphrag.embeddings import SentenceTransformerEmbeddings
from neo4j_graphrag.retrievers import HybridCypherRetriever, HybridRetriever

from note_service.config import Settings
from note_service.retrieval.chunk_aware_ranker import ChunkAwareDocumentRanker
from note_service.retrieval.embedder import EmbeddingService
from note_service.retrieval.query_builder import DynamicQueryBuilder, QueryGenerationResult
from note_service.retrieval.schema_introspector import SchemaIntrospector
from note_service.security.audit import AuditLogger
from note_service.security.validator import SecurityValidator

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """Result from retrieval operation."""

    query: str
    results: list[dict[str, Any]]
    num_results: int
    query_generation: QueryGenerationResult | None = None


class RetrievalService:
    """
    Production-ready retrieval service for academic note-taking system.

    Dynamically generates retrieval queries using LLM + schema and executes
    hybrid search (vector + full-text) with graph traversal enrichment.
    """

    def __init__(
        self,
        driver: Driver,
        settings: Settings,
        google_api_key: str | None = None,
    ):
        """
        Initialize retrieval service.

        Args:
            driver: Neo4j driver instance
            settings: Application settings
            google_api_key: Google API key for Gemini (or use GOOGLE_API_KEY env var)
        """
        self.driver = driver
        self.settings = settings

        logger.info("Initializing RetrievalService components...")

        self.schema_introspector = SchemaIntrospector(
            driver=driver,
            cache_ttl_seconds=300,
            sample_size=1000,
        )

        self.query_builder = DynamicQueryBuilder(
            driver=driver,
            schema_introspector=self.schema_introspector,
            llm_model=settings.llm.model_name,
            llm_temperature=settings.llm.temperature,
            llm_api_key=google_api_key
            or (settings.llm.api_key.get_secret_value() if settings.llm.api_key else None),
            max_self_heal_attempts=3,
        )

        self.embedding_service = EmbeddingService(
            model_name=settings.embedding.model_name,
            device=settings.embedding.device,
            cache_folder=settings.embedding.cache_folder,
            normalize_embeddings=settings.embedding.normalize_embeddings,
            batch_size=settings.embedding.batch_size,
        )

        self.neo4j_embedder = SentenceTransformerEmbeddings(
            model=settings.embedding.model_name,
            cache_folder=settings.embedding.cache_folder,
        )

        # Initialize chunk-aware document ranker for precision improvement
        self.chunk_ranker = ChunkAwareDocumentRanker(
            driver=driver,
            embedder=self.neo4j_embedder,
            settings=settings,
            top_chunks_per_doc=3,
            relevance_threshold=0.7,
        )

        # Initialize security and audit components
        self.audit_logger = AuditLogger(driver=driver)
        self.security_validator = SecurityValidator(driver=driver)

        logger.info("RetrievalService initialized successfully with security and audit logging")

    def search(
        self,
        query_text: str,
        student_id: str,
        top_k: int = 10,
        granularity: Literal["document", "chunk", "auto"] = "document",
        search_type: Literal["hybrid", "vector", "fulltext", "standalone"] = "hybrid",
        initial_node_type: str = "LectureNote",
        filter_topics: list[str] | None = None,
        filter_tags: list[str] | None = None,
        require_all_topics: bool = False,
        topic_boost: float = 1.0,
        return_parent_context: bool = True,
        return_surrounding_chunks: bool = False,
        use_chunk_ranking: bool = True,
    ) -> RetrievalResult:
        """
        Unified search method - supports both document and chunk-level retrieval.

        IMPORTANT: All searches are scoped to a specific student for data privacy.
        Users can ONLY query their own data.

        Args:
            query_text: User's natural language question
            student_id: Student ID - REQUIRED for data privacy, filters to only this student's notes
            top_k: Number of results to return
            granularity: Retrieval granularity:
                - "document": Return full LectureNotes (traditional behavior)
                - "chunk": Return specific chunks for precise retrieval
                - "auto": Automatically choose based on query (future enhancement)
            search_type: Type of search to perform (hybrid, vector, fulltext, standalone)
            initial_node_type: Starting node type for document-level search (default: LectureNote)
            filter_topics: List of Topic names to filter by (via COVERS_TOPIC relationships)
            filter_tags: List of tags to filter by (from tagged_topics field)
            require_all_topics: If True, require ALL topics/tags; if False, require ANY (default: False)
            topic_boost: Score multiplier for topic matches (document-level only, default: 1.0)
            return_parent_context: Include parent LectureNote metadata (chunk-level only)
            return_surrounding_chunks: Include prev/next chunks for context (chunk-level only)
            use_chunk_ranking: Re-rank document results using chunk-level relevance (default: True)

        Returns:
            RetrievalResult with query and results

        Raises:
            ValueError: If student_id is empty or None

        Examples:
            >>> # Document-level search (traditional)
            >>> service.search(
            ...     query_text="Explain neural networks",
            ...     student_id="STU001",
            ...     granularity="document",
            ...     top_k=5
            ... )

            >>> # Chunk-level search (precise)
            >>> service.search(
            ...     query_text="How do I declare a variable?",
            ...     student_id="STU001",
            ...     granularity="chunk",
            ...     top_k=10,
            ...     return_parent_context=True
            ... )

            >>> # Topic-filtered chunk search
            >>> service.search(
            ...     query_text="explain backpropagation",
            ...     student_id="STU001",
            ...     granularity="chunk",
            ...     filter_topics=["Neural Networks", "Deep Learning"],
            ...     require_all_topics=False
            ... )
        """
        # Validate student_id is provided for data privacy
        if not student_id or not student_id.strip():
            raise ValueError(
                "student_id is required for data privacy. "
                "Users can only query their own data."
            )

        logger.info(
            f"Executing {search_type} search for student '{student_id}': '{query_text}' "
            f"(granularity={granularity}, top_k={top_k}, node_type={initial_node_type}, "
            f"topics={filter_topics}, tags={filter_tags})"
        )

        # Verify student profile exists (security check)
        if not self.security_validator.verify_profile_exists(student_id):
            logger.error(f"Student profile not found: {student_id}")
            raise ValueError(f"Student profile '{student_id}' not found in database")

        # Route to chunk-level search if granularity is "chunk"
        if granularity == "chunk":
            if search_type == "standalone":
                raise ValueError("Standalone search not supported for chunk-level retrieval")

            result = self._dispatch_chunk_search(
                query_text=query_text,
                top_k=top_k,
                search_type=search_type,
                filter_topics=filter_topics,
                filter_tags=filter_tags,
                require_all_topics=require_all_topics,
                return_parent_context=return_parent_context,
                return_surrounding_chunks=return_surrounding_chunks,
                student_id=student_id,
            )

        # Route to document-level search
        elif granularity in ("document", "auto"):
            # Note: "auto" currently defaults to document-level
            # Future enhancement: use LLM to determine optimal granularity
            result = self._dispatch_document_search(
                query_text=query_text,
                top_k=top_k,
                search_type=search_type,
                initial_node_type=initial_node_type,
                filter_topics=filter_topics,
                filter_tags=filter_tags,
                require_all_topics=require_all_topics,
                topic_boost=topic_boost,
                use_chunk_ranking=use_chunk_ranking,
                student_id=student_id,
            )

        else:
            raise ValueError(f"Invalid granularity: {granularity}. Must be 'document', 'chunk', or 'auto'")

        # Audit log the search operation (non-blocking, failures don't break search)
        try:
            filters = {}
            if filter_topics:
                filters['topics'] = filter_topics
            if filter_tags:
                filters['tags'] = filter_tags
            if granularity:
                filters['granularity'] = granularity
            if search_type:
                filters['search_type'] = search_type

            self.audit_logger.log_search(
                student_id=student_id,
                query_text=query_text,
                result_count=result.num_results,
                filters=filters if filters else None
            )
        except Exception as e:
            # Don't fail search if audit logging fails
            logger.warning(f"Failed to log search audit: {e}")

        return result

    def _dispatch_document_search(
        self,
        query_text: str,
        top_k: int,
        search_type: str,
        initial_node_type: str,
        filter_topics: list[str] | None,
        filter_tags: list[str] | None,
        require_all_topics: bool,
        topic_boost: float,
        use_chunk_ranking: bool,
        student_id: str,
    ) -> RetrievalResult:
        """Internal dispatcher for document-level search."""
        if search_type == "hybrid":
            return self._hybrid_search(
                query_text, top_k, initial_node_type,
                filter_topics, filter_tags, require_all_topics, topic_boost,
                use_chunk_ranking, student_id
            )
        elif search_type == "vector":
            return self._vector_search(query_text, top_k, initial_node_type)
        elif search_type == "fulltext":
            return self._fulltext_search(query_text, top_k, initial_node_type)
        elif search_type == "standalone":
            return self._standalone_search(query_text)
        else:
            raise ValueError(f"Invalid search_type: {search_type}")

    def _dispatch_chunk_search(
        self,
        query_text: str,
        top_k: int,
        search_type: str,
        filter_topics: list[str] | None,
        filter_tags: list[str] | None,
        require_all_topics: bool,
        return_parent_context: bool,
        return_surrounding_chunks: bool,
        student_id: str,
    ) -> RetrievalResult:
        """Internal dispatcher for chunk-level search."""
        if search_type == "hybrid":
            return self._hybrid_chunk_search(
                query_text,
                top_k,
                filter_topics,
                filter_tags,
                require_all_topics,
                return_parent_context,
                return_surrounding_chunks,
            )
        elif search_type == "vector":
            return self._vector_chunk_search(
                query_text,
                top_k,
                return_parent_context,
                return_surrounding_chunks,
            )
        elif search_type == "fulltext":
            return self._fulltext_chunk_search(
                query_text,
                top_k,
                return_parent_context,
                return_surrounding_chunks,
            )
        else:
            raise ValueError(f"Invalid search_type for chunks: {search_type}")

    def _hybrid_search(
        self,
        query_text: str,
        top_k: int,
        initial_node_type: str,
        filter_topics: list[str] | None = None,
        filter_tags: list[str] | None = None,
        require_all_topics: bool = False,
        topic_boost: float = 1.0,
        use_chunk_ranking: bool = True,
        student_id: str = "",
    ) -> RetrievalResult:
        """
        Execute hybrid search with dynamic query generation.

        Combines vector + fulltext search, then uses LLM-generated Cypher
        to traverse the graph and enrich results. Optionally filters by topics/tags.
        Can re-rank results using chunk-level relevance for improved precision.
        """
        schema = self.schema_introspector.get_schema()

        vector_index = self._find_vector_index_for_node(initial_node_type, schema)
        fulltext_index = self._find_fulltext_index_for_node(initial_node_type, schema)

        # For LectureNote: Use chunk-level hybrid search instead of direct vector search
        # This leverages our chunk embeddings for better semantic matching
        # Then aggregate chunks to parent documents for document-level results
        if not vector_index and initial_node_type == "LectureNote" and use_chunk_ranking:
            logger.info(
                f"Using chunk-based hybrid search for {initial_node_type} (chunk embeddings available)"
            )
            # First, get top chunks using chunk-level search
            chunk_results = self._hybrid_chunk_search(
                query_text=query_text,
                top_k=top_k * 3,  # Get more chunks to ensure good document coverage
                filter_topics=filter_topics,
                filter_tags=filter_tags,
                require_all_topics=require_all_topics,
                return_parent_context=True,
                return_surrounding_chunks=False,
            )

            # Aggregate chunks to parent documents (best score per document)
            doc_scores = {}
            for result in chunk_results.results:
                parent_id = result.get('parent_id')
                score = result.get('score', 0)
                if parent_id:
                    if parent_id not in doc_scores or score > doc_scores[parent_id]['score']:
                        doc_scores[parent_id] = {
                            'parent_id': parent_id,
                            'parent_title': result.get('parent_title'),
                            'course_title': result.get('course_title'),
                            'tags': result.get('tags'),
                            'score': score
                        }

            # Sort by score and return top_k documents
            aggregated_docs = sorted(doc_scores.values(), key=lambda x: x['score'], reverse=True)[:top_k]

            # Fetch full document content for top results
            document_results = []
            if aggregated_docs:
                with self.driver.session() as session:
                    for doc in aggregated_docs:
                        result = session.run(
                            """
                            MATCH (ln:LectureNote {lecture_note_id: $parent_id})
                            OPTIONAL MATCH (ln)-[:BELONGS_TO]->(course:Course)
                            RETURN ln, course.title AS course_title
                            """,
                            parent_id=doc['parent_id']
                        )
                        record = result.single()
                        if record:
                            node_data = dict(record['ln'])
                            node_data['course_title'] = record['course_title']
                            document_results.append({
                                'node': node_data,
                                'score': doc['score']
                            })

            return RetrievalResult(
                query=query_text,
                results=document_results,
                num_results=len(document_results),
                query_generation=None
            )

        if not vector_index:
            logger.warning(
                f"No vector index found for {initial_node_type}, falling back to fulltext"
            )
            return self._fulltext_search(query_text, top_k, initial_node_type)

        if not fulltext_index:
            logger.warning(
                f"No fulltext index found for {initial_node_type}, falling back to vector"
            )
            return self._vector_search(query_text, top_k, initial_node_type)

        query_gen_result = self.query_builder.build_hybrid_retrieval_query(
            user_question=query_text,
            initial_node_type=initial_node_type,
            validate=True,
            filter_topics=filter_topics,
            filter_tags=filter_tags,
            require_all=require_all_topics,
            student_id=student_id,
        )

        if not query_gen_result.is_valid:
            logger.error(
                f"Failed to generate valid retrieval query: {query_gen_result.error_message}"
            )
            return RetrievalResult(
                query=query_gen_result.query,
                results=[],
                num_results=0,
                query_generation=query_gen_result,
            )

        logger.info(f"Using vector index: {vector_index}, fulltext index: {fulltext_index}")
        logger.debug(f"Generated retrieval query:\n{query_gen_result.query}")

        # Custom result formatter to extract all fields from Neo4j Record
        def format_record(record):
            from neo4j_graphrag.types import RetrieverResultItem
            # Extract all fields from the Record into a dict
            result_data = dict(record)
            # Use the entire record data as content (for compatibility)
            # but also include individual fields for chunk ranker access
            return RetrieverResultItem(
                content=str(record),  # Keep original behavior
                metadata=result_data  # Add all fields as metadata
            )

        retriever = HybridCypherRetriever(
            driver=self.driver,
            vector_index_name=vector_index,
            fulltext_index_name=fulltext_index,
            retrieval_query=query_gen_result.query,
            embedder=self.neo4j_embedder,
            result_formatter=format_record,
        )

        search_results = retriever.search(query_text=query_text, top_k=top_k)

        results = []
        for item in search_results.items:
            result_dict = {"content": item.content}
            if item.metadata:
                result_dict.update(item.metadata)
            results.append(result_dict)

        logger.info(f"Hybrid search returned {len(results)} results")

        # Apply chunk-aware ranking if enabled and results are LectureNotes
        if use_chunk_ranking and results and initial_node_type == "LectureNote":
            logger.info("Applying chunk-aware re-ranking for precision improvement")
            results = self.chunk_ranker.rank_documents(
                documents=results,
                query_text=query_text,
            )
            logger.info(f"Re-ranking complete. Final result count: {len(results)}")

        return RetrievalResult(
            query=query_gen_result.query,
            results=results,
            num_results=len(results),
            query_generation=query_gen_result,
        )

    def _vector_search(
        self, query_text: str, top_k: int, initial_node_type: str
    ) -> RetrievalResult:
        """Execute vector-only search with dynamic query generation."""
        schema = self.schema_introspector.get_schema()
        vector_index = self._find_vector_index_for_node(initial_node_type, schema)

        if not vector_index:
            logger.error(f"No vector index found for {initial_node_type}")
            return RetrievalResult(query="", results=[], num_results=0)

        query_gen_result = self.query_builder.build_hybrid_retrieval_query(
            user_question=query_text,
            initial_node_type=initial_node_type,
            validate=True,
        )

        if not query_gen_result.is_valid:
            logger.error(f"Query generation failed: {query_gen_result.error_message}")
            return RetrievalResult(
                query=query_gen_result.query,
                results=[],
                num_results=0,
                query_generation=query_gen_result,
            )

        from neo4j_graphrag.retrievers import VectorCypherRetriever

        retriever = VectorCypherRetriever(
            driver=self.driver,
            index_name=vector_index,
            retrieval_query=query_gen_result.query,
            embedder=self.neo4j_embedder,
        )

        search_results = retriever.search(query_text=query_text, top_k=top_k)

        results = []
        for item in search_results.items:
            result_dict = {"content": item.content}
            if item.metadata:
                result_dict.update(item.metadata)
            results.append(result_dict)

        return RetrievalResult(
            query=query_gen_result.query,
            results=results,
            num_results=len(results),
            query_generation=query_gen_result,
        )

    def _fulltext_search(
        self, query_text: str, top_k: int, initial_node_type: str
    ) -> RetrievalResult:
        """Execute fulltext-only search."""
        schema = self.schema_introspector.get_schema()
        fulltext_index = self._find_fulltext_index_for_node(initial_node_type, schema)

        if not fulltext_index:
            logger.error(f"No fulltext index found for {initial_node_type}")
            return RetrievalResult(query="", results=[], num_results=0)

        query = f"""
        CALL db.index.fulltext.queryNodes('{fulltext_index}', $query_text)
        YIELD node, score
        RETURN node, score
        ORDER BY score DESC
        LIMIT {top_k}
        """

        with self.driver.session() as session:
            result = session.run(query, query_text=query_text)
            records = list(result)

        results = []
        for record in records:
            node = record["node"]
            results.append({"node": dict(node), "score": record["score"]})

        return RetrievalResult(query=query, results=results, num_results=len(results))

    def _standalone_search(self, query_text: str) -> RetrievalResult:
        """
        Execute standalone Cypher query generated by LLM.

        This generates a complete query without hybrid search components.
        """
        query_gen_result = self.query_builder.build_standalone_query(
            user_question=query_text, validate=True
        )

        if not query_gen_result.is_valid:
            logger.error(f"Query generation failed: {query_gen_result.error_message}")
            return RetrievalResult(
                query=query_gen_result.query,
                results=[],
                num_results=0,
                query_generation=query_gen_result,
            )

        logger.debug(f"Executing standalone query:\n{query_gen_result.query}")

        with self.driver.session() as session:
            result = session.run(query_gen_result.query)
            records = [dict(record) for record in result]

        return RetrievalResult(
            query=query_gen_result.query,
            results=records,
            num_results=len(records),
            query_generation=query_gen_result,
        )

    def _find_vector_index_for_node(self, node_type: str, schema) -> str | None:
        """Find appropriate vector index for a node type."""
        for idx in schema.vector_indexes:
            if node_type in idx["labels"]:
                return idx["name"]
        return None

    def _find_fulltext_index_for_node(self, node_type: str, schema) -> str | None:
        """Find appropriate fulltext index for a node type."""
        for idx in schema.fulltext_indexes:
            if node_type in idx["labels"]:
                return idx["name"]
        return None

    def refresh_schema(self) -> None:
        """Manually refresh cached schema."""
        logger.info("Refreshing schema cache")
        self.schema_introspector.invalidate_cache()
        self.schema_introspector.get_schema(use_cache=False)

    def get_schema_summary(self) -> str:
        """Get formatted schema summary for debugging."""
        schema = self.schema_introspector.get_schema()
        return self.schema_introspector.format_schema_for_llm(schema)

    def search_by_topics(
        self,
        topics: list[str],
        query_text: str = "",
        top_k: int = 10,
        require_all_topics: bool = False,
        search_type: Literal["hybrid", "vector"] = "hybrid",
    ) -> RetrievalResult:
        """
        Convenience method to search for LectureNotes by Topic names.

        Args:
            topics: List of Topic names to filter by (via COVERS_TOPIC relationships)
            query_text: Optional semantic search query (if empty, pure topic filtering)
            top_k: Number of results to return
            require_all_topics: If True, require ALL topics; if False, require ANY
            search_type: Type of search to perform

        Returns:
            RetrievalResult with filtered notes

        Example:
            >>> service.search_by_topics(
            ...     topics=["Neural Networks", "Deep Learning"],
            ...     query_text="explain backpropagation",
            ...     require_all_topics=False
            ... )
        """
        logger.info(f"Searching by topics: {topics} (require_all={require_all_topics})")

        if not query_text:
            query_text = f"Find notes covering: {', '.join(topics)}"

        return self.search(
            query_text=query_text,
            top_k=top_k,
            search_type=search_type,
            initial_node_type="LectureNote",
            filter_topics=topics,
            require_all_topics=require_all_topics,
        )

    def search_by_tags(
        self,
        tags: list[str],
        query_text: str = "",
        top_k: int = 10,
        require_all_tags: bool = False,
        search_type: Literal["hybrid", "vector"] = "hybrid",
    ) -> RetrievalResult:
        """
        Convenience method to search for LectureNotes by tags (from tagged_topics field).

        Args:
            tags: List of tags to filter by (from node.tagged_topics array)
            query_text: Optional semantic search query (if empty, pure tag filtering)
            top_k: Number of results to return
            require_all_tags: If True, require ALL tags; if False, require ANY
            search_type: Type of search to perform

        Returns:
            RetrievalResult with filtered notes

        Example:
            >>> service.search_by_tags(
            ...     tags=["neural-networks", "cnn", "deep-learning"],
            ...     query_text="computer vision architectures",
            ...     require_all_tags=False
            ... )
        """
        logger.info(f"Searching by tags: {tags} (require_all={require_all_tags})")

        if not query_text:
            query_text = f"Find notes with tags: {', '.join(tags)}"

        return self.search(
            query_text=query_text,
            top_k=top_k,
            search_type=search_type,
            initial_node_type="LectureNote",
            filter_tags=tags,
            require_all_topics=require_all_tags,
        )

    def get_related_topics(
        self, topic_name: str, max_depth: int = 2
    ) -> list[dict[str, any]]:
        """
        Get topics related to a given topic via PREREQUISITE_FOR relationships.

        Args:
            topic_name: Name of the topic to start from
            max_depth: Maximum depth of traversal (default: 2)

        Returns:
            List of related topics with metadata

        Example:
            >>> service.get_related_topics("Neural Networks", max_depth=2)
        """
        logger.info(f"Finding related topics for: {topic_name} (depth={max_depth})")

        query = """
        MATCH (t:Topic {name: $topic_name})
        CALL apoc.path.expandConfig(t, {
            relationshipFilter: "PREREQUISITE_FOR>|<PREREQUISITE_FOR",
            minLevel: 1,
            maxLevel: $max_depth,
            uniqueness: "NODE_GLOBAL"
        })
        YIELD path
        WITH [node IN nodes(path) WHERE node.name <> $topic_name] AS related_topics
        UNWIND related_topics AS related_topic
        OPTIONAL MATCH (related_topic)<-[:COVERS_TOPIC]-(note:LectureNote)
        RETURN DISTINCT
            related_topic.name AS topic_name,
            related_topic.description AS description,
            related_topic.difficulty_level AS difficulty,
            count(DISTINCT note) AS note_count
        ORDER BY note_count DESC
        LIMIT 20
        """

        with self.driver.session() as session:
            result = session.run(query, topic_name=topic_name, max_depth=max_depth)
            topics = [dict(record) for record in result]

        logger.info(f"Found {len(topics)} related topics")
        return topics

    def search_chunks(
        self,
        query_text: str,
        top_k: int = 10,
        search_type: Literal["hybrid", "vector", "fulltext"] = "hybrid",
        filter_topics: list[str] | None = None,
        filter_tags: list[str] | None = None,
        require_all_topics: bool = False,
        return_parent_context: bool = True,
        return_surrounding_chunks: bool = False,
    ) -> RetrievalResult:
        """
        [DEPRECATED] Search for specific chunks instead of full LectureNotes.

        .. deprecated::
            Use `search(granularity="chunk", ...)` instead. This method is maintained
            for backwards compatibility but will be removed in a future version.

        Enables precise, paragraph-level retrieval for better context control.

        Args:
            query_text: User's natural language question
            top_k: Number of chunks to return
            search_type: Type of search (hybrid, vector, or fulltext)
            filter_topics: List of Topic names to filter by
            filter_tags: List of tags to filter by
            require_all_topics: If True, require ALL topics; if False, require ANY
            return_parent_context: Include parent LectureNote metadata
            return_surrounding_chunks: Include prev/next chunks for context

        Returns:
            RetrievalResult with chunk-level results

        Example:
            >>> # Old way (deprecated)
            >>> service.search_chunks(
            ...     query="How do I declare a variable in Python?",
            ...     top_k=5,
            ...     return_parent_context=True
            ... )
            >>>
            >>> # New way (recommended)
            >>> service.search(
            ...     query_text="How do I declare a variable in Python?",
            ...     granularity="chunk",
            ...     top_k=5,
            ...     return_parent_context=True
            ... )
        """
        logger.warning(
            "search_chunks() is deprecated. Use search(granularity='chunk', ...) instead."
        )

        # Delegate to unified search interface
        return self.search(
            query_text=query_text,
            top_k=top_k,
            granularity="chunk",
            search_type=search_type,
            filter_topics=filter_topics,
            filter_tags=filter_tags,
            require_all_topics=require_all_topics,
            return_parent_context=return_parent_context,
            return_surrounding_chunks=return_surrounding_chunks,
        )

    def _hybrid_chunk_search(
        self,
        query_text: str,
        top_k: int,
        filter_topics: list[str] | None,
        filter_tags: list[str] | None,
        require_all_topics: bool,
        return_parent_context: bool,
        return_surrounding_chunks: bool,
    ) -> RetrievalResult:
        """Execute hybrid chunk search."""
        schema = self.schema_introspector.get_schema()

        vector_index = "chunk_content_vector"
        fulltext_index = "chunk_fulltext"

        # Build retrieval query
        query = self._build_chunk_retrieval_query(
            vector_index,
            fulltext_index,
            filter_topics,
            filter_tags,
            require_all_topics,
            return_parent_context,
            return_surrounding_chunks,
        )

        # Execute hybrid search
        from neo4j_graphrag.retrievers import HybridRetriever

        # Create hybrid retriever with custom query
        query_embedding = self.neo4j_embedder.embed_query(query_text)

        with self.driver.session() as session:
            # Execute hybrid search manually
            result = session.run(
                query,
                query_text=query_text,
                query_vector=query_embedding,
                vector_index_name=vector_index,
                fulltext_index_name=fulltext_index,
                top_k=top_k,
            )
            records = [dict(record) for record in result]

        results = []
        for record in records:
            results.append(record)

        logger.info(f"Hybrid chunk search returned {len(results)} results")

        return RetrievalResult(
            query=query,
            results=results,
            num_results=len(results),
        )

    def _vector_chunk_search(
        self,
        query_text: str,
        top_k: int,
        return_parent_context: bool,
        return_surrounding_chunks: bool,
    ) -> RetrievalResult:
        """Execute vector-only chunk search."""
        from neo4j_graphrag.retrievers import VectorRetriever

        retriever = VectorRetriever(
            driver=self.driver,
            index_name="chunk_content_vector",
            embedder=self.neo4j_embedder,
        )

        search_results = retriever.search(query_text=query_text, top_k=top_k)

        # Enrich with parent context if requested
        results = []
        for item in search_results.items:
            result_dict = {"content": item.content}
            if item.metadata:
                result_dict.update(item.metadata)

            if return_parent_context:
                # Fetch parent LectureNote info
                chunk_id = result_dict.get("chunk_id")
                if chunk_id:
                    parent_info = self._get_parent_context(chunk_id)
                    result_dict["parent"] = parent_info

            results.append(result_dict)

        query = f"Vector search on chunk_content_vector index"
        return RetrievalResult(
            query=query,
            results=results,
            num_results=len(results),
        )

    def _fulltext_chunk_search(
        self,
        query_text: str,
        top_k: int,
        return_parent_context: bool,
        return_surrounding_chunks: bool,
    ) -> RetrievalResult:
        """Execute fulltext-only chunk search."""
        query = f"""
        CALL db.index.fulltext.queryNodes('chunk_fulltext', $query_text)
        YIELD node AS chunk, score
        RETURN chunk, score
        ORDER BY score DESC
        LIMIT {top_k}
        """

        with self.driver.session() as session:
            result = session.run(query, query_text=query_text)
            records = list(result)

        results = []
        for record in records:
            chunk = record["chunk"]
            result_dict = {
                "chunk_id": chunk.get("chunk_id"),
                "content": chunk.get("content"),
                "heading": chunk.get("heading"),
                "chunk_index": chunk.get("chunk_index"),
                "score": record["score"],
            }

            if return_parent_context:
                parent_info = self._get_parent_context(chunk.get("chunk_id"))
                result_dict["parent"] = parent_info

            results.append(result_dict)

        return RetrievalResult(query=query, results=results, num_results=len(results))

    def _build_chunk_retrieval_query(
        self,
        vector_index: str,
        fulltext_index: str,
        filter_topics: list[str] | None,
        filter_tags: list[str] | None,
        require_all_topics: bool,
        return_parent_context: bool,
        return_surrounding_chunks: bool,
    ) -> str:
        """Build Cypher query for chunk-based hybrid retrieval."""
        # Base hybrid search
        query = f"""
        CALL () {{
            CALL db.index.vector.queryNodes($vector_index_name, $top_k, $query_vector)
            YIELD node, score
            WITH collect({{node:node, score:score}}) AS nodes, max(score) AS vector_max_score
            UNWIND nodes AS n
            RETURN n.node AS chunk, (n.score / vector_max_score) AS score
            UNION
            CALL db.index.fulltext.queryNodes($fulltext_index_name, $query_text)
            YIELD node, score
            WITH collect({{node:node, score:score}}) AS nodes, max(score) AS ft_max_score
            UNWIND nodes AS n
            RETURN n.node AS chunk, (n.score / ft_max_score) AS score
        }}
        WITH chunk, max(score) AS score
        """

        # Add tag filtering via parent LectureNote
        # Note: Topics were removed - only tag filtering is supported
        if filter_tags:
            # Tags are stored on LectureNote, so we need to join through PART_OF
            tags_str = ", ".join(f"'{t}'" for t in filter_tags)
            logic = "ALL" if require_all_topics else "ANY"
            query += f"""
        MATCH (chunk)-[:PART_OF]->(ln:LectureNote)
        WHERE {logic}(tag IN [{tags_str}] WHERE tag IN ln.tagged_topics)
        """

        # Add parent context
        if return_parent_context:
            query += """
        MATCH (chunk)-[:PART_OF]->(ln:LectureNote)
        OPTIONAL MATCH (ln)-[:BELONGS_TO]->(course:Course)
        """

        # Add surrounding chunks
        if return_surrounding_chunks:
            query += """
        OPTIONAL MATCH (prev:Chunk)-[:NEXT_CHUNK]->(chunk)
        OPTIONAL MATCH (chunk)-[:NEXT_CHUNK]->(next:Chunk)
        """

        # Build RETURN clause
        return_fields = [
            "chunk.chunk_id AS chunk_id",
            "chunk.content AS content",
            "score",
        ]

        if return_parent_context:
            return_fields.extend([
                "ln.lecture_note_id AS parent_id",
                "ln.title AS parent_title",
                "ln.tagged_topics AS tags",
                "course.title AS course_title",
            ])

        if return_surrounding_chunks:
            return_fields.extend([
                "prev.content AS previous_chunk",
                "next.content AS next_chunk",
            ])

        query += f"\nRETURN {', '.join(return_fields)}"
        query += "\nORDER BY score DESC"
        query += "\nLIMIT $top_k"

        return query

    def _get_parent_context(self, chunk_id: str) -> dict[str, Any]:
        """Fetch parent LectureNote context for a chunk."""
        query = """
        MATCH (c:Chunk {chunk_id: $chunk_id})-[:PART_OF]->(ln:LectureNote)
        OPTIONAL MATCH (ln)-[:BELONGS_TO]->(course:Course)
        RETURN ln.lecture_note_id AS lecture_note_id,
               ln.title AS title,
               course.title AS course_title
        """

        with self.driver.session() as session:
            result = session.run(query, chunk_id=chunk_id)
            record = result.single()

        if record:
            return dict(record)
        return {}
