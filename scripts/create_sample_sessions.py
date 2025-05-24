"""
Script to create sample user sessions for testing
Run this script to populate the session management system with test data
"""
import os
import sys
import datetime
import hashlib
import secrets

# Add the parent directory to the path so we can import our models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db import connect_db
from models.types import Member, UserSession

def create_sample_sessions():
    """Create sample user sessions for testing session management"""
    
    # Connect to the database
    connect_db()
    
    # Sample session data
    sample_sessions = [
        {
            "device_info": "Chrome on macOS",
            "ip_address": "192.168.1.100",
            "location": "Chicago, IL",
            "hours_ago": 0,  # Current session
            "is_current": True
        },
        {
            "device_info": "Safari on iPhone",
            "ip_address": "10.0.0.45",
            "location": "Chicago, IL",
            "hours_ago": 3,
            "is_current": False
        },
        {
            "device_info": "Firefox on Windows",
            "ip_address": "192.168.1.105",
            "location": "Remote Office",
            "hours_ago": 24,
            "is_current": False
        },
        {
            "device_info": "Chrome on Android",
            "ip_address": "172.16.0.25",
            "location": "Mobile Network",
            "hours_ago": 72,
            "is_current": False
        }
    ]
    
    # Get all members in the system
    members = Member.objects.all()
    
    if not members:
        print("No members found in the system. Please create some users first.")
        return
    
    created_count = 0
    
    for member in members:
        print(f"Creating sessions for {member.name} ({member.email})")
        
        # Clear existing sessions for this member (for clean testing)
        UserSession.objects(member=member).delete()
        
        for session_data in sample_sessions:
            # Create session timestamp
            created_at = datetime.datetime.utcnow() - datetime.timedelta(hours=session_data["hours_ago"])
            last_activity = created_at + datetime.timedelta(minutes=30)
            
            # Generate a unique session token
            session_token = hashlib.sha256(
                f"{member.id}_{session_data['device_info']}_{secrets.token_hex(16)}".encode()
            ).hexdigest()
            
            session = UserSession(
                member=member,
                session_token=session_token,
                device_info=session_data["device_info"],
                ip_address=session_data["ip_address"],
                location=session_data["location"],
                created_at=created_at,
                last_activity=last_activity,
                is_active=True
            )
            session.save()
            created_count += 1
    
    print(f"\nSuccessfully created {created_count} sample sessions!")
    print("You can now test the session management system in the frontend.")

if __name__ == "__main__":
    create_sample_sessions() 