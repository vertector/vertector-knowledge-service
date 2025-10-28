# GraphRAG Note Service - Production Dockerfile
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies and uv
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy project files
COPY pyproject.toml .
COPY src/ ./src/
COPY schema/ ./schema/

# Install Python dependencies using uv
RUN uv pip install --system --no-cache .

# Create directories
RUN mkdir -p /app/logs /app/.cache/huggingface

# Set Python path
ENV PYTHONPATH=/app/src

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD python -c "import sys; sys.path.insert(0, '/app/src'); from note_service.db.connection import Neo4jConnection; from note_service.config import Settings; conn = Neo4jConnection(settings=Settings()); conn.close(); print('healthy')" || exit 1

# Run as non-root user
RUN useradd -m -u 1000 noteservice && chown -R noteservice:noteservice /app
USER noteservice

# Expose ports (if needed for future HTTP API)
EXPOSE 8000

# Run the application
CMD ["python", "-m", "note_service.main"]
