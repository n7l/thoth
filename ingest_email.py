import os.path
import base64
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Define the scope
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def authenticate():
    """Authenticate and return the Gmail API service."""
    creds = None
    # Check if token.json exists
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, prompt the user to log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for future use
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
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
        msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))
        mime_msg = email.message_from_bytes(msg_str)
        return mime_msg
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
    for msg in messages:
        mime_msg = get_message(service, msg['id'])
        if mime_msg:
            print(f'From: {mime_msg["From"]}')
            print(f'Subject: {mime_msg["Subject"]}')
            print(f'Date: {mime_msg["Date"]}')
            print('-' * 50)

if __name__ == '__main__':
    main()