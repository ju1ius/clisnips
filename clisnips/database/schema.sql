
-- Snippets table

CREATE TABLE IF NOT EXISTS snippets(
    -- Statistics
    created_at INTEGER DEFAULT (strftime('%s', 'now')),
    last_used_at INTEGER DEFAULT (strftime('%s', 'now')),
    usage_count INTEGER DEFAULT 0,
    ranking FLOAT DEFAULT 0.0,
    -- Contents
    title TEXT NOT NULL,
    cmd TEXT NOT NULL,
    tag TEXT,
    doc TEXT
);

-- Snippets search index

CREATE VIRTUAL TABLE IF NOT EXISTS snippets_index USING fts5(
    tokenize = "unicode61 remove_diacritics 2 tokenchars '-_'",
    content = "snippets",
    title,
    tag
);

-- Indexes for fast sorting

CREATE INDEX IF NOT EXISTS snip_created_idx ON snippets(created_at DESC);
CREATE INDEX IF NOT EXISTS snip_last_used_idx ON snippets(last_used_at DESC);
CREATE INDEX IF NOT EXISTS snip_usage_idx ON snippets(usage_count DESC);
CREATE INDEX IF NOT EXISTS snip_ranking_idx ON snippets(ranking DESC);

--
-- Triggers to keep snippets table and index in sync,
-- and to keep track of command usage and ranking.
--

-- drops triggers for old versions (we'll need a migration system at some point)
DROP TRIGGER IF EXISTS snippets_after_insert;
DROP TRIGGER IF EXISTS snippets_after_update;

CREATE TRIGGER IF NOT EXISTS snippets_after_insert
AFTER INSERT ON snippets
BEGIN
    INSERT INTO snippets_index(rowid, title, tag) VALUES(NEW.rowid, NEW.title, NEW.tag);
END;


CREATE TRIGGER IF NOT EXISTS snippets_before_delete
BEFORE DELETE ON snippets
BEGIN
    DELETE FROM snippets_index WHERE rowid=OLD.rowid;
END;


CREATE TRIGGER IF NOT EXISTS snippets_before_update
BEFORE UPDATE ON snippets
BEGIN
    DELETE FROM snippets_index WHERE rowid=OLD.rowid;
END;

CREATE TRIGGER IF NOT EXISTS snippets_after_update
AFTER UPDATE ON snippets
BEGIN
    INSERT INTO snippets_index(rowid, title, tag) VALUES(NEW.rowid, NEW.title, NEW.tag);
END;

-- Analyze the whole stuff
ANALYZE;
