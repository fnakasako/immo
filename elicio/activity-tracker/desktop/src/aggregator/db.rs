use anyhow::{Context, Result};
use rusqlite::Connection;
use std::path::Path;
use tracing::info;

pub(crate) fn init_database(db_path: &str, encryption_key: &str) -> Result<Connection> {
    let is_new_db = !Path::new(db_path).exists();
    
    // Open or create encrypted database
    let conn = Connection::open(db_path)
        .context("Failed to open database")?;

    // Configure encryption and performance settings
    conn.execute_batch(&format!(
        "PRAGMA key = '{}';
         PRAGMA cipher_page_size = 4096;
         PRAGMA kdf_iter = 64000;
         PRAGMA journal_mode = WAL;
         PRAGMA synchronous = NORMAL;
         PRAGMA cache_size = -2000;  -- Reserve 2MB for cache
         PRAGMA temp_store = MEMORY; -- Use memory for temp storage",
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

fn run_migrations(conn: &Connection) -> Result<()> {
    let tx = conn.transaction()?;

    // Create migrations table
    tx.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_at INTEGER NOT NULL,
            description TEXT,
            checksum TEXT
        )",
        [],
    )?;

    // Run core schema migrations
    let core_sql = include_str!("../../../db/migrations/001_initial.sql");
    tx.execute_batch(core_sql)?;

    // Run text aggregation schema migrations
    let text_sql = include_str!("../../../db/migrations/002_text_aggregation.sql");
    tx.execute_batch(text_sql)?;

    tx.commit()?;
    info!("Database migrations completed successfully");
    Ok(())
}

fn verify_schema(conn: &Connection) -> Result<()> {
    // Verify core tables
    let core_tables = [
        "events",
        "retention_policies",
        "event_types",
        "event_statistics",
    ];

    // Verify text aggregation tables
    let text_tables = [
        "text_captures",
        "text_summaries",
        "application_context",
        "content_relationships",
        "text_statistics"
    ];

    // Combined verification
    for table in core_tables.iter().chain(text_tables.iter()) {
        conn.query_row(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            [table],
            |_| Ok(()),
        ).context(format!("Table '{}' not found", table))?;
    }

    // Verify required indexes
    let required_indexes = [
        // Core indexes
        "idx_events_timestamp",
        "idx_events_source_type",
        "idx_events_partition",
        // Text capture indexes
        "idx_text_captures_timestamp",
        "idx_text_captures_app",
        "idx_text_captures_type",
        "idx_text_summaries_capture",
        "idx_content_relationships_source",
        "idx_content_relationships_target"
    ];

    for index in required_indexes.iter() {
        conn.query_row(
            "SELECT 1 FROM sqlite_master WHERE type='index' AND name=?",
            [index],
            |_| Ok(()),
        ).context(format!("Required index '{}' not found", index))?;
    }

    // Verify views
    let required_views = [
        // Core views
        "v_daily_activity",
        // Text aggregation views
        "v_text_activity_summary",
        "v_application_usage",
        "v_content_connections"
    ];

    for view in required_views.iter() {
        conn.query_row(
            "SELECT 1 FROM sqlite_master WHERE type='view' AND name=?",
            [view],
            |_| Ok(()),
        ).context(format!("Required view '{}' not found", view))?;
    }

    // Verify text-specific triggers exist
    let required_triggers = [
        "trg_text_capture_stats",
        "trg_summary_update",
        "trg_relationship_cleanup"
    ];

    for trigger in required_triggers.iter() {
        conn.query_row(
            "SELECT 1 FROM sqlite_master WHERE type='trigger' AND name=?",
            [trigger],
            |_| Ok(()),
        ).context(format!("Required trigger '{}' not found", trigger))?;
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

        // Verify text capture tables
        let tables = [
            "text_captures",
            "text_summaries",
            "application_context"
        ];

        for table in tables.iter() {
            conn.query_row(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                [table],
                |_| Ok(()),
            )?;
        }

        Ok(())
    }

    #[test]
    fn test_text_capture_insertion() -> Result<()> {
        let dir = tempdir()?;
        let db_path = dir.path().join("test.db");
        let conn = init_database(db_path.to_str().unwrap(), "test-key")?;

        conn.execute(
            "INSERT INTO text_captures (
                text, app_name, window_title, timestamp,
                text_type, context, summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?)",
            params![
                "Test text",
                "test_app",
                "Test Window",
                chrono::Utc::now().timestamp_millis(),
                "input",
                "{}",
                None::<String>,
            ],
        )?;

        let count: i64 = conn.query_row(
            "SELECT COUNT(*) FROM text_captures",
            [],
            |row| row.get(0),
        )?;

        assert_eq!(count, 1);
        Ok(())
    }
}