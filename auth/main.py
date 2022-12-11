import aioredis as aioredis
from sanic import Sanic, response, Request

app = Sanic(__name__)


@app.post('/login')
async def login(request: Request):
    params = request.json
    username = params.get("username")
    password = params.get("password")

    return response.json({'code': 'world'})


@app.listener('before_server_start')
async def setup_db_redis(app, loop):
    app.db = await aiomysql.create_pool(
    host=srvconf.mysql_host,
    port=srvconf.mysql_port,
    user=srvconf.mysql_user,
    password=srvconf.mysql_password,
    db=srvconf.database, loop=loop, charset='utf8', autocommit=True)

    app.redis_pool = await aioredis.create_pool(
        (srvconf.redis_host, srvconf.redis_port),
        minsize=5,
        maxsize=10,
        loop=loop
    )

@app.listener('after_server_stop')
async def close_db_redis(app, loop):
    app.db.close()
    await app.db.wait_closed()

    app.redis_pool.close()
    await app.redis_pool.wait_closed()

if __name__ == '__main__':
    app.run()
