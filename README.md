# thoth

https://en.wikipedia.org/wiki/Thoth

Thoth was the Egyptian God of wisdom, knowledge, writing, and other things. This is meant to be a central location for all my personal information.

This is very hacked together and a work in progress

Requires MacOS and works with Chrome only right now

Also
```sh
brew install uv
```

## Installation

Create a postgres database that's locally accessible. I use https://postgresapp.com/

The expected credentials are in `./database.py`. It uses port 5454 to hopefully avoid conflict with your other projects ;)

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

## Optional

Install fzf for interactive tab group opening

```sh
brew install fzf
source aliases.sh
tabs
```



## Examples

Watch for new files

```sh
uv run python thoth.py watch
```

Open the 10 most recently updated tabs

```sh
uv run python thoth.py query 'select url from tab order by updated_at desc limit 10'
```

Open 3 random youtube videos you've saved

```sh
uv run python thoth.py query "select url from tab where url like '%youtube.com/watch%' order by random() limit 3"
```

## TODO

- Treat youtube links with different time stamps as the same url?
- Add a mechanism for "removing" tabs or a weight algorithm that discounts tabs that have been removed from later versions of the same group (meaning with the same name)


