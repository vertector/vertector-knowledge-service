#!/usr/bin/env python3
"""
Rebuild relationships for existing nodes in the knowledge graph.

This script connects to Neo4j and creates relationships for all existing
nodes that have foreign key references.
"""
import sys
sys.path.insert(0, 'src')

from note_service.config import Settings
from note_service.db.connection import Neo4jConnection
from note_service.ingestion.data_loader import DataLoader


def main():
    print("=" * 80)
    print("GraphRAG Knowledge Graph - Relationship Rebuild")
    print("=" * 80)
    print()

    # Initialize connection and data loader
    settings = Settings()
    connection = Neo4jConnection(settings=settings)
    data_loader = DataLoader(connection=connection, settings=settings)

    print(f"✓ Connected to Neo4j at {settings.neo4j.uri}")
    print()

    # Rebuild all relationships
    print("Rebuilding relationships...")
    print("-" * 80)

    relationship_counts = data_loader.rebuild_all_relationships()

    print()
    print("=" * 80)
    print("Relationship Rebuild Complete!")
    print("=" * 80)
    print()

    if relationship_counts:
        print("Relationships created:")
        for rel_type, count in sorted(relationship_counts.items()):
            print(f"  • {rel_type}: {count}")
    else:
        print("No relationships were created.")
        print("This could mean:")
        print("  • No nodes exist that have relationship rules")
        print("  • All relationships already exist")
        print("  • Referenced target nodes don't exist yet")

    print()

    # Close connection
    connection.close()
    print("✓ Disconnected from Neo4j")


if __name__ == "__main__":
    main()
