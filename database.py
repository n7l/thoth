import psycopg2

DB_CONFIG = {
    "dbname": "thoth",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": 5454,
}


def connect_to_db():
    """Connect to the PostgreSQL database."""
    return psycopg2.connect(**DB_CONFIG)


def execute_query(query, params=None, fetch=True):
    """Execute a SQL query and optionally fetch results."""
    conn = connect_to_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            if fetch:
                return cursor.fetchall()
            conn.commit()
    finally:
        conn.close()


def search_emails(search_term, target_year):
    """Search for emails by term and year."""
    query = """
    WITH target_emails AS (
        SELECT *
        FROM email
        WHERE concat(subject, body) ILIKE %(search_term)s
          AND date >= make_date(%(target_year)s::INTEGER, 1, 1)
          AND date <= make_date(%(target_year)s::INTEGER, 12, 31)
    )
    SELECT DISTINCT ON (sender_domain)
           concat('https://mail.google.com/mail/u/0/#inbox/', message_id) AS gmail_link,
           *,
           substring(sender FROM '@(.*)$') AS sender_domain
    FROM target_emails
    ORDER BY sender_domain, date DESC;
    """

    params = {
        "search_term": f"%{search_term}%",
        "target_year": target_year,
    }

    results = execute_query(query, params)
    for row in results:
        print(row)
