import asyncio
import httptools
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s: %(levelname)s: %(message)s")
log = logging.getLogger(__name__)
HTTP_CONTEXT = b'HTTP/1.0 200 OK\r\nContent-Type: application/json; charset=utf-8\r\nContent-Length: %d\r\nConnection: close\r\n\r\n%b'
routes = {}


class HttpProtocol(asyncio.Protocol):

    def __init__(self, loop):
        self.parser = None
        self.request = None
        self.transport = None
        self.url = None
        self.headers = None
        self.loop = loop

    def connection_made(self, transport):
        """连接回调"""
        self.transport = transport

    def data_received(self, data):
        """接收数据"""
        if self.parser is None:
            self.headers, self.parser = {}, httptools.HttpRequestParser(self)
        try:
            self.parser.feed_data(data)
        except httptools.parser.errors.HttpParserError as e:
            self.bail_out("Invalid request data, connection closed ({})".format(e))

    def connection_lost(self, exc):
        """连接关闭回调"""
        self.transport.close()
        self.parser = None
        self.request = None
        self.transport = None
        self.loop = None

    def on_url(self, url):
        self.url = url

    def on_body(self, body):
        self.request = body

    def on_header(self, name, value):
        self.headers[name.decode()] = value.decode()

    def on_headers_complete(self):
        """认证"""

    def on_message_complete(self):
        self.loop.create_task(self.request_handler())

    async def request_handler(self):
        try:
            handler = routes.get(self.url)
            try:
                response_body = await handler(self.request)
            except Exception as e:
                response_body = b"An error occured while handling an error"
        except Exception as e:
            response_body = b"Not found"
        try:
            self.transport.write(HTTP_CONTEXT %((len(response_body), response_body)))
        except Exception as e:
            self.bail_out(f"Writing request failed, connection closed {e}")

    @staticmethod
    def bail_out(message):
        log.error(message)


def run(host="127.0.0.1", port=8000, debug=False):
    if debug:
        log.setLevel(logging.DEBUG)
    log.info(f'Go in\' Fast http://{host}:{port}')
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    server_coroutine = loop.create_server(lambda: HttpProtocol(loop), host, port)
    http_server = loop.run_until_complete(server_coroutine)
    try:
        loop.run_forever()
    finally:
        log.info("Stop requested, draining connections...")
        http_server.close()
        loop.run_until_complete(http_server.wait_closed())
        loop.close()
        log.info("Server Stopped")


def router(uri: bytes):
    def response(handler):
        routes[uri] = handler
        return handler
    return response
