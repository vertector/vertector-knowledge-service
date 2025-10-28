"""
Profile Service HTTP Client

Provides HTTP client for fetching profile data from the Profile Service REST API.
This serves as a fallback mechanism when profile data is not available via NATS events.
"""

import logging
from typing import Optional, List, Dict, Any
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)


class ProfileServiceClient:
    """
    HTTP client for Profile Service REST API.

    Provides methods to fetch student profiles and enrollments
    from the Profile Service as a fallback mechanism.
    """

    def __init__(self, base_url: str = "http://localhost:8001/api/v1", timeout: float = 10.0):
        """
        Initialize Profile Service client.

        Args:
            base_url: Base URL of the Profile Service API
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def get_profile(self, student_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a student profile by ID.

        Args:
            student_id: Student identifier

        Returns:
            Profile data if found, None otherwise
        """
        try:
            url = f"{self.base_url}/profiles/{student_id}"
            logger.info(f"Fetching profile for student {student_id} from {url}")

            response = await self.client.get(url)

            if response.status_code == 404:
                logger.warning(f"Profile {student_id} not found")
                return None

            response.raise_for_status()

            profile_data = response.json()
            logger.info(f"Successfully fetched profile for student {student_id}")

            return profile_data

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching profile {student_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching profile {student_id}: {e}")
            return None

    async def get_enrollments(self, student_id: str) -> List[Dict[str, Any]]:
        """
        Fetch all enrollments for a student.

        Args:
            student_id: Student identifier

        Returns:
            List of enrollment data
        """
        try:
            url = f"{self.base_url}/profiles/{student_id}/enrollments"
            logger.info(f"Fetching enrollments for student {student_id}")

            response = await self.client.get(url)

            if response.status_code == 404:
                logger.warning(f"Student {student_id} not found")
                return []

            response.raise_for_status()

            enrollments = response.json()
            logger.info(f"Successfully fetched {len(enrollments)} enrollments for student {student_id}")

            return enrollments

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching enrollments for {student_id}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching enrollments for {student_id}: {e}")
            return []

    async def get_profile_with_enrollments(self, student_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a student profile with all enrollments.

        Args:
            student_id: Student identifier

        Returns:
            Profile data with enrollments if found, None otherwise
        """
        try:
            url = f"{self.base_url}/profiles/{student_id}/full"
            logger.info(f"Fetching full profile for student {student_id}")

            response = await self.client.get(url)

            if response.status_code == 404:
                logger.warning(f"Profile {student_id} not found")
                return None

            response.raise_for_status()

            full_profile = response.json()
            logger.info(f"Successfully fetched full profile for student {student_id}")

            return full_profile

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching full profile {student_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching full profile {student_id}: {e}")
            return None

    async def list_profiles(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List all profiles with pagination.

        Args:
            limit: Maximum number of profiles to return
            offset: Number of profiles to skip

        Returns:
            List of profile data
        """
        try:
            url = f"{self.base_url}/profiles/"
            params = {"limit": limit, "offset": offset}
            logger.info(f"Listing profiles (limit={limit}, offset={offset})")

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            profiles = response.json()
            logger.info(f"Successfully fetched {len(profiles)} profiles")

            return profiles

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error listing profiles: {e}")
            return []
        except Exception as e:
            logger.error(f"Error listing profiles: {e}")
            return []

    async def health_check(self) -> bool:
        """
        Check if Profile Service is healthy.

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            # Use the root health endpoint
            url = f"{self.base_url.rsplit('/api', 1)[0]}/health"
            response = await self.client.get(url)

            if response.status_code == 200:
                health_data = response.json()
                logger.info(f"Profile Service health: {health_data}")
                return health_data.get('status') == 'healthy'

            return False

        except Exception as e:
            logger.error(f"Error checking Profile Service health: {e}")
            return False
