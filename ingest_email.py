import base64
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from psycopg2.extras import execute_values
import psycopg2
from email.utils import parsedate_to_datetime

# Define the scope
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Define paths for credentials and tokens
BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_PATH = BASE_DIR / "credentials.json"
TOKEN_PATH = BASE_DIR / "token.json"

# Database connection details
DB_CONFIG = {
    "dbname": "thoth",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": 5432,
}


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


def list_messages(service, user_id="me", page_token=None, since_date=None):
    """List messages incrementally, optionally filtered by a since_date."""
    try:
        query = f"after:{since_date}" if since_date else None
        response = (
            service.users()
            .messages()
            .list(userId=user_id, q=query, pageToken=page_token)
            .execute()
        )

        messages = response.get("messages", [])
        next_page_token = response.get("nextPageToken", None)
        return messages, next_page_token
    except Exception as error:
        print(f"An error occurred: {error}")
        return None, None


def get_message(service, msg_id, user_id="me"):
    """Get a message with its details."""
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
        recipient = next(
            (header["value"] for header in headers if header["name"] == "To"), None
        )
        date = next(
            (header["value"] for header in headers if header["name"] == "Date"), None
        )

        # Convert date to datetime object
        if date:
            date = parsedate_to_datetime(date)

        # Email body
        body = "No body available"
        if "parts" in payload:
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain" and "data" in part["body"]:
                    body = base64.urlsafe_b64decode(part["body"]["data"]).decode(
                        "utf-8"
                    )
        elif "body" in payload and "data" in payload["body"]:
            body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")

        # Email labels
        labels = message.get("labelIds", [])

        return {
            "message_id": msg_id,
            "sender": sender,
            "recipient": recipient.split(", ") if recipient else [],
            "subject": subject,
            "body": body,
            "date": date,
            "labels": labels,
        }
    except Exception as error:
        print(f"An error occurred: {error}")
        return None


def connect_to_db():
    """Connect to the PostgreSQL database."""
    return psycopg2.connect(**DB_CONFIG)


def save_emails_to_db_in_chunks(emails, chunk_size=100):
    """Save a list of emails to the database in manageable chunks."""
    conn = connect_to_db()
    cursor = conn.cursor()

    query = """
    INSERT INTO email (message_id, sender, recipient, subject, body, date, labels)
    VALUES %s
    ON CONFLICT (message_id) DO UPDATE
    SET sender = EXCLUDED.sender,
        recipient = EXCLUDED.recipient,
        subject = EXCLUDED.subject,
        body = EXCLUDED.body,
        date = EXCLUDED.date,
        labels = EXCLUDED.labels;
    """

    for i in range(0, len(emails), chunk_size):
        chunk = emails[i : i + chunk_size]
        email_data = [
            (
                email["message_id"],
                email["sender"],
                email["recipient"],
                email["subject"],
                email["body"],
                email["date"],
                email["labels"],
            )
            for email in chunk
        ]
        execute_values(cursor, query, email_data)
        conn.commit()
        print(f"Saved {min(i + chunk_size, len(emails))} of {len(emails)} emails.")
    cursor.close()
    conn.close()


def main(since_date=None):
    """Main function to fetch and save emails incrementally."""
    service = authenticate()
    next_page_token = None

    while True:
        print(f"Fetching emails... (since {since_date})")
        messages, next_page_token = list_messages(
            service, page_token=next_page_token, since_date=since_date
        )
        if not messages:
            print("No more messages to process.")
            break

        emails = []
        for msg in messages:
            email_data = get_message(service, msg["id"])
            if email_data:
                emails.append(email_data)

        print(emails[0]["date"])
        save_emails_to_db_in_chunks(emails)

        if not next_page_token:
            print("All emails processed.")
            break


if __name__ == "__main__":
    # Specify a date in YYYY-MM-DD format to filter emails
    SINCE_DATE = "1990-01-01"  # Example date
    main(since_date=SINCE_DATE)
