use anyhow::{Context, Result};
use rusqlite::Connection;
use std::path::Path;
use tracing::info;

// Initialize database with encryption and run migrations
pub(crate) fn init_database(db_path: &str, encryption_key: &str) -> Result<Connection> {
    let is_new_db = !Path::new(db_path).exists();
    
    // Open or create encrypted database
    let conn = Connection::open(db_path)
        .context("Failed to open database")?;

    // Configure encryption
    conn.execute_batch(&format!(
        "PRAGMA key = '{}';
         PRAGMA cipher_page_size = 4096;
         PRAGMA kdf_iter = 64000;
         PRAGMA journal_mode = WAL;
         PRAGMA synchronous = NORMAL;",
        encryption_key
    )).context("Failed to configure encryption")?;

    if is_new_db {
        info!("Creating new database at {}", db_path);
        run_migrations(&conn)?;
    } else {
        info!("Using existing database at {}", db_path);
        verify_schema(&conn)?;
    }

    Ok(conn)
}

// Run database migrations
fn run_migrations(conn: &Connection) -> Result<()> {
    // Start transaction for atomic migration
    let tx = conn.transaction()?;

    // Create migrations table if it doesn't exist
    tx.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_at INTEGER NOT NULL
        )",
        [],
    )?;

    // Read and execute migration files
    let migration_sql = include_str!("../../../db/migrations/001_initial.sql");
    tx.execute_batch(migration_sql)?;

    tx.commit()?;
    info!("Database migrations completed successfully");
    Ok(())
}

// Verify database schema matches expected structure
fn verify_schema(conn: &Connection) -> Result<()> {
    // Check core tables exist
    let core_tables = [
        "events",
        "retention_policies",
        "event_types",
        "event_statistics",
    ];

    for table in core_tables.iter() {
        conn.query_row(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            [table],
            |_| Ok(()),
        ).context(format!("Core table '{}' not found", table))?;
    }

    // Check health tables exist
    let health_tables = [
        "health_metrics",
        "workouts",
        "sleep_sessions",
    ];

    for table in health_tables.iter() {
        conn.query_row(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            [table],
            |_| Ok(()),
        ).context(format!("Health table '{}' not found", table))?;
    }

    // Verify indexes exist
    let required_indexes = [
        "idx_events_timestamp",
        "idx_events_source_type",
        "idx_events_partition",
        "idx_health_metrics_event",
        "idx_health_metrics_type_time",
        "idx_workouts_event",
        "idx_workouts_type_time",
        "idx_sleep_sessions_event",
        "idx_sleep_sessions_time",
    ];

    for index in required_indexes.iter() {
        conn.query_row(
            "SELECT 1 FROM sqlite_master WHERE type='index' AND name=?",
            [index],
            |_| Ok(()),
        ).context(format!("Required index '{}' not found", index))?;
    }

    // Verify views exist
    let required_views = [
        "v_daily_activity",
        "v_daily_health_metrics",
        "v_workout_summary",
    ];

    for view in required_views.iter() {
        conn.query_row(
            "SELECT 1 FROM sqlite_master WHERE type='view' AND name=?",
            [view],
            |_| Ok(()),
        ).context(format!("Required view '{}' not found", view))?;
    }

    info!("Database schema verification completed successfully");
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    #[test]
    fn test_database_initialization() -> Result<()> {
        let dir = tempdir()?;
        let db_path = dir.path().join("test.db");
        
        let conn = init_database(
            db_path.to_str().unwrap(),
            "test-key",
        )?;

        // Verify we can query the database
        let count: i64 = conn.query_row(
            "SELECT COUNT(*) FROM event_types",
            [],
            |row| row.get(0),
        )?;

        assert_eq!(count, 4); // 4 pre-defined health event types
        Ok(())
    }
}
