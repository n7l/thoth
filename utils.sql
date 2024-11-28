SELECT pg_size_pretty(pg_total_relation_size('email')) AS total_size;

-- Black Friday sales
WITH params AS (
    SELECT
        '2024'::INTEGER AS target_year
),
target_emails AS (
    SELECT *
    FROM email, params
    WHERE concat(subject, body) ILIKE '%black friday%'
      AND date >= make_date('2024'::INTEGER, 1, 1)
      AND date <= make_date('2024'::INTEGER, 12, 31)
)
SELECT DISTINCT ON (sender_domain)
       concat('https://mail.google.com/mail/u/0/#inbox/', message_id) AS gmail_link,
       *,
       substring(sender FROM '@(.*)$') AS sender_domain
FROM target_emails
ORDER BY sender_domain, date DESC;