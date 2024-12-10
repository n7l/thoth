from datetime import datetime, timedelta

import fire

from database import execute_query, search_emails
from ingest_email import ingest_emails
from ingest_tabs import ingest_file, open_tab_group, open_urls


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


if __name__ == "__main__":
    fire.Fire(Client)
