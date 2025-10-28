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
from note_service.retrieval.embedder import EmbeddingService
from note_service.retrieval.query_builder import DynamicQueryBuilder, QueryGenerationResult
from note_service.retrieval.schema_introspector import SchemaIntrospector

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

        logger.info("RetrievalService initialized successfully")

    def search(
        self,
        query_text: str,
        top_k: int = 10,
        search_type: Literal["hybrid", "vector", "fulltext", "standalone"] = "hybrid",
        initial_node_type: str = "Note",
    ) -> RetrievalResult:
        """
        Main search method - dynamically builds and executes retrieval query.

        Args:
            query_text: User's natural language question
            top_k: Number of results to return
            search_type: Type of search to perform
            initial_node_type: Starting node type for hybrid search

        Returns:
            RetrievalResult with query and results
        """
        logger.info(
            f"Executing {search_type} search for: '{query_text}' "
            f"(top_k={top_k}, node_type={initial_node_type})"
        )

        if search_type == "hybrid":
            return self._hybrid_search(query_text, top_k, initial_node_type)
        elif search_type == "vector":
            return self._vector_search(query_text, top_k, initial_node_type)
        elif search_type == "fulltext":
            return self._fulltext_search(query_text, top_k, initial_node_type)
        elif search_type == "standalone":
            return self._standalone_search(query_text)
        else:
            raise ValueError(f"Invalid search_type: {search_type}")

    def _hybrid_search(
        self, query_text: str, top_k: int, initial_node_type: str
    ) -> RetrievalResult:
        """
        Execute hybrid search with dynamic query generation.

        Combines vector + fulltext search, then uses LLM-generated Cypher
        to traverse the graph and enrich results.
        """
        schema = self.schema_introspector.get_schema()

        vector_index = self._find_vector_index_for_node(initial_node_type, schema)
        fulltext_index = self._find_fulltext_index_for_node(initial_node_type, schema)

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

        retriever = HybridCypherRetriever(
            driver=self.driver,
            vector_index_name=vector_index,
            fulltext_index_name=fulltext_index,
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

        logger.info(f"Hybrid search returned {len(results)} results")

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
