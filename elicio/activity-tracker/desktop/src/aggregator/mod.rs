// Aggregator module for processing both activity data and text content
// Provides unified handling of events and text captures with efficient batch processing
use anyhow::{Context, Result};
use chrono::{DateTime, Utc};
use rusqlite::{params, Connection};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tokio::sync::{mpsc, Mutex};
use tracing::{debug, error, info, warn};
use uuid::Uuid;
use rust_bert::pipelines::summarization::{SummarizationModel, SummarizationConfig};

// Module declarations
mod db;
mod health;
mod retention;
mod schema;
mod text_capture;

// Core data models
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Event {
    pub timestamp: i64,
    pub source: String,
    pub event_type: String,
    pub metadata: serde_json::Value,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub partition_key: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TextCapture {
    pub text: String,
    pub app_name: String,
    pub window_title: String,
    pub timestamp: i64,
    pub text_type: TextType,
    pub context: CaptureContext,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub partition_key: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TextType {
    Input,    // User-generated content (typing, pasting)
    Output,   // Application-generated content
    Static,   // Existing content being viewed
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CaptureContext {
    pub element_type: String,    // The UI element type (textbox, document, etc.)
    pub parent_element: String,  // Parent UI component identifier
    pub url: Option<String>,     // URL for web content
    pub interaction_type: String, // How the text was captured (type, paste, view)
}

// Configuration structures
#[derive(Debug, Clone)]
pub struct AggregatorConfig {
    pub db_path: String,
    pub encryption_key: String,
    pub batch_size: usize,
    pub batch_interval_ms: u64,
    pub text_capture_config: TextCaptureConfig,
}

#[derive(Debug, Clone)]
pub struct TextCaptureConfig {
    pub min_text_length: usize,         // Minimum length to store
    pub summarization_threshold: usize,  // Length at which to generate summaries
    pub model_path: String,             // Path to the LLM model
    pub enable_accessibility: bool,      // Whether to enable OS-level text capture
}

impl Default for AggregatorConfig {
    fn default() -> Self {
        Self {
            db_path: String::from("activity.db"),
            encryption_key: String::from("default-key"),
            batch_size: 100,
            batch_interval_ms: 5000,
            text_capture_config: TextCaptureConfig::default(),
        }
    }
}

impl Default for TextCaptureConfig {
    fn default() -> Self {
        Self {
            min_text_length: 10,
            summarization_threshold: 1000,
            model_path: String::from("models/bart-large-cnn"),
            enable_accessibility: true,
        }
    }
}

// Main aggregator service
pub struct Aggregator {
    config: AggregatorConfig,
    event_tx: mpsc::Sender<Event>,
    text_tx: mpsc::Sender<TextCapture>,
    db: Arc<Mutex<Connection>>,
    llm: Arc<Mutex<SummarizationModel>>,
}

impl Aggregator {
    pub async fn new(config: AggregatorConfig) -> Result<Self> {
        // Initialize the database with encryption
        let db = db::init_database(&config.db_path, &config.encryption_key)
            .context("Failed to initialize database")?;
        
        // Create channels for both event types
        let (event_tx, event_rx) = mpsc::channel(1000);
        let (text_tx, text_rx) = mpsc::channel(1000);
        
        // Initialize the LLM for text summarization
        let llm = SummarizationModel::new(SummarizationConfig::new()
            .model_type("facebook/bart-large-cnn")
            .model_path(&config.text_capture_config.model_path)
            .quantized(true))?;
        
        let db = Arc::new(Mutex::new(db));
        let llm = Arc::new(Mutex::new(llm));
        
        // Spawn both processing pipelines
        let event_db = Arc::clone(&db);
        let text_db = Arc::clone(&db);
        let text_llm = Arc::clone(&llm);
        let event_config = config.clone();
        let text_config = config.clone();

        // Launch event processor
        tokio::spawn(async move {
            Self::batch_processor(event_db, event_rx, event_config).await
        });

        // Launch text processor
        tokio::spawn(async move {
            Self::text_batch_processor(text_db, text_rx, text_llm, text_config).await
        });

        // Initialize text capture system if enabled
        if config.text_capture_config.enable_accessibility {
            text_capture::init_capture_system(text_tx.clone())?;
        }

        Ok(Self {
            config,
            event_tx,
            text_tx,
            db,
            llm,
        })
    }

    // Event processing pipeline (existing implementation remains unchanged)
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

    // Text processing pipeline
    async fn text_batch_processor(
        db: Arc<Mutex<Connection>>,
        mut text_rx: mpsc::Receiver<TextCapture>,
        llm: Arc<Mutex<SummarizationModel>>,
        config: AggregatorConfig,
    ) {
        let mut batch = Vec::with_capacity(config.batch_size);
        let mut interval = tokio::time::interval(
            tokio::time::Duration::from_millis(config.batch_interval_ms)
        );

        loop {
            tokio::select! {
                Some(capture) = text_rx.recv() => {
                    batch.push(capture);
                    if batch.len() >= config.batch_size {
                        if let Err(e) = Self::flush_text_batch(&db, &batch, &llm, &config).await {
                            error!("Failed to flush text batch: {}", e);
                        }
                        batch.clear();
                    }
                }
                _ = interval.tick() => {
                    if !batch.is_empty() {
                        if let Err(e) = Self::flush_text_batch(&db, &batch, &llm, &config).await {
                            error!("Failed to flush text batch: {}", e);
                        }
                        batch.clear();
                    }
                }
            }
        }
    }

    // Existing event batch flushing (unchanged)
    async fn flush_batch(db: &Arc<Mutex<Connection>>, events: &[Event]) -> Result<()> {
        // Existing implementation remains unchanged
    }

    // Text batch flushing with summarization
    async fn flush_text_batch(
        db: &Arc<Mutex<Connection>>,
        captures: &[TextCapture],
        llm: &Arc<Mutex<SummarizationModel>>,
        config: &AggregatorConfig,
    ) -> Result<()> {
        let db = db.lock().await;
        let tx = db.transaction()?;

        for capture in captures {
            // Generate summary for longer text
            let summary = if capture.text.len() >= config.text_capture_config.summarization_threshold {
                let model = llm.lock().await;
                Some(model.summarize(&capture.text).await?)
            } else {
                None
            };

            // Store the capture with its summary
            tx.execute(
                "INSERT INTO text_captures (
                    text, app_name, window_title, timestamp,
                    text_type, context, summary, partition_key
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                params![
                    capture.text,
                    capture.app_name,
                    capture.window_title,
                    capture.timestamp,
                    serde_json::to_string(&capture.text_type)?,
                    serde_json::to_string(&capture.context)?,
                    summary,
                    capture.partition_key.clone().unwrap_or_else(|| {
                        chrono::DateTime::from_timestamp(capture.timestamp / 1000, 0)
                            .map(|dt| format!("{}_{:02}", dt.year(), dt.month()))
                            .unwrap_or_else(|| "unknown".to_string())
                    })
                ],
            )?;
        }

        tx.commit()?;
        info!("Flushed {} text captures to database", captures.len());
        Ok(())
    }

    // Public API Methods

    // Existing event submission (unchanged)
    pub async fn submit_event(&self, mut event: Event) -> Result<()> {
        // Existing implementation remains unchanged
    }

    // New text capture submission
    pub async fn submit_text_capture(&self, mut capture: TextCapture) -> Result<()> {
        // Skip if text is too short
        if capture.text.len() < self.config.text_capture_config.min_text_length {
            debug!("Text too short, skipping capture");
            return Ok(());
        }

        // Set partition key if not provided
        if capture.partition_key.is_none() {
            capture.partition_key = Some(
                chrono::DateTime::from_timestamp(capture.timestamp / 1000, 0)
                    .map(|dt| format!("{}_{:02}", dt.year(), dt.month()))
                    .unwrap_or_else(|| "unknown".to_string())
            );
        }

        self.text_tx.send(capture).await
            .context("Failed to submit text capture")?;

        Ok(())
    }

    // Existing retention and health methods remain unchanged
    pub async fn run_retention(&self) -> Result<()> {
        // Existing implementation remains unchanged
    }

    pub async fn submit_health_metric(/* existing parameters */) -> Result<()> {
        // Existing implementation remains unchanged
    }

    pub async fn submit_workout(/* existing parameters */) -> Result<()> {
        // Existing implementation remains unchanged
    }

    pub async fn submit_sleep_session(/* existing parameters */) -> Result<()> {
        // Existing implementation remains unchanged
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    // Existing event test
    #[tokio::test]
    async fn test_event_submission() -> Result<()> {
        // Existing implementation remains unchanged
    }

    // New text capture test
    #[tokio::test]
    async fn test_text_capture() -> Result<()> {
        let dir = tempdir()?;
        let db_path = dir.path().join("test.db");
        
        let mut config = AggregatorConfig::default();
        config.db_path = db_path.to_str().unwrap().to_string();
        config.encryption_key = "test-key".to_string();
        config.text_capture_config.enable_accessibility = false;

        let aggregator = Aggregator::new(config).await?;

        let capture = TextCapture {
            text: "Test text content".to_string(),
            app_name: "test_app".to_string(),
            window_title: "Test Window".to_string(),
            timestamp: Utc::now().timestamp_millis(),
            text_type: TextType::Input,
            context: CaptureContext {
                element_type: "textbox".to_string(),
                parent_element: "main".to_string(),
                url: None,
                interaction_type: "type".to_string(),
            },
            partition_key: None,
        };

        aggregator.submit_text_capture(capture).await?;

        // Wait for batch processing
        tokio::time::sleep(tokio::time::Duration::from_millis(200)).await;

        let db = aggregator.db.lock().await;
        let count: i64 = db.query_row(
            "SELECT COUNT(*) FROM text_captures",
            params![],
            |row| row.get(0),
        )?;

        assert_eq!(count, 1);
        Ok(())
    }
}