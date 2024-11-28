SELECT pg_size_pretty(pg_total_relation_size('email')) AS total_size;

-- Black Friday sales 2024
select distinct on (sender_domain)
    concat('https://mail.google.com/mail/u/0/#inbox/', message_id),
    *,
    substring(sender from '@(.*)$') AS sender_domain
from email
where concat(subject, body) ilike '%black friday%'
and date > '2023-11-01'
and date < '2024-11-01'
order by sender_domain, date desc;
