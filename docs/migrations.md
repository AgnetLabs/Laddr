# Kafka Migration Guide

This document describes the migration from **Redis** to **Kafka** as the message broker for the Laddr multi-agent system.  
Kafka provides persistent messaging, horizontal scaling, and higher throughput for production workloads.

---

## Overview

Kafka offers durable, highly scalable messaging suitable for production.  
This guide walks through **architecture changes**, **configuration updates**, **deployment**, **verification**, and **rollback** steps to migrate from Redis to Kafka.

---

## Architecture Changes

### Before (Redis)
- Message broker: Redis (pub/sub)  
- Persistence: Ephemeral (lost on restart)  
- Scaling: Limited by single instance  
- Use case: Development and lightweight deployments  

### After (Kafka)
- Message broker: Apache Kafka with Zookeeper  
- Persistence: Durable with configurable retention  
- Scaling: Horizontal with partitions and consumer groups  
- Use case: Production deployments with high throughput  

### Topic Structure
- `laddr.tasks.<agent_name>` – Task queue for each agent  
- `laddr.responses` – Response messages  

Consumer groups follow the pattern:  
`laddr-<agent_name>-workers`

---

## Configuration Changes

### Environment Variables (`.env`)

```bash
# Message Broker Configuration (Kafka)
KAFKA_BOOTSTRAP=kafka:9092
QUEUE_BACKEND=kafka

# Previous Redis configuration (commented out)
# REDIS_URL=redis://redis:6379/0
# QUEUE_BACKEND=redis
```

> **Note:**  
> Use `kafka:9092` for client connections; `kafka:29092` is for inter-broker communication only.

### Docker Compose Services
- **Zookeeper** – Port 2181  
- **Kafka** – Ports 9092 (client), 9101 (metrics)  
- **Kafka UI** – Port 8080 (`http://localhost:8080`)

---

## Deployment Instructions

### Prerequisites
Install the Kafka dependencies:

```bash
pip install aiokafka>=0.11.0
# OR
pip install laddr[kafka]
```

### Starting the System

```bash
cd /path/to/your/project
docker-compose down
docker-compose up -d
```

Monitor system status:

```bash
docker-compose ps
docker-compose logs -f kafka
```

---

## Verification Steps

### Check Kafka Topics

```bash
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092
```

Expected topics:
- `laddr.tasks.coordinator`
- `laddr.tasks.researcher`
- `laddr.tasks.analyzer`
- `laddr.tasks.writer`
- `laddr.tasks.validator`
- `laddr.responses`

### Monitor Worker Logs

```bash
docker-compose logs -f coordinator_worker researcher_worker analyzer_worker writer_worker validator_worker
```

### Test via API

```bash
curl -X POST http://localhost:8000/api/v1/run \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_name": "test_workflow",
    "initial_task": {
      "agent": "researcher",
      "inputs": {"query": "test"}
    }
  }'
```

---

## Scaling

To scale workers horizontally:

```bash
docker-compose up -d --scale coordinator_worker=3 --scale researcher_worker=3 --scale analyzer_worker=2 --scale writer_worker=2 --scale validator_worker=2
```

Kafka automatically balances partitions across consumers, enabling seamless horizontal scaling.

---

## Rollback to Redis

```bash
REDIS_URL=redis://redis:6379/0
QUEUE_BACKEND=redis
# Comment out Kafka config
# KAFKA_BOOTSTRAP=kafka:9092
```

Update your `docker-compose.yml` to re-enable Redis, remove Kafka and Zookeeper, then restart:

```bash
docker-compose down && docker-compose up -d
```

---

## Summary

- Kafka improves **reliability**, **scaling**, and **persistence**.  
- Docker Compose now includes **Kafka**, **Zookeeper**, and **Kafka UI**.  
- Redis remains available for quick rollback.  

After migration, access Kafka UI at:  
`http://localhost:8080`  
to monitor system health and performance.
