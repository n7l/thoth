DROP TABLE IF EXISTS emails;
CREATE TABLE email (
    id SERIAL PRIMARY KEY,
    message_id TEXT UNIQUE NOT NULL,   -- Unique message identifier from Gmail
    sender TEXT,
    recipient TEXT[],
    subject TEXT,
    body TEXT,
    date TIMESTAMP WITH TIME ZONE,
    labels TEXT[]
);
