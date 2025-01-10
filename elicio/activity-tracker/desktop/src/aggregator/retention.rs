use anyhow::{Context, Result};
use chrono::Utc;
use rusqlite::{params, Connection};
use serde_json::Value;
use tracing::{info, warn};

// Run all configured retention policies
pub(crate) fn run_retention_policies(conn: &Connection) -> Result<()> {
    let tx = conn.transaction()?;

    // Get all active retention policies
    let mut stmt = tx.prepare(
        "SELECT source, retention_days, summary_table FROM retention_policies"
    )?;

    let policies = stmt.query_map([], |row| {
        Ok((
            row.get::<_, String>(0)?,
            row.get::<_, i64>(1)?,
            row.get::<_, Option<String>>(2)?,
        ))
    })?;

    for policy_result in policies {
        let (source, retention_days, summary_table) = policy_result?;
        
        // Calculate cutoff timestamp
        let cutoff = Utc::now().timestamp() - (retention_days * 86400);

        match apply_retention_policy(&tx, &source, cutoff, summary_table.as_deref())? {
            RetentionResult::Deleted(count) => {
                info!("Deleted {} old records for source: {}", count, source);
            }
            RetentionResult::Summarized { deleted, summarized } => {
                info!(
                    "Source {}: Summarized {} records and deleted {} old records",
                    source, summarized, deleted
                );
            }
        }
    }

    tx.commit()?;
    Ok(())
}

enum RetentionResult {
    Deleted(i64),
    Summarized {
        summarized: i64,
        deleted: i64,
    },
}

// Apply a single retention policy
fn apply_retention_policy(
    tx: &Connection,
    source: &str,
    cutoff: i64,
    summary_table: Option<&str>,
) -> Result<RetentionResult> {
    // If we have a summary table, create summaries before deletion
    if let Some(table) = summary_table {
        let summarized = summarize_old_data(tx, source, cutoff, table)
            .context("Failed to summarize old data")?;

        // Delete old records after summarization
        let deleted = delete_old_records(tx, source, cutoff)
            .context("Failed to delete old records after summarization")?;

        Ok(RetentionResult::Summarized {
            summarized,
            deleted,
        })
    } else {
        // Just delete old records
        let deleted = delete_old_records(tx, source, cutoff)
            .context("Failed to delete old records")?;
        
        Ok(RetentionResult::Deleted(deleted))
    }
}

// Delete records older than cutoff
fn delete_old_records(tx: &Connection, source: &str, cutoff: i64) -> Result<i64> {
    // First get IDs of events to delete
    let mut old_event_ids = Vec::new();
    let mut stmt = tx.prepare(
        "SELECT id FROM events 
         WHERE source = ? AND timestamp < ?"
    )?;

    let ids = stmt.query_map(params![source, cutoff], |row| {
        row.get::<_, i64>(0)
    })?;

    for id_result in ids {
        old_event_ids.push(id_result?);
    }

    if old_event_ids.is_empty() {
        return Ok(0);
    }

    // Delete from health-specific tables if this is health data
    if source == "health" {
        // Delete from health_metrics
        tx.execute(
            "DELETE FROM health_metrics WHERE event_id IN (
                SELECT id FROM events 
                WHERE source = ? AND timestamp < ?
            )",
            params![source, cutoff],
        )?;

        // Delete from workouts
        tx.execute(
            "DELETE FROM workouts WHERE event_id IN (
                SELECT id FROM events 
                WHERE source = ? AND timestamp < ?
            )",
            params![source, cutoff],
        )?;

        // Delete from sleep_sessions
        tx.execute(
            "DELETE FROM sleep_sessions WHERE event_id IN (
                SELECT id FROM events 
                WHERE source = ? AND timestamp < ?
            )",
            params![source, cutoff],
        )?;
    }

    // Finally delete from events table
    let deleted = tx.execute(
        "DELETE FROM events WHERE source = ? AND timestamp < ?",
        params![source, cutoff],
    )?;

    Ok(deleted as i64)
}

// Create summary records for old data before deletion
fn summarize_old_data(
    tx: &Connection,
    source: &str,
    cutoff: i64,
    summary_table: &str,
) -> Result<i64> {
    // Verify summary table exists
    if !summary_table.starts_with("event_statistics") {
        warn!("Invalid summary table: {}", summary_table);
        return Ok(0);
    }

    // Insert daily summaries
    let inserted = tx.execute(
        "INSERT INTO event_statistics (
            date, source, event_type, count, metadata, updated_at
        )
        SELECT 
            date(timestamp/1000, 'unixepoch') as day,
            source,
            event_type,
            COUNT(*) as event_count,
            json_object(
                'avg_duration', avg(json_extract(metadata, '$.duration')),
                'total_count', sum(json_extract(metadata, '$.count'))
            ) as summary_metadata,
            ? as updated_at
        FROM events
        WHERE source = ? AND timestamp < ?
        GROUP BY 
            date(timestamp/1000, 'unixepoch'),
            source,
            event_type
        ON CONFLICT(date, source, event_type) DO UPDATE SET
            count = count + excluded.count,
            metadata = json_patch(metadata, excluded.metadata),
            updated_at = excluded.updated_at",
        params![
            Utc::now().timestamp(),
            source,
            cutoff,
        ],
    )?;

    Ok(inserted as i64)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::aggregator::db;
    use tempfile::tempdir;

    #[test]
    fn test_retention_policy() -> Result<()> {
        let dir = tempdir()?;
        let db_path = dir.path().join("test.db");
        
        let conn = db::init_database(
            db_path.to_str().unwrap(),
            "test-key",
        )?;

        // Insert test data
        let now = Utc::now().timestamp_millis();
        let old = now - (90 * 86400 * 1000); // 90 days old

        // Insert current event
        conn.execute(
            "INSERT INTO events (
                timestamp, source, event_type, metadata, inserted_at, partition_key
            ) VALUES (?, ?, ?, ?, ?, ?)",
            params![
                now,
                "test",
                "test_event",
                "{}",
                now/1000,
                "2023_01",
            ],
        )?;

        // Insert old event
        conn.execute(
            "INSERT INTO events (
                timestamp, source, event_type, metadata, inserted_at, partition_key
            ) VALUES (?, ?, ?, ?, ?, ?)",
            params![
                old,
                "test",
                "test_event",
                "{}",
                old/1000,
                "2022_10",
            ],
        )?;

        // Set retention policy
        conn.execute(
            "INSERT INTO retention_policies (
                source, retention_days, summary_table, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?)",
            params![
                "test",
                30,
                "event_statistics",
                now/1000,
                now/1000,
            ],
        )?;

        // Run retention
        run_retention_policies(&conn)?;

        // Verify old event was deleted
        let count: i64 = conn.query_row(
            "SELECT COUNT(*) FROM events WHERE timestamp < ?",
            params![now - (30 * 86400 * 1000)],
            |row| row.get(0),
        )?;

        assert_eq!(count, 0);

        // Verify current event remains
        let count: i64 = conn.query_row(
            "SELECT COUNT(*) FROM events",
            params![],
            |row| row.get(0),
        )?;

        assert_eq!(count, 1);

        // Verify summary was created
        let count: i64 = conn.query_row(
            "SELECT COUNT(*) FROM event_statistics",
            params![],
            |row| row.get(0),
        )?;

        assert_eq!(count, 1);

        Ok(())
    }
}
