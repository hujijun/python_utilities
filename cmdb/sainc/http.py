import asyncio
import logging
import httptools
import ujson

from cmdb.sainc.utils import verify_sign


class ApiException(Exception):

    def __init__(self, status: bytes, msg: bytes):
        self.status = status
        self.msg = msg


class HttpProtocol(asyncio.Protocol):
    http_context = b'HTTP/1.0 %b \r\nContent-Type: application/json; charset=utf-8\r\nConnection: close\r\nContent-Length: %d\r\n\r\n%b'
    http = None

    def __init__(self):
        self.body = {}
        self.transport = self.url = self.token = None
        self.parser = httptools.HttpRequestParser(self)

    def connection_made(self, transport):
        """连接回调"""
        self.transport = transport

    def data_received(self, data):
        """接收数据"""
        logging.info(f"data_received: {data}")
        try:
            self.parser.feed_data(data)
        except httptools.parser.errors.HttpParserError as e:
            logging.error(f"Invalid request data, connection closed ({e})")

    def connection_lost(self, exc):
        """连接关闭回调"""
        self.transport.close()

    def on_url(self, url: bytes):
        self.url = url

    def on_body(self, body: bytes):
        if body:
            self.body = ujson.loads(body)

    def on_header(self, name: bytes, value: bytes):
        if name == b'authorization':
            self.token = value


    async def request_handler(self):
        try:
            handler: HandlerInterface = self.http.router[self.url]
        except Exception as e:
            self.write_body(b'404', b'404 Not found')
            return
        if handler.auth:
            user_id = verify_sign(self.token, handler.auth)
            if not user_id:
                self.write_body(b'401 Unauthorized', b'Unauthorized')
                return
        else:
            user_id = None
        try:
            result = handler(self.body, user_id).call()
            self.write_body(b'200 ok', ujson.dumps(result).encode())
        except ApiException as a:
            self.write_body(a.status, a.msg)
        except Exception as e:
            logging.exception(f"API[{self.url}]出错：{e}")
            self.write_body(b'500', b'system error')

    def on_message_complete(self):
        self.http.loop.create_task(self.request_handler())

    def write_body(self, code: bytes, body: bytes):
        try:
            self.transport.write(self.http_context % (code, len(body), body))
        except Exception as e:
            logging.error(f"写请求失败, 连接关闭 {e}")


class HandlerInterface(object):

    # 权限认证，默认不拦截 user_id 为空
    auth: str = ''

    def __init__(self, body: dict, user_id: int = None):
        self.body = body
        self.user_id = user_id

    def call(self):
        """请求执行逻辑"""


class HttpService(object):

    def __init__(self, router: dict):
        self.router = router
        self.http_server = None
        try:
            import uvloop
            self.loop = uvloop.new_event_loop()
        except:
            self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def run(self, port=8001):
        logging.info(f'Go in\' Fast http://127.0.0.1:{port}')
        HttpProtocol.http = self
        server_coroutine = self.loop.create_server(lambda: HttpProtocol(), '0.0.0.0', port)
        self.http_server = self.loop.run_until_complete(server_coroutine)
        try:
            self.loop.run_forever()
        finally:
            self.close()

    def close(self):
        logging.info("Server Stopped")
        if self.http_server:
            self.http_server.close()
            self.loop.run_until_complete(self.http_server.wait_closed())
        self.loop.close()
