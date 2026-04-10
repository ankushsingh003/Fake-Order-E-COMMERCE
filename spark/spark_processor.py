from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, window, count, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType, TimestampType
import os

# Define Schema based on producer's json schema
schema = StructType([
    StructField("order_id", StringType(), True),
    StructField("user_id", StringType(), True),
    StructField("product_id", StringType(), True),
    StructField("product_name", StringType(), True),
    StructField("category", StringType(), True),
    StructField("amount", DoubleType(), True),
    StructField("quantity", IntegerType(), True),
    StructField("payment_method", StringType(), True),
    StructField("ip_address", StringType(), True),
    StructField("timestamp", StringType(), True)
])

def main():
    # Configuration from environment or defaults
    kafka_bootstrap_servers = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092")
    postgres_db = os.environ.get("POSTGRES_DB", "ecommerce_orders")
    postgres_user = os.environ.get("POSTGRES_USER", "postgres")
    postgres_password = os.environ.get("POSTGRES_PASSWORD", "postgres")
    postgres_url = f"jdbc:postgresql://localhost:5432/{postgres_db}" # If running outside docker
    
    # Initialize Spark Session
    # Including both Kafka and Postgres JDBC packages
    spark = SparkSession.builder \
        .appName("RealTimeOrderProcessing") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.7.2") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("ERROR")

    print(f"Reading from Kafka topic 'orders' at {kafka_bootstrap_servers}...")

    # 1. Read from Kafka
    raw_df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
        .option("subscribe", "orders") \
        .option("startingOffsets", "latest") \
        .load()

    # 2. Parse JSON and Cast Types, assign Watermark for stateful processing
    parsed_df = raw_df.selectExpr("CAST(value AS STRING)") \
        .select(from_json(col("value"), schema).alias("data")) \
        .select("data.*") \
        .withColumn("timestamp", col("timestamp").cast(TimestampType())) \
        .withWatermark("timestamp", "1 minute")

    # 3. Feature Engineering: Windowed Aggregations (orders_per_user_last_minute)
    # This identifies bursts of orders, which is a fraud indicator
    orders_per_user = parsed_df \
        .groupBy(
            window(col("timestamp"), "1 minute", "30 seconds"),
            col("user_id")
        ).count() \
        .withColumnRenamed("count", "orders_per_user_1m")

    # Join back to the main stream to enrich with the feature
    # Note: Stream-Stream join requires watermarking on both sides
    enriched_df = parsed_df.join(
        orders_per_user,
        expr="""
            parsed_df.user_id = orders_per_user.user_id AND
            parsed_df.timestamp >= window.start AND
            parsed_df.timestamp < window.end
        """,
        "left"
    ).select(
        parsed_df["*"],
        col("orders_per_user_1m")
    ).fillna(0)

    # 4. Filter for high-risk orders (Placeholder logic)
    # Amount > 500 OR more than 5 orders in a minute
    high_risk_orders = enriched_df.filter(
        (col("amount") > 500) | (col("orders_per_user_1m") > 5)
    )

    # 5. Output sinks
    # a) Console sink for monitoring
    console_query = high_risk_orders \
        .writeStream \
        .outputMode("append") \
        .format("console") \
        .option("truncate", "false") \
        .start()

    # b) PostgreSQL sink (using foreachBatch as standard Postgres sink isn't streaming native)
    def write_to_postgres(batch_df, batch_id):
        batch_df.write \
            .format("jdbc") \
            .option("url", postgres_url) \
            .option("dbtable", "processed_orders") \
            .option("user", postgres_user) \
            .option("password", postgres_password) \
            .option("driver", "org.postgresql.Driver") \
            .mode("append") \
            .save()

    print("Starting PostgreSQL Sink...")
    postgres_query = high_risk_orders \
        .writeStream \
        .foreachBatch(write_to_postgres) \
        .option("checkpointLocation", "storage/checkpoints/spark_orders") \
        .start()

    spark.streams.awaitAnyTermination()

if __name__ == "__main__":
    main()

