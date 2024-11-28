SELECT pg_size_pretty(pg_total_relation_size('email')) AS total_size;

-- Black Friday sales 2024
WITH target_emails AS (
    SELECT *
    FROM email
    WHERE concat(subject, body) ILIKE '%black friday%'
      AND date > current_date - interval '1 year' -- Adjust dynamically
      AND date < current_date
)
SELECT DISTINCT ON (sender_domain)
       concat('https://mail.google.com/mail/u/0/#inbox/', message_id) AS gmail_link,
       *,
       substring(sender FROM '@(.*)$') AS sender_domain
FROM target_emails
ORDER BY sender_domain, date DESC;