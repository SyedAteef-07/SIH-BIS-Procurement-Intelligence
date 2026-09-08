CREATE TABLE IF NOT EXISTS standards (
    number TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    scope TEXT NOT NULL,
    edition TEXT NOT NULL,
    status TEXT NOT NULL,
    keywords JSONB NOT NULL DEFAULT '[]',
    related JSONB NOT NULL DEFAULT '[]',
    certification TEXT,
    requirements JSONB NOT NULL DEFAULT '[]',
    source_url TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS standards_title_search
    ON standards USING GIN (to_tsvector('english', title || ' ' || scope));
