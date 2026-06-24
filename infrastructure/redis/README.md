# redis

Redis runs with the stock `redis:7-alpine` image (no custom config yet).
Used for running jobs, the agent queue, temporary state, and locks.

Add a `redis.conf` here and mount it from `docker-compose.yml` if/when we need
custom persistence or eviction policies.
