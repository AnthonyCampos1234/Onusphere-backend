from fastapi import APIRouter, Depends, HTTPException
from models.types import Account, Member, Invitation
from models.request_bodies import SendInvitation, ResendInvitation, DeleteInvitation
from utils.dependencies import get_current_user
from typing import List
import datetime

router = APIRouter()

@router.post("/invitations/send")
def send_invitation(
    invitation_data: SendInvitation,
    current_user: Member = Depends(get_current_user)
):
    """Create an invitation and return data for mailto link"""
    
    # Check if user has permission to invite (admin or manager)
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="You don't have permission to send invitations")
    
    # Check if user is already a member
    existing_member = Member.objects(email=invitation_data.email, account=current_user.account).first()
    if existing_member:
        raise HTTPException(status_code=400, detail="User is already a member of this account")
    
    # Check if there's already a pending invitation
    existing_invitation = Invitation.objects(
        email=invitation_data.email, 
        account=current_user.account,
        status="pending"
    ).first()
    if existing_invitation:
        raise HTTPException(status_code=400, detail="An invitation has already been sent to this email")
    
    # Get account details
    account = Account.objects(id=current_user.account.id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Create invitation
    invitation = Invitation(
        account=current_user.account,
        email=invitation_data.email,
        role=invitation_data.role,
        message=invitation_data.message,
        invited_by=current_user
    ).save()
    
    # Return invitation data with email template info
    return {
        "id": str(invitation.id),
        "email": invitation.email,
        "role": invitation.role,
        "message": invitation.message,
        "date_created": invitation.date_created.isoformat(),
        "expires_at": invitation.expires_at.isoformat(),
        "status": invitation.status,
        "invited_by": current_user.name,
        "email_template": {
            "to": invitation.email,
            "subject": f"Invitation to join {account.name} on OnuSphere",
            "body": f"""Hi there!

{current_user.name} has invited you to join {account.name} on OnuSphere as a {invitation.role.title()}.

{f'Personal message: "{invitation.message}"' if invitation.message else ''}

To get started:
1. Click this link: http://localhost:3000/auth/register?invitation={invitation.invitation_token}&code={account.company_code}
2. Create your account using company code: {account.company_code}

This invitation will expire in 7 days.

Best regards,
{current_user.name}"""
        }
    }

@router.get("/invitations")
def get_pending_invitations(current_user: Member = Depends(get_current_user)):
    """Get all pending invitations for the current account"""
    
    invitations = Invitation.objects(
        account=current_user.account,
        status="pending",
        expires_at__gte=datetime.datetime.utcnow()
    )
    
    return [
        {
            "id": str(invitation.id),
            "email": invitation.email,
            "role": invitation.role,
            "message": invitation.message,
            "date_created": invitation.date_created.isoformat(),
            "expires_at": invitation.expires_at.isoformat(),
            "status": invitation.status,
            "invited_by": invitation.invited_by.name if invitation.invited_by else "Unknown"
        }
        for invitation in invitations
    ]

@router.post("/invitations/resend")
def resend_invitation(
    resend_data: ResendInvitation,
    current_user: Member = Depends(get_current_user)
):
    """Resend an existing invitation by providing new mailto data"""
    
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="You don't have permission to resend invitations")
    
    invitation = Invitation.objects(
        id=resend_data.invitation_id,
        account=current_user.account
    ).first()
    
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    if invitation.status != "pending":
        raise HTTPException(status_code=400, detail="Can only resend pending invitations")
    
    # Update expiration date
    invitation.expires_at = datetime.datetime.utcnow() + datetime.timedelta(days=7)
    invitation.save()
    
    # Get account details
    account = Account.objects(id=current_user.account.id).first()
    
    return {
        "id": str(invitation.id),
        "email": invitation.email,
        "role": invitation.role,
        "message": invitation.message,
        "date_created": invitation.date_created.isoformat(),
        "expires_at": invitation.expires_at.isoformat(),
        "status": invitation.status,
        "invited_by": invitation.invited_by.name if invitation.invited_by else "Unknown",
        "email_template": {
            "to": invitation.email,
            "subject": f"Invitation to join {account.name} on OnuSphere",
            "body": f"""Hi there!

{current_user.name} has invited you to join {account.name} on OnuSphere as a {invitation.role.title()}.

{f'Personal message: "{invitation.message}"' if invitation.message else ''}

To get started:
1. Click this link: http://localhost:3000/auth/register?invitation={invitation.invitation_token}&code={account.company_code}
2. Create your account using company code: {account.company_code}

This invitation will expire in 7 days.

Best regards,
{current_user.name}"""
        }
    }

@router.delete("/invitations/{invitation_id}")
def delete_invitation(
    invitation_id: str,
    current_user: Member = Depends(get_current_user)
):
    """Delete/cancel an invitation"""
    
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="You don't have permission to delete invitations")
    
    invitation = Invitation.objects(
        id=invitation_id,
        account=current_user.account
    ).first()
    
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    invitation.delete()
    
    return {"message": "Invitation deleted successfully"}

@router.post("/invitations/accept/{invitation_token}")
def accept_invitation(invitation_token: str):
    """Accept an invitation (this will be called during registration)"""
    
    invitation = Invitation.objects(
        invitation_token=invitation_token,
        status="pending"
    ).first()
    
    if not invitation:
        raise HTTPException(status_code=404, detail="Invalid or expired invitation")
    
    if invitation.expires_at < datetime.datetime.utcnow():
        invitation.status = "expired"
        invitation.save()
        raise HTTPException(status_code=400, detail="Invitation has expired")
    
    # Mark invitation as accepted
    invitation.status = "accepted"
    invitation.save()
    
    # Return invitation details for registration
    account = Account.objects(id=invitation.account.id).first()
    
    return {
        "company_code": account.company_code,
        "company_name": account.name,
        "role": invitation.role,
        "email": invitation.email
    } 