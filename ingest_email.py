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
TEST_MODE = False


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
                print(
                    f"Getting messages... Page: {page_token} Count: {len(response['messages'])}"
                )
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
    """Get a Message with given ID, including labels."""
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
        from email.utils import parsedate_to_datetime

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
    conn = psycopg2.connect(
        dbname="thoth",
        user="postgres",
        password="postgres",
        host="localhost",
        port=5432,
    )
    return conn


from psycopg2.extras import execute_values


def save_emails_to_db(emails):
    """Save a list of emails to the database."""
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

    email_data = [
        (
            email["message_id"],
            email["sender"],
            email["recipient"],  # Expecting a list
            email["subject"],
            email["body"],
            email["date"],
            email["labels"],  # Expecting a list
        )
        for email in emails
    ]

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
    # email_dir = BASE_DIR / "emails"
    # email_dir.mkdir(exist_ok=True)

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
