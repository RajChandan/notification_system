KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
NOTIFICATION_TOPIC = "notifications.delivery"


"""
docker exec -it notification-kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic notifications.delivery --partitions 3 --replication-factor 1
"""
