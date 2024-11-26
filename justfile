tabs:
    uv run python ingest_tabs.py ~/Downloads/tabs.json


models:
    uv run sqlacodegen postgresql+psycopg2://postgres:postgres@localhost:5432/thoth > models.py