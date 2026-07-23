KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
NOTIFICATION_TOPIC = "notifications.delivery"
NOTIFICATION_DLQ_TOPIC = "notifications.dlq"

MAX_RETRY_COUNT = 3

RETRY_DELAY_SECONDS = {1: 10, 2: 30, 3: 60}

"""
docker exec -it notification-kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic notifications.delivery --partitions 3 --replication-factor 1


docker exec -it notification-kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic notifications.dlq --partitions 3 --replication-factor 1

"""
