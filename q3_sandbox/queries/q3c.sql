WITH valid_subscriptions AS (
    SELECT subscription_id, user_id, product, start_date, end_date,
           daterange(start_date, end_date, '[)') AS active_period   -- start included, end excluded; NULL end = no end
    FROM subscriptions
    WHERE start_date IS NOT NULL
      AND (end_date IS NULL OR end_date > start_date)                -- drop zero-length and inverted periods (reported separately)
)
SELECT a.user_id,
       a.subscription_id AS subscription_id_1,
       a.product         AS product_1,
       a.start_date      AS start_date_1,
       a.end_date        AS end_date_1,
       b.subscription_id AS subscription_id_2,
       b.product         AS product_2,
       b.start_date      AS start_date_2,
       b.end_date        AS end_date_2,
       a.product = b.product                    AS same_product,
       lower(a.active_period * b.active_period) AS overlap_start,
       upper(a.active_period * b.active_period) AS overlap_end   -- first day no longer overlapping; NULL = still overlapping
FROM valid_subscriptions a
JOIN valid_subscriptions b
  ON  a.user_id = b.user_id
  AND a.subscription_id < b.subscription_id                      -- each pair once, never a subscription with itself
  AND a.active_period && b.active_period                         -- the periods share at least one day
ORDER BY a.user_id, a.subscription_id, b.subscription_id;
