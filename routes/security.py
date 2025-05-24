from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List
from pydantic import BaseModel
from datetime import datetime, timedelta
import secrets
import hashlib
from user_agents import parse

from models.types import Member, UserSession
from utils.dependencies import get_current_user
from utils.security import hash_password, verify_password
from routes.notification import create_system_notification

router = APIRouter()

# Pydantic models for request/response
class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class SessionResponse(BaseModel):
    id: str
    device_info: str
    ip_address: str
    location: str
    created_at: str
    last_activity: str
    is_current: bool

class NotificationPreferences(BaseModel):
    notify_orders: bool = True
    notify_customers: bool = True
    notify_team: bool = True
    notify_system: bool = True
    notify_marketing: bool = False
    notify_realtime: bool = True
    notify_tasks: bool = True

def get_device_info(user_agent: str) -> str:
    """Extract device information from user agent"""
    try:
        parsed = parse(user_agent)
        device = f"{parsed.browser.family}"
        if parsed.os.family:
            device += f" on {parsed.os.family}"
        return device
    except:
        return "Unknown Device"

def get_location_from_ip(ip_address: str) -> str:
    """Get location from IP address (placeholder - integrate with IP geolocation service)"""
    # For now, return a placeholder. In production, integrate with a service like MaxMind
    return "Unknown Location"

def generate_session_token() -> str:
    """Generate a secure session token"""
    return secrets.token_urlsafe(32)

@router.post("/security/change-password")
def change_password(
    request: ChangePasswordRequest,
    current_user: Member = Depends(get_current_user)
):
    """Change user password"""
    # Verify current password
    if not verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Validate new password
    if len(request.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters long")
    
    # Update password
    current_user.hashed_password = hash_password(request.new_password)
    current_user.save()
    
    # Create notification
    create_system_notification(
        member=current_user,
        title="Password Changed",
        description="Your password was successfully updated",
        notification_type="security"
    )
    
    # Invalidate all other sessions except current one
    UserSession.objects(
        member=current_user,
        is_active=True
    ).update(set__is_active=False)
    
    return {"status": "success", "message": "Password updated successfully"}

@router.get("/security/sessions", response_model=List[SessionResponse])
def get_user_sessions(
    request: Request,
    current_user: Member = Depends(get_current_user)
):
    """Get all active sessions for the current user"""
    sessions = UserSession.objects(
        member=current_user,
        is_active=True
    ).order_by('-last_activity')
    
    # Get current session token from request headers
    current_token = request.headers.get("authorization", "").replace("Bearer ", "")
    current_session_hash = hashlib.sha256(current_token.encode()).hexdigest() if current_token else ""
    
    return [
        SessionResponse(
            id=str(session.id),
            device_info=session.device_info or "Unknown Device",
            ip_address=session.ip_address or "Unknown IP",
            location=session.location or "Unknown Location",
            created_at=session.created_at.isoformat(),
            last_activity=session.last_activity.isoformat(),
            is_current=(session.session_token == current_session_hash)
        )
        for session in sessions
    ]

@router.delete("/security/sessions/{session_id}")
def logout_session(
    session_id: str,
    current_user: Member = Depends(get_current_user)
):
    """Log out a specific session"""
    session = UserSession.objects(
        id=session_id,
        member=current_user
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session.is_active = False
    session.save()
    
    return {"status": "success", "message": "Session logged out"}

@router.delete("/security/sessions")
def logout_all_sessions(
    request: Request,
    current_user: Member = Depends(get_current_user)
):
    """Log out all sessions except the current one"""
    # Get current session token
    current_token = request.headers.get("authorization", "").replace("Bearer ", "")
    current_session_hash = hashlib.sha256(current_token.encode()).hexdigest() if current_token else ""
    
    # Deactivate all sessions except current
    result = UserSession.objects(
        member=current_user,
        is_active=True,
        session_token__ne=current_session_hash
    ).update(set__is_active=False)
    
    # Create notification
    create_system_notification(
        member=current_user,
        title="Security Action",
        description=f"Logged out from {result} other devices",
        notification_type="security"
    )
    
    return {"status": "success", "logged_out_sessions": result}

@router.post("/security/create-session")
def create_user_session(
    request: Request,
    token: str,
    current_user: Member = Depends(get_current_user)
):
    """Create a new user session (called during login)"""
    # Hash the JWT token to store as session identifier
    session_token = hashlib.sha256(token.encode()).hexdigest()
    
    # Get client info
    user_agent = request.headers.get("user-agent", "")
    ip_address = request.client.host if request.client else "unknown"
    
    device_info = get_device_info(user_agent)
    location = get_location_from_ip(ip_address)
    
    # Create session
    session = UserSession(
        member=current_user,
        session_token=session_token,
        device_info=device_info,
        ip_address=ip_address,
        location=location
    ).save()
    
    return {"session_id": str(session.id)}

@router.get("/security/notification-preferences", response_model=NotificationPreferences)
def get_notification_preferences(current_user: Member = Depends(get_current_user)):
    """Get user notification preferences"""
    # For now, return default preferences. In production, store these in user profile
    preferences = getattr(current_user, 'notification_preferences', {})
    
    return NotificationPreferences(
        notify_orders=preferences.get('notify_orders', True),
        notify_customers=preferences.get('notify_customers', True),
        notify_team=preferences.get('notify_team', True),
        notify_system=preferences.get('notify_system', True),
        notify_marketing=preferences.get('notify_marketing', False),
        notify_realtime=preferences.get('notify_realtime', True),
        notify_tasks=preferences.get('notify_tasks', True)
    )

@router.put("/security/notification-preferences")
def update_notification_preferences(
    preferences: NotificationPreferences,
    current_user: Member = Depends(get_current_user)
):
    """Update user notification preferences"""
    # Store preferences in member document
    if not hasattr(current_user, 'notification_preferences'):
        current_user.notification_preferences = {}
    
    current_user.notification_preferences = {
        'notify_orders': preferences.notify_orders,
        'notify_customers': preferences.notify_customers,
        'notify_team': preferences.notify_team,
        'notify_system': preferences.notify_system,
        'notify_marketing': preferences.notify_marketing,
        'notify_realtime': preferences.notify_realtime,
        'notify_tasks': preferences.notify_tasks
    }
    current_user.save()
    
    return {"status": "success", "message": "Notification preferences updated"}

# Utility function to update session activity
def update_session_activity(token: str, member: Member):
    """Update last activity for a session"""
    session_token = hashlib.sha256(token.encode()).hexdigest()
    UserSession.objects(
        member=member,
        session_token=session_token,
        is_active=True
    ).update(set__last_activity=datetime.utcnow()) 