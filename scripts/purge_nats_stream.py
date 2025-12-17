import asyncio
import os
import argparse
from dotenv import load_dotenv
from nats.aio.client import Client as NATS
import json

# Load environment variables from .env file
load_dotenv()

# NATS Configuration from environment variables
NATS_SERVERS = os.getenv("NATS_SERVERS", '["nats://localhost:4222"]').replace("'", '"')
NATS_STREAM_NAME = os.getenv("NATS_STREAM_NAME", "ACADEMIC_EVENTS")


async def purge_stream():
    """Connects to NATS and purges a specific stream."""
    nc = NATS()

    try:
        servers = json.loads(NATS_SERVERS)

        await nc.connect(servers=servers)
        print(f"Connected to NATS at {nc.connected_url.netloc}...")

        js = nc.jetstream()
        print(f"Purging stream '{NATS_STREAM_NAME}'...")
        await js.purge_stream(name=NATS_STREAM_NAME)
        print(f"Stream '{NATS_STREAM_NAME}' has been purged.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        await nc.close()
        print("NATS connection closed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Purge a NATS JetStream stream.")
    parser.add_argument("-y", "--yes", action="store_true", help="Bypass confirmation prompt.")
    args = parser.parse_args()

    if args.yes:
        asyncio.run(purge_stream())
    else:
        print("This script will permanently delete all messages from the NATS stream.")
        print(f"Stream to be purged: {NATS_STREAM_NAME}")
        
        confirm = input("Are you sure you want to continue? (y/n): ")
        if confirm.lower() == 'y':
            asyncio.run(purge_stream())
        else:
            print("Operation cancelled.")

