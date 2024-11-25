-- CREATE DATABASE thoth;

-- Drop the table if it already exists
DROP TABLE IF EXISTS emails;

-- Create the email table
CREATE TABLE email (
    id SERIAL PRIMARY KEY,             -- Unique ID for the email (auto-incremented)
    message_id TEXT UNIQUE NOT NULL,   -- Unique message identifier from Gmail
    sender TEXT,                       -- Email sender
    recipient TEXT[],                  -- Array of recipients (To)
    subject TEXT,                      -- Subject of the email
    body TEXT,                         -- Email body
    date TIMESTAMP WITH TIME ZONE,     -- Date and time of the email with timezone
    labels TEXT[]                      -- Labels associated with the email (array)
);


SELECT pg_size_pretty(pg_total_relation_size('email')) AS total_size;