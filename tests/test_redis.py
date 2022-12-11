from service.redis_service import RedisService


def test_get_set(key, value):
    a = RedisService("redis://216.127.177.42:6379")
    a.set(key, value)
    print(a.get(key))


if __name__ == "__main__":
    test_get_set('ss', "ssaa")
