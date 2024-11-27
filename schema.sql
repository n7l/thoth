-- CREATE DATABASE thoth;

DROP TABLE IF EXISTS emails;
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


DROP TABLE IF EXISTS tab;
DROP TABLE IF EXISTS tab_group;

CREATE TABLE tab_group (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    tags TEXT[] NOT NULL
);

CREATE TABLE tab (
    id SERIAL PRIMARY KEY,
    tab_id INTEGER UNIQUE NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    favicon_url TEXT,
    group_id INTEGER REFERENCES tab_group(id) ON DELETE SET NULL
);