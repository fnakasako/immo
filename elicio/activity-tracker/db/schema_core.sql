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

-- 1. Privacy and Encryption Management
CREATE TABLE IF NOT EXISTS encryption_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key_id TEXT NOT NULL UNIQUE,
    key_type TEXT NOT NULL,  -- 'master', 'rotation', 'sharing'
    encryption_algorithm TEXT NOT NULL,
    key_material BLOB NOT NULL,  -- Encrypted key material
    created_at INTEGER NOT NULL,
    expires_at INTEGER,
    metadata TEXT,  -- JSON for additional properties
    UNIQUE(key_id, key_type)
);

-- 2. Data Sharing and Marketplace Support
CREATE TABLE IF NOT EXISTS data_packages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    package_id TEXT NOT NULL UNIQUE,
    creation_time INTEGER NOT NULL,
    data_categories TEXT NOT NULL,  -- JSON array of included data types
    anonymization_level TEXT NOT NULL,  -- 'full', 'partial', 'aggregated'
    encryption_key_id TEXT,
    price_model TEXT,  -- JSON for pricing rules
    access_control TEXT,  -- JSON for permitted operations
    metadata TEXT,  -- Additional package metadata
    FOREIGN KEY(encryption_key_id) REFERENCES encryption_keys(key_id)
);

-- 3. Content Feed Algorithm Support
CREATE TABLE IF NOT EXISTS content_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,  -- If multi-user support needed
    content_type TEXT NOT NULL,  -- 'article', 'product', 'social'
    preference_data TEXT NOT NULL,  -- JSON for preferences
    learning_model TEXT,  -- Reference to trained model
    last_updated INTEGER NOT NULL
);

-- 4. ML Model Management
CREATE TABLE IF NOT EXISTS ml_models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id TEXT NOT NULL UNIQUE,
    model_type TEXT NOT NULL,  -- 'recommendation', 'classification', etc.
    model_format TEXT NOT NULL,  -- 'pytorch', 'tensorflow', etc.
    model_data BLOB,  -- Serialized model
    training_metadata TEXT,  -- JSON for training params
    version TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    last_used INTEGER,
    performance_metrics TEXT  -- JSON for accuracy/performance stats
);

-- 5. Federated Learning Coordination
CREATE TABLE IF NOT EXISTS federated_updates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id TEXT NOT NULL,
    update_sequence INTEGER NOT NULL,
    update_data BLOB NOT NULL,  -- Encrypted model updates
    differential_privacy_params TEXT,  -- JSON for DP parameters
    created_at INTEGER NOT NULL,
    status TEXT NOT NULL,  -- 'pending', 'applied', 'rejected'
    FOREIGN KEY(model_id) REFERENCES ml_models(model_id)
);

-- 6. Enhanced Event Categorization
ALTER TABLE events ADD COLUMN IF NOT EXISTS privacy_level TEXT NOT NULL DEFAULT 'standard';
ALTER TABLE events ADD COLUMN IF NOT EXISTS data_category TEXT NOT NULL DEFAULT 'general';
ALTER TABLE events ADD COLUMN IF NOT EXISTS federation_eligible BOOLEAN NOT NULL DEFAULT FALSE;

-- 7. Access Control and Audit
CREATE TABLE IF NOT EXISTS access_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER,
    package_id TEXT,
    access_time INTEGER NOT NULL,
    access_type TEXT NOT NULL,  -- 'read', 'export', 'delete'
    requester TEXT NOT NULL,  -- Identity of accessing entity
    purpose TEXT,  -- Reason for access
    FOREIGN KEY(event_id) REFERENCES events(id),
    FOREIGN KEY(package_id) REFERENCES data_packages(package_id)
);

-- 8. Views for Marketplace Analytics
CREATE VIEW IF NOT EXISTS v_marketplace_metrics AS
SELECT 
    dp.package_id,
    dp.data_categories,
    dp.anonymization_level,
    COUNT(DISTINCT al.requester) as unique_accessors,
    COUNT(al.id) as total_accesses,
    MAX(al.access_time) as last_accessed
FROM data_packages dp
LEFT JOIN access_logs al ON dp.package_id = al.package_id
GROUP BY dp.package_id;

-- 9. Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_events_privacy_category 
    ON events(privacy_level, data_category);
    
CREATE INDEX IF NOT EXISTS idx_packages_anonymization 
    ON data_packages(anonymization_level, creation_time);

CREATE INDEX IF NOT EXISTS idx_federated_updates_sequence 
    ON federated_updates(model_id, update_sequence);

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
