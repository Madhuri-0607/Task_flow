#!/usr/bin/env python
"""
Database Initialization Script
This script initializes the database with all required tables.
Used as Railway release command to run migrations before app starts.
"""

import os
import sys
import logging

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from backend.models import db

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def init_database():
    """Initialize database tables"""
    app = create_app()
    
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            logger.info("✓ Database tables created/verified successfully")
            
            # Log database URL for debugging (without password)
            db_url = os.getenv("DATABASE_URL", "sqlite:///taskmanager.db")
            if "sqlite" in db_url:
                logger.info(f"  Using database: SQLite (local development)")
            else:
                # Mask password for security
                masked_url = db_url.split("@")[1] if "@" in db_url else "hidden"
                logger.info(f"  Using database: PostgreSQL ({masked_url})")
            
            return 0
        except Exception as e:
            logger.error(f"✗ Failed to initialize database: {str(e)}")
            return 1


if __name__ == "__main__":
    exit_code = init_database()
    sys.exit(exit_code)
