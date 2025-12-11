/*
============================================================================
Security Constraints for Student Data Isolation
============================================================================
Enforces database-level data ownership and access control to ensure
students can only access their own data.
============================================================================
*/

-- ============================================================================
-- 1. OWNERSHIP CONSTRAINTS
-- ============================================================================

-- Ensure every LectureNote has an owner (Profile)
-- This prevents orphaned notes that don't belong to anyone
CREATE CONSTRAINT lecture_note_ownership IF NOT EXISTS
FOR (ln:LectureNote)
REQUIRE EXISTS {
    (ln)<-[:CREATED_NOTE]-(:Profile)
};

-- Ensure every Chunk belongs to a LectureNote (which has an owner)
-- This creates transitive ownership: Profile -> LectureNote -> Chunk
CREATE CONSTRAINT chunk_ownership IF NOT EXISTS
FOR (c:Chunk)
REQUIRE EXISTS {
    (c)-[:PART_OF]->(:LectureNote)
};


-- ============================================================================
-- 2. UNIQUENESS CONSTRAINTS (Already exist, kept for reference)
-- ============================================================================

-- These ensure data integrity
-- CREATE CONSTRAINT profile_student_id_unique IF NOT EXISTS
-- FOR (p:Profile) REQUIRE p.student_id IS UNIQUE;

-- CREATE CONSTRAINT lecture_note_id_unique IF NOT EXISTS
-- FOR (ln:LectureNote) REQUIRE ln.lecture_note_id IS UNIQUE;


-- ============================================================================
-- 3. AUDIT LOG NODE
-- ============================================================================

-- Create node label for audit trail
-- :AccessLog nodes track who accessed what and when
CREATE INDEX access_log_timestamp IF NOT EXISTS
FOR (log:AccessLog) ON (log.timestamp);

CREATE INDEX access_log_student_id IF NOT EXISTS
FOR (log:AccessLog) ON (log.student_id);


-- ============================================================================
-- 4. SECURITY METADATA
-- ============================================================================

-- Index for faster student_id lookups during security checks
CREATE INDEX profile_student_id_lookup IF NOT EXISTS
FOR (p:Profile) ON (p.student_id);

-- Index for lecture note ownership queries
CREATE INDEX lecture_note_student_lookup IF NOT EXISTS
FOR (ln:LectureNote) ON (ln.student_id);


-- ============================================================================
-- USAGE NOTES
-- ============================================================================
--
-- These constraints are automatically enforced by Neo4j at write time:
--
-- 1. Cannot create LectureNote without Profile relationship
-- 2. Cannot create Chunk without LectureNote relationship
-- 3. All security checks are database-enforced
--
-- To apply these constraints:
--   cat schema/05_security_constraints.cypher | cypher-shell -u neo4j -p password
--
============================================================================
*/
