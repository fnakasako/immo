use anyhow::{Context, Result};
use rusqlite::{params, Connection};
use serde_json::{json, Value};
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::Mutex;
use tracing::{debug, warn};

// Cache of loaded schemas to avoid frequent DB lookups
type SchemaCache = Arc<Mutex<HashMap<(String, String), Value>>>;

// Initialize schema cache
pub(crate) async fn init_schema_cache(db: &Connection) -> Result<SchemaCache> {
    let mut cache = HashMap::new();
    
    let mut stmt = db.prepare(
        "SELECT source, event_type, schema FROM event_types"
    )?;

    let schemas = stmt.query_map([], |row| {
        Ok((
            row.get::<_, String>(0)?,
            row.get::<_, String>(1)?,
            row.get::<_, String>(2)?,
        ))
    })?;

    for schema_result in schemas {
        let (source, event_type, schema_str) = schema_result?;
        let schema: Value = serde_json::from_str(&schema_str)
            .context("Failed to parse schema JSON")?;
        
        cache.insert((source, event_type), schema);
    }

    Ok(Arc::new(Mutex::new(cache)))
}

// Register a new event type with its schema
pub(crate) async fn register_event_type(
    db: &Arc<Mutex<Connection>>,
    cache: &SchemaCache,
    source: &str,
    event_type: &str,
    schema: Value,
) -> Result<()> {
    // Validate schema is a valid JSON Schema
    validate_schema_structure(&schema)
        .context("Invalid schema structure")?;

    let db = db.lock().await;
    let tx = db.transaction()?;

    // Insert or update schema
    tx.execute(
        "INSERT INTO event_types (source, event_type, schema, created_at)
         VALUES (?, ?, ?, strftime('%s', 'now'))
         ON CONFLICT(source, event_type) DO UPDATE SET
         schema = excluded.schema",
        params![
            source,
            event_type,
            schema.to_string(),
        ],
    )?;

    tx.commit()?;

    // Update cache
    let mut cache = cache.lock().await;
    cache.insert((source.to_string(), event_type.to_string()), schema);

    debug!("Registered schema for {}:{}", source, event_type);
    Ok(())
}

// Validate event metadata against its schema
pub(crate) async fn validate_event_metadata(
    cache: &SchemaCache,
    source: &str,
    event_type: &str,
    metadata: &Value,
) -> Result<()> {
    let cache = cache.lock().await;
    
    if let Some(schema) = cache.get(&(source.to_string(), event_type.to_string())) {
        validate_against_schema(metadata, schema)
            .context("Metadata validation failed")?;
        Ok(())
    } else {
        warn!("No schema found for {}:{}", source, event_type);
        // Allow event without schema validation
        Ok(())
    }
}

// Basic schema structure validation
fn validate_schema_structure(schema: &Value) -> Result<()> {
    // Schema must be an object
    if !schema.is_object() {
        return Err(anyhow::anyhow!("Schema must be a JSON object"));
    }

    let obj = schema.as_object().unwrap();

    // Must have type field
    if !obj.contains_key("type") {
        return Err(anyhow::anyhow!("Schema must have 'type' field"));
    }

    // If it has properties, they must be an object
    if let Some(props) = obj.get("properties") {
        if !props.is_object() {
            return Err(anyhow::anyhow!("Schema properties must be an object"));
        }
    }

    Ok(())
}

// Validate data against a JSON schema
fn validate_against_schema(data: &Value, schema: &Value) -> Result<()> {
    let schema_obj = schema.as_object()
        .context("Schema must be an object")?;

    // Check type
    if let Some(type_val) = schema_obj.get("type") {
        let type_str = type_val.as_str()
            .context("Schema type must be a string")?;
        
        match type_str {
            "object" => {
                if !data.is_object() {
                    return Err(anyhow::anyhow!("Data must be an object"));
                }
                
                // Validate properties if specified
                if let Some(props) = schema_obj.get("properties") {
                    validate_object_properties(data.as_object().unwrap(), props)?;
                }
            }
            "array" => {
                if !data.is_array() {
                    return Err(anyhow::anyhow!("Data must be an array"));
                }
                
                // Validate items if specified
                if let Some(items) = schema_obj.get("items") {
                    validate_array_items(data.as_array().unwrap(), items)?;
                }
            }
            "string" => {
                if !data.is_string() {
                    return Err(anyhow::anyhow!("Data must be a string"));
                }
            }
            "number" => {
                if !data.is_number() {
                    return Err(anyhow::anyhow!("Data must be a number"));
                }
            }
            "boolean" => {
                if !data.is_boolean() {
                    return Err(anyhow::anyhow!("Data must be a boolean"));
                }
            }
            _ => {
                warn!("Unsupported schema type: {}", type_str);
            }
        }
    }

    Ok(())
}

// Validate object properties against schema
fn validate_object_properties(data: &serde_json::Map<String, Value>, schema: &Value) -> Result<()> {
    let props = schema.as_object()
        .context("Properties schema must be an object")?;

    for (key, prop_schema) in props {
        if let Some(value) = data.get(key) {
            validate_against_schema(value, prop_schema)?;
        }
    }

    Ok(())
}

// Validate array items against schema
fn validate_array_items(data: &[Value], schema: &Value) -> Result<()> {
    for item in data {
        validate_against_schema(item, schema)?;
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::aggregator::db;
    use tempfile::tempdir;

    #[tokio::test]
    async fn test_schema_validation() -> Result<()> {
        let dir = tempdir()?;
        let db_path = dir.path().join("test.db");
        
        let conn = db::init_database(
            db_path.to_str().unwrap(),
            "test-key",
        )?;

        let db = Arc::new(Mutex::new(conn));
        let cache = init_schema_cache(&db.lock().await?).await?;

        // Register test schema
        let schema = json!({
            "type": "object",
            "properties": {
                "count": { "type": "number" },
                "tags": { 
                    "type": "array",
                    "items": { "type": "string" }
                }
            }
        });

        register_event_type(
            &db,
            &cache,
            "test",
            "test_event",
            schema,
        ).await?;

        // Test valid data
        let valid_data = json!({
            "count": 42,
            "tags": ["test", "validation"]
        });

        validate_event_metadata(
            &cache,
            "test",
            "test_event",
            &valid_data,
        ).await?;

        // Test invalid data
        let invalid_data = json!({
            "count": "not a number",
            "tags": [1, 2, 3]
        });

        assert!(validate_event_metadata(
            &cache,
            "test",
            "test_event",
            &invalid_data,
        ).await.is_err());

        Ok(())
    }
}
