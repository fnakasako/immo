-- Initial database migration

-- Record migration metadata
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at INTEGER NOT NULL
);

-- Start transaction
BEGIN TRANSACTION;

-- Import core schema
.read '../schema_core.sql'

-- Import health schema
.read '../schema_health.sql'

-- Record this migration
INSERT INTO schema_migrations (version, applied_at) 
VALUES (1, strftime('%s', 'now'));

-- Commit transaction
COMMIT;

-- Verify tables were created
SELECT 'Core schema validation' as step;
SELECT count(*) as table_count 
FROM sqlite_master 
WHERE type='table' 
AND name IN ('events', 'retention_policies', 'event_types', 'event_statistics');

SELECT 'Health schema validation' as step;
SELECT count(*) as table_count 
FROM sqlite_master 
WHERE type='table' 
AND name IN ('health_metrics', 'workouts', 'sleep_sessions');

-- Verify indexes
SELECT 'Index validation' as step;
SELECT count(*) as index_count 
FROM sqlite_master 
WHERE type='index' 
AND name LIKE 'idx_%';

-- Verify views
SELECT 'View validation' as step;
SELECT count(*) as view_count 
FROM sqlite_master 
WHERE type='view' 
AND name LIKE 'v_%';
