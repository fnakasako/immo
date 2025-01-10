//! Test utilities and shared test functionality

use anyhow::Result;
use serde_json::Value;
use std::path::Path;

// Re-export test utilities
mod utils {
    use super::*;
    
    pub fn load_test_data(file_name: &str) -> Result<Value> {
        let path = Path::new("test_data").join(file_name);
        let data = std::fs::read_to_string(path)?;
        Ok(serde_json::from_str(&data)?)
    }
}

// Re-export for use in tests
pub use utils::*;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_load_test_data() -> Result<()> {
        let data = load_test_data("events.json")?;
        assert!(data.is_object());
        Ok(())
    }
}
