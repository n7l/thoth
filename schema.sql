-- CREATE DATABASE thoth;

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


-- Drop existing tables if recreating the database
DROP TABLE IF EXISTS tab_group_tab CASCADE;
DROP TABLE IF EXISTS tab_group CASCADE;
DROP TABLE IF EXISTS tab CASCADE;

CREATE TABLE tab (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    favicon_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tab_group (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    tags TEXT[],
    saved_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, -- Timestamp from the Chrome extension
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tab_group_tab (
    id SERIAL PRIMARY KEY,
    tab_id INT NOT NULL REFERENCES tab(id) ON DELETE CASCADE,
    group_id INT NOT NULL REFERENCES tab_group(id) ON DELETE CASCADE,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- When the tab was added to this group
    UNIQUE(tab_id, group_id)
);

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_updated_at_tab
BEFORE UPDATE ON tab
FOR EACH ROW
EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER set_updated_at_tab_group
BEFORE UPDATE ON tab_group
FOR EACH ROW
EXECUTE FUNCTION update_updated_at();

CREATE OR REPLACE VIEW tab_group_with_combined_tags AS
SELECT
    t.id,
    array_agg(DISTINCT tag) AS tags
FROM tab_group t,
LATERAL (
    SELECT unnest(t.tags) AS tag
    UNION
    SELECT unnest(regexp_split_to_array(t.name, '\s+')) AS tag
) combined_tags
GROUP BY t.id;