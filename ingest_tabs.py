import glob
import json
import subprocess
from pathlib import Path

from psycopg2.extras import execute_batch
from send2trash import send2trash

import config
from database import connect_to_db


def run_applescript(applescript):
    return str(subprocess.check_output(f"osascript -e '{applescript}'", shell=True))


def open_urls(urls):
    browsers = dict(
        chrome="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    )
    subprocess.run([browsers[config.BROWSER], "--new-window"] + urls)

    run_applescript(
        """
    tell application "Google Chrome"
        activate
    end tell
    """
    )


# Function to parse file content
def parse_file(file_path):
    file_path = Path(file_path)
    with file_path.open("r") as f:
        content = f.read()

    try:
        # Attempt to parse as JSON
        data = json.loads(content)
        if isinstance(data, dict) and "tabs" in data:
            # JSON with tabs and groups
            return data.get("groups", []), data["tabs"]
        elif isinstance(data, list):
            # JSON with a list of URLs
            return [], [
                {"id": i + 1, "title": url, "url": url} for i, url in enumerate(data)
            ]
    except json.JSONDecodeError:
        pass

    # Assume plain text format (list of URLs)
    urls = content.strip().splitlines()
    return [], [{"id": i + 1, "title": url, "url": url} for i, url in enumerate(urls)]


def ingest_file(file_path=None):
    # If no file_path is specified, find all matching files in Downloads
    if file_path is None:
        files = glob.glob("~/Downloads/tabs*.json")
        if not files:
            print("No matching files found in ~/Downloads/")
            return
        files.sort()  # Sort to process files in order (optional)
    else:
        files = [file_path]

    for file in files:
        path = Path(file)
        if not path.exists():
            print(f"File does not exist: {path}")
            continue

        print(f"Processing file: {path}")
        groups, tabs = parse_file(path)

        # Connect to the database and process tabs/groups
        conn = connect_to_db()
        cursor = conn.cursor()

        # Insert or update groups
        group_ids = {}
        if groups:
            group_query = """
            INSERT INTO tab_group (name, tags)
            VALUES (%s, %s)
            ON CONFLICT (name)
            DO UPDATE SET tags = EXCLUDED.tags
            RETURNING id
            """
            for group in groups:
                cursor.execute(group_query, (group["name"], group.get("tags", [])))
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
            for tab in tabs
        ]
        execute_batch(cursor, tab_query, tab_data)

        conn.commit()
        cursor.close()
        conn.close()

        if not config.TEST_MODE:
            send2trash(str(file_path))

        print(f"Ingested {len(tabs)} tabs and moved '{path}' to the trash.")


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


def open_tab_group(group_name):
    conn = connect_to_db()
    cursor = conn.cursor()

    query = """
    SELECT t.url
    FROM tab t
    JOIN tab_group g ON t.group_id = g.id
    WHERE g.name = %s
    """
    cursor.execute(query, (group_name,))
    rows = cursor.fetchall()

    if not rows:
        print(f"No tabs found for group '{group_name}'.")
        return

    print(f"Opening tabs for group '{group_name}':")
    open_urls([row[0] for row in rows])

    cursor.close()
    conn.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python script.py <path_to_tabs.json>")
        sys.exit(1)

    file_path = sys.argv[1]
    ingest_file(file_path)

    # print("\nTabs with their groups in the database:")
    # query_tabs_with_groups()

    open_tab_group("music")
