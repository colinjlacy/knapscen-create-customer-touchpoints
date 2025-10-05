#!/usr/bin/env python3
"""
Example script to demonstrate touchpoints creation.

This script shows how to use the create_touchpoints.py script
with environment variables.
"""

import os
import asyncio
from create_touchpoints import TouchpointsCreator


async def run_example():
    """Run an example of creating touchpoints."""
    
    # Set example environment variables (in production, these would come from your environment)
    os.environ['DB_HOST'] = 'localhost'
    os.environ['DB_PORT'] = '33006'
    os.environ['DB_NAME'] = 'bassline-boogie'
    os.environ['DB_USER'] = 'bassline-boogie-user'
    os.environ['DB_PASSWORD'] = '8Qd8*yZK&zIxS%!s'
    os.environ['NATS_SERVER'] = 'nats://localhost:40953'
    os.environ['NATS_SUBJECT'] = 'touchpoints-created'
    os.environ['NATS_USER'] = 'admin'
    os.environ['NATS_PASSWORD'] = 'admin'
    os.environ['CUSTOMER_NAME'] = 'Example Tech Solutions'
    
    print("Creating touchpoints for customer...")
    
    try:
        creator = TouchpointsCreator()
        success = await creator.create_touchpoints_for_customer()
        
        if success:
            print("✅ Touchpoints created successfully!")
        else:
            print("❌ Failed to create touchpoints")
            
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(run_example())
