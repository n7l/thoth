import fire
from ingest_tabs import ingest_file, open_tab_group


class Client:

    def ingest(self, file_path=None):
        return ingest_file(file_path)

    def open(self, group_name):
        return open_tab_group(group_name)


if __name__ == "__main__":
    fire.Fire(Client)
