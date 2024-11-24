import base64
import email
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Define the scope
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Define paths for credentials and tokens
BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_PATH = BASE_DIR / 'credentials.json'
TOKEN_PATH = BASE_DIR / 'token.json'

def authenticate():
    """Authenticate and return the Gmail API service."""
    creds = None
    # Check if token.json exists
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    # If there are no (valid) credentials available, prompt the user to log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for future use
        with TOKEN_PATH.open('w') as token_file:
            token_file.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def list_messages(service, user_id='me'):
    """List all messages from the user's mailbox."""
    try:
        response = service.users().messages().list(userId=user_id).execute()
        messages = []
        if 'messages' in response:
            messages.extend(response['messages'])
        while 'nextPageToken' in response:
            page_token = response['nextPageToken']
            response = service.users().messages().list(userId=user_id, pageToken=page_token).execute()
            if 'messages' in response:
                messages.extend(response['messages'])
        return messages
    except Exception as error:
        print(f'An error occurred: {error}')
        return None

def get_message(service, msg_id, user_id='me'):
    """Get a Message with given ID."""
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id, format='full').execute()
        payload = message.get('payload', {})
        headers = payload.get('headers', [])

        subject = next((header['value'] for header in headers if header['name'] == 'Subject'), "No Subject")
        sender = next((header['value'] for header in headers if header['name'] == 'From'), "Unknown Sender")
        date = next((header['value'] for header in headers if header['name'] == 'Date'), "Unknown Date")
        body = "No body available"

        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
        elif 'body' in payload and 'data' in payload['body']:
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')

        print(f"From: {sender}")
        print(f"Subject: {subject}")
        print(f"Date: {date}")
        print(f"Body:\n{body}")
        print("-" * 50)

        return {
            "from": sender,
            "subject": subject,
            "date": date,
            "body": body
        }
    except Exception as error:
        print(f'An error occurred: {error}')
        return None

def main():
    """Main function to download all emails."""
    service = authenticate()
    messages = list_messages(service)
    if not messages:
        print('No messages found.')
        return

    print(f'Total messages: {len(messages)}')

    # Create a directory to save emails
    email_dir = BASE_DIR / "emails"
    email_dir.mkdir(exist_ok=True)

    for index, msg in enumerate(messages):
        email_data = get_message(service, msg['id'])
        if email_data:
            email_file = email_dir / f"email_{index + 1}.txt"
            with email_file.open('w') as file:
                file.write(f"From: {email_data['from']}\n")
                file.write(f"Subject: {email_data['subject']}\n")
                file.write(f"Date: {email_data['date']}\n\n")
                file.write(email_data['body'])

if __name__ == '__main__':
    main()