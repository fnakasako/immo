-- Core schema for activity tracking data

-- Enable SQLCipher encryption
PRAGMA key = '$$KEY$$';  -- Placeholder, will be replaced with actual key
PRAGMA cipher_page_size = 4096;  -- Optimal for most SSDs
PRAGMA kdf_iter = 64000;  -- Strong key derivation

-- Enable WAL mode for better concurrency
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

-- Core events table - unified event model
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL,           -- Unix epoch in milliseconds
    source TEXT NOT NULL,                 -- 'browser', 'os', 'health', 'manual'
    event_type TEXT NOT NULL,             -- 'page_visit', 'app_focus', 'heart_rate', etc.
    metadata TEXT NOT NULL,               -- JSON string for flexible key/value pairs
    inserted_at INTEGER NOT NULL,         -- For retention policies
    partition_key TEXT NOT NULL           -- For time-based partitioning (YYYY_MM)
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_events_timestamp 
    ON events(timestamp);

CREATE INDEX IF NOT EXISTS idx_events_source_type 
    ON events(source, event_type);

CREATE INDEX IF NOT EXISTS idx_events_partition 
    ON events(partition_key, timestamp);

-- Retention policy tracking
CREATE TABLE IF NOT EXISTS retention_policies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,                 -- Which data source this policy applies to
    retention_days INTEGER NOT NULL,      -- How many days to keep data
    summary_table TEXT,                   -- Optional table name for summarized data
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

-- Event type metadata
CREATE TABLE IF NOT EXISTS event_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    event_type TEXT NOT NULL,
    schema TEXT NOT NULL,                 -- JSON schema for metadata validation
    created_at INTEGER NOT NULL,
    UNIQUE(source, event_type)
);

-- Statistics table for quick aggregations
CREATE TABLE IF NOT EXISTS event_statistics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,                   -- YYYY-MM-DD
    source TEXT NOT NULL,
    event_type TEXT NOT NULL,
    count INTEGER NOT NULL DEFAULT 0,
    metadata TEXT,                        -- Optional JSON for source-specific stats
    updated_at INTEGER NOT NULL,
    UNIQUE(date, source, event_type)
);

-- Views for common queries
CREATE VIEW IF NOT EXISTS v_daily_activity AS
SELECT 
    date(timestamp/1000, 'unixepoch') as day,
    source,
    event_type,
    count(*) as event_count
FROM events 
GROUP BY 
    date(timestamp/1000, 'unixepoch'),
    source,
    event_type;

-- Triggers for automatic partition key
CREATE TRIGGER IF NOT EXISTS trg_events_partition_key
BEFORE INSERT ON events
BEGIN
    SELECT CASE
        WHEN NEW.partition_key IS NULL THEN
            RAISE(ABORT, 'partition_key cannot be null')
        END;
END;

-- Triggers for statistics maintenance
CREATE TRIGGER IF NOT EXISTS trg_event_statistics_insert
AFTER INSERT ON events
BEGIN
    INSERT INTO event_statistics (date, source, event_type, count, updated_at)
    VALUES (
        date(NEW.timestamp/1000, 'unixepoch'),
        NEW.source,
        NEW.event_type,
        1,
        strftime('%s', 'now')
    )
    ON CONFLICT(date, source, event_type) DO UPDATE SET
        count = count + 1,
        updated_at = strftime('%s', 'now');
END;
