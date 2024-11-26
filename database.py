import psycopg2

DB_CONFIG = {
    "dbname": "thoth",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": 5432,
}


def connect_to_db():
    """Connect to the PostgreSQL database."""
    return psycopg2.connect(**DB_CONFIG)
