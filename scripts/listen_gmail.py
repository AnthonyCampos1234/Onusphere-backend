import os
import json
import base64
import threading

from google.cloud import pubsub_v1
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from email import policy
from email.parser import BytesParser
from dotenv import load_dotenv
import shared_state

# Load environment
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

# Load constants from .env
PROJECT_ID = os.getenv('PROJECT_ID')
SUBSCRIPTION_NAME = os.getenv('SUBSCRIPTION_NAME')
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), '..', 'service_account.json')
CLIENT_SECRET_FILE = os.path.join(os.path.dirname(__file__), '..', 'onusphere_secret.json')
TOKEN_FILE = os.path.join(os.path.dirname(__file__), '..', 'token.json')

# Scopes for Gmail API
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Global variables to track state
last_processed_history_id = None
processed_message_ids = set()

# --- Gmail Service using OAuth 2.0 token
def get_gmail_service():
    creds = None
    # The file token.json stores the user's access and refresh tokens
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    
    return build('gmail', 'v1', credentials=creds)

def get_email_body(payload, preferred_type='text/plain'):
    """
    Extract the email body from the message payload.
    
    Args:
        payload: The Gmail API message payload
        preferred_type: The preferred MIME type ('text/plain' or 'text/html')
    
    Returns:
        String containing the email body or None if not found
    """
    body = {}
    
    # Helper function to extract body parts recursively
    def extract_parts(part, indent=0):
        if part.get('mimeType') in ['text/plain', 'text/html']:
            body_data = part.get('body', {}).get('data')
            if body_data:
                mime_type = part.get('mimeType')
                if mime_type not in body:
                    body[mime_type] = []
                body[mime_type].append(base64.urlsafe_b64decode(body_data).decode('utf-8', errors='replace'))
        
        # Process any nested parts
        if 'parts' in part:
            for p in part['parts']:
                extract_parts(p, indent + 1)
    
    # Start extraction process with the payload
    if payload.get('mimeType') in ['text/plain', 'text/html']:
        body_data = payload.get('body', {}).get('data')
        if body_data:
            mime_type = payload.get('mimeType')
            body[mime_type] = [base64.urlsafe_b64decode(body_data).decode('utf-8', errors='replace')]
    
    # Process parts if available
    if 'parts' in payload:
        for part in payload['parts']:
            extract_parts(part)
    
    # Return the preferred type if available, or fall back to the other type
    if preferred_type in body and body[preferred_type]:
        return '\n'.join(body[preferred_type])
    elif 'text/plain' in body and body['text/plain']:
        return '\n'.join(body['text/plain'])
    elif 'text/html' in body and body['text/html']:
        return '\n'.join(body['text/html'])
    
    return None

def extract_plain_text(message):
    """Extract plain text body from a message."""
    def get_text_from_parts(parts):
        text = ''
        for part in parts:
            if part.get('mimeType') == 'text/plain':
                data = part['body'].get('data')
                if data:
                    decoded_text = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
                    text += decoded_text
            elif part.get('mimeType', '').startswith('multipart/'):
                if 'parts' in part:
                    text += get_text_from_parts(part['parts'])
        return text

    if 'parts' in message['payload']:
        return get_text_from_parts(message['payload']['parts']).strip()
    else:
        # Single part message
        if message['payload'].get('mimeType') == 'text/plain':
            data = message['payload']['body'].get('data')
            if data:
                return base64.urlsafe_b64decode(data).decode('utf-8', errors='replace').strip()
    
    return ''

def extract_email_metadata(message):
    headers = {header['name'].lower(): header['value'] for header in message['payload'].get('headers', [])}
    
    subject = headers.get('subject', '')
    sender = headers.get('from', '')
    recipient = headers.get('to', '')
    date = headers.get('date', '')
    
    body = extract_plain_text(message)
    
    return {
        'subject': subject,
        'from': sender,
        'to': recipient,
        'date': date,
        'body': body
    }


def process_message(service, msg_id):
    """
    Process a single email message
    
    Args:
        service: Gmail API service instance
        msg_id: The ID of the message to process
    
    Returns:
        Dict containing email details (subject, body, etc.)
    """

    message = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
    
    attachments = get_attachments(service, 'me', message)
    email_metadata = extract_email_metadata(message)
    
    email_data = {
        "csv_file": next((a['data'] for a in attachments if a['filename'].lower().endswith('.csv')), None),
        "pdf_file": next((a['data'] for a in attachments if a['filename'].lower().endswith('.pdf')), None),
        "subject": email_metadata['subject'],
        "from": email_metadata['from'],
        "to": email_metadata['to'],
        "date": email_metadata['date'],
        "email_body": email_metadata['body']
    }
    
    return email_data

def get_attachments(service, user_id, message):
    """
    Get all attachments from the message
    
    Args:
        service: Gmail API service instance
        user_id: User ID ('me' for the authenticated user)
        message: The full message object
    
    Returns:
        List of dicts containing attachment details
    """
    attachments = []
    
    def process_parts(parts, parent_mime_type=None):
        for part in parts:
            filename = part.get('filename')
            mime_type = part.get('mimeType', 'application/octet-stream')
            
            # Handle attachments with filenames
            if filename and filename.strip():
                body = part.get('body', {})
                if 'attachmentId' in body:
                    attachment_id = body['attachmentId']
                    try:
                        attachment = service.users().messages().attachments().get(
                            userId=user_id, 
                            messageId=message['id'], 
                            id=attachment_id
                        ).execute()
                        
                        data = base64.urlsafe_b64decode(attachment['data'])
                        
                        attachments.append({
                            'filename': filename,
                            'size': len(data),
                            'mime_type': mime_type,
                            'data': data
                        })
                        print(f"Processed attachment: {filename} ({mime_type})")
                    except Exception as e:
                        print(f"Error getting attachment {filename}: {e}")
            
            # Handle multipart message structures that might contain attachments
            elif mime_type.startswith('multipart/'):
                if 'parts' in part:
                    process_parts(part['parts'], mime_type)
            
            # Handle inline attachments that might not have filenames
            elif 'application/' in mime_type and not filename:
                # Generate a filename based on content type if none exists
                file_ext = mime_type.split('/')[-1]
                generated_filename = f"attachment_{len(attachments)+1}.{file_ext}"
                
                body = part.get('body', {})
                if 'attachmentId' in body:
                    attachment_id = body['attachmentId']
                    try:
                        attachment = service.users().messages().attachments().get(
                            userId=user_id, 
                            messageId=message['id'], 
                            id=attachment_id
                        ).execute()
                        
                        data = base64.urlsafe_b64decode(attachment['data'])
                        
                        attachments.append({
                            'filename': generated_filename,
                            'size': len(data),
                            'mime_type': mime_type,
                            'data': data
                        })
                        print(f"Processed unnamed attachment as: {generated_filename} ({mime_type})")
                    except Exception as e:
                        print(f"Error getting unnamed attachment: {e}")
            
            # Process any additional nested parts
            if 'parts' in part:
                process_parts(part['parts'], mime_type)
    
    # Process the payload
    if 'parts' in message['payload']:
        process_parts(message['payload']['parts'], message['payload'].get('mimeType'))
    else:
        # Handle single-part messages that might be attachments
        part = message['payload']
        filename = part.get('filename')
        mime_type = part.get('mimeType', 'application/octet-stream')
        
        if filename and filename.strip():
            body = part.get('body', {})
            if 'attachmentId' in body:
                attachment_id = body['attachmentId']
                try:
                    attachment = service.users().messages().attachments().get(
                        userId=user_id, 
                        messageId=message['id'], 
                        id=attachment_id
                    ).execute()
                    
                    data = base64.urlsafe_b64decode(attachment['data'])
                    
                    attachments.append({
                        'filename': filename,
                        'size': len(data),
                        'mime_type': mime_type,
                        'data': data
                    })
                    print(f"Processed single-part attachment: {filename} ({mime_type})")
                except Exception as e:
                    print(f"Error getting single-part attachment {filename}: {e}")
    
    # Debug output
    if attachments:
        print(f"Found {len(attachments)} attachments in message {message['id']}")
    else:
        print(f"No attachments found in message {message['id']}")
        
        # Debug information about the message structure
        if 'parts' in message['payload']:
            print(f"Message has {len(message['payload']['parts'])} parts")
            for i, part in enumerate(message['payload']['parts']):
                print(f"Part {i+1}: mimeType={part.get('mimeType')}, filename={part.get('filename', 'None')}")
        else:
            print(f"Message has no parts. Payload mimeType={message['payload'].get('mimeType')}")
    
    return attachments

def handle_parsed_email(email_data):
    if not (email_data.get("csv_file") or email_data.get("pdf_file")):
        print("Skipping email: No CSV or PDF attachments.")
        return

    shared_state.email_data = email_data
    shared_state.order_id_holder["id"] = None
    shared_state.pipeline_trigger_event.set()
    print("Email with attachment processed.")

def process_gmail_event(service, new_history_id):
    global last_processed_history_id

    try:
        # Get the most recent email in INBOX
        results = service.users().messages().list(
            userId='me',
            labelIds=['INBOX'],
            maxResults=1
        ).execute()
        
        messages = results.get('messages', [])
        if not messages:
            print("No recent messages found in inbox.")
            return
        
        msg_id = messages[0]['id']
        if msg_id in processed_message_ids:
            print(f"Message {msg_id} already processed, skipping.")
            return
        
        processed_message_ids.add(msg_id)
        
        print(f"Processing latest message with ID: {msg_id}")
        email_data = process_message(service, msg_id)

        # Handle the parsed email data (trigger downstream pipeline, etc.)
        handle_parsed_email(email_data)

        # ✅ Print metadata
        print(f"\nNew Email - Subject: {email_data['subject']}")
        print(f"From: {email_data['from']}")
        print(f"To: {email_data['to']}")
        print(f"Date: {email_data['date']}")
        
        # ✅ Print body preview
        if email_data['email_body']:
            preview = email_data['email_body'][:200] + ('...' if len(email_data['email_body']) > 200 else '')
            print(f"Body Preview:\n{preview}\n")
        else:
            print("⚠ No body found.")

        # ✅ Print attachments
        attachments_found = []
        if email_data.get('csv_file'):
            attachments_found.append('CSV')
            print(f"✔ Found CSV attachment ({len(email_data['csv_file'])} bytes)")
        if email_data.get('pdf_file'):
            attachments_found.append('PDF')
            print(f"✔ Found PDF attachment ({len(email_data['pdf_file'])} bytes)")

        if not attachments_found:
            print("⚠ No CSV or PDF attachments found.")

        # ✅ Update last processed history ID
        last_processed_history_id = new_history_id
        print(f"Updated last processed historyId: {new_history_id}")
    
    except Exception as e:
        print(f"Error processing latest message: {e}")
        import traceback
        traceback.print_exc()

# --- Pub/Sub Listener using Service Account
def start_pubsub_listener():
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
    subscriber = pubsub_v1.SubscriberClient(credentials=credentials)
    subscription_path = f'projects/{PROJECT_ID}/subscriptions/{SUBSCRIPTION_NAME}'
    
    # Reconnect with each new message to avoid SSL timeout issues
    def get_fresh_gmail_service():
        try:
            return get_gmail_service()
        except Exception as e:
            print(f"Error creating Gmail service: {e}")
            import traceback
            traceback.print_exc()
            return None

    # Initialize (but we'll refresh with each message)
    gmail_service = get_fresh_gmail_service()
    if gmail_service:
        # Get initial history ID to start from
        try:
            profile = gmail_service.users().getProfile(userId='me').execute()
            global last_processed_history_id
            last_processed_history_id = profile.get('historyId')
            print(f"Starting with history ID: {last_processed_history_id}")
        except Exception as e:
            print(f"Error getting profile: {e}")
            last_processed_history_id = None

    def callback(message):
        try:
            print(f"\nPub/Sub message received:\n{message.data.decode()}")
            payload = json.loads(message.data.decode())
            
            # Get a fresh Gmail service for each message to avoid timeout issues
            gmail_service = get_fresh_gmail_service()
            if not gmail_service:
                print("Failed to create Gmail service, skipping message processing")
                message.ack()
                return
                
            history_id = payload.get('historyId')
            if history_id:
                process_gmail_event(gmail_service, history_id)
            else:
                print("No historyId in message.")
        except Exception as e:
            print(f"Error processing message: {e}")
            import traceback
            traceback.print_exc()
        finally:
            message.ack()

    print(f"Listening to Pub/Sub subscription: {subscription_path}")
    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
    
    # Keep the main thread alive
    try:
        print("Listener started successfully. Press Ctrl+C to exit.")
        streaming_pull_future.result()  # Block forever
    except KeyboardInterrupt:
        print("\nStopping listener...")
        streaming_pull_future.cancel()
        print("Listener stopped.")

# --- Run the listener
def start_gmail_listener_thread():
    thread = threading.Thread(target=start_pubsub_listener, daemon=True)
    thread.start()
