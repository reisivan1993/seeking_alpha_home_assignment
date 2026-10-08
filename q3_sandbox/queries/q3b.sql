WITH params AS (
    SELECT CURRENT_DATE - 1 AS last_day
),
days AS (
    SELECT d::date AS activity_date
    FROM params p,
         generate_series(p.last_day - 29, p.last_day, INTERVAL '1 day') AS d
),
active_users AS (
    SELECT DISTINCT e.event_ts::date AS activity_date, e.user_id
    FROM events e, params p
    WHERE e.user_id IS NOT NULL
      AND e.event_ts >= p.last_day - 29
      AND e.event_ts <  p.last_day + 1
),
valid_subscriptions AS (                                              -- skip invalid rows: daterange() raises an error
    SELECT user_id, product,                                           -- when end_date is before start_date
           daterange(start_date, end_date, '[)') AS active_period     -- start included, end excluded; NULL end = no end
    FROM subscriptions
    WHERE start_date IS NOT NULL
      AND (end_date IS NULL OR end_date > start_date)
),
paying_active AS (                                                     -- active users paying for any product
    SELECT DISTINCT a.activity_date, a.user_id
    FROM active_users a
    JOIN valid_subscriptions s
      ON  s.user_id = a.user_id
      AND s.active_period @> a.activity_date
)
SELECT d.activity_date,
       COUNT(a.user_id)                                                  AS active_users,
       COUNT(p.user_id)                                                  AS paying_active_users,
       ROUND(100.0 * COUNT(p.user_id) / NULLIF(COUNT(a.user_id), 0), 2) AS pct_paying
FROM days d
LEFT JOIN active_users  a ON a.activity_date = d.activity_date
LEFT JOIN paying_active p ON p.activity_date = a.activity_date
                         AND p.user_id       = a.user_id
GROUP BY d.activity_date
ORDER BY d.activity_date;
