import asyncio
import base64
import hashlib
import hmac
import logging
import time

import httptools
import ujson

logging.basicConfig(level=logging.INFO, format="%(asctime)s: %(levelname)s: %(message)s")
log = logging.getLogger(__name__)
try:
    import uvloop
    loop = uvloop.new_event_loop()
except:
    loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)


def new_sha_password(body: bytes) -> str:
    """生成单向不可"""
    sha = hashlib.sha1()
    # 前后加盐
    sha.update(b"abc")
    sha.update(body)
    # 前后加盐
    sha.update(b"abc")
    return sha.hexdigest()


def new_token(body):
    body = base64.b64encode(ujson.dumps(body).encode())
    return new_sign(body) + body.decode()


def new_sign(body: bytes):
    return hmac.HMAC(b'keaaeay', body, hashlib.md5).hexdigest()


def verify_sign(body: bytes, auth: bytes) -> int:
    if not isinstance(body, bytes) or len(body) < 32:
        return 0
    sign, user = body[:32], body[32:]
    sign2 = new_sign(user).encode()
    print(user, sign, sign2)
    if not hmac.compare_digest(sign, sign2):
        return 0
    user: list = ujson.loads(base64.b64decode(user))
    expire_time = user.pop(0)
    user_id = user.pop(0)
    auths = user.pop(0)
    if expire_time < time.time() or auth not in auths:
        # token过期
        return 0
    return user_id


class ApiException(Exception):

    def __init__(self, status: bytes, msg: bytes):
        self.status = status
        self.msg = msg


class Request(object):

    def __init__(self):
        self._body = {}
        self._user_id = None
        self._authority = []

    def set_user(self, user_id: int, authority: list):
        self._user_id = user_id
        self._authority = authority

    @property
    def user_id(self) -> int:
        return self._user_id

    @user_id.setter
    def user_id(self, v):
        self.user_id = v

    @property
    def authority(self) -> list:
        return self._authority

    @authority.setter
    def _authority(self, v):
        self._authority = v

    @property
    def body(self):
        return self._body

    @body.setter
    def body(self, v: dict):
        self._body = v


class HttpProtocol(asyncio.Protocol):
    http_context = b'HTTP/1.0 %b \r\nContent-Type: application/json; charset=utf-8\r\nConnection: close\r\nContent-Length: %d\r\n\r\n%b'
    router = {}

    def __init__(self):
        self.body = {}
        self.transport = self.url = self.token = None
        self.parser = httptools.HttpRequestParser(self)

    def connection_made(self, transport):
        """连接回调"""
        log.info(f"connection_made: {type(transport)}")
        self.transport = transport

    def data_received(self, data):
        """接收数据"""
        log.info(f"data_received: {data}")
        try:
            self.parser.feed_data(data)
        except httptools.parser.errors.HttpParserError as e:
            log.error(f"Invalid request data, connection closed ({e})")

    def connection_lost(self, exc):
        """连接关闭回调"""
        self.transport.close()

    def on_url(self, url: bytes):
        log.info(f"on_url: {url}")
        self.url = url

    def on_body(self, body: bytes):
        if body:
            self.body = ujson.loads(body)

    def on_header(self, name: bytes, value: bytes):
        if name == b'Authorization':
            self.token = value

    async def request_handler(self):
        try:
            handler: HandlerInterface = self.router[self.url]
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
            log.exception(f"API[{self.url}]出错：{e}")
            self.write_body(b'500', b'system error')

    def on_message_complete(self):
        loop.create_task(self.request_handler())

    def write_body(self, code: bytes, body: bytes):
        try:
            self.transport.write(self.http_context % (code, len(body), body))
        except Exception as e:
            log.error(f"写请求失败, 连接关闭"
                      f" {e}")

    @classmethod
    def run(cls, router: dict, port=8000):
        log.info(f'Go in\' Fast http://127.0.0.1:8000')
        cls.router = router
        server_coroutine = loop.create_server(lambda: cls(), '0.0.0.0', port)
        http_server = loop.run_until_complete(server_coroutine)
        try:
            loop.run_forever()
        finally:
            log.info("Stop requested, draining connections...")
            http_server.close()
            loop.run_until_complete(http_server.wait_closed())
            loop.close()
            log.info("Server Stopped")


class HandlerInterface(object):

    # 权限认证，默认不拦截 user_id 为空
    auth: bytes = b''

    def __init__(self, body: dict, user_id: int = None):
        self.body = body
        self.user_id = user_id

    def call(self):
        """请求执行逻辑"""
