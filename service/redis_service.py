import time
import uuid
import redis


class RedisService(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, url):
        self.pool = redis.ConnectionPool.from_url(url, decode_responses=True)
        self._connection = None

    @property
    def connection(self):
        if self._connection is None:
            self._connection = redis.Redis(connection_pool=self.pool)
        return self._connection
    
    def get(self, key) -> str:
        return self.connection.get(key)

    def hgetall(self, key: str) -> dict:
        return self.connection.hgetall(key)   

    def hget(self, key: str, field: str) -> str:
        return self.connection.hget(key, field)
    
    def set(self, key: str, value: str):
        self.connection.set(key, value)
    
    def hset(self, key: str, field: str, value: str):
        self.connection.hset(key, field, value)
    
    def hmset(self, key: str, mapping: dict):
        self.connection.hmset(key, mapping)

    def hdel(self, key: str, field: str):
        self.connection.hdel(key, field)
    
    def delete(self, key: str):
        self.connection.delete(key)
    
    def expire(self, key: str, expire_time: int):
        self.connection.expire(key, expire_time)

    def get_lock(self, key: str, ex_time=30, value: str = None, sleep: int =1) -> str:
        """获锁"""
        if not value:
            value = str(uuid.uuid4())
        while True:
            if self.connection.set(key, value, nx=True, ex=ex_time):
                return value
            time.sleep(sleep)

    def unlock(self, key, value):
        """解锁"""
        result = self.get(key)
        if result == value:
            self.delete(key)

    def close(self):
        if self._connection:
            self._connection.close()
            self._connection = None


class RedisServiceA(object):

    def __init__(self, url):
        self.pool = redis.ConnectionPool.from_url(url, decode_responses=True)
        self._conn = None

    @property
    def conn(self):
        if self._conn is None or self._conn.closed:
            self._conn = redis.Redis(connection_pool=self.pool)
        return self._conn

    def set(self, key, value):
        self.conn.set(key, json.dumps(value))

    def hset(self, key, field, value):
        self.conn.hset(key, field, value)

    def hmset(self, key, mapping):
        self.conn.hmset(key, mapping)

    def delete(self, key):
        self.conn.delete(key)

    def expire(self, key, time):
        self.conn.expire(key, time)

    def lock(self, key, _time=30, value=None, sleep=1) -> str:
        """锁"""
        if value is None:
            value = str(uuid.uuid4())
        while True:
            if self.conn.set(key, value, nx=True, ex=_time):
                return value
            time.sleep(sleep)

    def unlock(self, key, value):
        """解锁"""
        result = self.conn.get(key)
        if result == value:
            self.conn.delete(key)

    def close(self):
        if self._conn and not self._conn.closed:
            self._conn.close()
        self.pool = self._conn = None


class Lock(object):

    def __init__(self, redis_service: RedisService):
        self.redis_service = redis_service

    def __enter__(self):
        self.lock_key = str(uuid.uuid4())
        self.redis_service.lock(self.lock_key, value=self.lock_key)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.redis_service.unlock(self.lock_key, self.lock_key)
