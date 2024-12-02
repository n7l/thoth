# thoth

This is very hacked together and a work in progress

Requires MacOS and works with Chrome only right now

Also
```sh
brew install uv
```

## Installation

Create a postgres database that's locally accessible. I use https://postgresapp.com/

The expected credentials are in `./database.py`

Run the sql in `./schema.sql` to create the schema
Note the commented out `CREATE DATABASE` command which you can run or otherwise create a `thoth` database

Load the unpacked extension at `./chrome_extension/`

https://developer.chrome.com/docs/extensions/get-started/tutorial/hello-world#load-unpacked


Install python dependencies

```sh
uv sync
uv run pre-commit install
```

Save some tabs with a name e.g. "work"

Ingest the tabs and reopen them by tab_group name

Note that this will ingest all files matching `~/Downloads/tabs*.json` and move them to the trash

```sh
uv run python thoth.py ingest
uv run python thoth.py open work
```

TODO: a whole heck of a lot. Feel free to add things here

- Open tabs by tag
- Auto-associate tabs with tags by domain name matches, etc
- Blacklist urls or domains so they aren't saved and/or aren't opened

