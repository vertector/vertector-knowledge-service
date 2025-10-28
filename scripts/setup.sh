#!/bin/bash

# ============================================================================
# Academic Note-Taking GraphRAG System - Setup Script
# ============================================================================
# Critical operations: Neo4j startup, index verification, plugin checks
# ============================================================================

set -e  # Exit on error

echo "=========================================="
echo "GraphRAG Academic System Setup"
echo "=========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_info() { echo -e "${YELLOW}ℹ $1${NC}"; }

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker not installed"
    exit 1
fi

# Create directories
mkdir -p neo4j/{data,logs,import,plugins} python/{models,services,db} tests/{unit,integration}

# Create .env if missing
[ ! -f .env ] && cp .env.example .env && print_success ".env created from template"

# Start Neo4j
print_info "Starting Neo4j..."
docker-compose up -d

# Wait for Neo4j (with actual query test)
print_info "Waiting for Neo4j to be ready..."
for i in {1..60}; do
    if docker exec neo4j-graphrag cypher-shell -u neo4j -p graphrag_secure_password_2025 "RETURN 1 AS test" &> /dev/null; then
        print_success "Neo4j is ready"
        break
    fi
    [ $i -eq 60 ] && print_error "Neo4j failed to start" && exit 1
    sleep 2
done

# CRITICAL: Verify APOC and GDS plugins loaded
print_info "Verifying plugins..."

# Check APOC by calling a procedure
if docker exec neo4j-graphrag cypher-shell -u neo4j -p graphrag_secure_password_2025 \
    "RETURN apoc.version() AS version" --format plain &> /dev/null; then
    print_success "APOC plugin loaded"
else
    print_error "APOC plugin NOT loaded - check docker-compose.yml"
    exit 1
fi

# Check GDS by calling a procedure
if docker exec neo4j-graphrag cypher-shell -u neo4j -p graphrag_secure_password_2025 \
    "RETURN gds.version() AS version" --format plain &> /dev/null; then
    print_success "Graph Data Science plugin loaded"
else
    print_error "GDS plugin NOT loaded - check docker-compose.yml"
    exit 1
fi

# Create constraints (Community Edition - UNIQUENESS constraints only)
print_info "Creating constraints..."
docker exec -i neo4j-graphrag cypher-shell -u neo4j -p graphrag_secure_password_2025 < schema/01_constraints.cypher
print_success "Constraints created"

# Create indexes
print_info "Creating indexes (including vector indexes)..."
docker exec -i neo4j-graphrag cypher-shell -u neo4j -p graphrag_secure_password_2025 < schema/02_indexes.cypher
print_success "Indexes created"

# CRITICAL: Wait for indexes to be ONLINE (especially vector indexes)
print_info "Waiting for indexes to populate (this is critical for vector indexes)..."
sleep 10

# Verify all indexes are ONLINE
INDEX_CHECK=$(docker exec neo4j-graphrag cypher-shell -u neo4j -p graphrag_secure_password_2025 \
    "SHOW INDEXES YIELD name, state, populationPercent
     WHERE state <> 'ONLINE' OR populationPercent < 100.0
     RETURN name, state, populationPercent" --format plain)

if [ -z "$INDEX_CHECK" ]; then
    print_success "All indexes are ONLINE and fully populated"
else
    print_info "Some indexes are still populating:"
    echo "$INDEX_CHECK"
    print_info "This is OK for empty database. Indexes will populate when data is added."
fi

# CRITICAL: Verify vector indexes specifically
print_info "Verifying vector indexes..."
VECTOR_INDEXES=$(docker exec neo4j-graphrag cypher-shell -u neo4j -p graphrag_secure_password_2025 \
    "SHOW INDEXES YIELD name, type, options WHERE type = 'VECTOR' RETURN name, options" \
    --format plain)

if echo "$VECTOR_INDEXES" | grep -q "1024"; then
    print_success "Vector indexes configured correctly (1024 dimensions)"
else
    print_error "Vector index dimension mismatch"
    echo "$VECTOR_INDEXES"
fi

if echo "$VECTOR_INDEXES" | grep -qi "cosine"; then
    print_success "Vector indexes using cosine similarity"
else
    print_error "Vector index similarity function incorrect"
    echo "$VECTOR_INDEXES"
fi

# Load sample data (optional)
read -p "Load sample data? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Loading sample data..."
    docker exec -i neo4j-graphrag cypher-shell -u neo4j -p graphrag_secure_password_2025 < schema/05_sample_data.cypher
    print_success "Sample data loaded"

    # Verify data loaded
    NODE_COUNT=$(docker exec neo4j-graphrag cypher-shell -u neo4j -p graphrag_secure_password_2025 \
        "MATCH (n) RETURN count(n) AS total" --format plain | grep -o '[0-9]*')
    print_success "$NODE_COUNT nodes created"
fi

# Python setup
read -p "Set up Python environment? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd python

    # Check Python version
    PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '(?<=Python )\d+\.\d+')
    if (( $(echo "$PYTHON_VERSION < 3.12" | bc -l) )); then
        print_error "Python 3.12+ required (found $PYTHON_VERSION)"
        exit 1
    fi
    print_success "Python $PYTHON_VERSION detected"

    # Create venv
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip setuptools wheel
    pip install -r requirements.txt

    print_success "Python dependencies installed"

    # CRITICAL: Download and cache embedding model
    print_info "Downloading embedding model (Qwen3-Embedding-0.6B, ~1.2GB)..."
    python3 << 'EOF'
from sentence_transformers import SentenceTransformer
import os

# Create cache directory
os.makedirs("./models/cache", exist_ok=True)

# Download model to cache
print("Loading model...")
model = SentenceTransformer(
    "Qwen/Qwen3-Embedding-0.6B",
    cache_folder="./models/cache"
)

# Test embedding generation
test_embedding = model.encode("Test sentence", prompt_name="query")
print(f"✓ Model loaded successfully")
print(f"✓ Embedding dimension: {len(test_embedding)}")
assert len(test_embedding) == 1024, "Dimension mismatch!"
EOF

    print_success "Embedding model cached and verified"

    cd ..
fi

# Summary
echo ""
echo "=========================================="
echo "Setup Complete! 🎉"
echo "=========================================="
echo ""
print_success "Neo4j Browser: http://localhost:7474"
print_success "Bolt URI:      bolt://localhost:7687"
print_success "Credentials:   neo4j / graphrag_secure_password_2025"
echo ""
print_info "Quick commands:"
echo "  docker-compose logs -f           # View logs"
echo "  docker-compose down              # Stop"
echo "  docker exec -it neo4j-graphrag cypher-shell -u neo4j -p graphrag_secure_password_2025"
echo ""
print_info "Python:"
echo "  cd python && source venv/bin/activate"
echo "  python -c 'from db.connection import get_connection; print(get_connection().health_check())'"
echo ""
