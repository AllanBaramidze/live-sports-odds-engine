import redis


# basic connection
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# decode_responses=True -> returns strings instead of bytes
# db=0 -> valkey supports databases 0-15 by defautl

# test connection
print(r.ping()) # true

# alternative connection
r = redis.from_url('redis://localhost:6379/0', decode_responses=True)

print(r.ping()) # true


# Connection Pooling
pool = redis.ConnectionPool(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True,
    max_connections=10
)

r = redis.Redis(connection_pool=pool)