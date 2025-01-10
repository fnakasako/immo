// Aggregator module for processing activity data
use anyhow::{Context, Result};
use chrono::{DateTime, Utc};
use rusqlite::{params, Connection};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tokio::sync::{mpsc, Mutex};
use tracing::{debug, error, info, warn};
use uuid::Uuid;

mod db;
mod health;
mod retention;
mod schema;

// Core event model matching our database schema
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Event {
    pub timestamp: i64,
    pub source: String,
    pub event_type: String,
    pub metadata: serde_json::Value,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub partition_key: Option<String>,
}

// Configuration for the aggregator
#[derive(Debug, Clone)]
pub struct AggregatorConfig {
    pub db_path: String,
    pub encryption_key: String,
    pub batch_size: usize,
    pub batch_interval_ms: u64,
}

impl Default for AggregatorConfig {
    fn default() -> Self {
        Self {
            db_path: String::from("activity.db"),
            encryption_key: String::from("default-key"),
            batch_size: 100,
            batch_interval_ms: 5000,
        }
    }
}

// Main aggregator service
pub struct Aggregator {
    config: AggregatorConfig,
    event_tx: mpsc::Sender<Event>,
    db: Arc<Mutex<Connection>>,
}

impl Aggregator {
    pub async fn new(config: AggregatorConfig) -> Result<Self> {
        // Initialize encrypted database connection
        let db = db::init_database(&config.db_path, &config.encryption_key)
            .context("Failed to initialize database")?;
        
        // Create channel for event processing
        let (event_tx, event_rx) = mpsc::channel(1000);
        
        // Wrap database connection in Arc<Mutex>
        let db = Arc::new(Mutex::new(db));
        
        // Clone references for background task
        let batch_db = Arc::clone(&db);
        let batch_config = config.clone();
        
        // Spawn background task for batch processing
        tokio::spawn(async move {
            Self::batch_processor(batch_db, event_rx, batch_config).await
        });

        Ok(Self {
            config,
            event_tx,
            db,
        })
    }

    // Process incoming events in batches
    async fn batch_processor(
        db: Arc<Mutex<Connection>>,
        mut event_rx: mpsc::Receiver<Event>,
        config: AggregatorConfig,
    ) {
        let mut batch = Vec::with_capacity(config.batch_size);
        let mut interval = tokio::time::interval(
            tokio::time::Duration::from_millis(config.batch_interval_ms)
        );

        loop {
            tokio::select! {
                Some(event) = event_rx.recv() => {
                    batch.push(event);
                    if batch.len() >= config.batch_size {
                        if let Err(e) = Self::flush_batch(&db, &batch).await {
                            error!("Failed to flush batch: {}", e);
                        }
                        batch.clear();
                    }
                }
                _ = interval.tick() => {
                    if !batch.is_empty() {
                        if let Err(e) = Self::flush_batch(&db, &batch).await {
                            error!("Failed to flush batch: {}", e);
                        }
                        batch.clear();
                    }
                }
            }
        }
    }

    // Write batch of events to database
    async fn flush_batch(db: &Arc<Mutex<Connection>>, events: &[Event]) -> Result<()> {
        let db = db.lock().await;
        let tx = db.transaction()?;

        for event in events {
            let partition_key = event.partition_key.clone().unwrap_or_else(|| {
                chrono::DateTime::from_timestamp(event.timestamp / 1000, 0)
                    .map(|dt| format!("{}_{:02}", dt.year(), dt.month()))
                    .unwrap_or_else(|| "unknown".to_string())
            });

            tx.execute(
                "INSERT INTO events (timestamp, source, event_type, metadata, inserted_at, partition_key)
                 VALUES (?, ?, ?, ?, ?, ?)",
                params![
                    event.timestamp,
                    event.source,
                    event.event_type,
                    event.metadata.to_string(),
                    Utc::now().timestamp(),
                    partition_key,
                ],
            )?;
        }

        tx.commit()?;
        info!("Flushed {} events to database", events.len());
        Ok(())
    }

    // Public API for submitting events
    pub async fn submit_event(&self, mut event: Event) -> Result<()> {
        // Set partition key if not provided
        if event.partition_key.is_none() {
            event.partition_key = Some(
                chrono::DateTime::from_timestamp(event.timestamp / 1000, 0)
                    .map(|dt| format!("{}_{:02}", dt.year(), dt.month()))
                    .unwrap_or_else(|| "unknown".to_string())
            );
        }

        // Validate event type exists
        let db = self.db.lock().await;
        let exists: bool = db.query_row(
            "SELECT 1 FROM event_types WHERE source = ? AND event_type = ?",
            params![event.source, event.event_type],
            |_| Ok(true),
        ).unwrap_or(false);

        if !exists {
            warn!("Unknown event type: {}:{}", event.source, event.event_type);
            // Auto-register new event type with basic schema
            db.execute(
                "INSERT INTO event_types (source, event_type, schema, created_at)
                 VALUES (?, ?, ?, ?)",
                params![
                    event.source,
                    event.event_type,
                    r#"{"type":"object","properties":{}}"#,
                    Utc::now().timestamp(),
                ],
            )?;
        }

        // Send event to batch processor
        self.event_tx.send(event).await
            .context("Failed to submit event to batch processor")?;

        Ok(())
    }

    // Run retention policies
    pub async fn run_retention(&self) -> Result<()> {
        let db = self.db.lock().await;
        retention::run_retention_policies(&db)
            .context("Failed to run retention policies")
    }

    // Health data specific methods
    pub async fn submit_health_metric(
        &self,
        metric_type: &str,
        value: f64,
        unit: &str,
        start_time: DateTime<Utc>,
        end_time: DateTime<Utc>,
        source_device: Option<&str>,
        accuracy: Option<i32>,
        metadata: Option<serde_json::Value>,
    ) -> Result<()> {
        health::submit_health_metric(
            &self.db,
            metric_type,
            value,
            unit,
            start_time,
            end_time,
            source_device,
            accuracy,
            metadata,
        ).await
    }

    pub async fn submit_workout(
        &self,
        workout_type: &str,
        start_time: DateTime<Utc>,
        end_time: DateTime<Utc>,
        distance: Option<f64>,
        calories: Option<f64>,
        avg_heart_rate: Option<f64>,
        max_heart_rate: Option<f64>,
        metadata: Option<serde_json::Value>,
    ) -> Result<()> {
        health::submit_workout(
            &self.db,
            workout_type,
            start_time,
            end_time,
            distance,
            calories,
            avg_heart_rate,
            max_heart_rate,
            metadata,
        ).await
    }

    pub async fn submit_sleep_session(
        &self,
        start_time: DateTime<Utc>,
        end_time: DateTime<Utc>,
        quality: &str,
        duration: i32,
        interruptions: Option<i32>,
        metadata: Option<serde_json::Value>,
    ) -> Result<()> {
        health::submit_sleep_session(
            &self.db,
            start_time,
            end_time,
            quality,
            duration,
            interruptions,
            metadata,
        ).await
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    #[tokio::test]
    async fn test_event_submission() -> Result<()> {
        let dir = tempdir()?;
        let db_path = dir.path().join("test.db");
        
        let config = AggregatorConfig {
            db_path: db_path.to_str().unwrap().to_string(),
            encryption_key: "test-key".to_string(),
            batch_size: 10,
            batch_interval_ms: 100,
        };

        let aggregator = Aggregator::new(config).await?;

        let event = Event {
            timestamp: Utc::now().timestamp_millis(),
            source: "test".to_string(),
            event_type: "test_event".to_string(),
            metadata: serde_json::json!({"test": true}),
            partition_key: None,
        };

        aggregator.submit_event(event).await?;

        // Wait for batch processing
        tokio::time::sleep(tokio::time::Duration::from_millis(200)).await;

        let db = aggregator.db.lock().await;
        let count: i64 = db.query_row(
            "SELECT COUNT(*) FROM events",
            params![],
            |row| row.get(0),
        )?;

        assert_eq!(count, 1);
        Ok(())
    }
}
