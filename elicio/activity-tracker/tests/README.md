# Testing the Activity Tracker

This document describes how to test the activity tracker's database and aggregator components.

## Prerequisites

- Rust toolchain (install via [rustup](https://rustup.rs/))
- SQLite with SQLCipher support
- Cargo test runner

## Running Tests

### All Tests
```bash
# From the desktop directory
cargo test

# With detailed output
cargo test -- --nocapture
Specific Test Categories
# Database tests only
cargo test db_

# Schema validation tests only
cargo test schema_

# Health data tests only
cargo test health_
Test Structure
1. Database Tests (db_tests.rs)
Tests database initialization
Verifies schema creation
Checks encryption setup
Tests migrations
2. Aggregator Tests (aggregator_tests.rs)
Tests event batching
Verifies data partitioning
Tests retention policies
3. Health Data Tests (health_tests.rs)
Tests health metrics ingestion
Verifies workout tracking
Tests sleep data recording
4. Schema Tests (schema_tests.rs)
Tests JSON schema validation
Verifies metadata constraints
Tests schema caching
Adding New Tests
Create test files in the tests directory
Use the test utilities from test_utils.rs
Follow the naming convention: test_[component]_[functionality]
Example:

#[cfg(test)]
mod tests {
    use super::*;
    use test_utils::setup_test_db;

    #[test]
    fn test_health_metric_insertion() {
        let db = setup_test_db();
        // Test implementation
    }
}
Test Data
Sample test data is provided in test_data/:

events.json: Sample events for testing
health_metrics.json: Sample health data
workouts.json: Sample workout data
Manual Testing
1. Database Inspection
# Open encrypted database (replace KEY with your encryption key)
sqlcipher activity.db
PRAGMA key = 'KEY';

# View tables
.tables

# Check schema
.schema events
2. Data Verification
-- Check event counts
SELECT source, COUNT(*) FROM events GROUP BY source;

-- View latest health metrics
SELECT * FROM health_metrics ORDER BY start_time DESC LIMIT 5;

-- Check retention policy status
SELECT * FROM retention_policies;
Common Issues
SQLCipher Key Issues

Ensure the encryption key is correctly set
Check PRAGMA settings match the application
Schema Validation Failures

Verify JSON schema format
Check metadata structure matches schema
Test Database Cleanup

Tests use temporary databases
Ensure cleanup runs after tests complete
Continuous Integration
The test suite runs automatically in CI:

On pull requests
On main branch commits
Nightly for long-running tests
CI Environment Setup
- name: Install SQLCipher
  run: |
    sudo apt-get update
    sudo apt-get install -y sqlcipher libsqlcipher-dev

- name: Run Tests
  run: cargo test --all-features
Performance Testing
For performance testing of batch operations:

#[test]
fn test_batch_performance() {
    let start = std::time::Instant::now();
    // Insert 10,000 events
    for i in 0..10000 {
        // Test implementation
    }
    let duration = start.elapsed();
    println!("Batch insertion took: {:?}", duration);
}
Coverage Reports
Generate test coverage reports:

# Install cargo-tarpaulin
cargo install cargo-tarpaulin

# Generate coverage report
cargo tarpaulin --out Html
Next Steps
Add more integration tests for:

Browser extension integration
OS hooks data collection
Health device synchronization
Implement stress tests for:

Large data volumes
Concurrent operations
Long-running processes
