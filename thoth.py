import fnmatch
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


if __name__ == "__main__":
    fire.Fire(Client)
