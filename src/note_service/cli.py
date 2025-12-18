"""
============================================================================
Note Service CLI
============================================================================
Command-line interface for LectureNote CRUD operations and search.

Usage:
    note-cli create --student-id STU001 --title "My Note" --content "..."
    note-cli get <note-id>
    note-cli update <note-id> --title "Updated Title"
    note-cli delete <note-id>
    note-cli list --student-id STU001
    note-cli search --query "graph algorithms" --student-id STU001
============================================================================
"""

import asyncio
import json
import os
import sys
from typing import Optional

import click

from note_service.config import Settings
from note_service.db.connection import Neo4jConnection
from note_service.crud.note_service import LectureNoteService
from note_service.retrieval.embedder import EmbeddingService
from note_service.retrieval.service import RetrievalService
from note_service.ingestion.lexical_graph_manager import (
    LexicalGraphManager,
    LectureNoteLexicalGraphConfig
)


# Global context for sharing services
class CLIContext:
    def __init__(self):
        self.settings = Settings()
        self.connection = Neo4jConnection(self.settings)
        self.embedding_service = EmbeddingService(
            model_name=self.settings.embedding.model_name,
            device=self.settings.embedding.device,
            cache_folder=self.settings.embedding.cache_folder,
            normalize_embeddings=self.settings.embedding.normalize_embeddings,
            batch_size=self.settings.embedding.batch_size,
        )

        lexical_config = LectureNoteLexicalGraphConfig(
            chunk_size=500,
            chunk_overlap=100,
        )
        self.lexical_graph_manager = LexicalGraphManager(
            driver=self.connection.driver,
            embedding_service=self.embedding_service,
            config=lexical_config
        )

        self.note_service = LectureNoteService(
            driver=self.connection.driver,
            embedding_service=self.embedding_service,
            lexical_graph_manager=self.lexical_graph_manager,
        )

        self.retrieval_service = RetrievalService(
            driver=self.connection.driver,
            settings=self.settings,
            google_api_key=os.getenv('GOOGLE_API_KEY')
        )

    def close(self):
        self.connection.close()


@click.group()
@click.pass_context
def cli(ctx):
    """Note Service CLI - Manage lecture notes with CRUD and search operations."""
    ctx.obj = CLIContext()


@cli.command()
@click.option('--student-id', required=True, help='Student ID who owns the note')
@click.option('--title', required=True, help='Note title')
@click.option('--content', required=True, help='Note content (use @file.txt to read from file)')
@click.option('--course-code', help='Course code (e.g., CS301)')
@click.option('--summary', help='Custom summary (auto-generated if not provided)')
@click.option('--key-concepts', multiple=True, help='Key concepts (can be specified multiple times)')
@click.option('--tags', multiple=True, help='Manual tags (can be specified multiple times, merged with LLM-generated)')
@click.option('--note-id', help='Custom note ID (auto-generated if not provided)')
@click.option('--json-output', is_flag=True, help='Output as JSON')
@click.pass_context
def create(ctx, student_id, title, content, course_code, summary, key_concepts, tags, note_id, json_output):
    """Create a new lecture note."""
    try:
        # Handle file input for content
        if content.startswith('@'):
            file_path = content[1:]
            with open(file_path, 'r') as f:
                content = f.read()

        # Look up course_id from course_code if provided
        course_id = None
        if course_code:
            course_id = ctx.obj.note_service._get_course_id_from_code(course_code, student_id=student_id)
            if not course_id:
                click.echo(f"Warning: Course with code '{course_code}' not found for student {student_id}. Note will be created without course link.", err=True)

        # Create note
        result = asyncio.run(ctx.obj.note_service.create_note(
            student_id=student_id,
            title=title,
            content=content,
            course_id=course_id,
            summary=summary,
            key_concepts=list(key_concepts) if key_concepts else None,
            tagged_topics=list(tags) if tags else None,
            lecture_note_id=note_id,
        ))

        if json_output:
            # Remove embedding vector from output (too large)
            result_copy = result.copy()
            result_copy.pop('embedding_vector', None)
            click.echo(json.dumps(result_copy, indent=2, default=str))
        else:
            click.echo(f"\n✓ Created LectureNote: {result['lecture_note_id']}")
            click.echo(f"  Title: {result['title']}")
            click.echo(f"  Student: {result['student_id']}")
            if result.get('course_title'):
                click.echo(f"  Course: {result['course_title']}")
            click.echo(f"  Tags: {', '.join(result.get('tagged_topics', []))}")
            click.echo(f"  Chunks: {result.get('chunk_count', 0)}")
            click.echo(f"  Summary: {result.get('summary', 'N/A')[:100]}...")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        ctx.obj.close()


@cli.command()
@click.option('--student-id', required=True, help='Student ID who owns the note')
@click.option('--title', help='Search query for note title (uses semantic search)')
@click.option('--course-code', help='Course code (e.g., CS301)')
@click.option('--note-id', help='Exact note ID (if known)')
@click.option('--json-output', is_flag=True, help='Output as JSON')
@click.pass_context
def get(ctx, student_id, title, course_code, note_id, json_output):
    """Get a lecture note by semantic search, course, or ID."""
    try:
        # If note_id provided, use it directly
        if note_id:
            result = ctx.obj.note_service.get_note(note_id)
        else:
            # Find by title using semantic search
            if not title and not course_code:
                click.echo("Error: Provide --title, --course-code, or --note-id", err=True)
                sys.exit(1)

            # Use retrieval service for semantic search
            search_results = ctx.obj.retrieval_service.search(
                query_text=title if title else f"course {course_code}",
                student_id=student_id,
                top_k=10,  # Get top 10 to filter by course if needed
                granularity='document',
                search_type='hybrid',
            )

            if search_results.num_results == 0:
                filters = []
                if title:
                    filters.append(f"query '{title}'")
                if course_code:
                    filters.append(f"course {course_code}")
                click.echo(f"Note not found with {' and '.join(filters)}", err=True)
                sys.exit(1)

            # Filter by course code if provided
            matching_notes = []
            for item in search_results.results:
                note_data = item.get('node', item)

                # If course_code filter provided, check if note belongs to that course
                if course_code:
                    # Get full note details to check course
                    full_note = ctx.obj.note_service.get_note(note_data['lecture_note_id'])
                    if full_note.get('course_id'):
                        # Parse course_id to get course code (e.g., "CS301-Fall2025" -> "CS301")
                        import re
                        match = re.match(r'([A-Z]+\d+)', full_note['course_id'])
                        if match and match.group(1) == course_code:
                            matching_notes.append(full_note)
                else:
                    matching_notes.append(note_data)

            if not matching_notes:
                click.echo(f"Note not found with course {course_code}", err=True)
                sys.exit(1)

            if len(matching_notes) > 1:
                titles = [n.get('title', 'N/A') for n in matching_notes]
                click.echo(f"Error: Multiple notes found. Please be more specific.\nMatching notes: {', '.join(titles)}", err=True)
                sys.exit(1)

            result = matching_notes[0]
            # Ensure we have full note data
            if 'lecture_note_id' in result and 'content' not in result:
                result = ctx.obj.note_service.get_note(result['lecture_note_id'])

        if json_output:
            # Remove embedding vector from output (too large)
            result_copy = result.copy()
            result_copy.pop('embedding_vector', None)
            click.echo(json.dumps(result_copy, indent=2, default=str))
        else:
            click.echo(f"\nLectureNote: {result['lecture_note_id']}")
            click.echo(f"  Title: {result['title']}")
            click.echo(f"  Student: {result['student_id']}")
            if result.get('course_title'):
                click.echo(f"  Course: {result['course_title']}")
            click.echo(f"  Tags: {', '.join(result.get('tagged_topics', []))}")
            click.echo(f"  Chunks: {result.get('chunk_count', 0)}")
            click.echo(f"  Created: {result.get('created_at', 'N/A')}")
            click.echo(f"  Updated: {result.get('updated_at', 'N/A')}")
            click.echo(f"\nSummary:\n{result.get('summary', 'N/A')}")
            click.echo(f"\nContent:\n{result.get('content', 'N/A')[:500]}...")

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        ctx.obj.close()


@cli.command()
@click.option('--student-id', required=True, help='Student ID who owns the note')
@click.option('--find-title', help='Search query to find note (uses semantic search)')
@click.option('--find-course', help='Course code to find note (e.g., CS301)')
@click.option('--note-id', help='Exact note ID to update (if known)')
@click.option('--new-title', help='New title')
@click.option('--content', help='New content (use @file.txt to read from file)')
@click.option('--summary', help='New summary (auto-generated if content changes)')
@click.option('--key-concepts', multiple=True, help='New key concepts')
@click.option('--tags', multiple=True, help='New manual tags (merged with LLM-generated)')
@click.option('--course-code', help='New course code (e.g., CS301)')
@click.option('--json-output', is_flag=True, help='Output as JSON')
@click.pass_context
def update(ctx, student_id, find_title, find_course, note_id, new_title, content, summary, key_concepts, tags, course_code, json_output):
    """Update an existing lecture note."""
    try:
        # Find the note first
        if note_id:
            existing_note = ctx.obj.note_service.get_note(note_id)
        else:
            if not find_title and not find_course:
                click.echo("Error: Provide --find-title, --find-course, or --note-id to locate the note", err=True)
                sys.exit(1)

            # Use retrieval service for semantic search
            search_results = ctx.obj.retrieval_service.search(
                query_text=find_title if find_title else f"course {find_course}",
                student_id=student_id,
                top_k=10,
                granularity='document',
                search_type='hybrid',
            )

            if search_results.num_results == 0:
                click.echo(f"Note not found", err=True)
                sys.exit(1)

            # Filter by course code if provided
            matching_notes = []
            for item in search_results.results:
                note_data = item.get('node', item)

                if find_course:
                    full_note = ctx.obj.note_service.get_note(note_data['lecture_note_id'])
                    if full_note.get('course_id'):
                        import re
                        match = re.match(r'([A-Z]+\d+)', full_note['course_id'])
                        if match and match.group(1) == find_course:
                            matching_notes.append(full_note)
                else:
                    matching_notes.append(ctx.obj.note_service.get_note(note_data['lecture_note_id']))

            if not matching_notes:
                click.echo(f"Note not found", err=True)
                sys.exit(1)

            if len(matching_notes) > 1:
                titles = [n.get('title', 'N/A') for n in matching_notes]
                click.echo(f"Error: Multiple notes found. Please be more specific.\nMatching notes: {', '.join(titles)}", err=True)
                sys.exit(1)

            existing_note = matching_notes[0]

        note_id = existing_note['lecture_note_id']
        click.echo(f"Updating note: {existing_note['title']}")

        # Handle file input for content
        if content and content.startswith('@'):
            file_path = content[1:]
            with open(file_path, 'r') as f:
                content = f.read()

        # Look up course_id from course_code if provided
        course_id = None
        if course_code:
            student_id = existing_note.get('student_id')
            course_id = ctx.obj.note_service._get_course_id_from_code(course_code, student_id=student_id)
            if not course_id:
                click.echo(f"Warning: Course with code '{course_code}' not found for student {student_id}. Course link will not be updated.", err=True)

        # Update note
        result = asyncio.run(ctx.obj.note_service.update_note(
            lecture_note_id=note_id,
            title=new_title,
            content=content,
            summary=summary,
            key_concepts=list(key_concepts) if key_concepts else None,
            tagged_topics=list(tags) if tags else None,
            course_id=course_id,
        ))

        if json_output:
            # Remove embedding vector from output (too large)
            result_copy = result.copy()
            result_copy.pop('embedding_vector', None)
            click.echo(json.dumps(result_copy, indent=2, default=str))
        else:
            click.echo(f"\n✓ Updated LectureNote: {result['lecture_note_id']}")
            click.echo(f"  Title: {result['title']}")
            click.echo(f"  Tags: {', '.join(result.get('tagged_topics', []))}")
            click.echo(f"  Chunks: {result.get('chunk_count', 0)}")
            click.echo(f"  Updated: {result.get('updated_at', 'N/A')}")

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        ctx.obj.close()


@cli.command()
@click.option('--student-id', required=True, help='Student ID who owns the note')
@click.option('--title', help='Search query for note (uses semantic search)')
@click.option('--course-code', help='Course code (e.g., CS301)')
@click.option('--note-id', help='Exact note ID to delete (if known)')
@click.option('--yes', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def delete(ctx, student_id, title, course_code, note_id, yes):
    """Delete a lecture note and all its chunks."""
    try:
        # Find the note first
        if note_id:
            existing_note = ctx.obj.note_service.get_note(note_id)
        else:
            if not title and not course_code:
                click.echo("Error: Provide --title, --course-code, or --note-id to locate the note", err=True)
                sys.exit(1)

            # Use retrieval service for semantic search
            search_results = ctx.obj.retrieval_service.search(
                query_text=title if title else f"course {course_code}",
                student_id=student_id,
                top_k=10,
                granularity='document',
                search_type='hybrid',
            )

            if search_results.num_results == 0:
                click.echo(f"Note not found", err=True)
                sys.exit(1)

            # Filter by course code if provided
            matching_notes = []
            for item in search_results.results:
                note_data = item.get('node', item)

                if course_code:
                    full_note = ctx.obj.note_service.get_note(note_data['lecture_note_id'])
                    if full_note.get('course_id'):
                        import re
                        match = re.match(r'([A-Z]+\d+)', full_note['course_id'])
                        if match and match.group(1) == course_code:
                            matching_notes.append(full_note)
                else:
                    matching_notes.append(ctx.obj.note_service.get_note(note_data['lecture_note_id']))

            if not matching_notes:
                click.echo(f"Note not found", err=True)
                sys.exit(1)

            if len(matching_notes) > 1:
                titles = [n.get('title', 'N/A') for n in matching_notes]
                click.echo(f"Error: Multiple notes found. Please be more specific.\nMatching notes: {', '.join(titles)}", err=True)
                sys.exit(1)

            existing_note = matching_notes[0]

        note_id = existing_note['lecture_note_id']
        note_title = existing_note['title']

        if not yes:
            click.confirm(f'Are you sure you want to delete "{note_title}" ({note_id})?', abort=True)

        success = asyncio.run(ctx.obj.note_service.delete_note(note_id))

        if success:
            click.echo(f"\n✓ Deleted LectureNote: {note_title}")
        else:
            click.echo(f"Note {note_id} not found", err=True)
            sys.exit(1)

    except click.Abort:
        click.echo("Cancelled")
        sys.exit(0)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        ctx.obj.close()


@cli.command()
@click.option('--student-id', help='Filter by student ID')
@click.option('--course-id', help='Filter by course ID')
@click.option('--tags', multiple=True, help='Filter by tags (notes must have at least one)')
@click.option('--limit', default=10, help='Maximum number of results (default: 10)')
@click.option('--skip', default=0, help='Number of results to skip (default: 0)')
@click.option('--json-output', is_flag=True, help='Output as JSON')
@click.pass_context
def list(ctx, student_id, course_id, tags, limit, skip, json_output):
    """List lecture notes with optional filters."""
    try:
        results = ctx.obj.note_service.list_notes(
            student_id=student_id,
            course_id=course_id,
            tags=list(tags) if tags else None,
            limit=limit,
            skip=skip,
        )

        if json_output:
            # Remove embedding vectors from output (too large)
            results_copy = []
            for result in results:
                r = result.copy()
                r.pop('embedding_vector', None)
                results_copy.append(r)
            click.echo(json.dumps(results_copy, indent=2, default=str))
        else:
            click.echo(f"\nFound {len(results)} note(s):\n")
            for i, note in enumerate(results, 1):
                click.echo(f"{i}. {note['lecture_note_id']}")
                click.echo(f"   Title: {note['title']}")
                click.echo(f"   Student: {note['student_id']}")
                if note.get('course_title'):
                    click.echo(f"   Course: {note['course_title']}")
                click.echo(f"   Tags: {', '.join(note.get('tagged_topics', []))}")
                click.echo(f"   Chunks: {note.get('chunk_count', 0)}")
                click.echo(f"   Updated: {note.get('updated_at', 'N/A')}")
                click.echo()

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        ctx.obj.close()


@cli.command()
@click.option('--query', required=True, help='Search query')
@click.option('--student-id', required=True, help='Student ID for data isolation')
@click.option('--granularity', type=click.Choice(['document', 'chunk']), default='document',
              help='Search granularity (default: document)')
@click.option('--search-type', type=click.Choice(['hybrid', 'vector', 'fulltext']), default='hybrid',
              help='Search type (default: hybrid)')
@click.option('--top-k', default=5, help='Number of results to return (default: 5)')
@click.option('--json-output', is_flag=True, help='Output as JSON')
@click.pass_context
def search(ctx, query, student_id, granularity, search_type, top_k, json_output):
    """Search lecture notes using semantic and keyword search."""
    try:
        result = ctx.obj.retrieval_service.search(
            query_text=query,
            student_id=student_id,
            top_k=top_k,
            granularity=granularity,
            search_type=search_type,
        )

        if json_output:
            click.echo(json.dumps({
                'query': result.query,
                'num_results': result.num_results,
                'results': result.results,
            }, indent=2, default=str))
        else:
            click.echo(f"\nSearch Results for: \"{result.query}\"")
            click.echo(f"Found {result.num_results} result(s)\n")

            for i, item in enumerate(result.results, 1):
                if granularity == 'document':
                    node_data = item.get('node', item)
                    click.echo(f"{i}. {node_data.get('title', 'N/A')}")
                    click.echo(f"   Score: {item.get('score', 0):.3f}")
                    click.echo(f"   ID: {node_data.get('lecture_note_id', 'N/A')}")
                    if node_data.get('tagged_topics'):
                        click.echo(f"   Tags: {', '.join(node_data['tagged_topics'])}")
                    if node_data.get('summary'):
                        click.echo(f"   Summary: {node_data['summary'][:150]}...")
                else:  # chunk
                    click.echo(f"{i}. Chunk from: {item.get('parent_title', 'N/A')}")
                    click.echo(f"   Score: {item.get('score', 0):.3f}")
                    content = item.get('content', '')
                    click.echo(f"   Content: {content[:200]}...")
                click.echo()

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        ctx.obj.close()


if __name__ == '__main__':
    cli()
