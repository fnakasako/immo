use activity_tracker_tests::*;
use anyhow::Result;

#[tokio::test]
async fn test_load_events() -> Result<()> {
    let events = load_test_data("events.json")?;
    assert!(events.is_object());
    Ok(())
}

#[tokio::test]
async fn test_load_health_metrics() -> Result<()> {
    let metrics = load_test_data("health_metrics.json")?;
    assert!(metrics.is_object());
    Ok(())
}

#[tokio::test]
async fn test_load_sleep() -> Result<()> {
    let sleep = load_test_data("sleep.json")?;
    assert!(sleep.is_object());
    Ok(())
}

#[tokio::test]
async fn test_load_workouts() -> Result<()> {
    let workouts = load_test_data("workouts.json")?;
    assert!(workouts.is_object());
    Ok(())
}
