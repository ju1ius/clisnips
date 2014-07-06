
-- Snippets table

CREATE TABLE IF NOT EXISTS snippets(
    title TEXT NOT NULL,
    cmd TEXT NOT NULL,
    doc TEXT,
    tag TEXT,
    created_at INTEGER DEFAULT (strftime('%s', 'now')),
    last_used_at INTEGER DEFAULT (strftime('%s', 'now')),
    usage_count INTEGER DEFAULT 0,
    ranking FLOAT DEFAULT 0.0 
);

-- Snippets search index

CREATE VIRTUAL TABLE IF NOT EXISTS snippets_index USING fts4(
    tokenize=unicode_words,
    content="snippets",
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

CREATE TRIGGER IF NOT EXISTS snippets_bu
BEFORE UPDATE ON snippets
BEGIN
    DELETE FROM snippets_index WHERE docid=OLD.rowid;
END;

CREATE TRIGGER IF NOT EXISTS snippets_bd
BEFORE DELETE ON snippets
BEGIN
    DELETE FROM snippets_index WHERE docid=OLD.rowid;
END;

CREATE TRIGGER IF NOT EXISTS snippets_au
AFTER UPDATE ON snippets
BEGIN
    -- Update Ranking
    UPDATE snippets SET ranking = rank(
        NEW.created_at,
        NEW.last_used_at,
        NEW.usage_count
    ) WHERE rowid = NEW.rowid;
    -- Update search index
    INSERT INTO snippets_index(docid, title, tag) VALUES(
        NEW.rowid, NEW.title, NEW.tag
    );
END;

CREATE TRIGGER IF NOT EXISTS snippets_ai
AFTER INSERT ON snippets
BEGIN
    -- Update Ranking
    UPDATE snippets SET ranking = rank(
        NEW.created_at,
        NEW.last_used_at,
        NEW.usage_count
    ) WHERE rowid = NEW.rowid;
    -- Update search index
    INSERT INTO snippets_index(docid, title, tag) VALUES(
        NEW.rowid, NEW.title, NEW.tag
    );
END;


-- Analyze the whole stuff
ANALYZE;
