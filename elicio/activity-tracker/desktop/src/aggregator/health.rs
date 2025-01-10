use anyhow::{Context, Result};
use chrono::{DateTime, Utc};
use rusqlite::{params, Connection};
use serde_json::Value;
use std::sync::Arc;
use tokio::sync::Mutex;
use tracing::{error, info};

use super::Event;

// Submit a health metric to both events and health_metrics tables
pub(crate) async fn submit_health_metric(
    db: &Arc<Mutex<Connection>>,
    metric_type: &str,
    value: f64,
    unit: &str,
    start_time: DateTime<Utc>,
    end_time: DateTime<Utc>,
    source_device: Option<&str>,
    accuracy: Option<i32>,
    metadata: Option<Value>,
) -> Result<()> {
    let db = db.lock().await;
    let tx = db.transaction()?;

    // First create the core event
    let event = Event {
        timestamp: start_time.timestamp_millis(),
        source: "health".to_string(),
        event_type: format!("health_metric_{}", metric_type),
        metadata: metadata.unwrap_or_else(|| serde_json::json!({
            "value": value,
            "unit": unit
        })),
        partition_key: Some(format!("{}_{:02}", start_time.year(), start_time.month())),
    };

    // Insert core event
    tx.execute(
        "INSERT INTO events (timestamp, source, event_type, metadata, inserted_at, partition_key)
         VALUES (?, ?, ?, ?, ?, ?)",
        params![
            event.timestamp,
            event.source,
            event.event_type,
            event.metadata.to_string(),
            Utc::now().timestamp(),
            event.partition_key,
        ],
    )?;

    let event_id = tx.last_insert_rowid();

    // Insert detailed health metric
    tx.execute(
        "INSERT INTO health_metrics (
            event_id, metric_type, value, unit, start_time, end_time,
            source_device, accuracy, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        params![
            event_id,
            metric_type,
            value,
            unit,
            start_time.timestamp_millis(),
            end_time.timestamp_millis(),
            source_device,
            accuracy,
            metadata.map(|m| m.to_string()),
        ],
    )?;

    tx.commit()?;
    info!("Submitted health metric: {} = {} {}", metric_type, value, unit);
    Ok(())
}

// Submit a workout session
pub(crate) async fn submit_workout(
    db: &Arc<Mutex<Connection>>,
    workout_type: &str,
    start_time: DateTime<Utc>,
    end_time: DateTime<Utc>,
    distance: Option<f64>,
    calories: Option<f64>,
    avg_heart_rate: Option<f64>,
    max_heart_rate: Option<f64>,
    metadata: Option<Value>,
) -> Result<()> {
    let db = db.lock().await;
    let tx = db.transaction()?;

    // Create core event
    let event = Event {
        timestamp: start_time.timestamp_millis(),
        source: "health".to_string(),
        event_type: "workout".to_string(),
        metadata: metadata.unwrap_or_else(|| serde_json::json!({
            "type": workout_type,
            "duration_minutes": (end_time - start_time).num_minutes(),
            "distance_meters": distance,
            "calories": calories
        })),
        partition_key: Some(format!("{}_{:02}", start_time.year(), start_time.month())),
    };

    // Insert core event
    tx.execute(
        "INSERT INTO events (timestamp, source, event_type, metadata, inserted_at, partition_key)
         VALUES (?, ?, ?, ?, ?, ?)",
        params![
            event.timestamp,
            event.source,
            event.event_type,
            event.metadata.to_string(),
            Utc::now().timestamp(),
            event.partition_key,
        ],
    )?;

    let event_id = tx.last_insert_rowid();

    // Insert workout details
    tx.execute(
        "INSERT INTO workouts (
            event_id, workout_type, start_time, end_time,
            distance, calories, avg_heart_rate, max_heart_rate, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        params![
            event_id,
            workout_type,
            start_time.timestamp_millis(),
            end_time.timestamp_millis(),
            distance,
            calories,
            avg_heart_rate,
            max_heart_rate,
            metadata.map(|m| m.to_string()),
        ],
    )?;

    tx.commit()?;
    info!("Submitted workout: {} ({} minutes)", 
          workout_type, 
          (end_time - start_time).num_minutes());
    Ok(())
}

// Submit a sleep session
pub(crate) async fn submit_sleep_session(
    db: &Arc<Mutex<Connection>>,
    start_time: DateTime<Utc>,
    end_time: DateTime<Utc>,
    quality: &str,
    duration: i32,
    interruptions: Option<i32>,
    metadata: Option<Value>,
) -> Result<()> {
    let db = db.lock().await;
    let tx = db.transaction()?;

    // Create core event
    let event = Event {
        timestamp: start_time.timestamp_millis(),
        source: "health".to_string(),
        event_type: "sleep".to_string(),
        metadata: metadata.unwrap_or_else(|| serde_json::json!({
            "quality": quality,
            "duration_minutes": duration,
            "interruptions": interruptions
        })),
        partition_key: Some(format!("{}_{:02}", start_time.year(), start_time.month())),
    };

    // Insert core event
    tx.execute(
        "INSERT INTO events (timestamp, source, event_type, metadata, inserted_at, partition_key)
         VALUES (?, ?, ?, ?, ?, ?)",
        params![
            event.timestamp,
            event.source,
            event.event_type,
            event.metadata.to_string(),
            Utc::now().timestamp(),
            event.partition_key,
        ],
    )?;

    let event_id = tx.last_insert_rowid();

    // Insert sleep session details
    tx.execute(
        "INSERT INTO sleep_sessions (
            event_id, start_time, end_time,
            quality, duration, interruptions, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?)",
        params![
            event_id,
            start_time.timestamp_millis(),
            end_time.timestamp_millis(),
            quality,
            duration,
            interruptions,
            metadata.map(|m| m.to_string()),
        ],
    )?;

    tx.commit()?;
    info!("Submitted sleep session: {} quality, {} minutes", quality, duration);
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::aggregator::db;
    use tempfile::tempdir;

    #[tokio::test]
    async fn test_health_metric_submission() -> Result<()> {
        let dir = tempdir()?;
        let db_path = dir.path().join("test.db");
        
        let conn = db::init_database(
            db_path.to_str().unwrap(),
            "test-key",
        )?;

        let db = Arc::new(Mutex::new(conn));
        
        let now = Utc::now();
        submit_health_metric(
            &db,
            "heart_rate",
            75.0,
            "bpm",
            now,
            now,
            Some("test_device"),
            Some(95),
            None,
        ).await?;

        let db = db.lock().await;
        
        // Verify event was created
        let event_count: i64 = db.query_row(
            "SELECT COUNT(*) FROM events WHERE source = 'health'",
            [],
            |row| row.get(0),
        )?;
        assert_eq!(event_count, 1);

        // Verify health metric was created
        let metric_count: i64 = db.query_row(
            "SELECT COUNT(*) FROM health_metrics WHERE metric_type = 'heart_rate'",
            [],
            |row| row.get(0),
        )?;
        assert_eq!(metric_count, 1);

        Ok(())
    }
}
