-- Initial database migration
-- Record migration metadata
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at INTEGER NOT NULL,
    description TEXT,  -- Adding description for better tracking
    checksum TEXT     -- For verifying schema file integrity
);

-- Start transaction
BEGIN TRANSACTION;

-- Enable SQLCipher encryption first
PRAGMA key = '$$KEY$$';
PRAGMA cipher_page_size = 4096;
PRAGMA kdf_iter = 64000;

-- Enable WAL mode for better concurrency
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

-- Import core schema
.read '../schema_core.sql'

-- Import health schema
.read '../schema_health.sql'

-- Verify core infrastructure tables
SELECT 'Core infrastructure validation' as step;
SELECT count(*) as table_count
FROM sqlite_master
WHERE type='table'
AND name IN (
    'events',
    'retention_policies',
    'event_types',
    'event_statistics',
    'encryption_keys',
    'schema_migrations'
);

-- Verify marketplace and ML infrastructure
SELECT 'Marketplace and ML infrastructure validation' as step;
SELECT count(*) as table_count
FROM sqlite_master
WHERE type='table'
AND name IN (
    'data_packages',
    'content_preferences',
    'ml_models',
    'federated_updates',
    'access_logs'
);

-- Verify health-specific tables
SELECT 'Health schema validation' as step;
SELECT count(*) as table_count
FROM sqlite_master
WHERE type='table'
AND name IN (
    'health_metrics',
    'workouts',
    'sleep_sessions'
);

-- Verify all required indexes exist
SELECT 'Index validation' as step;
SELECT count(*) as index_count
FROM sqlite_master
WHERE type='index'
AND name IN (
    'idx_events_timestamp',
    'idx_events_source_type',
    'idx_events_partition',
    'idx_events_privacy_category',
    'idx_packages_anonymization',
    'idx_federated_updates_sequence'
);

-- Verify views
SELECT 'View validation' as step;
SELECT count(*) as view_count
FROM sqlite_master
WHERE type='view'
AND name IN (
    'v_daily_activity',
    'v_marketplace_metrics',
    'v_daily_health_metrics',
    'v_workout_summary'
);

-- Verify triggers
SELECT 'Trigger validation' as step;
SELECT count(*) as trigger_count
FROM sqlite_master
WHERE type='trigger'
AND name IN (
    'trg_events_partition_key',
    'trg_event_statistics_insert'
);

-- Verify column additions to events table
SELECT 'Events table enhancement validation' as step;
SELECT 
    CASE 
        WHEN COUNT(*) = 3 THEN 'Success'
        ELSE 'Failure'
    END as validation_result
FROM pragma_table_info('events')
WHERE name IN ('privacy_level', 'data_category', 'federation_eligible');

-- Record this migration with additional metadata
INSERT INTO schema_migrations (
    version,
    applied_at,
    description,
    checksum
) VALUES (
    1,
    strftime('%s', 'now'),
    'Initial schema setup including core, health, marketplace, and ML infrastructure',
    'SHA256_CHECKSUM_PLACEHOLDER'  -- Should be replaced with actual file checksum
);

-- Commit transaction
COMMIT;

-- Verify final database state
PRAGMA integrity_check;
PRAGMA foreign_key_check;