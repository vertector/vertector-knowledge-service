"""
============================================================================
ID Generator Service
============================================================================
Generates unique IDs for entities created within the Note Service
============================================================================
"""

import uuid
from datetime import datetime


class IDGenerator:
    """
    Generates unique IDs for entities created within the Note Service.

    ID Format Patterns:
    - LectureNote: NOTE-{YYYYMMDDHHMMSS}-{short_uuid}
      Example: NOTE-20251114152030-a1b2c3
    """

    @staticmethod
    def generate_lecture_note_id(student_id: str | None = None) -> str:
        """
        Generate unique LectureNote ID.

        Format: NOTE-{YYYYMMDDHHMMSS}-{short_uuid}
        Example: NOTE-20251114152030-a1b2c3

        Args:
            student_id: Optional student ID for additional context

        Returns:
            Generated lecture_note_id
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        short_uuid = str(uuid.uuid4())[:6]  # First 6 chars of UUID

        return f"NOTE-{timestamp}-{short_uuid}"

    @staticmethod
    def generate_resource_id(title: str | None = None) -> str:
        """
        Generate unique Resource ID.

        Format: RES-{YYYYMMDDHHMMSS}-{short_uuid}
        Example: RES-20251114152030-x7y8z9

        Args:
            title: Optional resource title for context

        Returns:
            Generated resource_id
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        short_uuid = str(uuid.uuid4())[:6]

        return f"RES-{timestamp}-{short_uuid}"
