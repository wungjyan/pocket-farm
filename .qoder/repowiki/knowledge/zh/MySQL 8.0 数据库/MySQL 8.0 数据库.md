---
kind: external_dependency
name: MySQL 8.0 数据库
slug: mysql-8
category: external_dependency
category_hints:
    - vendor_identity
scope:
    - '**'
---

项目使用 MySQL 8.0（utf8mb4）作为唯一持久化存储，通过 docker-compose.yml 在本地启动。后端连接字符串格式为 `mysql+aiomysql://...`，默认数据库名、账号密码可通过同名环境变量覆盖，数据持久化在命名卷 `mysql_data` 中。MVP 不使用 Redis/Celery/RabbitMQ/Kafka/Elasticsearch 等中间件，所有状态落库。