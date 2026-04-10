#!/bin/bash

# Create 'orders' topic with 3 partitions and 1 replication factor
docker exec kafka kafka-topics --create \
    --topic orders \
    --bootstrap-server localhost:9092 \
    --partitions 3 \
    --replication-factor 1 \
    --if-not-exists

echo "Kafka topics created successfully."
