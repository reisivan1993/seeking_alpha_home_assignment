WITH params AS (
    SELECT CURRENT_DATE - 1 AS last_day                                -- yesterday (session time zone = UTC)
),
days AS (                                                              -- the 30 dates, so empty days still appear
    SELECT d::date AS activity_date
    FROM params p,
         generate_series(p.last_day - 29, p.last_day, INTERVAL '1 day') AS d
),
active_users AS (                                                      -- one row per (date, user)
    SELECT DISTINCT e.event_ts::date AS activity_date, e.user_id
    FROM events e, params p
    WHERE e.user_id IS NOT NULL                                        -- anonymous events don't count
      AND e.event_ts >= p.last_day - 29                                -- filter on the raw timestamp
      AND e.event_ts <  p.last_day + 1                                 -- so an index on event_ts can be used
),
valid_subscriptions AS (                                              -- skip invalid rows: daterange() raises an error
    SELECT user_id, product,                                           -- when end_date is before start_date
           daterange(start_date, end_date, '[)') AS active_period     -- start included, end excluded; NULL end = no end
    FROM subscriptions
    WHERE start_date IS NOT NULL
      AND (end_date IS NULL OR end_date > start_date)
),
active_paying AS (                                                     -- one row per (date, user, product)
    SELECT DISTINCT a.activity_date, a.user_id, s.product
    FROM active_users a
    JOIN valid_subscriptions s
      ON  s.user_id = a.user_id
      AND s.active_period @> a.activity_date                           -- subscription active that day
)
SELECT d.activity_date,
       COUNT(DISTINCT ap.user_id)                                    AS paying_active_users,
       COUNT(DISTINCT ap.user_id) FILTER (WHERE ap.product = 'pro') AS pro_paying_active_users,
       COUNT(DISTINCT ap.user_id) FILTER (WHERE ap.product = 'mp')  AS mp_paying_active_users
FROM days d
LEFT JOIN active_paying ap ON ap.activity_date = d.activity_date
GROUP BY d.activity_date
ORDER BY d.activity_date;
