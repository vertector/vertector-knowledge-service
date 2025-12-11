"""
============================================================================
Tag Generation Service for LectureNotes
============================================================================
Automatically generates topic tags for LectureNotes using LLM.
Merges LLM-generated tags with any manually provided tags.
Uses Google Gemini 2.5 Flash Lite for fast, efficient tag generation.
============================================================================
"""

import logging
import os
import re
from typing import List, Optional

from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger(__name__)


class TagGenerationService:
    """
    Service for automatically generating topic tags for LectureNotes using LLM.

    Features:
    - LLM-powered tag extraction from lecture content using Gemini 2.5 Flash Lite
    - API-based inference with generous rate limits
    - Merges auto-generated tags with manual tags
    - Normalizes tags to consistent format (lowercase, hyphenated)
    - Graceful fallback if API is unavailable
    """

    def __init__(self, google_api_key: Optional[str] = None, max_tags: int = 8):
        """
        Initialize tag generation service with Gemini 2.5 Flash Lite.

        Args:
            google_api_key: Google API key for Gemini (defaults to env var)
            max_tags: Maximum number of tags to generate
        """
        self.max_tags = max_tags
        self.llm = None

        # Get API key from parameter or environment
        api_key = google_api_key or os.getenv("GOOGLE_API_KEY")

        if not api_key:
            logger.warning("GOOGLE_API_KEY not provided. Tag generation will be disabled.")
            return

        try:
            logger.info("Initializing Gemini 2.5 Flash Lite for tag generation...")

            # Initialize Gemini 2.5 Flash Lite model
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash-lite",
                google_api_key=api_key,
                temperature=0.3,
                max_output_tokens=150,
            )

            logger.info("✅ TagGenerationService initialized with Gemini 2.5 Flash Lite")
        except Exception as e:
            logger.warning(f"Failed to initialize LLM: {e}. Tag generation will be disabled.")
            self.llm = None

    def normalize_tag(self, tag: str) -> str:
        """
        Normalize a tag to lowercase, hyphenated format.

        Examples:
            "Machine Learning" -> "machine-learning"
            "Python Programming" -> "python-programming"
            "data_structures" -> "data-structures"
        """
        # Remove leading numbers, bullets, or special characters
        tag = re.sub(r'^[\d\.\-\*\#\s]+', '', tag)

        # Convert to lowercase
        tag = tag.lower().strip()

        # Replace spaces and underscores with hyphens
        tag = re.sub(r'[\s_]+', '-', tag)

        # Remove any non-alphanumeric characters except hyphens
        tag = re.sub(r'[^a-z0-9\-]', '', tag)

        # Remove multiple consecutive hyphens
        tag = re.sub(r'-+', '-', tag)

        # Remove leading/trailing hyphens
        tag = tag.strip('-')

        return tag

    def generate_tags_from_text(
        self,
        title: str,
        content: Optional[str] = None,
        summary: Optional[str] = None,
        key_concepts: Optional[str] = None
    ) -> List[str]:
        """
        Generate topic tags from lecture note text using LLM.

        Args:
            title: Lecture note title (required)
            content: Full lecture content (optional)
            summary: Lecture summary (optional, preferred)
            key_concepts: Key concepts string (optional, preferred)

        Returns:
            List of normalized topic tags (lowercase, hyphenated)
        """
        if not self.llm:
            logger.warning("LLM not available, cannot generate tags")
            return []

        # Build text for analysis (prioritize summary and key_concepts)
        text_parts = [f"Title: {title}"]

        if summary:
            text_parts.append(f"Summary: {summary}")

        if key_concepts:
            text_parts.append(f"Key Concepts: {key_concepts}")

        # Only include content if summary and key_concepts aren't available
        if content and not (summary or key_concepts):
            # Truncate content to avoid token limits
            truncated_content = content[:1000] if len(content) > 1000 else content
            text_parts.append(f"Content: {truncated_content}")

        text_for_analysis = "\n\n".join(text_parts)

        # Construct prompt for tag extraction
        prompt = f"""Analyze this lecture note and extract {self.max_tags} concise topic tags.

Requirements:
- Tags should be 1-3 words each
- Use lowercase, hyphenated format (e.g., "machine-learning", "data-structures")
- Focus on core concepts, technologies, and subject areas
- Avoid generic tags like "introduction" or "basics"
- Return ONLY the tags, one per line, no numbering or bullets

Lecture Note:
{text_for_analysis}

Topic Tags:
"""

        try:
            # Generate tags using Gemini
            response = self.llm.invoke(prompt)
            response_text = response.content

            # Parse tags from response
            raw_tags = [line.strip() for line in response_text.split('\n') if line.strip()]

            # Normalize and deduplicate
            normalized_tags = []
            seen = set()

            for tag in raw_tags[:self.max_tags]:
                # Skip overly long tags or tags with periods (likely sentences)
                if len(tag) > 50 or '.' in tag:
                    continue

                normalized = self.normalize_tag(tag)

                # Only add valid, non-duplicate tags
                if normalized and normalized not in seen and len(normalized) > 2:
                    normalized_tags.append(normalized)
                    seen.add(normalized)

            logger.info(f"Generated {len(normalized_tags)} tags: {normalized_tags}")
            return normalized_tags

        except Exception as e:
            logger.error(f"Error generating tags with Gemini: {e}")
            return []

    def generate_and_merge_tags(
        self,
        manual_tags: Optional[List[str]] = None,
        title: Optional[str] = None,
        content: Optional[str] = None,
        summary: Optional[str] = None,
        key_concepts: Optional[str] = None
    ) -> List[str]:
        """
        Generate tags from text and merge with manual tags.

        Manual tags have priority and appear first in the result.

        Args:
            manual_tags: User-provided tags (optional)
            title: Lecture note title (required for generation)
            content: Full lecture content (optional)
            summary: Lecture summary (optional)
            key_concepts: Key concepts string (optional)

        Returns:
            List of normalized, deduplicated tags (manual + generated)
        """
        all_tags = []
        seen = set()

        # 1. Add and normalize manual tags first (they have priority)
        if manual_tags:
            for tag in manual_tags:
                normalized = self.normalize_tag(tag)
                if normalized and normalized not in seen:
                    all_tags.append(normalized)
                    seen.add(normalized)
            logger.info(f"Added {len(manual_tags)} manual tags: {all_tags}")

        # 2. Generate tags from text if model is available and title provided
        if title and self.llm:
            generated_tags = self.generate_tags_from_text(
                title=title,
                content=content,
                summary=summary,
                key_concepts=key_concepts
            )

            # Merge generated tags (avoid duplicates)
            for tag in generated_tags:
                if tag not in seen:
                    all_tags.append(tag)
                    seen.add(tag)

            logger.info(f"Total tags after LLM generation: {len(all_tags)}")
        elif not title:
            logger.warning("No title provided, skipping LLM tag generation")

        # Limit to max_tags
        final_tags = all_tags[:self.max_tags]

        logger.info(f"Final merged tags ({len(final_tags)}): {final_tags}")
        return final_tags

    def generate_summary(
        self,
        title: str,
        content: str,
        max_sentences: int = 3
    ) -> str:
        """
        Generate a concise summary of lecture note content using LLM.

        Args:
            title: Lecture note title
            content: Full lecture content
            max_sentences: Maximum number of sentences in summary

        Returns:
            Generated summary (empty string if LLM unavailable)
        """
        if not self.llm:
            logger.warning("LLM not available, cannot generate summary")
            return ""

        if not content or not title:
            logger.warning("Missing title or content, cannot generate summary")
            return ""

        # Truncate content to avoid token limits (keep first 2000 chars)
        truncated_content = content[:2000] if len(content) > 2000 else content

        prompt = f"""Generate a {max_sentences}-sentence summary of this lecture note.

Requirements:
- Write ONLY the summary, no preamble or labels
- Use clear, concise academic language
- Capture the main concepts and learning objectives
- Maximum {max_sentences} sentences

Title: {title}

Content:
{truncated_content}

Summary:
"""

        try:
            response = self.llm.invoke(prompt)
            summary = response.content.strip()

            # Remove any "Summary:" prefix if the LLM added it
            summary = re.sub(r'^(Summary|Overview):\s*', '', summary, flags=re.IGNORECASE)

            logger.info(f"Generated summary ({len(summary)} chars): {summary[:100]}...")
            return summary

        except Exception as e:
            logger.error(f"Error generating summary with Gemini: {e}")
            return ""
