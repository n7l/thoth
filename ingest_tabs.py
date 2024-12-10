import json
import subprocess
from datetime import datetime
from pathlib import Path

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


def parse_file(file_path):
    file_path = Path(file_path)
    with file_path.open("r") as f:
        content = f.read()

    try:
        # Attempt to parse as JSON
        data = json.loads(content)
        if isinstance(data, dict) and "tabs" in data:
            # JSON with tabs and groups
            saved_at = data.get("timestamp")
            return data.get("groups", []), data["tabs"], saved_at
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
        files = list(Path(config.TABS_LOCATION).expanduser().glob("tabs*.json"))
        if not files:
            print(f"No matching files found in {config.TABS_LOCATION}")
            return
        # files.sort()  # Sort to process files in order (optional)
    else:
        files = [file_path]

    for file in files:
        path = Path(file)
        if not path.exists():
            print(f"File does not exist: {path}")
            continue

        print(f"Processing file: {path}")
        groups, tabs, saved_at = parse_file(path)

        conn = connect_to_db()
        cursor = conn.cursor()
        # Add groups
        group_ids = {}
        for group in groups:
            urls = [
                tab.get("url") for tab in tabs if tab.get("group") == group.get("name")
            ]
            # print("-" * 10)
            # print(group)
            # print(urls)
            group_query = """--sql
            INSERT INTO tab_group (name, tags, url_hash, saved_at)
            VALUES (%s, %s, calculate_group_hash(%s), %s)
            RETURNING id
            """
            cursor.execute(
                group_query, (group["name"], group.get("tags", []), urls, saved_at)
            )
            group_ids[group["name"]] = cursor.fetchone()[0]

        # Add tabs and associate with groups
        for tab in tabs:
            tab_query = """ -- sql
            INSERT INTO tab (title, url, favicon_url)
            VALUES (%s, %s, %s)
            ON CONFLICT (url)
            DO UPDATE SET
                title = EXCLUDED.title,
                favicon_url = EXCLUDED.favicon_url
            RETURNING id
            """
            cursor.execute(tab_query, (tab["title"], tab["url"], tab.get("favIconUrl")))
            tab_id = cursor.fetchone()[0]

            # Associate tab with groups
            group_name = tab.get("group")
            if group_name in group_ids:
                tab_group_tab_query = """
                INSERT INTO tab_group_tab (tab_id, group_id, position)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING
                """
                position = tabs.index(tab)  # Preserve the order from JSON
                cursor.execute(
                    tab_group_tab_query, (tab_id, group_ids[group_name], position)
                )

        conn.commit()
        cursor.close()
        conn.close()

        if not config.TEST_MODE:
            send2trash(str(path))

        print(f"Ingested {len(tabs)} tabs and moved '{path}' to the trash.")


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


def open_tab_group(group_name=None, tags=None, merge=False):
    conn = connect_to_db()
    cursor = conn.cursor()

    if tags:
        print("-" * 10 + "\nQuerying by tags is a work in progress\n" + "-" * 10)
        formatted_tags = "ARRAY" + str(tags)
        # Get all tab groups with a case-insensitive match for all tags
        query = f"""
        SELECT DISTINCT url
        FROM combined_tags_per_url
        WHERE tags @> {formatted_tags}
        """

        print(query)
        # cursor.execute(query, (tags,))

        # print(cursor.mogrify(query, (formatted_tags,)).decode('utf-8'))

        # cursor.execute(query, (formatted_tags,))
        cursor.execute(query)

    else:

        # Adjust the query based on the `merge` parameter
        if merge:
            # Get all tab groups with a case-insensitive match for the name
            query = """
            SELECT t.url
            FROM tab t
            JOIN tab_group_tab tgt ON t.id = tgt.tab_id
            WHERE tgt.group_id IN (
                SELECT id
                FROM tab_group g
                WHERE LOWER(g.name) = LOWER(%s)
            )
            ORDER BY tgt.position ASC
            """
            cursor.execute(query, (group_name,))
        else:
            # Get only the most recent tab group with a case-insensitive match for the name
            query = """
            SELECT t.url
            FROM tab t
            JOIN tab_group_tab tgt ON t.id = tgt.tab_id
            WHERE tgt.group_id = (
                SELECT id
                FROM tab_group g
                WHERE LOWER(g.name) = LOWER(%s)
                ORDER BY g.saved_at DESC NULLS LAST
                LIMIT 1
            )
            ORDER BY tgt.position ASC
            """
            cursor.execute(query, (group_name,))

    rows = cursor.fetchall()

    if not rows:
        print(f"No tabs found for group '{group_name}' and tags {tags}.")
        return

    print(f"Opening tabs for group '{group_name}':")
    open_urls([row[0] for row in rows])

    cursor.close()
    conn.close()


if __name__ == "__main__":
    config.TEST_MODE = True
    config.TABS_LOCATION = "~/Downloads/tabs"

    ingest_file()
