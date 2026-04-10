-- 1. Live Order Count (Per Minute)
SELECT 
    date_trunc('minute', timestamp) as minute,
    count(*) as order_count
FROM processed_orders
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY 1
ORDER BY 1 DESC;

-- 2. Revenue by Region (Real-Time)
-- Note: 'region' could be derived from ip_address or added to producer.
-- For now, using Category as a proxy for revenue distribution.
SELECT 
    category,
    sum(amount) as total_revenue
FROM processed_orders
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY 1
ORDER BY 2 DESC;

-- 3. Fraud Alerts Feed
SELECT 
    timestamp,
    order_id,
    user_id,
    amount,
    orders_per_user_1m,
    fraud_score
FROM processed_orders
WHERE is_fraud = TRUE
ORDER BY timestamp DESC
LIMIT 10;

-- 4. Top Products by Volume
SELECT 
    product_name,
    count(*) as volume
FROM processed_orders
WHERE timestamp > NOW() - INTERVAL '6 hours'
GROUP BY 1
ORDER BY 2 DESC
LIMIT 5;

-- 5. Demand Forecast vs Actuals
-- This query joins the actual orders with the predictions
WITH actuals AS (
    SELECT 
        date_trunc('hour', timestamp) as hr,
        count(*) as actual_volume
    FROM processed_orders
    WHERE timestamp > NOW() - INTERVAL '6 hours'
    GROUP BY 1
),
forecasts AS (
    SELECT 
        forecast_time,
        predicted_orders
    FROM demand_forecast
    WHERE forecast_time > NOW() - INTERVAL '6 hours'
      AND forecast_time < NOW() + INTERVAL '6 hours'
)
SELECT 
    COALESCE(f.forecast_time, a.hr) as time,
    a.actual_volume,
    f.predicted_orders
FROM forecasts f
FULL OUTER JOIN actuals a ON f.forecast_time = a.hr
ORDER BY 1;
