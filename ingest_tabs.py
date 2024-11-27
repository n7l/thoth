import json
from pathlib import Path
import psycopg2
from psycopg2.extras import execute_batch
from send2trash import send2trash
from database import connect_to_db


# Insert or update tabs and groups
def ingest_tabs_and_groups(json_file_path):
    file_path = Path(json_file_path)
    if not file_path.exists():
        print(f"Error: File '{json_file_path}' does not exist.")
        return

    conn = connect_to_db()
    cursor = conn.cursor()

    with file_path.open("r") as f:
        data = json.load(f)

    # Insert or update groups
    group_query = """
    INSERT INTO tab_group (name, tags)
    VALUES (%s, %s)
    ON CONFLICT (name)
    DO UPDATE SET tags = EXCLUDED.tags
    RETURNING id
    """
    group_ids = {}
    for group in data.get("groups", []):
        cursor.execute(group_query, (group["name"], group["tags"]))
        group_ids[group["name"]] = cursor.fetchone()[0]

    # Insert or update tabs
    tab_query = """
    INSERT INTO tab (tab_id, title, url, favicon_url, group_id)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (tab_id)
    DO UPDATE SET
        title = EXCLUDED.title,
        url = EXCLUDED.url,
        favicon_url = EXCLUDED.favicon_url,
        group_id = EXCLUDED.group_id
    """
    tab_data = [
        (
            tab["id"],
            tab["title"],
            tab["url"],
            tab.get("favIconUrl"),
            group_ids.get(tab.get("group")),
        )
        for tab in data.get("tabs", [])
    ]
    execute_batch(cursor, tab_query, tab_data)

    conn.commit()
    cursor.close()
    conn.close()

    send2trash(json_file_path)
    print(
        f"Ingested {len(data.get('tabs', []))} tabs into the database and moved '{json_file_path}' to the trash."
    )


# Query all tabs and their groups
def query_tabs_with_groups():
    conn = connect_to_db()
    cursor = conn.cursor()

    query = """
    SELECT t.id, t.tab_id, t.title, t.url, t.favicon_url, g.name, g.tags
    FROM tab t
    LEFT JOIN tab_group g ON t.group_id = g.id
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    for row in rows:
        print(
            f"ID: {row[0]}, Tab ID: {row[1]}, Title: {row[2]}, URL: {row[3]}, Favicon URL: {row[4]}, Group: {row[5]}, Tags: {row[6]}"
        )

    cursor.close()
    conn.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python script.py <path_to_tabs.json>")
        sys.exit(1)

    json_file_path = sys.argv[1]
    ingest_tabs_and_groups(json_file_path)

    # print("\nTabs with their groups in the database:")
    # query_tabs_with_groups()
