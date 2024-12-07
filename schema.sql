CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- CREATE DATABASE thoth;

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
    url_hash TEXT UNIQUE NOT NULL,
    saved_at TIMESTAMP, -- Timestamp from the Chrome extension
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


-- Group hash
DROP FUNCTION IF EXISTS calculate_group_hash;
CREATE OR REPLACE FUNCTION calculate_group_hash(group_id_ INT) RETURNS TEXT AS $$
DECLARE
    sorted_urls TEXT[];
    concatenated_urls TEXT;
BEGIN
    -- Fetch and sort the URLs
    SELECT ARRAY_AGG(url ORDER BY url)
    INTO sorted_urls
    FROM tab
    JOIN tab_group_tab tgt ON tab.id = tgt.tab_id
    WHERE tgt.group_id = group_id_;

    -- Concatenate the sorted URLs into a single string
    concatenated_urls := array_to_string(sorted_urls, '');

    -- Compute the hash
    RETURN encode(digest(concatenated_urls, 'sha256'), 'hex');
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION enforce_group_hash() RETURNS TRIGGER AS $$
BEGIN
    -- Calculate the hash for the group
    NEW.url_hash := calculate_group_hash(NEW.id);

    IF NEW.url_hash IS NULL THEN
        -- NEW.url_hash = NEW.id;
        RAISE EXCEPTION 'URL hash could not be calculated for group ID %', NEW.id;
    END IF;

    -- Ensure the hash is unique
    IF EXISTS (SELECT 1 FROM tab_group WHERE url_hash = NEW.url_hash AND id != NEW.id) THEN
        RAISE EXCEPTION 'A tab group with the same URLs already exists';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER set_url_hash
AFTER INSERT OR UPDATE ON tab_group
FOR EACH ROW
EXECUTE FUNCTION enforce_group_hash();

-- Views

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