# Team Invitation System

This document explains how the team member invitation system works.

## How It Works

The invitation system uses **mailto links** to open the user's local email client with a pre-composed invitation email. This approach has several advantages:

- ✅ **No SMTP configuration required** - No need for email server setup
- ✅ **Personal touch** - Emails come from the actual team member's email address
- ✅ **User control** - Team members can edit the email before sending
- ✅ **Better deliverability** - Uses the sender's email reputation
- ✅ **Cross-platform** - Works with any email client (Outlook, Apple Mail, Gmail, etc.)

## Invitation Flow

1. **Admin/Manager** creates an invitation with:
   - Recipient email address
   - Role (Admin, Manager, Member)
   - Optional personal message

2. **System generates**:
   - Unique invitation token
   - Company code inclusion
   - Pre-composed email with registration link

3. **Email client opens** automatically with:
   - Pre-filled recipient
   - Professional subject line
   - Complete invitation message including company code
   - Direct registration link with pre-filled data

4. **Team member** reviews and sends the email

5. **Recipient** clicks the link and registers with auto-filled company code

## Email Template Features

The auto-generated invitation emails include:

- ✅ **Professional subject line** with company name
- ✅ **Personal greeting** from the inviting team member
- ✅ **Clear role designation** (Admin, Manager, Member)
- ✅ **Custom message** if provided by the inviter
- ✅ **Step-by-step instructions** for joining
- ✅ **Company code** prominently displayed
- ✅ **Direct registration link** with pre-filled company code
- ✅ **7-day expiration notice**
- ✅ **Professional signature** from the inviter

## Example Email Template

```
Subject: Invitation to join Acme Corp on Movomint

Hi there!

John Smith has invited you to join Acme Corp on Movomint as a Manager.

Personal message: "Welcome to the team! Looking forward to working with you."

To get started:
1. Click this link: http://localhost:3000/auth/register?invitation=abc123&code=ACME01
2. Create your account using company code: ACME01

This invitation will expire in 7 days.

Best regards,
John Smith
```

## Supported Email Clients

The mailto links work with all major email clients:

- **Desktop**: Outlook, Apple Mail, Thunderbird, etc.
- **Web**: Gmail (when set as default), Outlook.com, etc.
- **Mobile**: iOS Mail, Android Gmail, etc.

## Managing Invitations

### Creating Invitations
1. Navigate to the Users page
2. Click "Add Team Member"
3. Fill out the invitation form
4. Click "Create & Open Email"
5. Your email client opens with the pre-composed invitation
6. Review and send the email

### Pending Invitations
- View all pending invitations on the Users page
- See invitation details: email, role, inviter, expiration date
- Resend invitations (opens email client again)
- Cancel unwanted invitations

### Resending Invitations
1. Click "Resend" on any pending invitation
2. Email client opens with updated invitation
3. Expiration date is automatically extended by 7 days

## Registration Experience

When recipients click the invitation link:

1. **Auto-detection** - System detects invitation token from URL
2. **Pre-filled form** - Company code is automatically filled
3. **Enhanced UI** - Special messaging shows they're joining via invitation
4. **Simplified flow** - "Join Existing Business" tab is pre-selected
5. **Clear button** - "Accept Invitation & Join Team" instead of generic text

## Technical Implementation

### Backend
- Creates invitation records with unique tokens
- Returns email template data for mailto links
- Tracks invitation status (pending, accepted, expired)
- Handles invitation acceptance during registration

### Frontend
- Generates mailto links from template data
- Opens default email client automatically
- Provides fallback if email client doesn't open
- Shows clear feedback about the process

## Security Features

- ✅ **Unique tokens** - Each invitation has a cryptographically secure token
- ✅ **7-day expiration** - Invitations automatically expire
- ✅ **Permission checks** - Only Admins and Managers can invite
- ✅ **Duplicate prevention** - Can't invite existing members
- ✅ **Token validation** - Tokens are validated during registration

## Advantages Over Direct Email Sending

| Feature | Mailto Approach | SMTP Sending |
|---------|----------------|--------------|
| Setup complexity | None required | SMTP configuration needed |
| Email deliverability | Uses sender's reputation | Depends on server setup |
| Personal touch | From real team member | From system/noreply address |
| Customization | User can edit before sending | Fixed template only |
| Spam filtering | Less likely to be filtered | Often goes to spam |
| Security | No credentials stored | SMTP credentials in server |
| Reliability | Works everywhere | Can fail due to server issues |

## Troubleshooting

### Email Client Doesn't Open
- **Cause**: No default email client set
- **Solution**: Set a default email client in OS settings
- **Workaround**: Copy the invitation details manually

### Invitation Link Doesn't Work
- **Check**: Link format and invitation token
- **Verify**: Invitation hasn't expired
- **Confirm**: Company code is correct

### Email Not Sent
- **Remember**: The system only opens your email client
- **Action required**: You must actually click "Send" in your email client
- **Check**: Draft folder if email client saved it as draft

## Best Practices

1. **Review before sending** - Always check the invitation email before sending
2. **Add personal touch** - Include a custom message for better engagement  
3. **Follow up** - Check if invitations are accepted within a few days
4. **Clean up** - Cancel expired or unwanted invitations regularly
5. **Use appropriate roles** - Assign the minimum necessary permissions

## Mobile Experience

On mobile devices:
- Mailto links open the default mail app
- Works with iOS Mail, Gmail app, Outlook mobile, etc.
- Some browsers may ask which email app to use
- Users can copy invitation details if needed 