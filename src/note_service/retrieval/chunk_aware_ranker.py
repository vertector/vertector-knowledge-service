"""
============================================================================
Chunk-Aware Document Ranker
============================================================================
Re-ranks document-level search results using chunk-level relevance scores
to improve precision while maintaining document-level context.
============================================================================
"""

import logging
from dataclasses import dataclass
from typing import Any

from neo4j import Driver
from neo4j_graphrag.embeddings import SentenceTransformerEmbeddings

from note_service.config import Settings

logger = logging.getLogger(__name__)


@dataclass
class ChunkRelevanceMetrics:
    """Metrics about chunk-level relevance for a document."""

    max_chunk_score: float
    avg_top3_score: float
    num_relevant_chunks: int
    top_chunks: list[dict[str, Any]]

    def get_combined_score(
        self,
        original_doc_score: float | None = None,
        max_weight: float = 0.6,
        avg_weight: float = 0.3,
        doc_weight: float = 0.1,
    ) -> float:
        """
        Calculate combined relevance score.

        Args:
            original_doc_score: Original document-level hybrid score (optional)
            max_weight: Weight for max chunk score (default: 0.6)
            avg_weight: Weight for average top-3 chunk score (default: 0.3)
            doc_weight: Weight for original document score (default: 0.1)

        Returns:
            Combined weighted score
        """
        score = (max_weight * self.max_chunk_score) + (avg_weight * self.avg_top3_score)

        if original_doc_score is not None:
            score += doc_weight * original_doc_score

        return score


class ChunkAwareDocumentRanker:
    """
    Re-ranks document-level search results using chunk-level relevance.

    Strategy:
    1. For each document, find its top-K most relevant chunks
    2. Calculate chunk-based relevance metrics (max score, avg top-3, count)
    3. Re-rank documents by combined score (chunk metrics + original doc score)
    4. Enrich results with metadata about which chunks matched

    This improves precision by leveraging fine-grained chunk embeddings
    while maintaining document-level context.
    """

    def __init__(
        self,
        driver: Driver,
        embedder: SentenceTransformerEmbeddings,
        settings: Settings,
        top_chunks_per_doc: int = 3,
        relevance_threshold: float = 0.7,
    ):
        """
        Initialize chunk-aware document ranker.

        Args:
            driver: Neo4j driver
            embedder: Embedding service for vector search
            settings: Application settings
            top_chunks_per_doc: Number of top chunks to analyze per document
            relevance_threshold: Minimum score to count as relevant chunk
        """
        self.driver = driver
        self.embedder = embedder
        self.settings = settings
        self.top_chunks_per_doc = top_chunks_per_doc
        self.relevance_threshold = relevance_threshold

        logger.info(
            f"Initialized ChunkAwareDocumentRanker "
            f"(top_chunks={top_chunks_per_doc}, threshold={relevance_threshold})"
        )

    def rank_documents(
        self,
        documents: list[dict[str, Any]],
        query_text: str,
        filter_by_parent_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Re-rank documents using chunk-level relevance.

        Args:
            documents: List of document results from initial search
            query_text: Original user query
            filter_by_parent_ids: Optional list of lecture_note_ids to filter chunks by

        Returns:
            Re-ranked list of documents with enriched chunk metadata
        """
        if not documents:
            return documents

        logger.info(
            f"Re-ranking {len(documents)} documents using chunk-level relevance "
            f"for query: '{query_text}'"
        )

        # Calculate chunk metrics for each document
        enriched_docs = []
        for doc in documents:
            # Extract document ID (lecture_note_id)
            doc_id = self._extract_document_id(doc)

            if not doc_id:
                logger.warning(f"Could not extract document ID from result: {doc.keys()}")
                # Keep document but with low ranking
                enriched_doc = doc.copy()
                enriched_doc["_chunk_metrics"] = None
                enriched_doc["_combined_score"] = doc.get("score", 0) * 0.5
                enriched_docs.append(enriched_doc)
                continue

            # Find top chunks for this document
            chunk_metrics = self._get_chunk_metrics_for_document(
                doc_id=doc_id,
                query_text=query_text,
            )

            # Calculate combined score
            original_score = doc.get("score")
            combined_score = chunk_metrics.get_combined_score(original_score)

            # Enrich document with chunk metadata
            enriched_doc = doc.copy()
            enriched_doc["_chunk_metrics"] = {
                "max_chunk_score": chunk_metrics.max_chunk_score,
                "avg_top3_score": chunk_metrics.avg_top3_score,
                "num_relevant_chunks": chunk_metrics.num_relevant_chunks,
                "top_chunks": chunk_metrics.top_chunks,
            }
            enriched_doc["_combined_score"] = combined_score
            enriched_doc["_original_score"] = original_score

            enriched_docs.append(enriched_doc)

        # Re-rank by combined score
        ranked_docs = sorted(
            enriched_docs,
            key=lambda d: d.get("_combined_score", 0),
            reverse=True
        )

        logger.info(
            f"Re-ranking complete. Top document: "
            f"{self._extract_document_title(ranked_docs[0])} "
            f"(combined_score={ranked_docs[0].get('_combined_score', 0):.3f})"
        )

        return ranked_docs

    def _get_chunk_metrics_for_document(
        self,
        doc_id: str,
        query_text: str,
    ) -> ChunkRelevanceMetrics:
        """
        Get chunk-level relevance metrics for a specific document.

        Args:
            doc_id: lecture_note_id of the document
            query_text: User's query

        Returns:
            ChunkRelevanceMetrics with scores and top chunks
        """
        # Generate query embedding
        query_embedding = self.embedder.embed_query(query_text)

        # Hybrid search query for chunks from a specific parent document
        chunk_query = """
        CALL {
            CALL db.index.vector.queryNodes($vector_index_name, $top_k, $query_vector)
            YIELD node, score
            WITH collect({node:node, score:score}) AS nodes, max(score) AS vector_max_score
            UNWIND nodes AS n
            RETURN n.node AS chunk, (n.score / vector_max_score) AS score
            UNION
            CALL db.index.fulltext.queryNodes($fulltext_index_name, $query_text)
            YIELD node, score
            WITH collect({node:node, score:score}) AS nodes, max(score) AS ft_max_score
            UNWIND nodes AS n
            RETURN n.node AS chunk, (n.score / ft_max_score) AS score
        }
        WITH chunk, max(score) AS score

        MATCH (chunk:Chunk)-[:PART_OF]->(ln:LectureNote {lecture_note_id: $parent_id})

        RETURN chunk.chunk_id AS chunk_id,
               chunk.content AS content,
               chunk.heading AS heading,
               score
        ORDER BY score DESC
        LIMIT $top_k
        """

        # Execute query
        with self.driver.session() as session:
            result = session.run(
                chunk_query,
                query_text=query_text,
                query_vector=query_embedding,
                vector_index_name="chunk_content_vector",
                fulltext_index_name="chunk_fulltext",
                parent_id=doc_id,
                top_k=self.top_chunks_per_doc,
            )
            records = [dict(record) for record in result]

        if not records:
            # No chunks found - return zero metrics
            return ChunkRelevanceMetrics(
                max_chunk_score=0.0,
                avg_top3_score=0.0,
                num_relevant_chunks=0,
                top_chunks=[],
            )

        # Extract scores
        scores = [record.get("score", 0.0) for record in records]

        max_score = max(scores) if scores else 0.0
        avg_top3 = sum(scores[:3]) / min(len(scores), 3) if scores else 0.0
        num_relevant = sum(1 for s in scores if s >= self.relevance_threshold)

        # Extract top chunk metadata
        top_chunks = []
        for record in records[:self.top_chunks_per_doc]:
            content = str(record.get("content", ""))
            chunk_data = {
                "chunk_id": record.get("chunk_id"),
                "content": content[:200] + "..." if len(content) > 200 else content,
                "heading": record.get("heading"),
                "score": record.get("score", 0.0),
            }
            top_chunks.append(chunk_data)

        return ChunkRelevanceMetrics(
            max_chunk_score=max_score,
            avg_top3_score=avg_top3,
            num_relevant_chunks=num_relevant,
            top_chunks=top_chunks,
        )

    def _extract_document_id(self, doc: dict[str, Any]) -> str | None:
        """Extract lecture_note_id from document result."""
        # Try common field names
        for field in ["lecture_note_id", "parent_id", "note_id", "id"]:
            if field in doc and doc[field]:
                return doc[field]

        # Check nested metadata
        if "metadata" in doc and isinstance(doc["metadata"], dict):
            for field in ["lecture_note_id", "parent_id", "note_id", "id"]:
                if field in doc["metadata"]:
                    return doc["metadata"][field]

        return None

    def _extract_document_title(self, doc: dict[str, Any]) -> str:
        """Extract title from document result for logging."""
        for field in ["lecture_note_title", "title", "name"]:
            if field in doc and doc[field]:
                return str(doc[field])
        return "Unknown"
