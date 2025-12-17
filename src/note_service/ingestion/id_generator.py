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
    - Course: {CODE}{NUMBER}-{TERM}
      Example: CS301-Fall2025
    """

    @staticmethod
    def get_current_term() -> str:
        """
        Get the current academic term based on current date.

        Copied from ASMS course_agent/schema.py validate_term_year()

        Term format: "Season YYYY" (e.g., "Fall 2025")

        Academic terms:
        - Fall: Aug-Nov (months 8-11)
        - December: Treated as Fall (most institutions)
        - Spring: Jan-May (months 1-5)
        - Summer: Jun-Jul (months 6-7)
        - Winter: Detected in validation but December defaults to Fall

        Returns:
            Term string (e.g., "Fall 2025", "Spring 2025", "Summer 2025")
        """
        now = datetime.now()
        current_year = now.year
        current_month = now.month

        # Determine current term based on date
        # Fall: Aug-Dec, Spring: Jan-May, Summer: Jun-Jul, Winter: Dec-Jan
        if current_month in [8, 9, 10, 11]:  # Aug-Nov
            required_season = 'Fall'
            required_year = current_year
        elif current_month == 12:  # December - could be Fall or Winter
            required_season = 'Fall'  # Most institutions treat Dec as Fall
            required_year = current_year
        elif current_month in [1, 2, 3, 4, 5]:  # Jan-May
            required_season = 'Spring'
            required_year = current_year
        elif current_month in [6, 7]:  # Jun-Jul
            required_season = 'Summer'
            required_year = current_year
        else:
            required_season = 'Fall'
            required_year = current_year

        expected_term = f"{required_season} {required_year}"
        return expected_term

    @staticmethod
    def generate_course_id(course_code: str, term: str | None = None) -> str:
        """
        Generate course_id from course code and term.

        Pattern: {COURSE_CODE}-{TERM_NO_SPACES}
        Example: CS301-Fall2025

        Args:
            course_code: Course code including department and number (e.g., "CS301", "BUS202")
            term: Academic term (e.g., "Fall 2025"). If None, uses current term.

        Returns:
            Generated course_id (e.g., "CS301-Fall2025")

        Raises:
            ValueError: If course_code format is invalid
        """
        import re

        # Validate course code format (e.g., "CS301", "BUS202")
        if not re.match(r'^[A-Z]+\d+$', course_code):
            raise ValueError(
                f"Invalid course_code format: '{course_code}'. "
                f"Expected format: Department letters + course number (e.g., 'CS301', 'BUS202')"
            )

        if term is None:
            term = IDGenerator.get_current_term()

        # Remove spaces from term (e.g., "Fall 2025" -> "Fall2025")
        term_clean = term.replace(" ", "")

        return f"{course_code}-{term_clean}"

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
