-- Tables from the assignment. Constraints are deliberately loose so bad rows
-- (NULL start_date, end_date before start_date, events from unknown users) can be loaded and tested.
DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS subscriptions;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    user_id TEXT PRIMARY KEY
);

CREATE TABLE subscriptions (
    subscription_id INTEGER PRIMARY KEY,
    user_id         TEXT NOT NULL,
    product         TEXT NOT NULL,      -- 'pro' / 'mp'
    start_date      DATE,               -- first active date
    end_date        DATE                -- first inactive date; NULL = currently active
);

CREATE TABLE events (
    event_ts   TIMESTAMP NOT NULL,      -- UTC
    user_id    TEXT,                    -- NULL for anonymous events
    event_name TEXT NOT NULL
);

CREATE INDEX events_event_ts_idx ON events (event_ts);
CREATE INDEX subscriptions_user_id_idx ON subscriptions (user_id);
