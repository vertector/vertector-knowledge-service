# Investigation: Improving Document-Level Search Precision

## Problem Statement
Document-level search returns less precise results compared to chunk-level search. For query "What are the different data types in Python?", it returned all 3 lecture notes (including a calculus one) instead of just the Python-related note.

## Current Architecture Analysis

### 1. Document-Level Search Flow (service.py:258-329)
```
search(granularity="document") 
  → _dispatch_document_search()
    → _hybrid_search()  
      → query_builder.build_hybrid_retrieval_query()  # Generates Cypher
      → HybridCypherRetriever.search()                # Executes hybrid search
```

### 2. How Hybrid Search Works
- **Vector Search**: Uses embedding similarity on entire document (title + content + summary + key_concepts)
- **Fulltext Search**: Keyword matching on document text fields
- **Score Normalization**: Normalizes vector and fulltext scores separately, then combines
- **Graph Traversal**: LLM-generated Cypher query enriches results with related entities

### 3. Current Limitations

#### A. Coarse-Grained Embeddings
- Document embeddings combine ALL content into one vector
- A Python lecture note embedding includes:
  - Title: "Python Variables and Data Types"
  - Content: Full markdown with variables, types, examples
  - Summary: Auto-generated summary
  - Key concepts: ['variables', 'data types', 'type conversion', ...]

**Issue**: The embedding dilutes specific concepts across hundreds of words

#### B. No Relevance Re-ranking
- Results are sorted by hybrid score (vector + fulltext)
- No post-retrieval filtering based on semantic relevance
- No use of chunked content for relevance validation

#### C. Limited Use of Metadata
- Auto-generated tags (`tagged_topics`) are created but not heavily weighted
- Tags like `['python-variables', 'data-types', ...]` could improve filtering
- Current tag filtering requires explicit user specification

## Proposed Improvements

### Strategy 1: Chunk-Aware Document Ranking ⭐ RECOMMENDED
**Concept**: Use chunk-level scores to re-rank document-level results

**Implementation**:
1. Perform hybrid search at document level (as now)
2. For each matched document, find top-K matching chunks
3. Re-rank documents by:
   - Max chunk score (best matching chunk)
   - Average top-3 chunk scores
   - Count of highly-relevant chunks (score > threshold)
4. Return documents with enriched metadata about which chunks matched

**Pros**:
- Leverages existing chunk infrastructure
- Provides better precision without losing document context
- Can show users which parts of the document are most relevant
- Minimal changes to existing code

**Cons**:
- Requires additional chunk queries (performance hit)
- More complex scoring logic

**Code Changes**:
- Add `_chunk_aware_document_search()` method in service.py
- Modify `_dispatch_document_search()` to optionally use this strategy
- Add parameter `use_chunk_ranking: bool = True` to search()

---

### Strategy 2: Tag-Based Relevance Filtering
**Concept**: Auto-filter using the tagged_topics field

**Implementation**:
1. Extract key terms from user query using LLM
2. Match against `tagged_topics` arrays in candidates
3. Boost scores for documents with matching tags
4. Filter out documents with zero tag overlap (optional)

**Pros**:
- Leverages existing tag generation
- Fast - no additional queries needed
- Works well for topical filtering

**Cons**:
- Depends on quality of auto-generated tags
- Might filter out relevant documents with different terminology

**Code Changes**:
- Add `_extract_query_keywords()` using LLM
- Modify scoring in `_hybrid_search()` to include tag matching
- Add tag overlap calculation to result metadata

---

### Strategy 3: Semantic Summary Matching
**Concept**: Use auto-generated summaries for relevance checking

**Implementation**:
1. For each matched document, compare query embedding vs summary embedding
2. Use summary similarity as a precision gate
3. Filter documents where summary similarity < threshold

**Pros**:
- Summaries are concise and topical
- Already generated automatically
- Good proxy for document relevance

**Cons**:
- Summary quality varies
- Another embedding comparison (slight performance hit)

**Code Changes**:
- Pre-compute summary embeddings at ingestion time
- Add summary similarity check in search results
- Filter/re-rank based on summary relevance

---

### Strategy 4: LLM-Based Result Filtering (Expensive)
**Concept**: Use LLM to judge relevance of each result

**Implementation**:
1. Get initial hybrid search results
2. For each result, ask LLM: "Is this document relevant to: {query}?"
3. Filter or re-rank based on LLM judgment

**Pros**:
- Highest precision possible
- Can handle nuanced relevance judgments

**Cons**:
- Expensive (LLM call per result)
- Slow (serial processing)
- Requires careful prompt engineering

---

### Strategy 5: Hybrid Granularity (Best of Both Worlds)
**Concept**: Return both documents AND top chunks in same result

**Implementation**:
1. When granularity="document", also find top chunks
2. Return documents with embedded top-K relevant chunks
3. Front-end can show document with highlighted relevant sections

**Pros**:
- Gives users full context + precision
- Better UX - shows exactly where answer is
- Reuses chunk search infrastructure

**Cons**:
- Larger response payloads
- UI complexity

---

## Recommended Implementation Plan

### Phase 1: Chunk-Aware Document Ranking (Immediate)
1. Implement Strategy 1 as the primary improvement
2. Add parameter `use_chunk_ranking: bool = True` to search()
3. For document search, query top-3 chunks per document
4. Re-rank by max chunk score

### Phase 2: Tag-Based Filtering (Enhancement)
1. Implement Strategy 2 as an enhancement
2. Extract query keywords automatically
3. Boost documents with matching tags
4. Add tag overlap to result metadata

### Phase 3: Evaluation & Tuning
1. Create comprehensive test suite
2. Compare precision/recall for:
   - Pure document search
   - Chunk-aware document search
   - Tag-filtered search
3. Tune scoring weights and thresholds

## Code Locations to Modify

### service.py
- Line 258: `_hybrid_search()` - add chunk re-ranking logic
- Line 193: `_dispatch_document_search()` - route to chunk-aware search
- Line 93: `search()` - add `use_chunk_ranking` parameter

### New file: chunk_aware_ranker.py
```python
class ChunkAwareDocumentRanker:
    """Re-ranks documents using chunk-level relevance."""
    
    def rank_documents(
        self,
        documents: list[dict],
        query_text: str,
        top_chunks_per_doc: int = 3
    ) -> list[dict]:
        """
        Re-rank documents by their best matching chunks.
        
        For each document:
        1. Find top-K chunks using hybrid chunk search
        2. Calculate max_chunk_score, avg_chunk_score
        3. Re-sort documents by chunk-derived score
        """
        pass
```

## Test Cases to Create

1. **Specific Topic Query**: "What are Python data types?"
   - Expected: Only Python lecture notes
   - Current: Returns all notes including calculus

2. **Specific Concept Query**: "Explain the LIATE rule"
   - Expected: Only integration techniques note
   - Current: Should work (verify)

3. **Broad Query**: "Show me all programming concepts"
   - Expected: All Python notes
   - Current: Unknown

4. **Cross-Topic Query**: "Compare functions in math and programming"
   - Expected: Both Python functions and calculus notes
   - Current: Unknown

## Metrics to Track

- **Precision@K**: % of top-K results that are relevant
- **MRR (Mean Reciprocal Rank)**: 1/rank of first relevant result
- **nDCG**: Normalized discounted cumulative gain
- **User Feedback**: Explicit relevance judgments

## Next Steps

1. ✅ Document current architecture (this file)
2. ⏭️ Implement chunk-aware document ranking
3. ⏭️ Create test suite with ground truth labels
4. ⏭️ Evaluate improvement in precision
5. ⏭️ Deploy and monitor
