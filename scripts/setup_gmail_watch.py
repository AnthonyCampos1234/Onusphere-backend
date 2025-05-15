import os
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CLIENT_SECRET_FILE = os.path.join(BASE_DIR, os.getenv('CLIENT_SECRET_FILE'))

# Run the OAuth flow to get credentials
flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
creds = flow.run_local_server(port=0)

service = build('gmail', 'v1', credentials=creds)

# Start watching Gmail inbox
request = {
    'labelIds': ['INBOX'],
    'topicName': f'projects/{os.getenv("PROJECT_ID")}/topics/{os.getenv("TOPIC_NAME")}'
}

response = service.users().watch(userId='me', body=request).execute()
print("Gmail watch started successfully:", response)
