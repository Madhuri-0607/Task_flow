#!/usr/bin/env python
"""
Create Admin User Script
Usage: python create_admin_user.py <name> <email> <password>

This script creates an admin user for TaskFlow.
Admin users can create projects, manage team members, and create/assign tasks.
"""

import os
import sys
import logging

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from backend.models import db, User
from werkzeug.security import generate_password_hash

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_admin(name, email, password):
    """Create an admin user"""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if user already exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                logger.warning(f"User with email {email} already exists")
                return False
            
            # Validate inputs
            if len(name) < 2:
                logger.error("Name must be at least 2 characters")
                return False
            
            if len(password) < 6:
                logger.error("Password must be at least 6 characters")
                return False
            
            # Create admin user
            hashed_pw = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
            admin = User(
                name=name,
                email=email,
                password=hashed_pw,
                role="admin"
            )
            
            db.session.add(admin)
            db.session.commit()
            
            logger.info(f"✓ Admin user created successfully")
            logger.info(f"  Email: {email}")
            logger.info(f"  Name: {name}")
            logger.info(f"  ID: {admin.id}")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"✗ Failed to create admin user: {str(e)}")
            return False


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python create_admin_user.py <name> <email> <password>")
        print("\nExample:")
        print("  python create_admin_user.py 'John Doe' admin@example.com password123")
        sys.exit(1)
    
    name = sys.argv[1]
    email = sys.argv[2]
    password = sys.argv[3]
    
    success = create_admin(name, email, password)
    sys.exit(0 if success else 1)