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


-- Drop existing tables if recreating the database
DROP TABLE IF EXISTS tab_group_tab CASCADE;
DROP TABLE IF EXISTS tab_group CASCADE;
DROP TABLE IF EXISTS tab CASCADE;

-- Create `tab` table
CREATE TABLE tab (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    favicon_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create `tab_group` table
CREATE TABLE tab_group (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    tags TEXT[],
    saved_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, -- Timestamp from the Chrome extension
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create `tab_group_tab` table to support many-to-many relationships
CREATE TABLE tab_group_tab (
    id SERIAL PRIMARY KEY,
    tab_id INT NOT NULL REFERENCES tab(id) ON DELETE CASCADE,
    group_id INT NOT NULL REFERENCES tab_group(id) ON DELETE CASCADE,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- When the tab was added to this group
    UNIQUE(tab_id, group_id)
);

-- Create a function to update `updated_at` column
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add triggers for the `tab` table
CREATE TRIGGER set_updated_at_tab
BEFORE UPDATE ON tab
FOR EACH ROW
EXECUTE FUNCTION update_updated_at();

-- Add triggers for the `tab_group` table
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