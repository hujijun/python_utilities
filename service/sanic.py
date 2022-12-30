import asyncio
import httptools
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s: %(levelname)s: %(message)s")
log = logging.getLogger(__name__)


class HttpProtocol(asyncio.Protocol):
    http_context = b'HTTP/1.0 200 OK\r\nContent-Type: application/json; charset=utf-8\r\nConnection: close\r\nContent-Length: %d\r\n\r\n%b'

    def __init__(self, sanic):
        self.sanic = sanic
        self.request = self.transport = self.url = self.token = None
        self.parser = httptools.HttpRequestParser(self)

    def connection_made(self, transport):
        """连接回调"""
        log.error(f"connection_made: {type(transport)}")
        self.transport = transport

    def data_received(self, data):
        """接收数据"""
        log.error(f"data_received: {data}")
        try:
            self.parser.feed_data(data)
        except httptools.parser.errors.HttpParserError as e:
            log.error(f"Invalid request data, connection closed ({e})")

    def connection_lost(self, exc):
        """连接关闭回调"""
        self.transport.close()
        log.error("connection_lost")

    def on_url(self, url):
        log.error(f"on_url{url}")
        self.url = url

    def on_body(self, body: bytes):
        log.error(f"on_body{body}")
        self.request = body

    def on_header(self, name: bytes, value: bytes):
        log.error(f"on_header{name, value}")
        if name == b'Authorization':
            self.token = value.decode()

    def on_message_complete(self):
        log.error('on_message_complete')
        self.sanic.loop.create_task(self.request_handler())

    async def request_handler(self):
        try:
            handler = self.sanic.routes[self.url]
            try:
                response_body = await handler(self.request)
            except Exception as e:
                response_body = b"An error occured while handling an error"
        except Exception as e:
            response_body = b"404 Not found"
        try:
            self.transport.write(self.http_context % (len(response_body), response_body))
        except Exception as e:
            log.error(f"写请求失败, 连接关闭 {e}")


class Sanic(object):

    def __init__(self):
        self.routes = {}
        try:
            import uvloop
            self.loop = uvloop.new_event_loop()
        except:
            self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def router(self, uri: bytes):
        def response(handler):
            self.routes[uri] = handler
            return handler
        return response

    def run(self, host="127.0.0.1", port=8000, debug=False):
        if debug:
            log.setLevel(logging.DEBUG)
        log.info(f'Go in\' Fast http://{host}:{port}')
        server_coroutine = self.loop.create_server(lambda: HttpProtocol(self), host, port)
        http_server = self.loop.run_until_complete(server_coroutine)
        try:
            self.loop.run_forever()
        finally:
            log.info("Stop requested, draining connections...")
            http_server.close()
            self.loop.run_until_complete(http_server.wait_closed())
            self.loop.close()
            log.info("Server Stopped")
