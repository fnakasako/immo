-- Health data schema for activity tracking

-- Health metrics table for detailed health data
CREATE TABLE IF NOT EXISTS health_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,            -- References events.id
    metric_type TEXT NOT NULL,            -- 'heart_rate', 'steps', 'sleep', etc.
    value REAL NOT NULL,                  -- The actual measurement
    unit TEXT NOT NULL,                   -- 'bpm', 'count', 'minutes', etc.
    start_time INTEGER NOT NULL,          -- Unix epoch in milliseconds
    end_time INTEGER NOT NULL,            -- For duration-based metrics
    source_device TEXT,                   -- Device that provided the data
    accuracy INTEGER,                     -- Optional accuracy level (0-100)
    metadata TEXT,                        -- Additional JSON metadata
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
);

-- Index for efficient joins with events table
CREATE INDEX IF NOT EXISTS idx_health_metrics_event 
    ON health_metrics(event_id);

CREATE INDEX IF NOT EXISTS idx_health_metrics_type_time 
    ON health_metrics(metric_type, start_time);

-- Workouts table for tracking exercise sessions
CREATE TABLE IF NOT EXISTS workouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,            -- References events.id
    workout_type TEXT NOT NULL,           -- 'running', 'cycling', 'swimming', etc.
    start_time INTEGER NOT NULL,
    end_time INTEGER NOT NULL,
    distance REAL,                        -- In meters
    calories REAL,                        -- Calories burned
    avg_heart_rate REAL,                  -- Average BPM
    max_heart_rate REAL,                  -- Max BPM
    metadata TEXT,                        -- Additional JSON metadata
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_workouts_event 
    ON workouts(event_id);

CREATE INDEX IF NOT EXISTS idx_workouts_type_time 
    ON workouts(workout_type, start_time);

-- Sleep tracking table
CREATE TABLE IF NOT EXISTS sleep_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,            -- References events.id
    start_time INTEGER NOT NULL,
    end_time INTEGER NOT NULL,
    quality TEXT NOT NULL,                -- 'deep', 'light', 'rem', 'awake'
    duration INTEGER NOT NULL,            -- In minutes
    interruptions INTEGER,                -- Number of wake periods
    metadata TEXT,                        -- Additional JSON metadata
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_sleep_sessions_event 
    ON sleep_sessions(event_id);

CREATE INDEX IF NOT EXISTS idx_sleep_sessions_time 
    ON sleep_sessions(start_time, end_time);

-- Views for health data analysis
CREATE VIEW IF NOT EXISTS v_daily_health_metrics AS
SELECT 
    date(hm.start_time/1000, 'unixepoch') as day,
    hm.metric_type,
    avg(hm.value) as avg_value,
    min(hm.value) as min_value,
    max(hm.value) as max_value,
    count(*) as reading_count
FROM health_metrics hm
GROUP BY 
    date(hm.start_time/1000, 'unixepoch'),
    hm.metric_type;

CREATE VIEW IF NOT EXISTS v_workout_summary AS
SELECT 
    date(w.start_time/1000, 'unixepoch') as day,
    w.workout_type,
    count(*) as workout_count,
    sum(w.duration) as total_duration,
    sum(w.distance) as total_distance,
    sum(w.calories) as total_calories,
    avg(w.avg_heart_rate) as avg_heart_rate
FROM workouts w
GROUP BY 
    date(w.start_time/1000, 'unixepoch'),
    w.workout_type;

-- Pre-defined health event types
INSERT OR IGNORE INTO event_types (source, event_type, schema, created_at)
VALUES 
    ('health', 'heart_rate', 
     '{"type":"object","properties":{"bpm":{"type":"number"}}}',
     strftime('%s', 'now')),
    ('health', 'steps',
     '{"type":"object","properties":{"count":{"type":"number"}}}',
     strftime('%s', 'now')),
    ('health', 'workout',
     '{"type":"object","properties":{"type":{"type":"string"},"duration":{"type":"number"}}}',
     strftime('%s', 'now')),
    ('health', 'sleep',
     '{"type":"object","properties":{"quality":{"type":"string"},"duration":{"type":"number"}}}',
     strftime('%s', 'now'));

-- Default retention policy for health data
INSERT OR IGNORE INTO retention_policies 
    (source, retention_days, summary_table, created_at, updated_at)
VALUES 
    ('health', 365, 'event_statistics', 
     strftime('%s', 'now'), strftime('%s', 'now'));
