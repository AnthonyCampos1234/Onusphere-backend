from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from bson import ObjectId

from models.types import Notification, Member
from utils.dependencies import get_current_user

router = APIRouter()

# Pydantic models for request/response
class NotificationResponse(BaseModel):
    id: str
    title: str
    description: str
    type: str
    is_read: bool
    created_at: str
    read_at: Optional[str] = None
    metadata: dict = {}

class CreateNotification(BaseModel):
    title: str
    description: str
    type: str
    member_ids: Optional[List[str]] = None  # If None, send to all members in account
    metadata: dict = {}

class MarkReadRequest(BaseModel):
    notification_ids: List[str]

@router.get("/notifications", response_model=List[NotificationResponse])
def get_notifications(
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    unread_only: bool = Query(default=False),
    current_user: Member = Depends(get_current_user)
):
    """Get notifications for the current user"""
    query = {"account": current_user.account, "member": current_user.id}
    
    if unread_only:
        query["is_read"] = False
    
    notifications = (Notification.objects(**query)
                   .order_by('-created_at')
                   .skip(offset)
                   .limit(limit))
    
    return [
        NotificationResponse(
            id=str(notification.id),
            title=notification.title,
            description=notification.description,
            type=notification.type,
            is_read=notification.is_read,
            created_at=notification.created_at.isoformat(),
            read_at=notification.read_at.isoformat() if notification.read_at else None,
            metadata=notification.metadata or {}
        )
        for notification in notifications
    ]

@router.get("/notifications/count")
def get_unread_count(current_user: Member = Depends(get_current_user)):
    """Get count of unread notifications"""
    count = Notification.objects(
        account=current_user.account,
        member=current_user.id,
        is_read=False
    ).count()
    
    return {"unread_count": count}

@router.post("/notifications/mark-read")
def mark_notifications_read(
    request: MarkReadRequest,
    current_user: Member = Depends(get_current_user)
):
    """Mark specific notifications as read"""
    notification_object_ids = []
    for notification_id in request.notification_ids:
        try:
            notification_object_ids.append(ObjectId(notification_id))
        except:
            raise HTTPException(status_code=400, detail=f"Invalid notification ID: {notification_id}")
    
    # Update notifications
    result = Notification.objects(
        id__in=notification_object_ids,
        account=current_user.account,
        member=current_user.id,
        is_read=False
    ).update(
        set__is_read=True,
        set__read_at=datetime.utcnow()
    )
    
    return {"marked_read": result}

@router.post("/notifications/mark-all-read")
def mark_all_notifications_read(current_user: Member = Depends(get_current_user)):
    """Mark all notifications as read for current user"""
    result = Notification.objects(
        account=current_user.account,
        member=current_user.id,
        is_read=False
    ).update(
        set__is_read=True,
        set__read_at=datetime.utcnow()
    )
    
    return {"marked_read": result}

@router.delete("/notifications/{notification_id}")
def delete_notification(
    notification_id: str,
    current_user: Member = Depends(get_current_user)
):
    """Delete a specific notification"""
    try:
        notification_object_id = ObjectId(notification_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid notification ID")
    
    notification = Notification.objects(
        id=notification_object_id,
        account=current_user.account,
        member=current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.delete()
    return {"status": "success"}

@router.delete("/notifications")
def clear_all_notifications(current_user: Member = Depends(get_current_user)):
    """Clear all notifications for current user"""
    result = Notification.objects(
        account=current_user.account,
        member=current_user.id
    ).delete()
    
    return {"deleted_count": result}

@router.post("/notifications/create")
def create_notification(
    request: CreateNotification,
    current_user: Member = Depends(get_current_user)
):
    """Create notifications (admin/manager only)"""
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # If no specific members, send to all members in account
    if not request.member_ids:
        target_members = Member.objects(account=current_user.account)
    else:
        member_object_ids = []
        for member_id in request.member_ids:
            try:
                member_object_ids.append(ObjectId(member_id))
            except:
                raise HTTPException(status_code=400, detail=f"Invalid member ID: {member_id}")
        
        target_members = Member.objects(
            id__in=member_object_ids,
            account=current_user.account
        )
    
    # Create notifications for each target member
    created_notifications = []
    for member in target_members:
        notification = Notification(
            account=current_user.account,
            member=member,
            title=request.title,
            description=request.description,
            type=request.type,
            metadata=request.metadata
        ).save()
        created_notifications.append(str(notification.id))
    
    return {
        "status": "success",
        "created_count": len(created_notifications),
        "notification_ids": created_notifications
    }

# Utility function to create notifications (for internal use)
def create_system_notification(
    member: Member,
    title: str,
    description: str,
    notification_type: str = "system",
    metadata: dict = None
):
    """Helper function to create system notifications"""
    notification = Notification(
        account=member.account,
        member=member,
        title=title,
        description=description,
        type=notification_type,
        metadata=metadata or {}
    ).save()
    return notification 