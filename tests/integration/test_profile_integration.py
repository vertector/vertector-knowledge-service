"""
Test Profile Service Integration with GraphRAG

This script tests the complete flow:
1. Create profiles via Profile Service REST API
2. Verify profiles are created in Profile Service Neo4j
3. Check that profile events are published to NATS
4. Verify GraphRAG Note Service consumes events
5. Check that Profile nodes are created in GraphRAG Neo4j
6. Test relationships (Assignment → Profile, etc.)
7. Test enrollments

Usage:
    python test_profile_integration.py
"""

import asyncio
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List
import httpx

# Add vertector-nats to path
sys.path.insert(0, '/Users/en_tetteh/Documents/vertector-nats-jetstream/src')

from vertector_nats import (
    NATSClient,
    NATSConfig,
    EventPublisher,
    ProfileCreatedEvent,
    ProfileUpdatedEvent,
    ProfileEnrolledEvent,
    AssignmentCreatedEvent,
    EventMetadata,
)


class ProfileIntegrationTester:
    """Tests Profile Service integration with GraphRAG."""

    def __init__(self):
        self.profile_service_url = "http://localhost:8001/api/v1"
        self.graphrag_neo4j_uri = "bolt://localhost:7687"
        self.graphrag_neo4j_user = "neo4j"
        self.graphrag_neo4j_password = "graphrag_secure_password_2025"

        self.nats_config = NATSConfig(
            servers=["nats://localhost:4222"],
            client_name="profile-integration-tester"
        )
        self.nats_client = None
        self.publisher = None

        self.test_student_id = f"S{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.test_course_id = "CS101"

    async def setup(self):
        """Setup NATS connection."""
        print("🔧 Setting up NATS connection...")
        self.nats_client = NATSClient(self.nats_config)
        await self.nats_client.connect()
        self.publisher = EventPublisher(self.nats_client)
        print("✅ NATS connection established\n")

    async def cleanup(self):
        """Cleanup connections."""
        if self.nats_client:
            await self.nats_client.close()
        print("\n🧹 Cleanup complete")

    async def test_profile_service_health(self) -> bool:
        """Test Profile Service health check."""
        print("=" * 80)
        print("TEST 1: Profile Service Health Check")
        print("=" * 80)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get("http://localhost:8001/health")
                health_data = response.json()

                print(f"Status: {health_data.get('status')}")
                print(f"Neo4j: {health_data.get('neo4j')}")
                print(f"NATS: {health_data.get('nats')}")

                if health_data.get('status') == 'healthy':
                    print("✅ Profile Service is healthy\n")
                    return True
                else:
                    print("❌ Profile Service is unhealthy\n")
                    return False

        except Exception as e:
            print(f"❌ Error checking Profile Service health: {e}\n")
            return False

    async def test_create_profile_via_api(self) -> bool:
        """Test creating a profile via REST API."""
        print("=" * 80)
        print("TEST 2: Create Profile via REST API")
        print("=" * 80)

        profile_data = {
            "student_id": self.test_student_id,
            "email": f"{self.test_student_id.lower()}@university.edu",
            "first_name": "John",
            "last_name": "Doe",
            "major": "Computer Science",
            "minor": "Mathematics",
            "year": 2,
            "student_type": "Undergraduate",
            "enrollment_status": "Active",
            "matriculation_date": datetime.utcnow().isoformat(),
            "expected_graduation": (datetime.utcnow() + timedelta(days=730)).isoformat(),
            "cumulative_gpa": 3.75,
            "phone": "+1-555-0123",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                print(f"Creating profile for {self.test_student_id}...")
                response = await client.post(
                    f"{self.profile_service_url}/profiles/",
                    json=profile_data
                )
                response.raise_for_status()

                created_profile = response.json()
                print(f"✅ Profile created successfully")
                print(f"   Student ID: {created_profile['student_id']}")
                print(f"   Name: {created_profile['first_name']} {created_profile['last_name']}")
                print(f"   Email: {created_profile['email']}")
                print(f"   Major: {created_profile['major']}")
                print(f"   GPA: {created_profile['cumulative_gpa']}\n")

                return True

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400 and "already exists" in e.response.text:
                print(f"⚠️  Profile already exists, continuing with tests...\n")
                return True
            print(f"❌ HTTP Error creating profile: {e}\n")
            print(f"   Response: {e.response.text}")
            return False
        except Exception as e:
            print(f"❌ Error creating profile: {e}\n")
            return False

    async def test_create_course_enrollment(self) -> bool:
        """Test creating a course enrollment."""
        print("=" * 80)
        print("TEST 3: Create Course Enrollment")
        print("=" * 80)

        enrollment_data = {
            "student_id": self.test_student_id,
            "course_id": self.test_course_id,
            "enrollment_date": datetime.utcnow().isoformat(),
            "grading_basis": "Letter",
            "enrollment_status": "Active",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                print(f"Enrolling {self.test_student_id} in {self.test_course_id}...")
                response = await client.post(
                    f"{self.profile_service_url}/profiles/{self.test_student_id}/enrollments",
                    json=enrollment_data
                )
                response.raise_for_status()

                enrollment = response.json()
                print(f"✅ Enrollment created successfully")
                print(f"   Student: {enrollment['student_id']}")
                print(f"   Course: {enrollment['course_id']}")
                print(f"   Status: {enrollment['enrollment_status']}\n")

                return True

        except Exception as e:
            print(f"❌ Error creating enrollment: {e}\n")
            return False

    async def test_publish_assignment_with_student(self) -> bool:
        """Test publishing an assignment with student_id."""
        print("=" * 80)
        print("TEST 4: Publish Assignment with student_id")
        print("=" * 80)

        assignment_event = AssignmentCreatedEvent(
            assignment_id=f"A{datetime.now().strftime('%Y%m%d%H%M%S')}",
            title="Test Assignment with Student",
            course_id=self.test_course_id,
            student_id=self.test_student_id,  # Link to profile
            type="Homework",
            description="This assignment is assigned to a specific student",
            due_date=datetime.utcnow() + timedelta(days=7),
            points_possible=100.0,
            weight=0.25,  # Required field
            submission_types=["online_text_entry"],
            metadata=EventMetadata(
                source_service="profile-integration-test",
                correlation_id="test-assignment-001",
            )
        )

        try:
            print(f"Publishing assignment for student {self.test_student_id}...")
            await self.publisher.publish(assignment_event)
            print(f"✅ Assignment event published")
            print(f"   Assignment ID: {assignment_event.assignment_id}")
            print(f"   Student ID: {assignment_event.student_id}")
            print(f"   Course ID: {assignment_event.course_id}\n")

            # Wait for processing
            print("⏳ Waiting 3 seconds for event processing...")
            await asyncio.sleep(3)

            return True

        except Exception as e:
            print(f"❌ Error publishing assignment: {e}\n")
            return False

    async def test_verify_profile_in_graphrag(self) -> bool:
        """Verify Profile node exists in GraphRAG Neo4j."""
        print("=" * 80)
        print("TEST 5: Verify Profile in GraphRAG Neo4j")
        print("=" * 80)

        try:
            from neo4j import GraphDatabase

            driver = GraphDatabase.driver(
                self.graphrag_neo4j_uri,
                auth=(self.graphrag_neo4j_user, self.graphrag_neo4j_password)
            )

            with driver.session(database="neo4j") as session:
                # Check if Profile node exists
                query = """
                MATCH (p:Profile {student_id: $student_id})
                RETURN p
                """

                result = session.run(query, student_id=self.test_student_id)
                record = result.single()

                if record:
                    profile = dict(record['p'])
                    print(f"✅ Profile found in GraphRAG Neo4j")
                    print(f"   Student ID: {profile.get('student_id')}")
                    print(f"   Email: {profile.get('email')}")
                    print(f"   Name: {profile.get('first_name')} {profile.get('last_name')}")
                    print(f"   Major: {profile.get('major')}")

                    driver.close()
                    print()
                    return True
                else:
                    print(f"❌ Profile not found in GraphRAG Neo4j")
                    print(f"   Expected student_id: {self.test_student_id}\n")
                    driver.close()
                    return False

        except Exception as e:
            print(f"❌ Error checking GraphRAG Neo4j: {e}\n")
            return False

    async def test_verify_assignment_profile_relationship(self) -> bool:
        """Verify Assignment → Profile relationship exists."""
        print("=" * 80)
        print("TEST 6: Verify Assignment → Profile Relationship")
        print("=" * 80)

        try:
            from neo4j import GraphDatabase

            driver = GraphDatabase.driver(
                self.graphrag_neo4j_uri,
                auth=(self.graphrag_neo4j_user, self.graphrag_neo4j_password)
            )

            with driver.session(database="neo4j") as session:
                # Check for ASSIGNED_TO relationship
                query = """
                MATCH (a:Assignment)-[r:ASSIGNED_TO]->(p:Profile {student_id: $student_id})
                RETURN a, r, p
                LIMIT 1
                """

                result = session.run(query, student_id=self.test_student_id)
                record = result.single()

                if record:
                    assignment = dict(record['a'])
                    profile = dict(record['p'])
                    print(f"✅ Assignment → Profile relationship found")
                    print(f"   Assignment: {assignment.get('title')}")
                    print(f"   Assigned to: {profile.get('first_name')} {profile.get('last_name')}")
                    print(f"   Student ID: {profile.get('student_id')}")

                    driver.close()
                    print()
                    return True
                else:
                    print(f"❌ Assignment → Profile relationship not found")
                    print(f"   This may be normal if assignment was created before profile\n")
                    driver.close()
                    return False

        except Exception as e:
            print(f"❌ Error checking relationship: {e}\n")
            return False

    async def test_profile_client_fallback(self) -> bool:
        """Test ProfileServiceClient (API fallback)."""
        print("=" * 80)
        print("TEST 7: Test Profile Client (API Fallback)")
        print("=" * 80)

        try:
            sys.path.insert(0, '/Users/en_tetteh/Documents/graphrag/src')
            from note_service.nats_integration import ProfileServiceClient

            client = ProfileServiceClient(base_url=self.profile_service_url)

            print(f"Fetching profile via ProfileServiceClient...")
            profile = await client.get_profile(self.test_student_id)

            if profile:
                print(f"✅ Profile fetched via client")
                print(f"   Student ID: {profile['student_id']}")
                print(f"   Name: {profile['first_name']} {profile['last_name']}")
                print(f"   Email: {profile['email']}")

                # Test get enrollments
                print(f"\nFetching enrollments...")
                enrollments = await client.get_enrollments(self.test_student_id)
                print(f"✅ Found {len(enrollments)} enrollment(s)")
                for enr in enrollments:
                    print(f"   - {enr['course_id']}: {enr['enrollment_status']}")

                await client.close()
                print()
                return True
            else:
                print(f"❌ Profile not found via client\n")
                await client.close()
                return False

        except Exception as e:
            print(f"❌ Error testing ProfileServiceClient: {e}\n")
            return False

    async def run_all_tests(self):
        """Run all integration tests."""
        print("\n" + "=" * 80)
        print("PROFILE SERVICE INTEGRATION TEST SUITE")
        print("=" * 80 + "\n")

        results = {}

        # Test 1: Health Check
        results['health'] = await self.test_profile_service_health()

        if not results['health']:
            print("❌ Profile Service is not healthy. Cannot continue tests.")
            return results

        # Test 2: Create Profile via API
        results['create_profile'] = await self.test_create_profile_via_api()

        # Give time for NATS event to be published and consumed
        print("⏳ Waiting 5 seconds for profile event to propagate to GraphRAG...")
        await asyncio.sleep(5)

        # Test 3: Create Enrollment
        results['create_enrollment'] = await self.test_create_course_enrollment()

        # Wait for enrollment event
        print("⏳ Waiting 3 seconds for enrollment event processing...")
        await asyncio.sleep(3)

        # Test 4: Publish Assignment with student_id
        results['publish_assignment'] = await self.test_publish_assignment_with_student()

        # Test 5: Verify Profile in GraphRAG
        results['verify_profile'] = await self.test_verify_profile_in_graphrag()

        # Test 6: Verify Assignment → Profile relationship
        results['verify_relationship'] = await self.test_verify_assignment_profile_relationship()

        # Test 7: Test Profile Client
        results['client_fallback'] = await self.test_profile_client_fallback()

        return results

    def print_summary(self, results: Dict[str, bool]):
        """Print test summary."""
        print("=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)

        total = len(results)
        passed = sum(1 for v in results.values() if v)
        failed = total - passed

        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {test_name}")

        print("\n" + "=" * 80)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        print("=" * 80 + "\n")


async def main():
    """Main test runner."""
    tester = ProfileIntegrationTester()

    try:
        await tester.setup()
        results = await tester.run_all_tests()
        tester.print_summary(results)

    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
