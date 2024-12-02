from datetime import datetime, timedelta

import fire

from ingest_email import black_friday, ingest_emails
from ingest_tabs import ingest_file, open_tab_group


class Client:

    def ingest(self, file_path=None):
        return ingest_file(file_path)

    def ingest_email(self, since=None, days=None):
        days = days or 1
        if since is None:
            since_date = datetime.today() - timedelta(days=days)
            since = since_date.strftime("%Y-%m-%d")
        return ingest_emails(since)

    def open(self, group_name):
        return open_tab_group(group_name)

    def black_friday(self):
        return black_friday()


if __name__ == "__main__":
    fire.Fire(Client)
