"""
Script to create sample notifications for testing
Run this script to populate the notification system with test data
"""
import os
import sys
import datetime

# Add the parent directory to the path so we can import our models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db import connect_db
from models.types import Account, Member, Notification

def create_sample_notifications():
    """Create sample notifications for all users in the system"""
    
    # Connect to the database
    connect_db()
    
    # Sample notification data
    sample_notifications = [
        {
            "title": "New shipment request",
            "description": "ABC Logistics added a new delivery request for Route 245",
            "type": "order",
            "metadata": {"route_id": "245", "customer": "ABC Logistics"}
        },
        {
            "title": "Route optimization complete",
            "description": "Your routes have been optimized for today. 15% efficiency improvement detected.",
            "type": "system",
            "metadata": {"efficiency_gain": "15%", "routes_optimized": 8}
        },
        {
            "title": "New team member joined",
            "description": "Sarah Johnson has joined your team as a Driver",
            "type": "team",
            "metadata": {"member_name": "Sarah Johnson", "role": "Driver"}
        },
        {
            "title": "Customer profile updated",
            "description": "XYZ Corporation updated their delivery preferences",
            "type": "customer",
            "metadata": {"customer": "XYZ Corporation", "changes": "delivery_preferences"}
        },
        {
            "title": "System maintenance scheduled",
            "description": "Platform maintenance is scheduled for Saturday 2 AM - 4 AM EST",
            "type": "system",
            "metadata": {"maintenance_date": "Saturday", "duration": "2 hours"}
        },
        {
            "title": "Load plan generated",
            "description": "Load Plan Pro has generated an optimized truck loading plan for Order #1234",
            "type": "order",
            "metadata": {"order_id": "1234", "plan_type": "optimized"}
        },
        {
            "title": "Security alert",
            "description": "New login detected from unknown device. If this wasn't you, please secure your account.",
            "type": "security",
            "metadata": {"device": "Chrome on Windows", "location": "New York, NY"}
        },
        {
            "title": "Weekly report ready",
            "description": "Your weekly performance report is now available in the dashboard",
            "type": "system",
            "metadata": {"report_type": "weekly", "period": "last_week"}
        }
    ]
    
    # Get all members in the system
    members = Member.objects.all()
    
    if not members:
        print("No members found in the system. Please create some users first.")
        return
    
    created_count = 0
    
    for member in members:
        print(f"Creating notifications for {member.name} ({member.email})")
        
        for i, notification_data in enumerate(sample_notifications):
            # Create notification with some time variation
            created_at = datetime.datetime.utcnow() - datetime.timedelta(
                hours=i * 2,  # Space notifications 2 hours apart
                minutes=i * 15  # Add some random minutes
            )
            
            # Mark some notifications as read (simulate user activity)
            is_read = i < 3  # Mark first 3 as read
            read_at = created_at + datetime.timedelta(minutes=30) if is_read else None
            
            notification = Notification(
                account=member.account,
                member=member,
                title=notification_data["title"],
                description=notification_data["description"],
                type=notification_data["type"],
                metadata=notification_data["metadata"],
                is_read=is_read,
                created_at=created_at,
                read_at=read_at
            )
            notification.save()
            created_count += 1
    
    print(f"\nSuccessfully created {created_count} sample notifications!")
    print("You can now test the notification system in the frontend.")

if __name__ == "__main__":
    create_sample_notifications() 