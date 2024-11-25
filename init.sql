CREATE DATABASE thoth;


CREATE TABLE emails (
    id SERIAL PRIMARY KEY,
    message_id TEXT UNIQUE NOT NULL,
    sender TEXT,
    subject TEXT,
    body TEXT,
    date TIMESTAMP,
    labels TEXT[]
);