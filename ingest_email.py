import base64
import email
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import psycopg2
from psycopg2.extras import execute_values
from email.utils import parsedate_to_datetime

# Define the scope
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Define paths for credentials and tokens
BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_PATH = BASE_DIR / "credentials.json"
TOKEN_PATH = BASE_DIR / "token.json"
TEST_MODE = True


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
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_PATH), SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for future use
        with TOKEN_PATH.open("w") as token_file:
            token_file.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def list_messages(service, user_id="me"):
    """List all messages from the user's mailbox."""
    try:
        response = service.users().messages().list(userId=user_id).execute()
        messages = []
        if "messages" in response:
            messages.extend(response["messages"])
        if not TEST_MODE:
            while "nextPageToken" in response:
                page_token = response["nextPageToken"]
                response = (
                    service.users()
                    .messages()
                    .list(userId=user_id, pageToken=page_token)
                    .execute()
                )
                if "messages" in response:
                    messages.extend(response["messages"])
        return messages
    except Exception as error:
        print(f"An error occurred: {error}")
        return None


def get_message(service, msg_id, user_id="me"):
    """Get a Message with given ID."""
    try:
        message = (
            service.users()
            .messages()
            .get(userId=user_id, id=msg_id, format="full")
            .execute()
        )
        payload = message.get("payload", {})
        headers = payload.get("headers", [])

        subject = next(
            (header["value"] for header in headers if header["name"] == "Subject"),
            "No Subject",
        )
        sender = next(
            (header["value"] for header in headers if header["name"] == "From"),
            "Unknown Sender",
        )
        date = next(
            (header["value"] for header in headers if header["name"] == "Date"),
            "Unknown Date",
        )
        body = "No body available"

        if "parts" in payload:
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain" and "data" in part["body"]:
                    body = base64.urlsafe_b64decode(part["body"]["data"]).decode(
                        "utf-8"
                    )
        elif "body" in payload and "data" in payload["body"]:
            body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")

        # print(f"From: {sender}")
        # print(f"Subject: {subject}")
        # print(f"Date: {date}")
        # print(f"Body:\n{body}")
        # print("-" * 50)

        return {"from": sender, "subject": subject, "date": date, "body": body}
    except Exception as error:
        print(f"An error occurred: {error}")
        return None


def connect_to_db():
    """Connect to the PostgreSQL database."""
    conn = psycopg2.connect(
        dbname="thoth",
        user="postgres",
        password="postgres",
        host="localhost",
        port=5432,
    )
    return conn


def save_emails_to_db(emails):
    """Save a list of emails to the database."""
    conn = connect_to_db()
    cursor = conn.cursor()

    # Insert query
    # INSERT INTO emails (message_id, sender, recipient, subject, body, date, labels)
    query = """
    INSERT INTO emails (message_id, sender, subject, body, date)
    VALUES %s
    ON CONFLICT (message_id) DO NOTHING;  -- Skip duplicates
    """
    email_data = []
    for email_ in emails:
        breakpoint()
        if email_["date"] == "Unknown Date":
            dt = None
        else:
            dt = parsedate_to_datetime(email_["date"])

        # Prepare data for insertion
        email_data.append(
            (
                email_["id"],
                email_["from"],
                # email_['recipient'],  # Expecting a list
                email_["subject"],
                email_["body"],
                # email_['date'],
                dt,
                # email_['labels']      # Expecting a list
            )
        )

    # Use execute_values for efficient bulk insert
    execute_values(cursor, query, email_data)
    conn.commit()
    cursor.close()
    conn.close()


def main():
    """Main function to download all emails."""
    service = authenticate()
    messages = list_messages(service)
    if not messages:
        print("No messages found.")
        return

    print(f"Total messages: {len(messages)}")

    # Create a directory to save emails
    email_dir = BASE_DIR / "emails"
    email_dir.mkdir(exist_ok=True)

    emails = []
    for index, msg in enumerate(messages):
        email_data = get_message(service, msg["id"])
        if email_data:
            email_data["id"] = msg["id"]
            emails.append(email_data)
            # breakpoint()
            # email_file = email_dir / f"email_{index + 1}.txt"
            # with email_file.open("w") as file:
            #     file.write(f"From: {email_data['from']}\n")
            #     file.write(f"Subject: {email_data['subject']}\n")
            #     file.write(f"Date: {email_data['date']}\n\n")
            #     file.write(email_data["body"])

    save_emails_to_db(emails)


if __name__ == "__main__":
    main()
