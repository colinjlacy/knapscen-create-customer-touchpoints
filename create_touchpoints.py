#!/usr/bin/env python3
"""
Customer Touchpoints Creation Script

This script creates a new touchpoints record for a corporate customer and publishes
an event to NATS for downstream processing.

Environment Variables Required:
- DB_HOST: MySQL database host
- DB_PORT: MySQL database port (default: 3306)
- DB_NAME: Database name
- DB_USER: Database username
- DB_PASSWORD: Database password
- NATS_URL: NATS server URL
- NATS_SUBJECT: NATS subject for publishing events (default: touchpoints-created)
- NATS_USER: NATS username for authentication
- NATS_PASSWORD: NATS password for authentication
- CUSTOMER_NAME: Name of the corporate customer to create touchpoints for
"""

import os
import sys
import json
import uuid
import logging
from datetime import datetime
from typing import Optional, Dict, Any

import mysql.connector
from mysql.connector import Error
import nats
from nats.errors import ConnectionClosedError, TimeoutError


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TouchpointsCreator:
    """Handles touchpoints creation and NATS event publishing."""
    
    def __init__(self):
        """Initialize with environment variables."""
        self.db_config = {
            'host': os.getenv('DB_HOST'),
            'port': int(os.getenv('DB_PORT', '3306')),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'charset': 'utf8mb4',
            'collation': 'utf8mb4_unicode_ci'
        }
        self.nats_url = os.getenv('NATS_URL')
        self.nats_subject = os.getenv('NATS_SUBJECT', 'touchpoints-created')
        self.nats_user = os.getenv('NATS_USER')
        self.nats_password = os.getenv('NATS_PASSWORD')
        self.customer_name = os.getenv('CUSTOMER_NAME')
        
        # Validate required environment variables
        self._validate_env_vars()
    
    def _validate_env_vars(self) -> None:
        """Validate that all required environment variables are set."""
        required_vars = [
            'DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 
            'NATS_URL', 'NATS_USER', 'NATS_PASSWORD', 'CUSTOMER_NAME'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            sys.exit(1)
    
    def get_customer_id(self, customer_name: str) -> Optional[str]:
        """
        Look up customer ID by name in the corporate_customers table.
        
        Args:
            customer_name: Name of the corporate customer
            
        Returns:
            Customer ID if found, None otherwise
        """
        try:
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor()
            
            query = "SELECT id, name, subscription_tier FROM corporate_customers WHERE name = %s"
            cursor.execute(query, (customer_name,))
            result = cursor.fetchone()
            
            if result:
                customer_id, name, subscription_tier = result
                logger.info(f"Found customer: {name} (ID: {customer_id}, Tier: {subscription_tier})")
                return customer_id
            else:
                logger.error(f"Customer '{customer_name}' not found in database")
                return None
                
        except Error as e:
            logger.error(f"Database error while looking up customer: {e}")
            return None
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()
    
    def create_touchpoints_record(self, customer_id: str) -> Optional[str]:
        """
        Create a new touchpoints record with empty date fields.
        
        Args:
            customer_id: ID of the corporate customer
            
        Returns:
            Touchpoints record ID if successful, None otherwise
        """
        try:
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor()
            
            # Generate UUID for the touchpoints record
            touchpoints_id = str(uuid.uuid4())
            
            # Insert new touchpoints record with NULL date fields
            query = """
            INSERT INTO touchpoints (id, customer_id, welcome_outreach, technical_onboarding, 
                                   follow_up_call, feedback_session)
            VALUES (%s, %s, NULL, NULL, NULL, NULL)
            """
            
            cursor.execute(query, (touchpoints_id, customer_id))
            connection.commit()
            
            logger.info(f"Created touchpoints record {touchpoints_id} for customer {customer_id}")
            return touchpoints_id
            
        except Error as e:
            logger.error(f"Database error while creating touchpoints record: {e}")
            return None
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()
    
    def get_customer_details(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Get customer details for the event payload.
        
        Args:
            customer_id: ID of the corporate customer
            
        Returns:
            Dictionary with customer details or None if not found
        """
        try:
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor(dictionary=True)
            
            query = """
            SELECT id, name, subscription_tier, created_at, updated_at
            FROM corporate_customers 
            WHERE id = %s
            """
            
            cursor.execute(query, (customer_id,))
            result = cursor.fetchone()
            
            if result:
                # Convert datetime objects to ISO format strings
                if result['created_at']:
                    result['created_at'] = result['created_at'].isoformat()
                if result['updated_at']:
                    result['updated_at'] = result['updated_at'].isoformat()
            
            return result
            
        except Error as e:
            logger.error(f"Database error while fetching customer details: {e}")
            return None
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()
    
    async def publish_touchpoints_created_event(self, touchpoints_id: str, customer_details: Dict[str, Any]) -> bool:
        """
        Publish touchpoints-created event to NATS.
        
        Args:
            touchpoints_id: ID of the created touchpoints record
            customer_details: Customer information for the event
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Connect to NATS with authentication
            nc = await nats.connect(
                self.nats_url,
                user=self.nats_user,
                password=self.nats_password
            )
            
            # Prepare event payload
            event_payload = {
                "event_type": "touchpoints-created",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "touchpoints_id": touchpoints_id,
                "customer": customer_details,
                "touchpoints": {
                    "welcome_outreach": None,
                    "technical_onboarding": None,
                    "follow_up_call": None,
                    "feedback_session": None
                },
                "next_actions": [
                    "Schedule welcome outreach",
                    "Plan technical onboarding session",
                    "Set up follow-up call",
                    "Arrange feedback session"
                ]
            }
            
            # Publish event
            await nc.publish(
                self.nats_subject,
                json.dumps(event_payload, indent=2).encode('utf-8')
            )
            
            logger.info(f"Published {self.nats_subject} event for touchpoints {touchpoints_id}")
            await nc.close()
            return True
            
        except (ConnectionClosedError, TimeoutError) as e:
            logger.error(f"NATS connection error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error publishing NATS event: {e}")
            return False
    
    async def create_touchpoints_for_customer(self) -> bool:
        """
        Main method to create touchpoints for the specified customer.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Creating touchpoints for customer: {self.customer_name}")
        
        # Step 1: Look up customer ID
        customer_id = self.get_customer_id(self.customer_name)
        if not customer_id:
            logger.error("Failed to find customer")
            return False
        
        # Step 2: Create touchpoints record
        touchpoints_id = self.create_touchpoints_record(customer_id)
        if not touchpoints_id:
            logger.error("Failed to create touchpoints record")
            return False
        
        # Step 3: Get customer details for event
        customer_details = self.get_customer_details(customer_id)
        if not customer_details:
            logger.error("Failed to fetch customer details")
            return False
        
        # Step 4: Publish NATS event
        event_success = await self.publish_touchpoints_created_event(touchpoints_id, customer_details)
        if not event_success:
            logger.error("Failed to publish NATS event")
            return False
        
        logger.info("Successfully created touchpoints and published event")
        return True


async def main():
    """Main entry point."""
    try:
        creator = TouchpointsCreator()
        success = await creator.create_touchpoints_for_customer()
        
        if success:
            logger.info("Touchpoints creation completed successfully")
            sys.exit(0)
        else:
            logger.error("Touchpoints creation failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
