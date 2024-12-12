import fnmatch
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

import fire
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

import config
from database import execute_query, search_emails
from ingest_email import ingest_emails
from ingest_tabs import ingest_file, open_tab_group, open_urls


class DownloadEventHandler(FileSystemEventHandler):
    def __init__(self, client, ingest_directory):
        self.client = client
        self.ingest_directory = os.path.expanduser(ingest_directory)

    def on_created(self, event):
        if event.is_directory:
            return

        file_path = event.src_path
        filename = os.path.basename(file_path)

        if fnmatch.fnmatch(filename, "tabs*.json"):
            print(f"New file detected: {file_path}")
            self.client.ingest(file_path)


class Client:

    def ingest(self, file_path=None):
        return ingest_file(file_path)

    def ingest_email(self, since=None, days=1):
        if since is None:
            since_date = datetime.today() - timedelta(days=days)
            since = since_date.strftime("%Y-%m-%d")
        return ingest_emails(since)

    def open(self, group_name=None, tags=None, merge=False):
        return open_tab_group(group_name, tags, merge)

    def black_friday(self):
        return search_emails("black friday", 2024)

    def names(self):
        results = execute_query("select distinct name from tab_group;")
        print("\n".join([row[0] for row in results]))

    def tags(self):
        results = execute_query(
            "SELECT DISTINCT unnest(tags) AS unique_tag FROM tab_group_with_combined_tags;"
        )
        print("\n".join([row[0] for row in results]))

    def query(self, sql):
        results = execute_query(sql)
        print(results)
        open_urls([row[0] for row in results])

    def watch(self, directory=None):
        self.ingest()
        if not directory:
            directory = Path(config.TABS_LOCATION)
        directory = directory.expanduser()
        if not directory.is_dir():
            raise ValueError(f"Directory {directory} does not exist.")

        event_handler = DownloadEventHandler(client=self, ingest_directory=directory)
        observer = Observer()
        observer.schedule(event_handler, directory, recursive=False)
        observer.start()

        print(f"Watching {directory} for new files. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

    def load_file(self, file_path):
        file_path = os.path.expanduser(file_path)
        if not os.path.isfile(file_path):
            raise ValueError(f"File {file_path} does not exist.")

        with open(file_path, "r") as f:
            data = json.load(f)

        urls = [t.get("url") for t in data.get("tabs", [])]
        if not urls:
            print("No tabs found in the provided file.")
            return

        open_urls(urls)
        print(f"Opened {len(urls)} tabs from {file_path}")


if __name__ == "__main__":
    fire.Fire(Client)
