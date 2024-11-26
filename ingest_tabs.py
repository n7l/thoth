import json
import psycopg2
from psycopg2.extras import execute_batch
from send2trash import send2trash

# Database configuration
DB_CONFIG = {
    "dbname": "thoth",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": 5432,
}


# Insert or update tabs in the database
def ingest_tabs(json_file_path):
    # Connect to the database
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Open and parse the JSON file
    with open(json_file_path, "r") as f:
        tabs = json.load(f)

    # Insert or update records
    insert_query = """
    INSERT INTO tab (tab_id, title, url, favicon_url)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (tab_id)
    DO UPDATE SET
        title = EXCLUDED.title,
        url = EXCLUDED.url,
        favicon_url = EXCLUDED.favicon_url
    """
    tab_data = [
        (tab["id"], tab["title"], tab["url"], tab.get("favIconUrl")) for tab in tabs
    ]

    # Use execute_batch for efficient batch inserts
    execute_batch(cursor, insert_query, tab_data)

    # Commit and close
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Ingested {len(tabs)} tabs into the database.")

    send2trash(json_file_path)

    print(f"Moved {json_file_path} to the trash.")


# Query all tabs from the database
def query_tabs():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Fetch all tabs
    cursor.execute("SELECT id, tab_id, title, url, favicon_url FROM tab")
    rows = cursor.fetchall()
    for row in rows:
        print(
            f"ID: {row[0]}, Tab ID: {row[1]}, Title: {row[2]}, URL: {row[3]}, Favicon URL: {row[4]}"
        )

    cursor.close()
    conn.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python script.py <path_to_tabs.json>")
        sys.exit(1)

    json_file_path = sys.argv[1]
    ingest_tabs(json_file_path)

    # print("\nTabs in the database:")
    # query_tabs()
